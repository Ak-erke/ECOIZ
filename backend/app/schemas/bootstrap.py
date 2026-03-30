from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    fullName: str
    email: str
    points: int
    streakDays: int
    co2SavedTotal: float
    level: str


class ActivityResponse(BaseModel):
    id: str
    category: str
    title: str
    co2Saved: float
    points: int
    createdAt: datetime


class ChallengeResponse(BaseModel):
    id: str
    title: str
    description: str
    targetCount: int
    currentCount: int
    rewardPoints: int
    badgeSymbol: str
    badgeTintHex: int
    badgeBackgroundHex: int
    isCompleted: bool
    isClaimed: bool


class PostMediaResponse(BaseModel):
    id: str
    kind: str
    base64Data: str


class PostResponse(BaseModel):
    id: str
    author: str
    text: str
    createdAt: datetime
    media: list[PostMediaResponse]


class ChatMessageResponse(BaseModel):
    id: str
    isUser: bool
    text: str
    createdAt: datetime


class CommunityImpactResponse(BaseModel):
    totalUsers: int
    activeUsers: int
    totalActivities: int
    totalPosts: int
    totalChallengesCompleted: int
    totalCo2Saved: float
    totalPoints: int


class BootstrapResponse(BaseModel):
    user: UserProfileResponse
    activities: list[ActivityResponse]
    challenges: list[ChallengeResponse]
    posts: list[PostResponse]
    chatMessages: list[ChatMessageResponse]
    communityImpact: CommunityImpactResponse
