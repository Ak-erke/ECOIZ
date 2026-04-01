"use client";

import { useQuery } from "@tanstack/react-query";

import { MetricCards } from "@/components/metric-cards";
import { StatePanel } from "@/components/state-panel";
import { getAchievementMetrics, listAchievements } from "@/lib/api/achievements";
import { getCategoryMetrics } from "@/lib/api/categories";
import { isMockMode } from "@/lib/config";
import { getHabitMetrics } from "@/lib/api/habits";
import { getPostMetrics, listPosts } from "@/lib/api/posts";
import { queryKeys } from "@/lib/query-keys";
import { getAdminUserMetrics, listAdminUsers } from "@/lib/api/users";
import type {
  Achievement,
  AchievementMetrics,
  CommunityPost,
  PostMetrics,
  UserMetrics,
} from "@/lib/types";

type DashboardWorkspaceProps = {
  initialUserMetrics: UserMetrics;
  initialHabitMetrics: {
    totalHabits: number;
    totalPoints: number;
    categoriesUsed: number;
  };
  initialAchievementMetrics: AchievementMetrics;
  initialPostMetrics: PostMetrics;
  initialCategoryMetrics: {
    totalCategories: number;
    uniqueColors: number;
    iconCount: number;
  };
  initialPosts: CommunityPost[];
  initialUsers: Array<{
    id: string;
    username: string;
    email: string;
    role: "USER" | "ADMIN" | "MODERATOR";
    isEmailVerified: boolean;
    ecoPoints: number;
    streakDays: number;
    postsCount: number;
    createdAt: string;
    status: "ACTIVE" | "REVIEW" | "SUSPENDED";
  }>;
  initialAchievements: Achievement[];
};

export function DashboardWorkspace({
  initialUserMetrics,
  initialHabitMetrics,
  initialAchievementMetrics,
  initialPostMetrics,
  initialCategoryMetrics,
  initialPosts,
  initialUsers,
  initialAchievements,
}: DashboardWorkspaceProps) {
  const postStateLabels: Record<CommunityPost["state"], string> = {
    Published: "Опубликован",
    Flagged: "Отмечен",
    "Needs review": "Нужна проверка",
    Hidden: "Скрыт",
  };

  const userMetricsQuery = useQuery({
    queryKey: queryKeys.users.metrics,
    queryFn: getAdminUserMetrics,
    initialData: initialUserMetrics,
  });

  const habitMetricsQuery = useQuery({
    queryKey: queryKeys.habits.metrics,
    queryFn: getHabitMetrics,
    initialData: initialHabitMetrics,
  });

  const achievementMetricsQuery = useQuery({
    queryKey: queryKeys.achievements.metrics,
    queryFn: getAchievementMetrics,
    initialData: initialAchievementMetrics,
  });

  const postMetricsQuery = useQuery({
    queryKey: queryKeys.posts.metrics,
    queryFn: getPostMetrics,
    initialData: initialPostMetrics,
  });

  const categoryMetricsQuery = useQuery({
    queryKey: queryKeys.categories.metrics,
    queryFn: getCategoryMetrics,
    initialData: initialCategoryMetrics,
  });

  const postsQuery = useQuery({
    queryKey: queryKeys.posts.list("dashboard"),
    queryFn: () => listPosts(),
    initialData: initialPosts,
    placeholderData: (previousData) => previousData,
  });

  const usersQuery = useQuery({
    queryKey: queryKeys.users.list("dashboard"),
    queryFn: () => listAdminUsers(),
    initialData: initialUsers,
    placeholderData: (previousData) => previousData,
  });

  const achievementsQuery = useQuery({
    queryKey: queryKeys.achievements.list("dashboard"),
    queryFn: () => listAchievements(),
    initialData: initialAchievements,
    placeholderData: (previousData) => previousData,
  });

  const hasError =
    userMetricsQuery.isError ||
    habitMetricsQuery.isError ||
    achievementMetricsQuery.isError ||
    postMetricsQuery.isError ||
    categoryMetricsQuery.isError ||
    postsQuery.isError ||
    usersQuery.isError ||
    achievementsQuery.isError;

  if (hasError) {
    return (
      <StatePanel
        title="Не удалось загрузить панель"
        description="Часть данных панели сейчас недоступна. Попробуй обновить страницу."
        tone="error"
      />
    );
  }

  const userMetrics = userMetricsQuery.data;
  const habitMetrics = habitMetricsQuery.data;
  const achievementMetrics = achievementMetricsQuery.data;
  const postMetrics = postMetricsQuery.data;
  const categoryMetrics = categoryMetricsQuery.data;
  const posts = postsQuery.data;
  const users = usersQuery.data;
  const achievements = achievementsQuery.data;

  const isBootstrappingLiveDashboard =
    !isMockMode() &&
    (userMetricsQuery.isFetching ||
      habitMetricsQuery.isFetching ||
      achievementMetricsQuery.isFetching ||
      postMetricsQuery.isFetching ||
      categoryMetricsQuery.isFetching ||
      postsQuery.isFetching ||
      usersQuery.isFetching ||
      achievementsQuery.isFetching) &&
    userMetrics.totalUsers === 0 &&
    habitMetrics.totalHabits === 0 &&
    achievementMetrics.totalAchievements === 0 &&
    postMetrics.totalPosts === 0 &&
    categoryMetrics.totalCategories === 0 &&
    posts.length === 0 &&
    users.length === 0 &&
    achievements.length === 0;

  if (isBootstrappingLiveDashboard) {
    return (
      <StatePanel
        title="Загружаем панель"
        description="Получаем live-метрики, каталоги и текущее состояние модерации."
      />
    );
  }

  const topMetrics = [
    {
      label: "Пользователи",
      value: String(userMetrics.totalUsers),
      note: `${userMetrics.verifiedCount} подтверждено, ${userMetrics.needsReview} на проверке`,
    },
    {
      label: "Каталог активностей",
      value: String(habitMetrics.totalHabits),
      note: `${habitMetrics.categoriesUsed} категорий, ${habitMetrics.totalPoints} баллов`,
    },
    {
      label: "Посты на модерации",
      value: String(
        posts.filter(
          (post) => post.state === "Flagged" || post.state === "Needs review",
        ).length,
      ),
      note: `${postMetrics.flaggedPosts} отмечено, ${postMetrics.totalReports} жалоб`,
    },
    {
      label: "Ачивки",
      value: String(achievementMetrics.totalAchievements),
      note: `${achievementMetrics.totalRewardPoints} баллов награды в каталоге`,
    },
  ];

  const moderationQueue = posts
    .filter((post) => post.state === "Flagged" || post.state === "Needs review")
    .map((post) => ({
      label: `Пост от ${post.author}`,
      status: postStateLabels[post.state],
      owner: "Модератор",
    }));

  const operationsQueue = [
    {
      label: "Пользователи на проверке",
      status: `${userMetrics.needsReview} ожидают`,
      owner: "Админ",
    },
    {
      label: "Состояние категорий",
      status: `${categoryMetrics.totalCategories} активно`,
      owner: "Контент",
    },
    {
      label: "Состояние ачивок",
      status: `${achievements.length} настроено`,
      owner: "Продукт",
    },
  ];

  const recentItems = [
    `${postMetrics.flaggedPosts} постов сейчас отмечены для модерации`,
    `${userMetrics.adminCount} пользователей имеют расширенный доступ`,
    `${habitMetrics.totalHabits} активностей доступны в каталоге`,
    `${achievementMetrics.maxTargetValue} — текущий максимальный порог у ачивок`,
  ];

  return (
    <>
      <MetricCards items={topMetrics} columns="four" />

      <section className="split" style={{ marginTop: 16 }}>
        <article className="card">
          <h2 className="section-title">Фокус на сегодня</h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Очередь</th>
                  <th>Статус</th>
                  <th>Ответственный</th>
                </tr>
              </thead>
              <tbody>
                {[...moderationQueue, ...operationsQueue].map((item) => (
                  <tr key={`${item.label}-${item.status}`}>
                    <td>{item.label}</td>
                    <td>
                      <span className="pill">{item.status}</span>
                    </td>
                    <td>{item.owner}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>

        <article className="card">
          <h2 className="section-title">Сводка по системе</h2>
          <div className="grid">
            {recentItems.map((item) => (
              <div key={item} className="card" style={{ padding: 14 }}>
                {item}
              </div>
            ))}
          </div>
        </article>
      </section>
    </>
  );
}
