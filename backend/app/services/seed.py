from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.admin import EcoCategory, Habit
from app.models.challenge import Challenge, UserChallenge
from app.models.chat import ChatMessage
from app.models.post import Post
from app.models.user import Activity, User
from app.services.auth import hash_password
from app.services.bootstrap import unlocked_challenge_count


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


def assign_challenges_for_user(db: Session, user: User, challenges: list[Challenge]) -> None:
    unlocked_count = min(unlocked_challenge_count(user.points), len(challenges))
    order_map = {title: index for index, title in enumerate(CHALLENGE_UNLOCK_ORDER)}
    unlocked_challenges = sorted(challenges, key=lambda item: order_map.get(item.title, len(order_map)))[:unlocked_count]
    existing_by_challenge_id = {
        item.challenge_id
        for item in db.scalars(select(UserChallenge).where(UserChallenge.user_id == user.id)).all()
    }
    for challenge in unlocked_challenges:
        if challenge.id in existing_by_challenge_id:
            continue
        db.add(
            UserChallenge(
                user_id=user.id,
                challenge_id=challenge.id,
                current_count=0,
                is_completed=False,
            )
        )


def ensure_seed_data(db: Session) -> None:
    last_activity_seed_date = (datetime.now(timezone.utc) - timedelta(days=1)).date()

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
            points=90,
            streak_days=2,
            last_activity_on=last_activity_seed_date,
            co2_saved_total=8.6,
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

    challenge_specs = [
        ("7 эко-действий за неделю", "Добавь 7 любых экологичных активностей", 7, 60, "leaf.fill", 0x43B244, 0xEAF8DF),
        ("3 дня без пластика", "Отмечай действия категории Пластик", 3, 40, "waterbottle.fill", 0x1AA5E6, 0xE7F5FF),
        ("Эко-транспорт", "5 поездок пешком/велосипедом/метро", 5, 45, "figure.walk.circle.fill", 0xF09A00, 0xFFF5E2),
        ("Водный баланс", "Добавь 4 активности по экономии воды", 4, 35, "drop.fill", 0x1AA5E6, 0xE7F5FF),
        ("Энергия под контролем", "Сделай 6 действий из категории Энергия", 6, 55, "bolt.fill", 0xF5B100, 0xFFF4D6),
        ("Неделя сортировки", "5 раз отсортируй отходы или сдай на переработку", 5, 50, "arrow.3.trianglepath.circle.fill", 0x43B244, 0xEAF8DF),
        ("Эко-утро", "3 дня начинай день с полезной привычки", 3, 25, "sun.max.fill", 0xF6A623, 0xFFF0D9),
        ("Чистый воздух", "4 раза выбери пешую прогулку вместо авто", 4, 40, "wind", 0x7BC6CC, 0xEAFBFC),
        ("Многоразовый герой", "5 раз используй многоразовые вещи", 5, 45, "tray.full.fill", 0x5CB85C, 0xE6F7E6),
        ("Осознанный шопинг", "3 раза откажись от лишней упаковки", 3, 30, "bag.fill", 0xC08B5C, 0xF8EEDF),
        ("Эко-комьюнити", "Опубликуй 2 поста про экопривычки", 2, 20, "person.3.fill", 0x9B7BFF, 0xF1EBFF),
        ("Зеленая неделя", "10 активностей за 7 дней", 10, 80, "calendar", 0x3FAE5A, 0xE6F7EA),
        ("Ноль отходов", "4 дня подряд без одноразового пластика", 4, 55, "trash.slash.fill", 0x556B2F, 0xEEF5E1),
        ("Дом без потерь", "5 привычек для дома и ресурсов", 5, 50, "house.fill", 0xE67E22, 0xFFF1E3),
        ("Эко-мастер", "Собери 250 очков экопрогресса", 250, 120, "crown.fill", 0xD4AF37, 0xFFF8D9),
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
        challenges.append(challenge)

    categories: list[EcoCategory] = []
    for name, description, color, icon in [
        ("Энергия", "Привычки для экономии электричества и тепла", "#F09A00", "bolt"),
        ("Вода", "Привычки для бережного использования воды", "#1AA5E6", "drop"),
        ("Пластик", "Сокращение одноразового пластика", "#43B244", "leaf"),
        ("Транспорт", "Экологичные способы передвижения", "#7BC6CC", "figure.walk"),
        ("Отходы", "Сортировка и сокращение мусора", "#8E8E93", "trash"),
        ("Покупки", "Осознанное потребление и упаковка", "#C08B5C", "bag"),
    ]:
        category = db.scalar(select(EcoCategory).where(EcoCategory.name == name))
        if not category:
            category = EcoCategory(name=name, description=description, color=color, icon=icon)
            db.add(category)
            db.flush()
        categories.append(category)

    category_by_name = {item.name: item for item in categories}
    for title, description, points, co2_value, water_value, energy_value, category_name in [
        ("Выключать лишний свет", "Отключай свет при выходе из комнаты", 10, 0.3, 0, 0.5, "Энергия"),
        ("Отключать зарядку из розетки", "Не держи зарядные устройства подключенными без нужды", 8, 0.2, 0, 0.3, "Энергия"),
        ("Короткий душ", "Сократи время душа до пяти минут", 12, 0.2, 8, 0.2, "Вода"),
        ("Закрывать кран во время чистки зубов", "Экономь воду в быту каждый день", 7, 0.1, 5, 0, "Вода"),
        ("Многоразовая бутылка", "Используй свою бутылку вместо одноразовой", 9, 0.1, 0, 0, "Пластик"),
        ("Эко-сумка вместо пакета", "Бери многоразовую сумку в магазин", 8, 0.1, 0, 0, "Пластик"),
        ("Прогулка пешком", "Замени короткую поездку пешей прогулкой", 11, 0.6, 0, 0, "Транспорт"),
        ("Велосипед вместо машины", "Выбери велосипед для короткого маршрута", 14, 0.9, 0, 0, "Транспорт"),
        ("Сортировка бумаги", "Отделяй бумагу и картон на переработку", 10, 0.2, 0, 0, "Отходы"),
        ("Сдать пластик на переработку", "Отнеси пластик в пункт приема", 13, 0.4, 0, 0, "Отходы"),
        ("Покупка без лишней упаковки", "Выбирай товары с минимальной упаковкой", 9, 0.1, 0, 0, "Покупки"),
        ("Локальные продукты", "Выбери продукты местного производства", 10, 0.3, 0, 0, "Покупки"),
    ]:
        if not db.scalar(select(Habit).where(Habit.title == title)):
            db.add(
                Habit(
                    title=title,
                    description=description,
                    points=points,
                    co2_value=co2_value,
                    water_value=water_value,
                    energy_value=energy_value,
                    category_id=category_by_name[category_name].id,
                )
            )

    assign_challenges_for_user(db, user, challenges)
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

    now = datetime.now(timezone.utc)
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
        db.add(ChatMessage(user_id=user.id, role="assistant", text="Привет! Я эко-ИИ. Помогу улучшить твои экопривычки и мотивацию.", created_at=now))
    db.commit()
