import type { CommunityPost, PostFilters } from "@/lib/types";

type PostTableProps = {
  posts: CommunityPost[];
  selectedPostId: string;
  filters: PostFilters;
  onSelect: (postId: string) => void;
  onFilterChange: (filters: PostFilters) => void;
};

const stateOptions: Array<CommunityPost["state"] | "ALL"> = [
  "ALL",
  "Published",
  "Flagged",
  "Needs review",
  "Hidden",
];

const visibilityOptions: Array<CommunityPost["visibility"] | "ALL"> = [
  "ALL",
  "PUBLIC",
  "FOLLOWERS",
  "PRIVATE",
];

const stateLabels: Record<CommunityPost["state"] | "ALL", string> = {
  ALL: "Все статусы",
  Published: "Опубликован",
  Flagged: "Отмечен",
  "Needs review": "Нужна проверка",
  Hidden: "Скрыт",
};

const visibilityLabels: Record<CommunityPost["visibility"] | "ALL", string> = {
  ALL: "Вся видимость",
  PUBLIC: "Публичный",
  FOLLOWERS: "Подписчики",
  PRIVATE: "Приватный",
};

export function PostTable({
  posts,
  selectedPostId,
  filters,
  onSelect,
  onFilterChange,
}: PostTableProps) {
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
          <h2 className="section-title">Очередь модерации</h2>
        </div>
        <div className="filter-stack">
          <label className="inline-field inline-field-search">
            <span className="sr-only">Поиск постов</span>
            <input
              value={filters.search ?? ""}
              onChange={(event) =>
                onFilterChange({ ...filters, search: event.target.value })
              }
              placeholder="Поиск по автору или содержимому"
            />
          </label>
          <div className="filters-row">
            <label className="inline-field">
              <span className="sr-only">Фильтр по статусу</span>
              <select
                value={filters.state ?? "ALL"}
                onChange={(event) =>
                  onFilterChange({
                    ...filters,
                    state: event.target.value as CommunityPost["state"] | "ALL",
                  })
                }
              >
                {stateOptions.map((option) => (
                  <option key={option} value={option}>
                    {stateLabels[option]}
                  </option>
                ))}
              </select>
            </label>
            <label className="inline-field">
              <span className="sr-only">Фильтр по видимости</span>
              <select
                value={filters.visibility ?? "ALL"}
                onChange={(event) =>
                  onFilterChange({
                    ...filters,
                    visibility: event.target.value as
                      | CommunityPost["visibility"]
                      | "ALL",
                  })
                }
              >
                {visibilityOptions.map((option) => (
                  <option key={option} value={option}>
                    {visibilityLabels[option]}
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
              <th>Автор</th>
              <th>Видимость</th>
              <th>Статус</th>
              <th>Жалобы</th>
              <th>Создан</th>
            </tr>
          </thead>
          <tbody>
            {posts.map((post) => (
              <tr
                key={post.id}
                className={selectedPostId === post.id ? "table-row-active" : ""}
                onClick={() => onSelect(post.id)}
              >
                <td>{post.author}</td>
                <td>{visibilityLabels[post.visibility]}</td>
                <td>
                  <span className="pill">{stateLabels[post.state]}</span>
                </td>
                <td>{post.reportsCount}</td>
                <td>{formatDate(post.createdAt)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}
