"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { useToast } from "@/components/toast-provider";
import { deleteActivity } from "@/lib/api/activities";
import { queryKeys } from "@/lib/query-keys";
import type { AdminActivity } from "@/lib/types";

type ActivityDetailPanelProps = {
  activity: AdminActivity;
};

export function ActivityDetailPanel({ activity }: ActivityDetailPanelProps) {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const deleteMutation = useMutation({
    mutationFn: () => deleteActivity(activity.id),
    onSuccess: async () => {
      showToast({
        tone: "success",
        title: "Активность удалена",
        description: `Запись "${activity.title}" была удалена.`,
      });
      await queryClient.invalidateQueries({ queryKey: queryKeys.activities.all });
      await queryClient.invalidateQueries({ queryKey: queryKeys.activities.metrics });
      await queryClient.invalidateQueries({ queryKey: queryKeys.users.all });
      await queryClient.invalidateQueries({ queryKey: queryKeys.users.detail(activity.userId) });
      await queryClient.invalidateQueries({ queryKey: queryKeys.users.metrics });
    },
    onError: () => {
      showToast({
        tone: "error",
        title: "Удаление не удалось",
        description: "Не получилось удалить активность.",
      });
    },
  });

  function formatDate(value: string) {
    return new Intl.DateTimeFormat("ru-RU", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  }

  function onDelete() {
    const confirmed = window.confirm(
      `Удалить активность "${activity.title}"? Это действие нельзя отменить.`,
    );
    if (!confirmed) return;
    deleteMutation.mutate();
  }

  return (
    <article className="card">
      <h2 className="section-title">Выбранная активность</h2>
      <div className="detail-stack">
        <div className="detail-row">
          <span className="muted">Пользователь</span>
          <strong>{activity.username}</strong>
        </div>
        <div className="detail-row">
          <span className="muted">Email</span>
          <strong>{activity.userEmail}</strong>
        </div>
        <div className="detail-row">
          <span className="muted">Категория</span>
          <strong>{activity.category}</strong>
        </div>
        <div className="detail-row">
          <span className="muted">Название</span>
          <strong>{activity.title}</strong>
        </div>
        <div className="detail-row">
          <span className="muted">Баллы</span>
          <strong>{activity.points}</strong>
        </div>
        <div className="detail-row">
          <span className="muted">Сэкономлено CO2</span>
          <strong>{activity.co2Saved.toFixed(1)} кг</strong>
        </div>
        <div className="detail-row">
          <span className="muted">Создано</span>
          <strong>{formatDate(activity.createdAt)}</strong>
        </div>
      </div>

      <div className="form-shell">
        <label className="field">
          <span>Заметка пользователя</span>
          <textarea
            rows={5}
            value={activity.note || "Для этой активности заметка не указана."}
            readOnly
          />
        </label>
        <p className="form-status muted">
          Активности пока редактируются только частично. Этот блок нужен для просмотра, поддержки и удаления.
        </p>
        <div className="button-row">
          <button
            type="button"
            className="ghost-button danger-button"
            onClick={onDelete}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? "Удаляем..." : "Удалить активность"}
          </button>
        </div>
      </div>
    </article>
  );
}
