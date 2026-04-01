"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";

import { useToast } from "@/components/toast-provider";
import { useAuth } from "@/components/auth-provider";
import {
  deleteAdminUser,
  getAdminUserDetail,
  updateAdminUser,
  verifyAdminUserEmail,
} from "@/lib/api/users";
import { queryKeys } from "@/lib/query-keys";
import type { AdminUser, AdminUserDetail, UpdateAdminUserPayload } from "@/lib/types";
import { userFormSchema, type UserFormValues } from "@/lib/validation";

type UserDetailPanelProps = {
  user: AdminUser;
};

const roleLabels = {
  ADMIN: "Админ",
  MODERATOR: "Модератор",
  USER: "Пользователь",
} as const;

const statusLabels = {
  ACTIVE: "Активный",
  REVIEW: "На проверке",
  SUSPENDED: "Приостановлен",
} as const;

export function UserDetailPanel({ user }: UserDetailPanelProps) {
  const [challengesExpanded, setChallengesExpanded] = useState(false);
  const { user: currentStaff } = useAuth();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const detailQuery = useQuery({
    queryKey: queryKeys.users.detail(user.id),
    queryFn: () => getAdminUserDetail(user.id),
  });
  const detail = detailQuery.data;
  const defaultAdminNote =
    detail?.adminNote ||
    "Изменения роли и статуса позже будут попадать в аудит-лог backend.";
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors, isDirty },
  } = useForm<UserFormValues>({
    resolver: zodResolver(userFormSchema),
    defaultValues: {
      role: user.role,
      status: user.status,
      adminNote:
        "Изменения роли и статуса позже будут попадать в аудит-лог backend.",
    },
  });
  const mutation = useMutation({
    mutationFn: (payload: UpdateAdminUserPayload) => updateAdminUser(user.id, payload),
    onSuccess: async (updated) => {
      showToast({
        tone: "success",
        title: "Пользователь обновлен",
        description: `Изменения для ${updated.username} сохранены.`,
      });
      await queryClient.invalidateQueries({ queryKey: queryKeys.users.all });
      await queryClient.invalidateQueries({ queryKey: queryKeys.users.detail(user.id) });
      await queryClient.invalidateQueries({ queryKey: queryKeys.users.metrics });
    },
    onError: () => {
      showToast({
        tone: "error",
        title: "Не удалось сохранить",
        description: "Изменения пользователя не были сохранены.",
      });
    },
  });
  const deleteMutation = useMutation({
    mutationFn: () => deleteAdminUser(user.id),
    onSuccess: async () => {
      showToast({
        tone: "success",
        title: "Пользователь удален",
        description: `Аккаунт ${user.username} был удален.`,
      });
      await queryClient.invalidateQueries({ queryKey: queryKeys.users.all });
      await queryClient.invalidateQueries({ queryKey: queryKeys.users.metrics });
      await queryClient.invalidateQueries({ queryKey: queryKeys.activities.all });
      await queryClient.invalidateQueries({ queryKey: queryKeys.activities.metrics });
      await queryClient.invalidateQueries({ queryKey: queryKeys.posts.all });
      await queryClient.invalidateQueries({ queryKey: queryKeys.posts.metrics });
    },
    onError: () => {
      showToast({
        tone: "error",
        title: "Удаление не удалось",
        description: "Не получилось удалить пользователя.",
      });
    },
  });
  const verifyEmailMutation = useMutation({
    mutationFn: () => verifyAdminUserEmail(user.id),
    onSuccess: async () => {
      showToast({
        tone: "success",
        title: "Email подтвержден",
        description: `Email пользователя ${user.username} отмечен как подтвержденный.`,
      });
      await queryClient.invalidateQueries({ queryKey: queryKeys.users.all });
      await queryClient.invalidateQueries({ queryKey: queryKeys.users.detail(user.id) });
      await queryClient.invalidateQueries({ queryKey: queryKeys.users.metrics });
    },
    onError: () => {
      showToast({
        tone: "error",
        title: "Не удалось подтвердить email",
        description: "Попробуй выполнить действие еще раз.",
      });
    },
  });

  useEffect(() => {
    reset({
      role: detail?.role ?? user.role,
      status: detail?.status ?? user.status,
      adminNote: detail?.adminNote || defaultAdminNote,
    });
  }, [defaultAdminNote, detail, reset, user]);

  function onSubmit(values: UserFormValues) {
    mutation.mutate(values);
  }

  function onDelete() {
    const confirmed = window.confirm(
      `Удалить пользователя ${user.username}? Это действие нельзя отменить.`,
    );
    if (!confirmed) return;
    deleteMutation.mutate();
  }

  function formatDate(value: string) {
    return new Intl.DateTimeFormat("ru-RU", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  }

  function renderEmpty(message: string) {
    return <p className="muted">{message}</p>;
  }

  function renderSectionHeader(
    title: string,
    expanded: boolean,
    onToggle: () => void,
  ) {
    return (
      <div
        style={{
          alignItems: "center",
          display: "flex",
          justifyContent: "space-between",
          marginBottom: 12,
        }}
      >
        <h3 className="section-title" style={{ marginBottom: 0 }}>
          {title}
        </h3>
        <button
          className="ghost-button"
          type="button"
          onClick={onToggle}
        >
          {expanded ? "Свернуть" : "Развернуть"}
        </button>
      </div>
    );
  }

  const displayUser: AdminUser | AdminUserDetail = detail ?? user;
  const isModerator = currentStaff?.role === "MODERATOR";
  const canModerateSelectedUser = !isModerator || displayUser.role === "USER";
  const sortedChallenges =
    "challenges" in displayUser
      ? [...displayUser.challenges].sort((left, right) => {
          const leftPriority =
            left.isClaimed || left.isCompleted || left.currentCount > 0 ? 0 : 1;
          const rightPriority =
            right.isClaimed || right.isCompleted || right.currentCount > 0 ? 0 : 1;
          if (leftPriority !== rightPriority) return leftPriority - rightPriority;
          if (left.isCompleted !== right.isCompleted) return left.isCompleted ? -1 : 1;
          return right.currentCount - left.currentCount;
        })
      : [];

  const completedChallenges =
    "challenges" in displayUser
      ? displayUser.challenges.filter((item) => item.isCompleted).length
      : 0;

  return (
    <article className="card">
      <h2 className="section-title">Выбранный пользователь</h2>
      <div className="detail-stack">
        {"fullName" in displayUser ? (
          <div className="detail-row">
            <span className="muted">Полное имя</span>
            <strong>{displayUser.fullName}</strong>
          </div>
        ) : null}
        <div className="detail-row">
          <span className="muted">Имя пользователя</span>
          <strong>{displayUser.username}</strong>
        </div>
        <div className="detail-row">
          <span className="muted">Email</span>
          <strong>{displayUser.email}</strong>
        </div>
        <div className="detail-row">
          <span className="muted">Текущая роль</span>
          <strong>{roleLabels[displayUser.role]}</strong>
        </div>
        <div className="detail-row">
          <span className="muted">Статус</span>
          <strong>{statusLabels[displayUser.status]}</strong>
        </div>
        <div className="detail-row">
          <span className="muted">Eco баллы</span>
          <strong>{displayUser.ecoPoints}</strong>
        </div>
        <div className="detail-row">
          <span className="muted">Серия дней</span>
          <strong>{displayUser.streakDays}</strong>
        </div>
        {"level" in displayUser ? (
          <>
            <div className="detail-row">
              <span className="muted">Уровень</span>
              <strong>{displayUser.level}</strong>
            </div>
            <div className="detail-row">
              <span className="muted">Суммарно CO2</span>
              <strong>{displayUser.co2SavedTotal.toFixed(1)} кг</strong>
            </div>
            <div className="detail-row">
              <span className="muted">Создано постов</span>
              <strong>{displayUser.postsCount}</strong>
            </div>
            <div className="detail-row">
              <span className="muted">Дата регистрации</span>
              <strong>{formatDate(displayUser.createdAt)}</strong>
            </div>
          </>
        ) : null}
      </div>

      <div className="form-shell">
        <h3 className="section-title" style={{ marginBottom: 12 }}>
          Eco статистика
        </h3>
        {detailQuery.isLoading ? (
          <p className="muted">Загружаем сводку по пользователю...</p>
        ) : (
          <div className="stats-grid">
            <div className="stat-chip">
              <span className="muted">Подтверждение</span>
              <strong>{displayUser.isEmailVerified ? "Подтвержден" : "Ожидает"}</strong>
            </div>
            <div className="stat-chip">
              <span className="muted">Прогресс ачивок</span>
              <strong>
                {"challenges" in displayUser
                  ? `${completedChallenges}/${displayUser.challenges.length} завершено`
                  : "Загрузка..."}
              </strong>
            </div>
          </div>
        )}
        <div className="action-group">
          <p className="muted action-group-title">Быстрые действия</p>
          <div className="action-grid">
            <Link
              className="ghost-button"
              href={`/activities?search=${encodeURIComponent(displayUser.email)}`}
            >
              Активности пользователя
            </Link>
            <Link
              className="ghost-button"
              href={`/posts?search=${encodeURIComponent(
                "fullName" in displayUser ? displayUser.fullName : displayUser.username,
              )}`}
            >
              Посты пользователя
            </Link>
            {!displayUser.isEmailVerified && !isModerator ? (
              <button
                type="button"
                className="ghost-button"
                onClick={() => verifyEmailMutation.mutate()}
                disabled={verifyEmailMutation.isPending}
              >
                {verifyEmailMutation.isPending ? "Подтверждаем..." : "Подтвердить email"}
              </button>
            ) : null}
          </div>
        </div>
      </div>

      <div className="form-shell">
        {renderSectionHeader("Ачивки", challengesExpanded, () =>
          setChallengesExpanded((current) => !current),
        )}
        {detailQuery.isLoading ? (
          <p className="muted">Загружаем прогресс по ачивкам...</p>
        ) : !challengesExpanded ? (
          <p className="muted">
            {"challenges" in displayUser
              ? `${displayUser.challenges.length} скрыто`
              : "Разверни блок, чтобы увидеть прогресс."}
          </p>
        ) : "challenges" in displayUser && sortedChallenges.length > 0 ? (
          <div className="challenge-list">
            {sortedChallenges.map((challenge) => (
              <div
                key={challenge.id}
                className={`challenge-card${challenge.isCompleted ? " challenge-card-complete" : ""}`}
              >
                <div>
                  <strong>{challenge.title}</strong>
                  <p className="muted">
                    {challenge.currentCount}/{challenge.targetCount} · {challenge.rewardPoints} баллов
                  </p>
                </div>
                <strong className={challenge.isCompleted ? "challenge-status-complete" : ""}>
                  {challenge.isCompleted ? "Получено" : "В процессе"}
                </strong>
              </div>
            ))}
          </div>
        ) : (
          renderEmpty("Прогресс по ачивкам пока пустой.")
        )}
      </div>

      <div className="form-shell">
        {!isModerator ? (
          <label className="field">
            <span>Роль</span>
            <select {...register("role")}>
              <option value="USER">Пользователь</option>
              <option value="MODERATOR">Модератор</option>
              <option value="ADMIN">Админ</option>
            </select>
            {errors.role ? <p className="field-error">{errors.role.message}</p> : null}
          </label>
        ) : (
          <div className="detail-row">
            <span className="muted">Роль</span>
            <strong>{roleLabels[displayUser.role]}</strong>
          </div>
        )}

        <label className="field">
          <span>Статус</span>
          <select {...register("status")} disabled={!canModerateSelectedUser}>
            <option value="ACTIVE">Активный</option>
            <option value="REVIEW">На проверке</option>
            <option value="SUSPENDED">Приостановлен</option>
          </select>
          {errors.status ? (
            <p className="field-error">{errors.status.message}</p>
          ) : null}
        </label>

        <label className="field">
          <span>Заметка админа</span>
          <textarea rows={4} {...register("adminNote")} disabled={!canModerateSelectedUser} />
          {errors.adminNote ? (
            <p className="field-error">{errors.adminNote.message}</p>
          ) : null}
        </label>

        {isModerator && !canModerateSelectedUser ? (
          <p className="form-status muted">
            Модератор может менять статус и заметку только у обычных пользователей.
          </p>
        ) : null}

        <p className="form-status muted">
          {isDirty ? "Есть несохраненные изменения." : "Изменений нет."}
        </p>

        <div className="button-row">
          <button
            type="button"
            className="primary-button"
            onClick={handleSubmit(onSubmit)}
            disabled={mutation.isPending || !isDirty || !canModerateSelectedUser}
          >
            {mutation.isPending ? "Сохраняем..." : "Сохранить"}
          </button>
          <button
            type="button"
            className="ghost-button"
            onClick={() =>
              setValue("status", "SUSPENDED", {
                shouldValidate: true,
                shouldDirty: true,
              })
            }
            disabled={!canModerateSelectedUser}
          >
            Приостановить
          </button>
          {!isModerator ? (
            <button
              type="button"
              className="ghost-button danger-button"
              onClick={onDelete}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? "Удаляем..." : "Удалить пользователя"}
            </button>
          ) : null}
          <button
            type="button"
            className="ghost-button"
            onClick={() =>
              reset({
                role: detail?.role ?? user.role,
                status: detail?.status ?? user.status,
                adminNote: detail?.adminNote || defaultAdminNote,
              })
            }
            disabled={!isDirty}
          >
            Сбросить
          </button>
        </div>
      </div>
    </article>
  );
}
