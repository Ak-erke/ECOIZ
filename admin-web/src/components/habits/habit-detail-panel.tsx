"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";

import { useToast } from "@/components/toast-provider";
import { updateHabit } from "@/lib/api/habits";
import { queryKeys } from "@/lib/query-keys";
import type { Habit, UpdateHabitPayload } from "@/lib/types";
import { habitFormSchema, type HabitFormValues } from "@/lib/validation";

type HabitDetailPanelProps = {
  habit: Habit;
  categoryOptions: string[];
};

export function HabitDetailPanel({
  habit,
  categoryOptions,
}: HabitDetailPanelProps) {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors, isDirty },
  } = useForm<HabitFormValues>({
    resolver: zodResolver(habitFormSchema),
    defaultValues: {
      title: habit.title,
      category: habit.category,
      points: habit.points,
      co2Value: habit.co2Value,
      waterValue: habit.waterValue,
      energyValue: habit.energyValue,
    },
  });
  const mutation = useMutation({
    mutationFn: (payload: UpdateHabitPayload) => updateHabit(habit.id, payload),
    onSuccess: async (updated) => {
      showToast({
        tone: "success",
        title: "Активность обновлена",
        description: `Изменения для "${updated.title}" сохранены.`,
      });
      await queryClient.invalidateQueries({ queryKey: queryKeys.habits.all });
      await queryClient.invalidateQueries({ queryKey: queryKeys.habits.metrics });
    },
    onError: () => {
      showToast({
        tone: "error",
        title: "Не удалось сохранить",
        description: "Изменения активности не были сохранены.",
      });
    },
  });

  useEffect(() => {
    reset({
      title: habit.title,
      category: habit.category,
      points: habit.points,
      co2Value: habit.co2Value,
      waterValue: habit.waterValue,
      energyValue: habit.energyValue,
    });
  }, [habit, reset]);

  function onSubmit(values: HabitFormValues) {
    mutation.mutate(values);
  }

  return (
    <article className="card">
      <h2 className="section-title">Выбранная активность</h2>
      <div className="detail-stack">
        <div className="detail-row">
          <span className="muted">Название</span>
          <strong>{habit.title}</strong>
        </div>
        <div className="detail-row">
          <span className="muted">Категория</span>
          <strong>{habit.category}</strong>
        </div>
        <div className="detail-row">
          <span className="muted">Баллы</span>
          <strong>{habit.points}</strong>
        </div>
      </div>

      <div className="form-shell">
        <label className="field">
          <span>Название</span>
          <input {...register("title")} />
          {errors.title ? (
            <p className="field-error">{errors.title.message}</p>
          ) : null}
        </label>

        <label className="field">
          <span>Категория</span>
          <select {...register("category")}>
            {categoryOptions.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
          {errors.category ? (
            <p className="field-error">{errors.category.message}</p>
          ) : null}
        </label>

        <div className="form-grid-two">
          <label className="field">
            <span>Баллы</span>
            <input type="number" {...register("points", { valueAsNumber: true })} />
            {errors.points ? (
              <p className="field-error">{errors.points.message}</p>
            ) : null}
          </label>

          <label className="field">
            <span>CO2 значение</span>
            <input
              type="number"
              step="0.1"
              {...register("co2Value", { valueAsNumber: true })}
            />
            {errors.co2Value ? (
              <p className="field-error">{errors.co2Value.message}</p>
            ) : null}
          </label>

          <label className="field">
            <span>Вода</span>
            <input
              type="number"
              {...register("waterValue", { valueAsNumber: true })}
            />
            {errors.waterValue ? (
              <p className="field-error">{errors.waterValue.message}</p>
            ) : null}
          </label>

          <label className="field">
            <span>Энергия</span>
            <input
              type="number"
              {...register("energyValue", { valueAsNumber: true })}
            />
            {errors.energyValue ? (
              <p className="field-error">{errors.energyValue.message}</p>
            ) : null}
          </label>
        </div>

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
              setValue("points", habit.points + 5, {
                shouldValidate: true,
                shouldDirty: true,
              })
            }
          >
            Добавить 5 баллов
          </button>
          <button
            type="button"
            className="ghost-button"
            onClick={() =>
              reset({
                title: habit.title,
                category: habit.category,
                points: habit.points,
                co2Value: habit.co2Value,
                waterValue: habit.waterValue,
                energyValue: habit.energyValue,
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
