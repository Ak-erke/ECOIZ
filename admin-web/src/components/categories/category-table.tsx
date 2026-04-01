import type { CategoryFilters, EcoCategory } from "@/lib/types";

type CategoryTableProps = {
  categories: EcoCategory[];
  selectedCategoryId: string;
  filters: CategoryFilters;
  onSelect: (categoryId: string) => void;
  onFilterChange: (filters: CategoryFilters) => void;
};

export function CategoryTable({
  categories,
  selectedCategoryId,
  filters,
  onSelect,
  onFilterChange,
}: CategoryTableProps) {
  return (
    <article className="card">
      <div className="section-head section-head-stack">
        <div>
          <h2 className="section-title">Список категорий</h2>
        </div>
        <div className="filter-stack">
          <label className="inline-field inline-field-search">
            <span className="sr-only">Поиск категорий</span>
            <input
              value={filters.search ?? ""}
              onChange={(event) =>
                onFilterChange({ ...filters, search: event.target.value })
              }
              placeholder="Поиск по названию, описанию или иконке"
            />
          </label>
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Название</th>
              <th>Описание</th>
              <th>Цвет</th>
              <th>Иконка</th>
            </tr>
          </thead>
          <tbody>
            {categories.map((category) => (
              <tr
                key={category.id}
                className={
                  selectedCategoryId === category.id ? "table-row-active" : ""
                }
                onClick={() => onSelect(category.id)}
              >
                <td>{category.name}</td>
                <td>{category.description}</td>
                <td>
                  <span className="pill">{category.color}</span>
                </td>
                <td>{category.icon}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}
