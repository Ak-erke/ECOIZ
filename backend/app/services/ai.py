from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
import re

import httpx

from app.core.config import get_settings
from app.models.user import User


DEFAULT_SYSTEM_PROMPT = """
Ты EcoIZ AI Eco Assistant, eco-buddy внутри мобильного приложения EcoIZ.

Твоя миссия: быть для пользователя обычным умным собеседником и eco-buddy одновременно.
Отвечай как живой ассистент в стиле ChatGPT: сначала пойми смысл реплики и контекст, потом дай уже готовый, естественный ответ.

Роль и стиль:
- отвечай только на русском;
- говори дружелюбно, просто и поддерживающе;
- оставайся вдохновляющим, но не навязчивым;
- можно добавить 0-2 уместных эмодзи;
- допустим лёгкий экологичный юмор без сарказма и давления.

Правила ответа:
- обычно отвечай в 1-5 коротких предложениях;
- если даёшь совет, предлагай 1-3 конкретных и применимых шага;
- если пользователь уже сделал полезное действие, сначала похвали его;
- если пользователь устал, сомневается или пассивен, предложи микро-действие;
- по возможности кратко объясняй эффект: меньше отходов, экономия воды/энергии, меньше CO2;
- учитывай историю действий, серию, очки и релевантные категории, но не пересказывай сырые данные без пользы;
- если пользователь меняет условия, сразу подстрой ответ под новый контекст.
- сначала отвечай на настоящий вопрос пользователя, а не на воображаемый eco-шаблон;
- если вопрос не про экологию напрямую, всё равно отвечай нормально и по-человечески, без попытки насильно свести всё к экопривычкам;
- если уместно, мягко добавь eco-friendly угол или следующий экологичный шаг, но только когда это реально подходит ситуации;
- small talk, приветствия, эмоции и обычный разговор тоже обрабатывай естественно;
- никогда не показывай внутренние рассуждения, план решения, скрытый разбор запроса или служебные заметки;
- не пиши фразы вроде "пользователь говорит", "нужно подстроить", "сначала посмотрю", "значит нужно";
- пользователю показывай только финальный дружелюбный ответ.

Нельзя:
- осуждать пользователя;
- guilt-trip, давить или читать лекцию;
- выдумывать факты и точные цифры, если нет опоры на контекст;
- звучать как шаблонная техподдержка.

Предпочтительный тон:
- как хороший eco-buddy, а не строгий эксперт;
- маленькие шаги тоже считаются вкладом;
- лучше естественный живой ответ, чем канцелярский шаблон.
""".strip()


def _fallback_response(text: str) -> str:
    lowercase = text.lower()
    if _is_greeting_or_smalltalk(text):
        return "Привет. Могу помочь с идеями на день, экопривычками или просто нормально ответить на вопрос без шаблонов."
    if "что делать сегодня" in lowercase or "что мне делать сегодня" in lowercase:
        return "На сегодня можно выбрать что-то одно: короткий душ, многоразовую бутылку с собой или выключить лишний свет дома. Этого уже достаточно."
    if "вод" in lowercase:
        return "По воде самый простой вариант: душ чуть короче и не держать кран открытым без дела. Это даёт быстрый эффект без напряга."
    if "транспорт" in lowercase or "машин" in lowercase:
        return "Если речь про транспорт, самый реалистичный шаг: хотя бы часть коротких поездок заменить на пешком, автобус или метро."
    if "мотивац" in lowercase or "сложно" in lowercase:
        return "Не надо менять всё сразу. Лучше один маленький шаг сегодня, чем большой план, который быстро надоест."
    if any(phrase in lowercase for phrase in ("иду гулять", "я иду гулять", "пойду гулять", "гулять")):
        walk_actions = _outdoor_actions()
        return f"Тогда лучше оттолкнуться от прогулки: можно пройти часть пути пешком подольше, взять с собой {walk_actions[1]} и не брать по дороге одноразовый стакан или бутылку."
    if any(word in lowercase for word in ("как", "почему", "зачем", "что")):
        return "Если коротко, могу помочь практично. Напиши чуть конкретнее, что именно хочешь понять или сделать, и я подстроюсь под ситуацию."
    return "Могу ответить более точно, если напишешь чуть подробнее, что именно тебе сейчас нужно."


def _contains_any(text: str, *phrases: str) -> bool:
    return any(phrase in text for phrase in phrases)


def _normalized_user_text(text: str) -> str:
    lowered = text.lower().strip()
    return re.sub(r"(.)\1{2,}", r"\1", lowered)


def _is_greeting_or_smalltalk(text: str) -> bool:
    normalized = _normalized_user_text(text)
    if any(token in normalized for token in ("прив", "здрав", "hello", "hi", "хай")):
        return True
    if "как дела" in normalized or "как ты" in normalized:
        return True
    return False


def _is_smalltalk_request(text: str) -> bool:
    normalized = " ".join(_normalized_user_text(text).split())
    if _is_greeting_or_smalltalk(text):
        return True
    smalltalk_phrases = (
        "что делаешь",
        "чем занят",
        "как настроение",
        "доброе утро",
        "добрый вечер",
        "добрый день",
        "спокойной ночи",
    )
    return any(phrase in normalized for phrase in smalltalk_phrases)


def _home_actions_for_category(category: str) -> list[str]:
    category_lower = category.lower()
    if "энерг" in category_lower:
        return [
            "выключи лишний свет и зарядки, которые сейчас не нужны",
            "включай свет только в той комнате, где реально находишься",
            "если работаешь дома, начни с режима энергосбережения на ноутбуке",
        ]
    if "вод" in category_lower:
        return [
            "сделай душ короче на 2-3 минуты",
            "не держи воду открытой во время чистки зубов и умывания",
            "проверь, не подтекает ли кран на кухне или в ванной",
        ]
    if "пласт" in category_lower:
        return [
            "возьми одну многоразовую бутылку или кружку на весь день",
            "откажись сегодня хотя бы от одной одноразовой упаковки",
            "подготовь многоразовую сумку заранее, чтобы не брать пакет",
        ]
    if "отход" in category_lower:
        return [
            "раздели сегодня бумагу, пластик и смешанные отходы",
            "отложи чистую упаковку отдельно, а не в общий мусор",
            "выброси старые коробки и бутылки уже отсортированными",
        ]
    if "транспорт" in category_lower:
        return [
            "завтра снова выбрать автобус, метро или пеший отрезок вместо машины",
            "запланируй следующую поездку без машины заранее",
            "если всё же нужно выйти, выбери пеший маршрут хотя бы на короткий отрезок",
        ]
    return [
        "выключи лишний свет",
        "сделай душ короче",
        "откажись от одной одноразовой вещи сегодня",
    ]


def _outdoor_actions() -> list[str]:
    return [
        "пройтись пешком вместо короткой поездки",
        "многоразовую бутылку или кружку",
        "если хочется, захватить пакет и убрать пару мелких бумажек по пути",
    ]


def _work_actions_for_category(category: str) -> list[str]:
    category_lower = category.lower()
    if "вод" in category_lower:
        return [
            "наливать воду в кружку или бутылку без одноразового стаканчика",
            "не оставлять кран открытым в офисной кухне или туалете",
            "брать ровно столько воды, сколько реально выпьешь",
        ]
    if "энерг" in category_lower:
        return [
            "перевести ноутбук в энергосбережение",
            "выключать свет или монитор, когда уходишь надолго",
            "отключать ненужную зарядку от розетки",
        ]
    if "пласт" in category_lower:
        return [
            "взять свою кружку или бутылку вместо одноразового стакана",
            "не брать лишние пластиковые приборы и упаковку на обеде",
            "держать многоразовую ложку или контейнер на работе",
        ]
    if "отход" in category_lower:
        return [
            "отдельно собрать бумагу и пластик со стола",
            "не выбрасывать чистую бумагу в общий мусор",
            "начать с одного маленького контейнера для сортировки рядом с рабочим местом",
        ]
    if "транспорт" in category_lower:
        return [
            "доехать до работы на автобусе, метро или пройти часть пути пешком",
            "на обратной дороге выбрать пеший отрезок вместо короткой поездки",
            "заранее спланировать маршрут без машины на завтра",
        ]
    return [
        "взять свою кружку вместо одноразового стакана",
        "перевести ноутбук в энергосбережение",
        "не брать лишнюю упаковку на обеде",
    ]


def _supportive_close(seed_text: str) -> str:
    return _pick_variant(
        seed_text,
        [
            "Маленький шаг тоже считается 🌱",
            "Спокойный ритм тут важнее идеальности.",
            "Планета любит такие маленькие победы 🌍",
        ],
    )


def _category_impact_hint(category: str) -> str:
    category_lower = category.lower()
    if "транспорт" in category_lower:
        return "это помогает уменьшать выбросы CO2"
    if "вод" in category_lower:
        return "это помогает экономить воду и ресурсы"
    if "энерг" in category_lower:
        return "это помогает экономить энергию"
    if "пласт" in category_lower or "отход" in category_lower:
        return "это помогает уменьшать отходы"
    return "это тоже полезный вклад для планеты"


def _recent_completed_action(user: User) -> object | None:
    activities = sorted(user.activities, key=lambda item: _as_utc(item.created_at), reverse=True)
    if not activities:
        return None
    latest = activities[0]
    if _as_utc(latest.created_at) < datetime.now(timezone.utc) - timedelta(days=2):
        return None
    return latest


def _is_activity_sharing_message(text: str) -> bool:
    lowercase = text.lower()
    action_markers = (
        "сегодня",
        "поехал",
        "поехала",
        "пошел",
        "пошла",
        "сделал",
        "сделала",
        "взял",
        "взяла",
        "выбрал",
        "выбрала",
        "использовал",
        "использовала",
        "отказался",
        "отказалась",
    )
    return any(marker in lowercase for marker in action_markers)


def _message_category(text: str, fallback_category: str | None = None) -> str | None:
    lowercase = text.lower()
    if any(word in lowercase for word in ("автобус", "метро", "поезд", "машин", "пеш", "велосип", "самокат", "транспорт")):
        return "Транспорт"
    if any(word in lowercase for word in ("душ", "кран", "вода", "стирк", "утеч")):
        return "Вода"
    if any(word in lowercase for word in ("свет", "энерг", "заряд", "электр", "ламп")):
        return "Энергия"
    if any(word in lowercase for word in ("пластик", "бутыл", "пакет", "упаков", "многораз")):
        return "Пластик"
    if any(word in lowercase for word in ("отход", "мусор", "сортир", "переработ", "вторсыр")):
        return "Отходы"
    return fallback_category


def _praise_for_action(text: str, user: User, category: str | None) -> str:
    latest = _recent_completed_action(user)
    impact_line = _category_impact_hint(category or (latest.category if latest else ""))
    praise = _pick_variant(
        text,
        [
            "Отличный выбор!",
            "Классный шаг!",
            "Хороший eco-ход!",
        ],
    )
    if latest and latest.co2_saved > 0 and category in (None, latest.category, _message_category(latest.title, latest.category)):
        return f"{praise} Ты уже сделал полезное действие, и {impact_line}. Примерно {latest.co2_saved:.2f} кг CO2 уже в плюс для планеты."
    return f"{praise} Это реально хороший вклад, и {impact_line}."


def _streak_line(user: User) -> str:
    if user.streak_days >= 7:
        return f"У тебя уже {user.streak_days} дней подряд, не дадим серии остыть 🔥"
    if user.streak_days >= 3:
        return f"У тебя уже {user.streak_days} дня подряд, хороший ритм."
    return ""


def _micro_action(category: str) -> str:
    actions = _home_actions_for_category(category)
    return actions[0]


def _natural_next_step(category: str, topic: str | None = None) -> str:
    category_lower = category.lower()
    if topic == "outdoor" or "транспорт" in category_lower:
        return "завтра снова выбрать автобус, метро или короткий пеший отрезок вместо машины"
    if "вод" in category_lower:
        return "сделать душ чуть короче или не оставлять кран открытым без дела"
    if "энерг" in category_lower:
        return "выключить лишний свет и оставить устройства в энергосбережении"
    if "пласт" in category_lower:
        return "взять с собой многоразовую бутылку или сумку"
    if "отход" in category_lower:
        return "отсортировать хотя бы часть отходов дома"
    return _micro_action(category)


def _pick_variant(seed_text: str, variants: list[str]) -> str:
    if not variants:
        return ""
    index = sum(ord(char) for char in seed_text) % len(variants)
    return variants[index]


def _analytics_snapshot(user: User) -> dict[str, object]:
    activities = sorted(user.activities, key=lambda item: _as_utc(item.created_at))
    category_counts: dict[str, int] = defaultdict(int)
    last_seen_by_category: dict[str, datetime] = {}
    last_7_days = datetime.now(timezone.utc) - timedelta(days=7)
    recent_points = 0

    for item in activities:
        created_at = _as_utc(item.created_at)
        category_counts[item.category] += 1
        last_seen_by_category[item.category] = created_at
        if created_at >= last_7_days:
            recent_points += item.points

    strongest = max(category_counts, key=category_counts.get) if category_counts else None
    weakest = min(category_counts, key=category_counts.get) if category_counts else None

    preferred_order = ["Энергия", "Вода", "Пластик", "Отходы", "Транспорт", "Своя активность"]
    missing = [category for category in preferred_order if category not in category_counts]
    if missing:
        suggested = missing[0]
    elif last_seen_by_category:
        suggested = min(last_seen_by_category.items(), key=lambda item: item[1])[0]
    else:
        suggested = "Энергия"

    return {
        "activities_count": len(activities),
        "recent_points": recent_points,
        "strongest_category": strongest,
        "weakest_category": weakest,
        "suggested_category": suggested,
        "last_activity": activities[-1] if activities else None,
    }


def _friendly_intro(user: User) -> str:
    if user.streak_days >= 14:
        return _pick_variant(
            f"intro:{user.streak_days}",
            [
                "У тебя уже очень уверенный eco-ритм.",
                "У тебя уже прям хороший устойчивый ритм.",
                "Чувствуется, что eco-привычка уже закрепляется.",
            ],
        )
    if user.streak_days >= 5:
        return _pick_variant(
            f"intro:{user.streak_days}",
            [
                "У тебя уже формируется хороший eco-ритм.",
                "Ты уже неплохо держишь темп.",
                "Ритм уже начинает складываться.",
            ],
        )
    if user.activities:
        return _pick_variant(
            f"intro:{len(user.activities)}",
            [
                "Ты уже хорошо втянулся.",
                "У тебя уже есть хороший старт.",
                "Ты уже не с нуля, это видно.",
            ],
        )
    return _pick_variant(
        f"intro:{user.points}",
        [
            "Начало уже положено.",
            "Старт уже есть, это главное.",
            "Первый шаг уже сделан.",
        ],
    )


def _recent_user_messages(user: User, limit: int = 3) -> list[str]:
    messages = sorted(user.chat_messages, key=lambda item: _as_utc(item.created_at))
    return [item.text.strip().lower() for item in messages if item.role == "user" and item.text.strip()][-limit:]


def _context_topic(user: User, text: str) -> str | None:
    current = text.lower()
    if any(word in current for word in ("завтра", "послезавтра")):
        return "tomorrow"

    recent = _recent_user_messages(user)
    combined = " ".join(recent + [current])
    if any(word in combined for word in ("гулять", "погулять", "прогул", "улиц", "выйти")):
        return "outdoor"
    if any(word in combined for word in ("работ", "офис", "на работе")):
        return "work"
    if any(word in combined for word in ("дом", "дома")):
        return "home"
    if any(word in combined for word in ("вода", "душ", "кран")):
        return "water"
    if any(word in combined for word in ("свет", "энерг", "электр")):
        return "energy"
    if any(word in combined for word in ("пластик", "бутыл", "пакет", "упаков")):
        return "plastic"
    if any(word in combined for word in ("мусор", "отход", "сортир", "переработ")):
        return "waste"
    if any(word in combined for word in ("транспорт", "машин", "автобус", "пеш")):
        return "transport"
    return None


def _last_activity_line(snapshot: dict[str, object]) -> str:
    last_activity = snapshot.get("last_activity")
    if last_activity is None:
        return ""
    return f"Последнее действие у тебя было в категории «{last_activity.category}»: {last_activity.title.lower()}."


def _actions_for_context(category: str, topic: str | None) -> list[str]:
    if topic == "work":
        return _work_actions_for_category(category)
    if topic == "outdoor":
        walk_actions = _outdoor_actions()
        return [
            walk_actions[0],
            f"взять с собой {walk_actions[1]}",
            "не покупать по дороге ничего одноразового",
        ]
    return _home_actions_for_category(category)


def _infer_user_intent(text: str) -> str:
    lowercase = text.lower()
    if _is_activity_sharing_message(lowercase):
        return "praise"
    if _is_smalltalk_request(text):
        return "smalltalk"
    if any(phrase in lowercase for phrase in ("что такое co2", "что такое co₂", "что значит co2", "что значит co₂")):
        return "explain"
    if any(phrase in lowercase for phrase in ("мой вклад", "мой прогресс", "как у меня дела", "что у меня по вкладу", "мой результат")):
        return "progress"
    if any(
        phrase in lowercase
        for phrase in ("проанализируй мои активности", "что видно по моим активностям", "что скажешь по моим активностям", "анализ моих активностей")
    ):
        return "analysis"
    if any(word in lowercase for word in ("мотивац", "не хочу", "лень", "сложно", "устал")):
        return "motivation"
    return "advice"


def _effective_topic(user: User, text: str) -> str | None:
    topic = _context_topic(user, text)
    if topic == "tomorrow":
        previous_context = _context_topic(user, " ".join(_recent_user_messages(user)))
        return previous_context or "tomorrow"
    return topic


def _personalized_fallback_response(text: str, user: User) -> str:
    lowercase = text.lower()
    snapshot = _analytics_snapshot(user)
    suggested_category = str(snapshot["suggested_category"])
    strongest_category = snapshot["strongest_category"]
    weakest_category = snapshot["weakest_category"]
    recent_points = int(snapshot["recent_points"])
    intro = _friendly_intro(user)
    last_activity_line = _last_activity_line(snapshot)
    strongest_line = f"Сильнее всего у тебя сейчас идёт «{strongest_category}»." if strongest_category else ""
    weakest_line = f"Меньше внимания пока получает «{weakest_category}»." if weakest_category else ""
    raw_topic = _context_topic(user, text)
    topic = _effective_topic(user, text)
    seed = f"{text}:{user.points}:{user.streak_days}"
    message_category = _message_category(text, suggested_category)
    streak_line = _streak_line(user)
    intent = _infer_user_intent(text)
    focus_category = message_category or suggested_category
    actions = _actions_for_context(focus_category, topic)
    context_lead = {
        "work": "Если говорить именно про то, что можно сделать на работе,",
        "outdoor": "Если отталкиваться от твоего маршрута или прогулки,",
        "home": "Если отталкиваться от дома,",
        "tomorrow": "Если смотреть на следующий шаг на завтра,",
    }.get(topic, "Если смотреть на это практично,")
    if raw_topic == "tomorrow":
        context_lead = "Если смотреть на следующий шаг на завтра,"

    if intent == "smalltalk":
        return (
            f"{_pick_variant(seed, ['Привет 🌱', 'Привет, я на связи 🌿', 'Привет, рад тебя видеть.'])} "
            f"{_pick_variant(seed, ['У меня всё спокойно, спасибо. Если захочешь, можем поболтать или придумать лёгкий eco-шаг на сегодня.', 'Всё хорошо. Если хочешь, могу просто поболтать или помочь с экологичной идеей без перегруза.', 'Всё ок. Могу и просто пообщаться, и помочь с eco-советом, если понадобится.'])}"
        )

    if intent == "praise":
        response_parts = [
            _praise_for_action(text, user, focus_category),
            streak_line,
            f"Если хочешь, следующим шагом можно { _natural_next_step(focus_category, topic) }.",
        ]
        return " ".join(part for part in response_parts if part).strip()

    if intent == "progress":
        return (
            f"Сейчас у тебя {user.points} очков, серия {user.streak_days} дн. и примерно {user.co2_saved_total:.1f} кг CO₂ экономии. "
            f"{strongest_line} {weakest_line} Если хочешь, я подберу следующий экологичный шаг без перегруза."
        ).strip()

    if intent == "explain":
        return (
            "CO2, или углекислый газ, это один из газов в атмосфере. "
            "Когда его становится слишком много из-за транспорта, энергии и производства, он усиливает изменение климата. "
            "Поэтому эко-привычки часто помогают уменьшать выбросы CO2."
        )

    if intent == "analysis":
        return (
            f"Если коротко по твоим активностям, за последние 7 дней у тебя уже {recent_points} очков. "
            f"{strongest_line} {weakest_line} {last_activity_line} "
            f"Логичнее всего сейчас дать чуть больше внимания категории «{focus_category}»."
        ).strip()

    if intent == "motivation":
        return (
            f"{_pick_variant(seed, ['Не тащи всё сразу.', 'Лучше не перегружать себя.', 'Тут не нужно делать много.'])} "
            f"Попробуй один микро-шаг: {actions[0]}. "
            f"{_pick_variant(seed, ['Этого уже достаточно, чтобы не выпадать из ритма.', 'Один спокойный шаг тоже считается вкладом.', 'Лучше маленький реальный шаг, чем большой план без сил.'])}"
        )

    return (
        f"{context_lead} логичнее всего сейчас сфокусироваться на категории «{focus_category}». "
        f"Например: {actions[0]}, {actions[1]} или {actions[2]}. "
        f"{_category_impact_hint(focus_category).capitalize()}. {_supportive_close(seed)}"
    ).strip()


def _is_too_generic_response(text: str) -> bool:
    normalized = " ".join(text.lower().split())
    generic_markers = [
        "если коротко: начни с самого простого практического шага",
        "если хочешь, уточни вопрос, и я отвечу точнее",
        "напиши вопрос чуть точнее",
        "по сути: сейчас логичнее всего дать чуть больше внимания категории",
    ]
    return any(marker in normalized for marker in generic_markers)


def _is_low_quality_model_response(user_text: str, response_text: str) -> bool:
    normalized_response = " ".join(response_text.lower().split())

    awkward_markers = [
        "давайте посмотрим в конкретности",
        "улучшить баланс",
        "это подойдет для",
        "сработает для твоего",
        "для твоего «своей активности»",
        "наслаждаться природой",
        "судя по твоим активностям",
        "если смотреть на твои действия",
        "если опираться на твой ритм",
        "перетянутый бутылок",
        "чашку чай",
        "за кухонь",
        "пользователь говорит",
        "нужно подстроить",
        "сначала посмотрю",
        "он говорит, что",
        "значит, нужно",
        "его данные:",
        "lastactivitydate",
        "streakdays:",
        "recordedactivities",
        "currentstreakdays",
        "strongestcategory",
        "weakestcategory",
        "topcategories",
        "последние активности:",
        "completedchallenges",
        "pendingchallengeclaims",
        "recentcategorycoverage",
        "основной состав атмосферы",
    ]
    if any(marker in normalized_response for marker in awkward_markers):
        return True

    if len(normalized_response.split()) > 160:
        return True

    # Reject answers that are clearly empty or useless.
    if len(normalized_response.split()) < 3:
        return True

    return False


def _fmt_dt(value: datetime) -> str:
    return value.strftime("%Y-%m-%d")


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _compact_activity_highlights(user: User, limit: int = 3) -> str:
    activities = sorted(user.activities, key=lambda item: _as_utc(item.created_at), reverse=True)[:limit]
    if not activities:
        return "нет записанных активностей"
    return "; ".join(
        f"{item.title} ({item.category}, {item.co2_saved:.2f} CO2, {_fmt_dt(item.created_at)})"
        for item in activities
    )


def _compact_challenge_highlights(user: User, limit: int = 3) -> str:
    items = sorted(user.user_challenges, key=lambda item: (item.is_completed, item.challenge.title), reverse=True)[:limit]
    if not items:
        return "нет активных челленджей"
    return "; ".join(
        f"{item.challenge.title} ({item.current_count}/{item.challenge.target_count}, {'completed' if item.is_completed else 'active'})"
        for item in items
    )


def _compact_profile_summary(user: User) -> str:
    pieces = [
        f"{user.points} очков",
        f"серия {user.streak_days} дн.",
        f"{user.co2_saved_total:.2f} кг CO2 сохранено",
    ]
    return ", ".join(pieces)


def _build_prompt(user: User, text: str) -> str:
    display_name = user.full_name.strip() or user.username
    return f"""
Пользователь EcoIZ:
- name: {display_name}
- profile: {_compact_profile_summary(user)}
- recentActivities: {_compact_activity_highlights(user)}
- challengeFocus: {_compact_challenge_highlights(user)}

Используй этот контекст мягко и выборочно.
""".strip() + f"\n\nТекущая реплика пользователя:\n{text.strip()}"


def _conversation_messages(user: User, text: str, history_limit: int) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [
        {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
        {
            "role": "system",
            "content": (
                "Ниже контекст пользователя EcoIZ. Это не шаблон ответа и не чеклист. "
                "Используй его мягко и выборочно, только когда он помогает ответить умнее и естественнее. "
                "Не пересказывай весь контекст и не делай сухой анализ без запроса.\n\n"
                f"{_build_prompt(user, text)}"
            ),
        },
    ]

    history = sorted(user.chat_messages, key=lambda item: _as_utc(item.created_at))[-history_limit:]
    for item in history:
        if not item.text.strip():
            continue
        role = "assistant" if item.role == "assistant" else "user"
        messages.append({"role": role, "content": item.text.strip()})

    messages.append({"role": "user", "content": text.strip()})
    return messages


def _openrouter_response(messages: list[dict[str, str]]) -> str | None:
    settings = get_settings()
    if not settings.openrouter_api_key:
        return None

    response = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.openrouter_model,
            "messages": messages,
            "temperature": settings.ai_temperature,
            "max_tokens": settings.ai_max_tokens,
        },
        timeout=settings.ai_timeout_seconds,
    )
    response.raise_for_status()
    payload = response.json()
    content = payload["choices"][0]["message"]["content"].strip()
    return content or None


def _openai_response(messages: list[dict[str, str]]) -> str | None:
    settings = get_settings()
    if not settings.openai_api_key:
        return None

    response = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.openai_model,
            "messages": messages,
            "temperature": settings.ai_temperature,
            "max_tokens": settings.ai_max_tokens,
        },
        timeout=settings.ai_timeout_seconds,
    )
    response.raise_for_status()
    payload = response.json()
    content = payload["choices"][0]["message"]["content"].strip()
    return content or None


def _normalize_model_response(text: str) -> str:
    normalized = text.strip()
    prefixes = (
        "ecoiz ai:",
        "ecoiz assistant:",
        "ассистент:",
        "ответ:",
    )
    lower = normalized.lower()
    for prefix in prefixes:
        if lower.startswith(prefix):
            normalized = normalized[len(prefix):].strip()
            lower = normalized.lower()
    return normalized


def ai_response(text: str, *, user: User | None = None) -> str:
    settings = get_settings()
    if user is None:
        return _fallback_response(text)

    messages = _conversation_messages(user, text, settings.ai_history_limit)
    personalized_fallback = _personalized_fallback_response(text, user)

    provider = settings.ai_provider
    if provider == "openrouter" and not settings.openrouter_api_key:
        provider = "openai" if settings.openai_api_key else "fallback"
    if provider == "openai" and not settings.openai_api_key:
        provider = "openrouter" if settings.openrouter_api_key else "fallback"
    if provider == "fallback":
        return personalized_fallback

    try:
        if provider == "openai":
            content = _openai_response(messages)
        else:
            content = _openrouter_response(messages)
        content = _normalize_model_response(content or "")
        if not content or _is_too_generic_response(content) or _is_low_quality_model_response(text, content):
            return personalized_fallback
        return content
    except Exception:
        return personalized_fallback
