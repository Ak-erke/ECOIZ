"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";

import { useToast } from "@/components/toast-provider";
import { deletePost, updatePost } from "@/lib/api/posts";
import { queryKeys } from "@/lib/query-keys";
import type { CommunityPost, UpdatePostPayload } from "@/lib/types";
import { postFormSchema, type PostFormValues } from "@/lib/validation";

type PostDetailPanelProps = {
  post: CommunityPost;
};

export function PostDetailPanel({ post }: PostDetailPanelProps) {
  const visibilityLabels: Record<CommunityPost["visibility"], string> = {
    PUBLIC: "Публичный",
    FOLLOWERS: "Подписчики",
    PRIVATE: "Приватный",
  };

  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors, isDirty },
  } = useForm<PostFormValues>({
    resolver: zodResolver(postFormSchema),
    defaultValues: {
      visibility: post.visibility,
      state: post.state,
      moderatorNote: "Действие модерации позже будет попадать в аудит-лог backend.",
    },
  });
  const mutation = useMutation({
    mutationFn: (payload: UpdatePostPayload) => updatePost(post.id, payload),
    onSuccess: async (updated) => {
      showToast({
        tone: "success",
        title: "Модерация сохранена",
        description: `Изменения для поста ${updated.author} сохранены.`,
      });
      await queryClient.invalidateQueries({ queryKey: queryKeys.posts.all });
      await queryClient.invalidateQueries({ queryKey: queryKeys.posts.metrics });
    },
    onError: () => {
      showToast({
        tone: "error",
        title: "Не удалось сохранить",
        description: "Изменения модерации не были сохранены.",
      });
    },
  });
  const deleteMutation = useMutation({
    mutationFn: () => deletePost(post.id),
    onSuccess: async () => {
      showToast({
        tone: "success",
        title: "Пост удален",
        description: `Пост от ${post.author} был удален.`,
      });
      await queryClient.invalidateQueries({ queryKey: queryKeys.posts.all });
      await queryClient.invalidateQueries({ queryKey: queryKeys.posts.metrics });
    },
    onError: () => {
      showToast({
        tone: "error",
        title: "Удаление не удалось",
        description: "Не получилось удалить пост.",
      });
    },
  });

  useEffect(() => {
    reset({
      visibility: post.visibility,
      state: post.state,
      moderatorNote:
        "Действие модерации позже будет попадать в аудит-лог backend.",
    });
  }, [post, reset]);

  function onSubmit(values: PostFormValues) {
    mutation.mutate(values);
  }

  function onDelete() {
    const confirmed = window.confirm(
      `Удалить пост от ${post.author}? Это действие нельзя отменить.`,
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

  return (
    <article className="card">
      <h2 className="section-title">Выбранный пост</h2>
      <div className="detail-stack">
        <div className="detail-row">
          <span className="muted">Автор</span>
          <strong>{post.author}</strong>
        </div>
        <div className="detail-row">
          <span className="muted">Жалобы</span>
          <strong>{post.reportsCount}</strong>
        </div>
        <div className="detail-row">
          <span className="muted">Создан</span>
          <strong>{formatDate(post.createdAt)}</strong>
        </div>
      </div>

      <div className="card inset-card">
        <p className="muted">Содержимое поста</p>
        <p>{post.content}</p>
      </div>

      <div className="form-shell" style={{ marginTop: 16 }}>
        <label className="field">
          <span>Видимость</span>
          <select {...register("visibility")}>
            <option value="PUBLIC">{visibilityLabels.PUBLIC}</option>
            <option value="FOLLOWERS">{visibilityLabels.FOLLOWERS}</option>
            <option value="PRIVATE">{visibilityLabels.PRIVATE}</option>
          </select>
          {errors.visibility ? (
            <p className="field-error">{errors.visibility.message}</p>
          ) : null}
        </label>

        <label className="field">
          <span>Статус модерации</span>
          <select {...register("state")}>
            <option value="Published">Опубликован</option>
            <option value="Flagged">Отмечен</option>
            <option value="Needs review">Нужна проверка</option>
            <option value="Hidden">Скрыт</option>
          </select>
          {errors.state ? (
            <p className="field-error">{errors.state.message}</p>
          ) : null}
        </label>

        <label className="field">
          <span>Заметка модератора</span>
          <textarea rows={4} {...register("moderatorNote")} />
          {errors.moderatorNote ? (
            <p className="field-error">{errors.moderatorNote.message}</p>
          ) : null}
        </label>

        <p className="form-status muted">
          {isDirty ? "Есть несохраненные изменения." : "Изменений нет."}
        </p>

        <div className="button-row">
          <button
            type="button"
            className="primary-button"
            onClick={handleSubmit(onSubmit)}
            disabled={mutation.isPending || !isDirty}
          >
            {mutation.isPending ? "Сохраняем..." : "Сохранить"}
          </button>
          <button
            type="button"
            className="ghost-button"
            onClick={() =>
              setValue("state", "Hidden", {
                shouldValidate: true,
                shouldDirty: true,
              })
            }
          >
            Скрыть пост
          </button>
          <button
            type="button"
            className="ghost-button danger-button"
            onClick={onDelete}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? "Удаляем..." : "Удалить пост"}
          </button>
          <button
            type="button"
            className="ghost-button"
            onClick={() =>
              reset({
                visibility: post.visibility,
                state: post.state,
                moderatorNote:
                  "Действие модерации позже будет попадать в аудит-лог backend.",
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
