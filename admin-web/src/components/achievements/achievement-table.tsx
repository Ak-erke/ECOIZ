import type { Achievement, AchievementFilters } from "@/lib/types";

type AchievementTableProps = {
  achievements: Achievement[];
  selectedAchievementId: string;
  filters: AchievementFilters;
  onSelect: (achievementId: string) => void;
  onFilterChange: (filters: AchievementFilters) => void;
};

export function AchievementTable({
  achievements,
  selectedAchievementId,
  filters,
  onSelect,
  onFilterChange,
}: AchievementTableProps) {
  return (
    <article className="card">
      <div className="section-head section-head-stack">
        <div>
          <h2 className="section-title">Список ачивок</h2>
        </div>
        <div className="filter-stack">
          <label className="inline-field inline-field-search">
            <span className="sr-only">Поиск ачивок</span>
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
              <th>Иконка</th>
              <th>Цель</th>
              <th>Награда</th>
            </tr>
          </thead>
          <tbody>
            {achievements.map((achievement) => (
              <tr
                key={achievement.id}
                className={
                  selectedAchievementId === achievement.id
                    ? "table-row-active"
                    : ""
                }
                onClick={() => onSelect(achievement.id)}
              >
                <td>{achievement.title}</td>
                <td>{achievement.icon}</td>
                <td>{achievement.targetValue}</td>
                <td>{achievement.rewardPoints}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}
