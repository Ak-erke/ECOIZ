import unittest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import SessionToken, User
from app.services.auth import hash_password
from app.services.seed import ensure_seed_data


class BackendAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            future=True,
        )
        cls.SessionLocal = sessionmaker(bind=cls.engine, autoflush=False, autocommit=False, future=True)

        def override_get_db():
            db = cls.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    def setUp(self) -> None:
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        with self.SessionLocal() as db:
            ensure_seed_data(db)

    @classmethod
    def tearDownClass(cls) -> None:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        cls.engine.dispose()

    def test_login_bootstrap_and_chat_flow(self) -> None:
        login = self.client.post(
            "/auth/login",
            json={"email": "user@ecoiz.app", "password": "password123"},
        )
        self.assertEqual(login.status_code, 200)
        token = login.json()["token"]

        bootstrap = self.client.get(
            "/bootstrap",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(bootstrap.status_code, 200)
        bootstrap_body = bootstrap.json()
        self.assertEqual(bootstrap_body["user"]["email"], "user@ecoiz.app")
        self.assertGreaterEqual(len(bootstrap_body["activities"]), 2)
        self.assertGreaterEqual(len(bootstrap_body["chatMessages"]), 1)
        self.assertEqual(len(bootstrap_body["challenges"]), 5)
        self.assertIn("communityImpact", bootstrap_body)
        self.assertGreaterEqual(bootstrap_body["communityImpact"]["totalUsers"], 2)
        self.assertGreaterEqual(bootstrap_body["communityImpact"]["totalActivities"], 2)
        self.assertGreaterEqual(
            bootstrap_body["communityImpact"]["totalPoints"],
            bootstrap_body["user"]["points"],
        )

        chat = self.client.post(
            "/chat/messages",
            json={"text": "Как не забывать про воду?"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(chat.status_code, 201)
        messages = chat.json()["messages"]
        self.assertEqual(len(messages), 2)
        self.assertTrue(messages[0]["isUser"])
        self.assertFalse(messages[1]["isUser"])
        self.assertIn("душ", messages[1]["text"])
        self.assertNotIn("уточни вопрос", messages[1]["text"].lower())

    def test_chat_uses_personalized_fallback_for_next_step_questions(self) -> None:
        login = self.client.post(
            "/auth/login",
            json={"email": "user@ecoiz.app", "password": "password123"},
        )
        self.assertEqual(login.status_code, 200)
        token = login.json()["token"]

        chat = self.client.post(
            "/chat/messages",
            json={"text": "Я сегодня дома, что мне дальше делать?"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(chat.status_code, 201)
        assistant_text = chat.json()["messages"][1]["text"].lower()
        self.assertTrue(any(word in assistant_text for word in ("свет", "душ", "вода", "пласт", "энерг")))
        self.assertNotIn("уточни вопрос", assistant_text)

    def test_chat_analyzes_user_activities_individually(self) -> None:
        login = self.client.post(
            "/auth/login",
            json={"email": "user@ecoiz.app", "password": "password123"},
        )
        self.assertEqual(login.status_code, 200)
        token = login.json()["token"]

        chat = self.client.post(
            "/chat/messages",
            json={"text": "Проанализируй мои активности"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(chat.status_code, 201)
        assistant_text = chat.json()["messages"][1]["text"].lower()
        self.assertIn("активност", assistant_text)
        self.assertTrue(any(word in assistant_text for word in ("категор", "вклад", "последн", "очков")))
        self.assertNotIn("уточни вопрос", assistant_text)

    def test_chat_keeps_context_for_outdoor_follow_up(self) -> None:
        login = self.client.post(
            "/auth/login",
            json={"email": "user@ecoiz.app", "password": "password123"},
        )
        self.assertEqual(login.status_code, 200)
        token = login.json()["token"]

        first = self.client.post(
            "/chat/messages",
            json={"text": "Я хочу выйти погулять, что могу сделать?"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(first.status_code, 201)
        first_text = first.json()["messages"][1]["text"].lower()
        self.assertTrue(any(word in first_text for word in ("гуля", "пеш", "прогул", "бутыл")))

        second = self.client.post(
            "/chat/messages",
            json={"text": "А завтра?"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(second.status_code, 201)
        second_text = second.json()["messages"][1]["text"].lower()
        self.assertIn("завтра", second_text)
        self.assertTrue(any(word in second_text for word in ("пеш", "бутыл", "ритм")))

    def test_error_responses(self) -> None:
        unauthorized = self.client.get(
            "/bootstrap",
            headers={"Authorization": "Bearer invalid-token"},
        )
        self.assertEqual(unauthorized.status_code, 401)
        self.assertEqual(unauthorized.json()["error"], "Missing or invalid bearer token.")

        login = self.client.post(
            "/auth/login",
            json={"email": "user@ecoiz.app", "password": "password123"},
        )
        token = login.json()["token"]

        empty_message = self.client.post(
            "/chat/messages",
            json={"text": "   "},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(empty_message.status_code, 400)
        self.assertEqual(empty_message.json()["error"], "Message text is required.")

    def test_session_rotation_and_expiry(self) -> None:
        first_login = self.client.post(
            "/auth/login",
            json={"email": "user@ecoiz.app", "password": "password123"},
        )
        self.assertEqual(first_login.status_code, 200)
        first_token = first_login.json()["token"]

        second_login = self.client.post(
            "/auth/login",
            json={"email": "user@ecoiz.app", "password": "password123"},
        )
        self.assertEqual(second_login.status_code, 200)
        second_token = second_login.json()["token"]
        self.assertNotEqual(first_token, second_token)

        first_bootstrap = self.client.get(
            "/bootstrap",
            headers={"Authorization": f"Bearer {first_token}"},
        )
        self.assertEqual(first_bootstrap.status_code, 401)

        with self.SessionLocal() as db:
            session = db.get(SessionToken, second_token)
            session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            db.commit()

        expired_bootstrap = self.client.get(
            "/bootstrap",
            headers={"Authorization": f"Bearer {second_token}"},
        )
        self.assertEqual(expired_bootstrap.status_code, 401)

    def test_activity_guardrails_and_real_streaks(self) -> None:
        login = self.client.post(
            "/auth/login",
            json={"email": "user@ecoiz.app", "password": "password123"},
        )
        self.assertEqual(login.status_code, 200)
        token = login.json()["token"]

        bootstrap = self.client.get(
            "/bootstrap",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(bootstrap.status_code, 200)
        before_user = bootstrap.json()["user"]
        before_plastic = next(
            item for item in bootstrap.json()["challenges"] if item["title"] == "3 дня без пластика"
        )

        first_plastic = self.client.post(
            "/activities",
            json={
                "category": "Пластик",
                "title": "Без пакета",
                "co2Saved": 0.05,
                "points": 10,
                "note": "",
                "media": [],
                "shareToNews": False,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(first_plastic.status_code, 201)
        self.assertEqual(first_plastic.json()["user"]["streakDays"], before_user["streakDays"] + 1)

        duplicate_plastic = self.client.post(
            "/activities",
            json={
                "category": "Пластик",
                "title": "Без пакета",
                "co2Saved": 0.05,
                "points": 10,
                "note": "",
                "media": [],
                "shareToNews": False,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(duplicate_plastic.status_code, 409)

        second_plastic = self.client.post(
            "/activities",
            json={
                "category": "Пластик",
                "title": "Многоразовая бутылка",
                "co2Saved": 0.12,
                "points": 20,
                "note": "",
                "media": [],
                "shareToNews": False,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(second_plastic.status_code, 201)
        self.assertEqual(second_plastic.json()["user"]["streakDays"], first_plastic.json()["user"]["streakDays"])
        after_plastic = next(
            item for item in second_plastic.json()["challenges"] if item["title"] == "3 дня без пластика"
        )
        self.assertEqual(after_plastic["currentCount"], before_plastic["currentCount"] + 1)

    def test_custom_activity_uses_server_side_estimation(self) -> None:
        login = self.client.post(
            "/auth/login",
            json={"email": "user@ecoiz.app", "password": "password123"},
        )
        self.assertEqual(login.status_code, 200)
        token = login.json()["token"]

        custom = self.client.post(
            "/activities",
            json={
                "category": "Своя активность",
                "title": "Взял велосипед вместо машины",
                "co2Saved": 999,
                "points": 999,
                "note": "Доехал до учебы на велосипеде и взял многоразовую бутылку.",
                "media": [],
                "shareToNews": False,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(custom.status_code, 201)
        body = custom.json()
        self.assertEqual(body["activity"]["category"], "Своя активность")
        self.assertLessEqual(body["activity"]["points"], 14)
        self.assertLessEqual(body["activity"]["co2Saved"], 1.1)

    def test_admin_endpoints(self) -> None:
        login = self.client.post(
            "/admin/login",
            json={"email": "admin@ecoiz.app", "password": "admin123"},
        )
        self.assertEqual(login.status_code, 200)
        token = login.json()["token"]

        me = self.client.get(
            "/admin/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["role"], "ADMIN")

        users = self.client.get(
            "/admin/users?status=ACTIVE",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(users.status_code, 200)
        self.assertGreaterEqual(len(users.json()), 2)
        user_id = users.json()[0]["id"]

        user_detail = self.client.get(
            f"/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(user_detail.status_code, 200)
        self.assertIn("recentActivities", user_detail.json())
        self.assertIn("recentPosts", user_detail.json())

        activity_metrics = self.client.get(
            "/admin/activities/metrics",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(activity_metrics.status_code, 200)
        self.assertGreaterEqual(activity_metrics.json()["totalActivities"], 1)

        activities = self.client.get(
            "/admin/activities",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(activities.status_code, 200)
        self.assertGreaterEqual(len(activities.json()), 1)

        categories = self.client.get(
            "/admin/categories",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(categories.status_code, 200)
        self.assertGreaterEqual(len(categories.json()), 3)

        category_id = categories.json()[0]["id"]
        category_name = categories.json()[0]["name"]
        updated_category = self.client.patch(
            f"/admin/categories/{category_id}",
            json={
                "name": category_name,
                "description": "Обновленное описание",
                "color": "#000000",
                "icon": "flash",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(updated_category.status_code, 200)
        self.assertEqual(updated_category.json()["icon"], "flash")

        habits = self.client.get(
            "/admin/habits",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(habits.status_code, 200)
        self.assertGreaterEqual(len(habits.json()), 3)

        achievements = self.client.get(
            "/admin/achievements",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(achievements.status_code, 200)
        self.assertGreaterEqual(len(achievements.json()), 15)

        created_category = self.client.post(
            "/admin/categories",
            json={
                "name": "Воздух",
                "description": "Привычки для чистого воздуха",
                "color": "#7BC6CC",
                "icon": "wind",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(created_category.status_code, 400)

        created_habit = self.client.post(
            "/admin/habits",
            json={
                "title": "Проветривать комнату осознанно",
                "description": "Короткое и эффективное проветривание",
                "category": "Энергия",
                "points": 6,
                "co2Value": 0.1,
                "waterValue": 0.0,
                "energyValue": 0.0,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(created_habit.status_code, 201)
        created_habit_body = created_habit.json()

        created_achievement = self.client.post(
            "/admin/achievements",
            json={
                "title": "Тестовая ачивка",
                "description": "Проверка создания achievement",
                "icon": "star.fill",
                "targetValue": 2,
                "rewardPoints": 15,
                "badgeTintHex": 4497988,
                "badgeBackgroundHex": 15464671,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(created_achievement.status_code, 201)
        created_achievement_body = created_achievement.json()

        created_post = self.client.post(
            "/admin/posts",
            json={
                "author": "Admin",
                "content": "Пост для проверки admin CRUD",
                "visibility": "PUBLIC",
                "state": "Published",
                "reportsCount": 0,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(created_post.status_code, 201)
        created_post_body = created_post.json()

        posts = self.client.get(
            "/admin/posts",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(posts.status_code, 200)
        self.assertGreaterEqual(len(posts.json()), 2)

        deleted_post = self.client.delete(
            f"/admin/posts/{created_post_body['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(deleted_post.status_code, 204)

        deleted_achievement = self.client.delete(
            f"/admin/achievements/{created_achievement_body['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(deleted_achievement.status_code, 204)

        deleted_habit = self.client.delete(
            f"/admin/habits/{created_habit_body['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(deleted_habit.status_code, 204)

    def test_moderator_cannot_change_user_roles(self) -> None:
        with self.SessionLocal() as db:
            moderator = User(
                full_name="Moderator",
                email="moderator@ecoiz.app",
                username="moderator",
                password_hash=hash_password("moderator123"),
                role="MODERATOR",
                status="ACTIVE",
                is_email_verified=True,
                points=0,
                streak_days=0,
                co2_saved_total=0,
            )
            db.add(moderator)
            db.commit()

        login = self.client.post(
            "/admin/login",
            json={"email": "moderator@ecoiz.app", "password": "moderator123"},
        )
        self.assertEqual(login.status_code, 200)
        token = login.json()["token"]

        users = self.client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(users.status_code, 200)
        target_user_id = next(item["id"] for item in users.json() if item["email"] == "user@ecoiz.app")

        patch_response = self.client.patch(
            f"/admin/users/{target_user_id}",
            json={"role": "ADMIN", "status": "ACTIVE", "adminNote": "Escalation attempt"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(patch_response.status_code, 403)

    def test_claim_completed_challenge(self) -> None:
        login = self.client.post(
            "/auth/login",
            json={"email": "user@ecoiz.app", "password": "password123"},
        )
        self.assertEqual(login.status_code, 200)
        token = login.json()["token"]

        bootstrap = self.client.get(
            "/bootstrap",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(bootstrap.status_code, 200)
        challenge = next(item for item in bootstrap.json()["challenges"] if item["title"] == "7 эко-действий за неделю")

        remaining = challenge["targetCount"] - challenge["currentCount"]
        for index in range(remaining):
            mutation = self.client.post(
                "/activities",
                json={
                    "category": "Вода",
                    "title": f"Test activity {index}",
                    "co2Saved": 0.1,
                    "points": 1,
                    "note": "",
                    "media": [],
                    "shareToNews": False,
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            self.assertEqual(mutation.status_code, 201)

        claim = self.client.post(
            f"/challenges/{challenge['id']}/claim",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(claim.status_code, 200)
        self.assertTrue(claim.json()["challenge"]["isClaimed"])

        second_claim = self.client.post(
            f"/challenges/{challenge['id']}/claim",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(second_claim.status_code, 409)

    def test_unlocks_five_more_challenges_on_level_up(self) -> None:
        login = self.client.post(
            "/auth/login",
            json={"email": "user@ecoiz.app", "password": "password123"},
        )
        self.assertEqual(login.status_code, 200)
        token = login.json()["token"]

        before = self.client.get(
            "/bootstrap",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(before.status_code, 200)
        self.assertEqual(len(before.json()["challenges"]), 5)

        level_up = self.client.post(
            "/activities",
            json={
                "category": "Энергия",
                "title": "Большой апгрейд уровня",
                "co2Saved": 1.0,
                "points": 40,
                "note": "",
                "media": [],
                "shareToNews": False,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(level_up.status_code, 201)
        self.assertEqual(len(level_up.json()["challenges"]), 10)


if __name__ == "__main__":
    unittest.main()
