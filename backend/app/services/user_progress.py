from __future__ import annotations

from datetime import date, datetime, timezone

from app.models.challenge import UserChallenge
from app.models.user import Activity, User


def _streak_from_dates(activity_dates: list[date]) -> tuple[int, date | None]:
    if not activity_dates:
        return 0, None

    unique_dates = sorted(set(activity_dates), reverse=True)
    streak = 1
    latest = unique_dates[0]

    for previous, current in zip(unique_dates, unique_dates[1:]):
        if previous.toordinal() - current.toordinal() == 1:
            streak += 1
            continue
        break

    return streak, latest


def _progress_for_challenge(title: str, activities: list[Activity], posts_count: int, base_points: int) -> int:
    normalized = title.casefold()
    activities_sorted = sorted(activities, key=lambda item: item.created_at)
    distinct_days_by_category: dict[str, set[date]] = {}

    for item in activities_sorted:
        distinct_days_by_category.setdefault(item.category, set()).add(item.created_at.date())

    count_by_category = {
        category: sum(1 for item in activities_sorted if item.category == category)
        for category in {item.category for item in activities_sorted}
    }

    def keyword_matches(*keywords: str) -> int:
        return sum(
            1
            for item in activities_sorted
            if any(
                keyword in f"{item.title} {item.note or ''}".casefold()
                for keyword in keywords
            )
        )

    if normalized == "7 эко-действий за неделю":
        return len(activities_sorted)
    if normalized == "3 дня без пластика":
        return len(distinct_days_by_category.get("Пластик", set()))
    if normalized == "эко-транспорт":
        return len(distinct_days_by_category.get("Транспорт", set()))
    if normalized == "водный баланс":
        return count_by_category.get("Вода", 0)
    if normalized == "энергия под контролем":
        return count_by_category.get("Энергия", 0)
    if normalized == "неделя сортировки":
        return count_by_category.get("Отходы", 0)
    if normalized == "эко-утро":
        return sum(1 for item in activities_sorted if item.created_at.hour < 12)
    if normalized == "чистый воздух":
        return keyword_matches("пеш", "велосип", "самокат", "метро", "поезд", "общ.")
    if normalized == "многоразовый герой":
        return keyword_matches("многораз", "бутыл", "сумк")
    if normalized == "осознанный шопинг":
        return keyword_matches("пакет", "упаков", "сумк", "бутыл")
    if normalized == "эко-комьюнити":
        return posts_count
    if normalized == "зеленая неделя":
        return len(activities_sorted)
    if normalized == "ноль отходов":
        return len(distinct_days_by_category.get("Отходы", set()))
    if normalized == "дом без потерь":
        return count_by_category.get("Вода", 0) + count_by_category.get("Энергия", 0)
    if normalized == "эко-мастер":
        return base_points

    return 0


def recalculate_user_progress(user: User) -> None:
    activities = sorted(user.activities, key=lambda item: item.created_at)
    base_points = sum(item.points for item in activities)
    total_co2 = round(sum(item.co2_saved for item in activities), 2)
    streak_days, last_activity_on = _streak_from_dates([item.created_at.date() for item in activities])
    posts_count = len(user.posts)

    earned_reward_points = 0
    latest_activity_at = activities[-1].created_at if activities else datetime.now(timezone.utc)

    for item in user.user_challenges:
        progress = _progress_for_challenge(item.challenge.title, activities, posts_count, base_points)
        item.current_count = progress

        is_completed = progress >= item.challenge.target_count
        if is_completed:
            earned_reward_points += item.challenge.reward_points
            item.is_completed = True
            if item.completed_at is None:
                item.completed_at = latest_activity_at
        else:
            item.is_completed = False
            item.completed_at = None
            item.claimed_at = None

    user.points = base_points + earned_reward_points
    user.co2_saved_total = total_co2
    user.streak_days = streak_days
    user.last_activity_on = last_activity_on
