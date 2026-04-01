import base64

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat import ChatMessage
from app.models.challenge import Challenge
from app.models.challenge import UserChallenge
from app.models.post import Post, PostMedia
from app.models.user import Activity, User
from app.schemas.bootstrap import (
    ActivityResponse,
    BootstrapResponse,
    CommunityImpactResponse,
    ChallengeResponse,
    ChatMessageResponse,
    PostMediaResponse,
    PostResponse,
    UserProfileResponse,
)

LEVELS = [
    (1, "Эко-новичок", 0, 200),
    (2, "Эко-исследователь", 200, 400),
    (3, "Эко-помощник", 400, 700),
    (4, "Хранитель природы", 700, 1100),
    (5, "Зеленый герой", 1100, 1600),
    (6, "Эко-наставник", 1600, 2200),
    (7, "Защитник планеты", 2200, 3000),
    (8, "Мастер устойчивости", 3000, 4000),
    (9, "Амбассадор Eco Iz", 4000, 5500),
    (10, "Хранитель Земли", 5500, None),
]


def user_level_number(points: int) -> int:
    for number, _, lower_bound, upper_bound in LEVELS:
        if upper_bound is None or lower_bound <= points < upper_bound:
            return number
    return LEVELS[-1][0]


def user_level(points: int) -> str:
    level_number = user_level_number(points)
    return next(name for number, name, _, _ in LEVELS if number == level_number)


def unlocked_challenge_count(points: int) -> int:
    if points < 120:
        return 5
    if points < 320:
        return 10
    return 15


def challenge_sort_key(challenge: Challenge) -> tuple[int, str]:
    return (challenge.reward_points, challenge.title)


def serialize_user(user: User) -> UserProfileResponse:
    return UserProfileResponse(
        id=str(user.id),
        fullName=user.full_name,
        email=user.email,
        points=user.points,
        streakDays=user.streak_days,
        co2SavedTotal=user.co2_saved_total,
        level=user_level(user.points),
    )


def serialize_activity(activity: Activity) -> ActivityResponse:
    return ActivityResponse(
        id=str(activity.id),
        category=activity.category,
        title=activity.title,
        co2Saved=activity.co2_saved,
        points=activity.points,
        createdAt=activity.created_at,
    )


def serialize_user_challenge(item: UserChallenge) -> ChallengeResponse:
    challenge = item.challenge
    display_count = min(item.current_count, challenge.target_count)
    return ChallengeResponse(
        id=str(challenge.id),
        title=challenge.title,
        description=challenge.description,
        targetCount=challenge.target_count,
        currentCount=display_count,
        rewardPoints=challenge.reward_points,
        badgeSymbol=challenge.badge_symbol,
        badgeTintHex=challenge.badge_tint_hex,
        badgeBackgroundHex=challenge.badge_background_hex,
        isCompleted=item.is_completed,
        isClaimed=item.claimed_at is not None,
    )


def serialize_media(item: PostMedia) -> PostMediaResponse:
    return PostMediaResponse(
        id=str(item.id),
        kind=item.kind,
        base64Data=base64.b64encode(item.data).decode("utf-8"),
    )


def serialize_post(post: Post) -> PostResponse:
    return PostResponse(
        id=str(post.id),
        author=post.author_name,
        text=post.text,
        createdAt=post.created_at,
        media=[serialize_media(media) for media in post.media],
    )


def serialize_chat_message(message: ChatMessage) -> ChatMessageResponse:
    return ChatMessageResponse(
        id=str(message.id),
        isUser=message.role == "user",
        text=message.text,
        createdAt=message.created_at,
    )


def serialize_community_impact(db: Session) -> CommunityImpactResponse:
    users = db.scalars(select(User)).all()
    activities = db.scalars(select(Activity)).all()
    posts = db.scalars(select(Post)).all()
    challenge_items = db.scalars(select(UserChallenge)).all()

    active_user_ids = {item.user_id for item in activities}
    completed_challenge_count = sum(1 for item in challenge_items if item.is_completed)

    return CommunityImpactResponse(
        totalUsers=len(users),
        activeUsers=len(active_user_ids),
        totalActivities=len(activities),
        totalPosts=len(posts),
        totalChallengesCompleted=completed_challenge_count,
        totalCo2Saved=round(sum(item.co2_saved for item in activities), 2),
        totalPoints=sum(item.points for item in users),
    )


def build_bootstrap(user: User, db: Session) -> BootstrapResponse:
    return BootstrapResponse(
        user=serialize_user(user),
        activities=[serialize_activity(item) for item in sorted(user.activities, key=lambda value: value.created_at, reverse=True)],
        challenges=[serialize_user_challenge(item) for item in user.user_challenges],
        posts=[serialize_post(item) for item in sorted(user.posts, key=lambda value: value.created_at, reverse=True)],
        chatMessages=[serialize_chat_message(item) for item in sorted(user.chat_messages, key=lambda value: value.created_at)],
        communityImpact=serialize_community_impact(db),
    )
