import { MetricCards } from "@/components/metric-cards";
import type { PostMetrics } from "@/lib/types";

type PostMetricsProps = {
  metrics: PostMetrics;
};

export function PostMetricsCards({ metrics }: PostMetricsProps) {
  const cards = [
    {
      label: "Всего постов",
      value: metrics.totalPosts,
      note: "Текущий объем модерации",
    },
    {
      label: "Отмеченные",
      value: metrics.flaggedPosts,
      note: "Требуют внимания в первую очередь",
    },
    {
      label: "Скрытые",
      value: metrics.hiddenPosts,
      note: "Уже убраны из публичного просмотра",
    },
    {
      label: "Жалобы",
      value: metrics.totalReports,
      note: "Общее количество жалоб по текущим постам",
    },
  ];

  return <MetricCards items={cards} columns="four" />;
}
