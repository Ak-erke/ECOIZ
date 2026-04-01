import { MetricCards } from "@/components/metric-cards";
import type { AchievementMetrics } from "@/lib/types";

type AchievementMetricsProps = {
  metrics: AchievementMetrics;
};

export function AchievementMetricsCards({
  metrics,
}: AchievementMetricsProps) {
  const cards = [
    {
      label: "Всего ачивок",
      value: metrics.totalAchievements,
      note: "Текущий каталог ачивок",
    },
    {
      label: "Баллы наград",
      value: metrics.totalRewardPoints,
      note: "Суммарные награды по всем ачивкам",
    },
    {
      label: "Максимальная цель",
      value: metrics.maxTargetValue,
      note: "Наибольшее пороговое значение",
    },
  ];

  return <MetricCards items={cards} columns="three" />;
}
