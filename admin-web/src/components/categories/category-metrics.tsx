import { MetricCards } from "@/components/metric-cards";
import type { CategoryMetrics } from "@/lib/types";

type CategoryMetricsProps = {
  metrics: CategoryMetrics;
};

export function CategoryMetricsCards({ metrics }: CategoryMetricsProps) {
  const cards = [
    {
      label: "Всего категорий",
      value: metrics.totalCategories,
      note: "Текущие разделы eco-каталога",
    },
    {
      label: "Уникальные цвета",
      value: metrics.uniqueColors,
      note: "Используются для визуального различия",
    },
    {
      label: "Иконки",
      value: metrics.iconCount,
      note: "Количество используемых иконок",
    },
  ];

  return <MetricCards items={cards} columns="three" />;
}
