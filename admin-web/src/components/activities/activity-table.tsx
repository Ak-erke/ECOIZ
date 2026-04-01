import type { ActivityFilters, AdminActivity } from "@/lib/types";

type ActivityTableProps = {
  activities: AdminActivity[];
  selectedActivityId: string;
  filters: ActivityFilters;
  categoryOptions: string[];
  onSelect: (activityId: string) => void;
  onFilterChange: (filters: ActivityFilters) => void;
};

export function ActivityTable({
  activities,
  selectedActivityId,
  filters,
  categoryOptions,
  onSelect,
  onFilterChange,
}: ActivityTableProps) {
  function formatDate(value: string) {
    return new Intl.DateTimeFormat("ru-RU", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  }

  return (
    <article className="card">
      <div className="section-head section-head-stack">
        <div>
          <h2 className="section-title">Журнал активностей</h2>
        </div>
        <div className="filter-stack">
          <label className="inline-field inline-field-search">
            <span className="sr-only">Поиск активностей</span>
            <input
              value={filters.search ?? ""}
              onChange={(event) =>
                onFilterChange({ ...filters, search: event.target.value })
              }
              placeholder="Поиск по пользователю, названию, заметке или категории"
            />
          </label>
          <div className="filters-row">
            <label className="inline-field">
              <span className="sr-only">Фильтр по категории</span>
              <select
                value={filters.category ?? "ALL"}
                onChange={(event) =>
                  onFilterChange({
                    ...filters,
                    category: event.target.value,
                  })
                }
              >
                <option value="ALL">Все</option>
                {categoryOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Пользователь</th>
              <th>Категория</th>
              <th>Активность</th>
              <th>Баллы</th>
              <th>CO2</th>
              <th>Создано</th>
            </tr>
          </thead>
          <tbody>
            {activities.map((activity) => (
              <tr
                key={activity.id}
                className={selectedActivityId === activity.id ? "table-row-active" : ""}
                onClick={() => onSelect(activity.id)}
              >
                <td>{activity.username}</td>
                <td>{activity.category}</td>
                <td>{activity.title}</td>
                <td>{activity.points}</td>
                <td>{activity.co2Saved.toFixed(1)} кг</td>
                <td>{formatDate(activity.createdAt)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}
