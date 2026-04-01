import type { AdminUser, UserFilters, UserRole, UserStatus } from "@/lib/types";

type UserTableProps = {
  users: AdminUser[];
  selectedUserId: string;
  filters: UserFilters;
  onSelect: (userId: string) => void;
  onFilterChange: (filters: UserFilters) => void;
};

const roleOptions: Array<UserRole | "ALL"> = ["ALL", "ADMIN", "MODERATOR", "USER"];
const statusOptions: Array<UserStatus | "ALL"> = [
  "ALL",
  "ACTIVE",
  "REVIEW",
  "SUSPENDED",
];

const roleLabels: Record<UserRole | "ALL", string> = {
  ALL: "Все роли",
  ADMIN: "Админ",
  MODERATOR: "Модератор",
  USER: "Пользователь",
};

const statusLabels: Record<UserStatus | "ALL", string> = {
  ALL: "Все статусы",
  ACTIVE: "Активный",
  REVIEW: "На проверке",
  SUSPENDED: "Приостановлен",
};

export function UserTable({
  users,
  selectedUserId,
  filters,
  onSelect,
  onFilterChange,
}: UserTableProps) {
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
          <h2 className="section-title">Список пользователей</h2>
        </div>
        <div className="filter-stack">
          <label className="inline-field inline-field-search">
            <span className="sr-only">Поиск пользователей</span>
            <input
              value={filters.search ?? ""}
              onChange={(event) =>
                onFilterChange({ ...filters, search: event.target.value })
              }
              placeholder="Поиск по username или email"
            />
          </label>
          <div className="filters-row">
            <label className="inline-field">
              <span className="sr-only">Фильтр по роли</span>
              <select
                value={filters.role ?? "ALL"}
                onChange={(event) =>
                  onFilterChange({
                    ...filters,
                    role: event.target.value as UserRole | "ALL",
                  })
                }
              >
                {roleOptions.map((option) => (
                  <option key={option} value={option}>
                    {roleLabels[option]}
                  </option>
                ))}
              </select>
            </label>
            <label className="inline-field">
              <span className="sr-only">Фильтр по статусу</span>
              <select
                value={filters.status ?? "ALL"}
                onChange={(event) =>
                  onFilterChange({
                    ...filters,
                    status: event.target.value as UserStatus | "ALL",
                  })
                }
              >
                {statusOptions.map((option) => (
                  <option key={option} value={option}>
                    {statusLabels[option]}
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
              <th>Имя пользователя</th>
              <th>Email</th>
              <th>Роль</th>
              <th>Статус</th>
              <th>Eco баллы</th>
              <th>Создан</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr
                key={user.id}
                className={selectedUserId === user.id ? "table-row-active" : ""}
                onClick={() => onSelect(user.id)}
              >
                <td>{user.username}</td>
                <td>{user.email}</td>
                <td>
                  <span className="pill">{roleLabels[user.role]}</span>
                </td>
                <td>
                  <span className="pill">{statusLabels[user.status]}</span>
                </td>
                <td>{user.ecoPoints}</td>
                <td>{formatDate(user.createdAt)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}
