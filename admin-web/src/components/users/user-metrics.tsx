import { MetricCards } from "@/components/metric-cards";
import type { UserMetrics } from "@/lib/types";

type UserMetricsProps = {
  metrics: UserMetrics;
};

export function UserMetricsCards({ metrics }: UserMetricsProps) {
  const cards = [
    {
      label: "Всего пользователей",
      value: metrics.totalUsers,
      note: "Текущий размер пользовательской базы",
    },
    {
      label: "Расширенный доступ",
      value: metrics.adminCount,
      note: "Админы и модераторы платформы",
    },
    {
      label: "На проверке",
      value: metrics.needsReview,
      note: "Аккаунты, которым нужна модерация",
    },
    {
      label: "Подтвержден email",
      value: metrics.verifiedCount,
      note: "Готовы к безопасным действиям админа",
    },
  ];

  return <MetricCards items={cards} columns="four" />;
}
