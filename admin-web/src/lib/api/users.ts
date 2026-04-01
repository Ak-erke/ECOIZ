import { apiRequest } from "@/lib/api/client";
import { wait } from "@/lib/api/helpers";
import { isMockMode } from "@/lib/config";
import { mockAchievements, mockPosts, mockUsers } from "@/lib/mocks";
import type {
  AdminUserDetail,
  AdminUser,
  UpdateAdminUserPayload,
  UserFilters,
  UserMetrics,
} from "@/lib/types";

export async function listAdminUsers(
  filters: UserFilters = {},
): Promise<AdminUser[]> {
  if (!isMockMode()) {
    const params = new URLSearchParams();
    if (filters.role && filters.role !== "ALL") params.set("role", filters.role);
    if (filters.status && filters.status !== "ALL") {
      params.set("status", filters.status);
    }
    if (filters.search?.trim()) params.set("search", filters.search.trim());

    return apiRequest<AdminUser[]>(
      `/admin/users${params.size ? `?${params.toString()}` : ""}`,
    );
  }

  await wait(80);

  return mockUsers.filter((user) => {
    const matchesRole =
      !filters.role || filters.role === "ALL" || user.role === filters.role;
    const matchesStatus =
      !filters.status ||
      filters.status === "ALL" ||
      user.status === filters.status;
    const query = filters.search?.trim().toLowerCase();
    const matchesSearch =
      !query ||
      user.username.toLowerCase().includes(query) ||
      user.email.toLowerCase().includes(query);

    return matchesRole && matchesStatus && matchesSearch;
  });
}

export async function getAdminUserMetrics(): Promise<UserMetrics> {
  if (!isMockMode()) {
    return apiRequest<UserMetrics>("/admin/users/metrics");
  }

  await wait(40);

  return {
    totalUsers: mockUsers.length,
    adminCount: mockUsers.filter((user) =>
      user.role === "ADMIN" || user.role === "MODERATOR",
    ).length,
    needsReview: mockUsers.filter((user) => user.status === "REVIEW").length,
    verifiedCount: mockUsers.filter((user) => user.isEmailVerified).length,
  };
}

function mockUserLevel(points: number): string {
  if (points < 200) return "Эко-новичок";
  if (points < 400) return "Эко-исследователь";
  if (points < 700) return "Эко-помощник";
  if (points < 1100) return "Хранитель природы";
  if (points < 1600) return "Зеленый герой";
  if (points < 2200) return "Эко-наставник";
  if (points < 3000) return "Защитник планеты";
  if (points < 4000) return "Мастер устойчивости";
  if (points < 5500) return "Амбассадор Eco Iz";
  return "Хранитель Земли";
}

export async function getAdminUserDetail(userId: string): Promise<AdminUserDetail> {
  if (!isMockMode()) {
    return apiRequest<AdminUserDetail>(`/admin/users/${userId}`);
  }

  await wait(80);

  const user = mockUsers.find((item) => item.id === userId);
  if (!user) {
    throw new Error("User not found");
  }

  return {
    ...user,
    fullName: user.username,
    level: mockUserLevel(user.ecoPoints),
    co2SavedTotal: Number((user.ecoPoints / 42).toFixed(1)),
    adminNote: "Role and status changes will later be sent to backend audit logs.",
    recentActivities: [
      {
        id: `${user.id}-activity-1`,
        userId: user.id,
        username: user.username,
        userEmail: user.email,
        category: "Транспорт",
        title: "Пешая прогулка",
        co2Saved: 1.5,
        points: 20,
        note: "Университет вместо такси",
        createdAt: "2026-03-29T08:30:00Z",
      },
      {
        id: `${user.id}-activity-2`,
        userId: user.id,
        username: user.username,
        userEmail: user.email,
        category: "Вода",
        title: "Короткий душ",
        co2Saved: 0,
        points: 15,
        note: "Сократила душ до 5 минут",
        createdAt: "2026-03-28T09:10:00Z",
      },
    ],
    challenges: mockAchievements.slice(0, 4).map((achievement, index) => ({
      id: achievement.id,
      title: achievement.title,
      description: achievement.description,
      targetCount: achievement.targetValue,
      currentCount: Math.min(achievement.targetValue, (index + 1) * 3),
      rewardPoints: achievement.rewardPoints,
      badgeSymbol: achievement.icon,
      badgeTintHex: 0x43b244,
      badgeBackgroundHex: 0xeaf8df,
      isCompleted: index % 2 === 0,
      isClaimed: index === 0,
    })),
    recentPosts: mockPosts
      .filter((post) => post.author === user.username)
      .slice(0, 3)
      .map((post) => ({
        ...post,
        mediaCount: 0,
      })),
  };
}

export async function updateAdminUser(
  userId: string,
  payload: UpdateAdminUserPayload,
): Promise<AdminUser> {
  if (!isMockMode()) {
    return apiRequest<AdminUser>(`/admin/users/${userId}`, {
      method: "PATCH",
      body: payload,
    });
  }

  await wait(120);

  const user = mockUsers.find((item) => item.id === userId);
  if (!user) {
    throw new Error("User not found");
  }

  return {
    ...user,
    role: payload.role,
    status: payload.status,
  };
}

export async function verifyAdminUserEmail(userId: string): Promise<AdminUser> {
  if (!isMockMode()) {
    return apiRequest<AdminUser>(`/admin/users/${userId}/verify-email`, {
      method: "POST",
    });
  }

  await wait(120);

  const user = mockUsers.find((item) => item.id === userId);
  if (!user) {
    throw new Error("User not found");
  }

  user.isEmailVerified = true;
  return { ...user };
}

export async function deleteAdminUser(userId: string): Promise<void> {
  if (!isMockMode()) {
    return apiRequest<void>(`/admin/users/${userId}`, {
      method: "DELETE",
    });
  }

  await wait(120);

  const index = mockUsers.findIndex((item) => item.id === userId);
  if (index === -1) {
    throw new Error("User not found");
  }

  mockUsers.splice(index, 1);
}
