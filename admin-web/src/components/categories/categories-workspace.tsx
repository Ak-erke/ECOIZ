"use client";

import { useDeferredValue, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { CategoryDetailPanel } from "@/components/categories/category-detail-panel";
import { CategoryMetricsCards } from "@/components/categories/category-metrics";
import { CategoryTable } from "@/components/categories/category-table";
import { StatePanel } from "@/components/state-panel";
import { getCategoryMetrics, listCategories } from "@/lib/api/categories";
import { queryKeys } from "@/lib/query-keys";
import type { CategoryFilters, CategoryMetrics, EcoCategory } from "@/lib/types";

type CategoriesWorkspaceProps = {
  initialCategories: EcoCategory[];
  metrics: CategoryMetrics;
};

export function CategoriesWorkspace({
  initialCategories,
  metrics,
}: CategoriesWorkspaceProps) {
  const [filters, setFilters] = useState<CategoryFilters>({ search: "" });
  const [selectedCategoryId, setSelectedCategoryId] = useState(
    initialCategories[0]?.id ?? "",
  );
  const deferredSearch = useDeferredValue(filters.search ?? "");
  const queryFilters = useMemo(
    () => ({ ...filters, search: deferredSearch }),
    [deferredSearch, filters],
  );
  const filtersKey = JSON.stringify(queryFilters);

  const categoriesQuery = useQuery({
    queryKey: queryKeys.categories.list(filtersKey),
    queryFn: () => listCategories(queryFilters),
    initialData: initialCategories,
    placeholderData: (previousData) => previousData,
  });

  const metricsQuery = useQuery({
    queryKey: queryKeys.categories.metrics,
    queryFn: getCategoryMetrics,
    initialData: metrics,
  });

  const filteredCategories = categoriesQuery.data;

  const selectedCategory =
    filteredCategories.find((category: EcoCategory) => category.id === selectedCategoryId) ??
    filteredCategories[0];

  return (
    <>
      <CategoryMetricsCards metrics={metricsQuery.data} />

      <section className="split" style={{ marginTop: 16 }}>
        <CategoryTable
          categories={filteredCategories}
          selectedCategoryId={selectedCategory?.id ?? ""}
          filters={filters}
          onSelect={setSelectedCategoryId}
          onFilterChange={setFilters}
        />
        {selectedCategory ? (
          <CategoryDetailPanel category={selectedCategory} />
        ) : categoriesQuery.isLoading || categoriesQuery.isFetching ? (
          <StatePanel
            title="Загружаем категории"
            description="Обновляем каталог категорий и применяем поиск."
          />
        ) : categoriesQuery.isError ? (
          <StatePanel
            title="Не удалось загрузить категории"
            description="Каталог категорий не загрузился. Попробуй обновить страницу."
            tone="error"
          />
        ) : (
          <StatePanel
            title="Категории не найдены"
            description="Очисти поиск, чтобы снова увидеть весь каталог категорий."
            tone="warning"
          />
        )}
      </section>
    </>
  );
}
