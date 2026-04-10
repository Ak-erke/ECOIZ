from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.admin import EcoCategory, Habit
from app.models.challenge import Challenge, UserChallenge
from app.models.chat import ChatMessage
from app.models.post import Post
from app.models.user import Activity, User
from app.services.auth import hash_password
from app.services.bootstrap import unlocked_challenge_count
from app.services.user_progress import recalculate_user_progress


CHALLENGE_UNLOCK_ORDER = [
    "7 эко-действий за неделю",
    "3 дня без пластика",
    "Эко-транспорт",
    "Водный баланс",
    "Энергия под контролем",
    "Неделя сортировки",
    "Эко-утро",
    "Чистый воздух",
    "Многоразовый герой",
    "Осознанный шопинг",
    "Эко-комьюнити",
    "Зеленая неделя",
    "Ноль отходов",
    "Дом без потерь",
    "Эко-мастер",
]

FIXED_CATEGORY_SPECS = [
    ("Энергия", "Привычки для экономии электричества и тепла", "#F2BF18", "bolt"),
    ("Вода", "Привычки для бережного использования воды", "#2DA9F5", "drop"),
    ("Пластик", "Сокращение одноразового пластика", "#20D8C3", "leaf"),
    ("Транспорт", "Экологичные способы передвижения", "#FF9D1F", "figure.walk"),
    ("Отходы", "Сортировка и сокращение мусора", "#69D85A", "trash"),
]

FIXED_HABIT_SPECS = [
    ("Пешая прогулка", "Заменить поездку пешей прогулкой", 20, 1.5, 0.0, 0.0, "Транспорт"),
    ("Мотоцикл", "Выбрать более экономичный транспорт", 5, 0.2, 0.0, 0.0, "Транспорт"),
    ("Велосипед", "Проехать маршрут на велосипеде", 25, 2.0, 0.0, 0.0, "Транспорт"),
    ("Самокат", "Выбрать самокат вместо машины", 15, 0.8, 0.0, 0.0, "Транспорт"),
    ("Машина", "Использовать машину осознанно", 0, 0.0, 0.0, 0.0, "Транспорт"),
    ("Общ. транспорт", "Выбрать общественный транспорт", 15, 1.0, 0.0, 0.0, "Транспорт"),
    ("Поезд", "Выбрать поезд вместо машины или самолета", 15, 1.2, 0.0, 0.0, "Транспорт"),
    ("Совместная поездка", "Поехать вместе с кем-то вместо отдельной машины", 18, 1.3, 0.0, 0.0, "Транспорт"),
    ("Короткий душ", "Сократить время душа", 15, 0.0, 25.0, 0.0, "Вода"),
    ("Закрыл кран вовремя", "Закрыть кран во время бытовых действий", 10, 0.0, 8.0, 0.0, "Вода"),
    ("Полная загрузка стирки", "Стирать только при полной загрузке", 20, 0.0, 40.0, 0.0, "Вода"),
    ("Устранил утечку", "Исправить утечку воды", 30, 0.0, 60.0, 0.0, "Вода"),
    ("Установил аэратор", "Установить аэратор на кран", 25, 0.0, 35.0, 0.0, "Вода"),
    ("Без пакета", "Отказаться от одноразового пакета", 10, 0.0, 0.0, 0.0, "Пластик"),
    ("Многоразовая сумка", "Использовать многоразовую сумку", 15, 0.0, 0.0, 0.0, "Пластик"),
    ("Многоразовая бутылка", "Использовать многоразовую бутылку", 20, 0.0, 0.0, 0.0, "Пластик"),
    ("Сдал пластик", "Сдать пластик на переработку", 25, 0.0, 0.0, 0.0, "Пластик"),
    ("Сортировка", "Отсортировать отходы", 15, 0.0, 0.0, 0.0, "Отходы"),
    ("Сдал вторсырье", "Сдать вторсырье", 20, 0.0, 0.0, 0.0, "Отходы"),
    ("Компост", "Отправить органику в компост", 20, 0.0, 0.0, 0.0, "Отходы"),
    ("Выключил свет", "Выключить свет, когда он не нужен", 10, 0.0, 0.0, 2.0, "Энергия"),
    ("Отключил приборы из сети", "Отключить приборы из сети", 15, 0.0, 0.0, 3.0, "Энергия"),
    ("Использую LED-лампы", "Поставить LED-лампы", 20, 0.0, 0.0, 5.0, "Энергия"),
    ("Использую дневной свет", "Чаще использовать дневной свет", 15, 0.0, 0.0, 3.0, "Энергия"),
]


def assign_challenges_for_user(db: Session, user: User, challenges: list[Challenge]) -> None:
    if user.role != "USER":
        return

    now = datetime.now(timezone.utc)
    unlocked_count = min(unlocked_challenge_count(user.points), len(challenges))
    order_map = {title: index for index, title in enumerate(CHALLENGE_UNLOCK_ORDER)}
    unlocked_challenges = sorted(challenges, key=lambda item: order_map.get(item.title, len(order_map)))[:unlocked_count]
    unlocked_ids = {challenge.id for challenge in unlocked_challenges}
    existing_items = db.scalars(select(UserChallenge).where(UserChallenge.user_id == user.id)).all()
    existing_by_challenge_id = {item.challenge_id: item for item in existing_items}
    is_initial_unlock = len(existing_items) == 0

    for stale_item in existing_items:
        if stale_item.challenge_id not in unlocked_ids:
            db.delete(stale_item)

    for challenge in unlocked_challenges:
        if challenge.id in existing_by_challenge_id:
            continue
        db.add(
            UserChallenge(
                user_id=user.id,
                challenge_id=challenge.id,
                current_count=0,
                is_completed=False,
                unlocked_at=None if is_initial_unlock else now,
            )
        )


def _fetch_user_with_relations(db: Session, user_id) -> User | None:
    return db.scalar(
        select(User)
        .options(
            selectinload(User.activities),
            selectinload(User.posts),
            selectinload(User.user_challenges).selectinload(UserChallenge.challenge),
        )
        .where(User.id == user_id)
    )


def ensure_seed_data(db: Session) -> None:
    last_activity_seed_date = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    now = datetime.now(timezone.utc)

    existing = db.scalar(select(User).where(User.email == "user@ecoiz.app"))
    if not existing:
        user = User(
            full_name="Пользователь",
            email="user@ecoiz.app",
            username="user",
            password_hash=hash_password("password123"),
            role="USER",
            status="ACTIVE",
            is_email_verified=True,
            points=0,
            streak_days=0,
            last_activity_on=last_activity_seed_date,
            co2_saved_total=0,
        )
        db.add(user)
        db.flush()
    else:
        user = existing
        user.last_activity_on = last_activity_seed_date

    admin = db.scalar(select(User).where(User.email == "admin@ecoiz.app"))
    if not admin:
        admin = User(
            full_name="Администратор",
            email="admin@ecoiz.app",
            username="admin",
            password_hash=hash_password("admin123"),
            role="ADMIN",
            status="ACTIVE",
            is_email_verified=True,
            points=0,
            streak_days=0,
            last_activity_on=None,
            co2_saved_total=0,
        )
        db.add(admin)
        db.flush()
    else:
        admin.full_name = "Администратор"
        admin.username = "admin"
        admin.password_hash = hash_password("admin123")
        admin.role = "ADMIN"
        admin.status = "ACTIVE"
        admin.is_email_verified = True

    moderator = db.scalar(select(User).where(User.email == "moderator@ecoiz.app"))
    if not moderator:
        moderator = User(
            full_name="Модератор",
            email="moderator@ecoiz.app",
            username="moderator",
            password_hash=hash_password("moderator123"),
            role="MODERATOR",
            status="ACTIVE",
            is_email_verified=True,
            points=0,
            streak_days=0,
            last_activity_on=None,
            co2_saved_total=0,
        )
        db.add(moderator)
        db.flush()
    else:
        moderator.full_name = "Модератор"
        moderator.username = "moderator"
        moderator.password_hash = hash_password("moderator123")
        moderator.role = "MODERATOR"
        moderator.status = "ACTIVE"
        moderator.is_email_verified = True

    # Normalize legacy activity-post copy so old posts use the same neutral wording as new ones.
    legacy_activity_prefix = "Добавил активити:"
    normalized_activity_prefix = "Добавил(а) активити:"
    for post in db.scalars(select(Post).where(Post.text.startswith(legacy_activity_prefix))).all():
        post.text = post.text.replace(legacy_activity_prefix, normalized_activity_prefix, 1)

    challenge_specs = [
        ("7 эко-действий за неделю", "Добавь 7 экологичных активностей за последние 7 дней.", 7, 60, "leaf.fill", 0x43B244, 0xEAF8DF),
        ("3 дня без пластика", "Отметь 3 действия из категории Пластик и сократи одноразовые вещи.", 3, 40, "waterbottle.fill", 0x1AA5E6, 0xE7F5FF),
        ("Эко-транспорт", "Выбери пешую прогулку, велосипед, самокат или общественный транспорт 5 раз.", 5, 45, "figure.walk.circle.fill", 0xF09A00, 0xFFF5E2),
        ("Водный баланс", "Сделай 4 полезных действия из категории Вода.", 4, 35, "drop.fill", 0x1AA5E6, 0xE7F5FF),
        ("Энергия под контролем", "Выполни 6 действий из категории Энергия.", 6, 55, "bolt.fill", 0xF5B100, 0xFFF4D6),
        ("Неделя сортировки", "5 раз отсортируй отходы, сдай вторсырье или отправь органику в компост.", 5, 50, "arrow.3.trianglepath.circle.fill", 0x43B244, 0xEAF8DF),
        ("Эко-утро", "3 дня подряд начинай утро с полезной экопривычки.", 3, 25, "sun.max.fill", 0xF6A623, 0xFFF0D9),
        ("Чистый воздух", "4 раза выбери пешую прогулку вместо поездки на машине.", 4, 40, "wind", 0x7BC6CC, 0xEAFBFC),
        ("Многоразовый герой", "5 раз используй многоразовые вещи, например сумку или бутылку.", 5, 45, "tray.full.fill", 0x5CB85C, 0xE6F7E6),
        ("Осознанный шопинг", "3 раза откажись от лишней упаковки или одноразового пакета.", 3, 30, "bag.fill", 0xC08B5C, 0xF8EEDF),
        ("Эко-комьюнити", "Опубликуй 2 поста о своих экопривычках и поделись примером с другими.", 2, 20, "person.3.fill", 0x9B7BFF, 0xF1EBFF),
        ("Зеленая неделя", "Добавь 10 экологичных активностей за одну неделю.", 10, 80, "calendar", 0x3FAE5A, 0xE6F7EA),
        ("Ноль отходов", "4 дня подряд обходись без одноразового пластика.", 4, 55, "trash.slash.fill", 0x556B2F, 0xEEF5E1),
        ("Дом без потерь", "Выполни 5 домашних привычек, которые экономят ресурсы.", 5, 50, "house.fill", 0xE67E22, 0xFFF1E3),
        ("Эко-мастер", "Набери 250 очков экопрогресса и дойди до уровня мастера.", 250, 120, "crown.fill", 0xD4AF37, 0xFFF8D9),
    ]
    challenges: list[Challenge] = []
    for title, description, target_count, reward_points, badge_symbol, badge_tint_hex, badge_background_hex in challenge_specs:
        challenge = db.scalar(select(Challenge).where(Challenge.title == title))
        if not challenge:
            challenge = Challenge(
                title=title,
                description=description,
                target_count=target_count,
                reward_points=reward_points,
                badge_symbol=badge_symbol,
                badge_tint_hex=badge_tint_hex,
                badge_background_hex=badge_background_hex,
            )
            db.add(challenge)
            db.flush()
        else:
            challenge.description = description
            challenge.target_count = target_count
            challenge.reward_points = reward_points
            challenge.badge_symbol = badge_symbol
            challenge.badge_tint_hex = badge_tint_hex
            challenge.badge_background_hex = badge_background_hex
        challenges.append(challenge)

    allowed_category_names = {name for name, *_ in FIXED_CATEGORY_SPECS}
    categories: list[EcoCategory] = []
    for name, description, color, icon in FIXED_CATEGORY_SPECS:
        category = db.scalar(select(EcoCategory).where(EcoCategory.name == name))
        if not category:
            category = EcoCategory(name=name, description=description, color=color, icon=icon)
            db.add(category)
            db.flush()
        else:
            category.description = description
            category.color = color
            category.icon = icon
        categories.append(category)

    category_by_name = {item.name: item for item in categories}
    allowed_habit_titles = {title for title, *_ in FIXED_HABIT_SPECS}

    for stale_habit in db.scalars(select(Habit)).all():
        category = next((item for item in categories if item.id == stale_habit.category_id), None)
        if not category or category.name not in allowed_category_names or stale_habit.title not in allowed_habit_titles:
            db.delete(stale_habit)
    db.flush()

    for stale_category in db.scalars(select(EcoCategory)).all():
        if stale_category.name not in allowed_category_names:
            db.delete(stale_category)
    db.flush()

    for title, description, points, co2_value, water_value, energy_value, category_name in FIXED_HABIT_SPECS:
        habit = db.scalar(select(Habit).where(Habit.title == title))
        if not habit:
            habit = Habit(
                title=title,
                description=description,
                points=points,
                co2_value=co2_value,
                water_value=water_value,
                energy_value=energy_value,
                category_id=category_by_name[category_name].id,
            )
            db.add(habit)
            continue

        habit.description = description
        habit.points = points
        habit.co2_value = co2_value
        habit.water_value = water_value
        habit.energy_value = energy_value
        habit.category_id = category_by_name[category_name].id

    for challenge_user in db.scalars(select(User).where(User.role == "USER")).all():
        assign_challenges_for_user(db, challenge_user, challenges)
    db.flush()

    user_challenges = db.scalars(select(UserChallenge).where(UserChallenge.user_id == user.id)).all()
    if len(user_challenges) >= 3:
        user_challenges_by_title = {
            item.challenge.title: item
            for item in db.scalars(
                select(UserChallenge)
                .join(UserChallenge.challenge)
                .where(UserChallenge.user_id == user.id)
            ).all()
        }
        if "7 эко-действий за неделю" in user_challenges_by_title:
            user_challenges_by_title["7 эко-действий за неделю"].current_count = max(
                user_challenges_by_title["7 эко-действий за неделю"].current_count,
                2,
            )
        if "3 дня без пластика" in user_challenges_by_title:
            user_challenges_by_title["3 дня без пластика"].current_count = max(
                user_challenges_by_title["3 дня без пластика"].current_count,
                1,
            )
        if "Эко-транспорт" in user_challenges_by_title:
            user_challenges_by_title["Эко-транспорт"].current_count = max(
                user_challenges_by_title["Эко-транспорт"].current_count,
                0,
            )

    if not db.scalar(select(Activity).where(Activity.user_id == user.id)):
        db.add_all(
            [
                Activity(user_id=user.id, category="Энергия", title="Отключил ненужные приборы", co2_saved=0.5, points=10, created_at=now - timedelta(hours=20)),
                Activity(user_id=user.id, category="Пластик", title="Многоразовая сумка", co2_saved=0.5, points=10, created_at=now - timedelta(hours=44)),
            ]
        )
    if not db.scalar(select(Post).where(Post.user_id == user.id)):
        db.add_all(
            [
                Post(user_id=user.id, author_name="Нурс", text="Сегодня выбрал метро вместо машины", visibility="PUBLIC", moderation_state="Published", reports_count=0, created_at=now - timedelta(hours=1)),
                Post(user_id=user.id, author_name="Ая", text="Сортирую отходы уже 5 дней подряд", visibility="PUBLIC", moderation_state="Needs review", reports_count=2, created_at=now - timedelta(hours=3)),
            ]
        )
    if not db.scalar(select(ChatMessage).where(ChatMessage.user_id == user.id)):
        db.add(ChatMessage(user_id=user.id, role="assistant", text="Привет. Я могу подсказать идеи на день, помочь с экопривычками или просто нормально ответить на вопрос.", created_at=now))
    db.flush()

    user_ids = [item.id for item in db.scalars(select(User)).all()]
    for post in db.scalars(select(Post)).all():
        if post.moderation_state == "Flagged":
            post.moderation_state = "Needs review"

    for user_id in user_ids:
        db.expire_all()
        synced_user = _fetch_user_with_relations(db, user_id)
        if not synced_user:
            continue
        recalculate_user_progress(synced_user)
        if synced_user.role == "USER":
            assign_challenges_for_user(db, synced_user, challenges)
            db.flush()
            db.expire_all()
            synced_user = _fetch_user_with_relations(db, user_id)
            if not synced_user:
                continue
            recalculate_user_progress(synced_user)

    db.commit()
