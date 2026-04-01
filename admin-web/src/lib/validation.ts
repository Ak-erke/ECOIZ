import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Введите корректный email."),
  password: z
    .string()
    .min(6, "Пароль должен содержать минимум 6 символов."),
});

export const userFormSchema = z.object({
  role: z.enum(["USER", "MODERATOR", "ADMIN"]),
  status: z.enum(["ACTIVE", "REVIEW", "SUSPENDED"]),
  adminNote: z
    .string()
    .min(8, "Добавь заметку админа минимум из 8 символов."),
});

export const categoryFormSchema = z.object({
  name: z.string().min(2, "Название категории должно быть не короче 2 символов."),
  description: z
    .string()
    .min(8, "Описание должно содержать минимум 8 символов."),
  color: z.string().min(3, "Значение цвета должно быть не короче 3 символов."),
  icon: z.string().min(2, "Название иконки должно быть не короче 2 символов."),
});

export const habitFormSchema = z.object({
  title: z.string().min(2, "Название активности должно быть не короче 2 символов."),
  category: z.string().min(2, "Выбери корректную категорию."),
  points: z.coerce.number().min(0, "Баллы не могут быть отрицательными."),
  co2Value: z.coerce.number().min(0, "Значение CO2 не может быть отрицательным."),
  waterValue: z.coerce.number().min(0, "Значение воды не может быть отрицательным."),
  energyValue: z.coerce.number().min(0, "Значение энергии не может быть отрицательным."),
});

export const achievementFormSchema = z.object({
  title: z.string().min(2, "Название ачивки должно быть не короче 2 символов."),
  description: z
    .string()
    .min(8, "Описание должно содержать минимум 8 символов."),
  icon: z.string().min(2, "Название иконки должно быть не короче 2 символов."),
  targetValue: z.coerce.number().min(1, "Целевое значение должно быть не меньше 1."),
  rewardPoints: z.coerce.number().min(0, "Баллы награды не могут быть отрицательными."),
});

export const postFormSchema = z.object({
  visibility: z.enum(["PUBLIC", "FOLLOWERS", "PRIVATE"]),
  state: z.enum(["Published", "Flagged", "Needs review", "Hidden"]),
  moderatorNote: z
    .string()
    .min(8, "Заметка модератора должна содержать минимум 8 символов."),
});

export type LoginFormValues = z.infer<typeof loginSchema>;
export type UserFormValues = z.infer<typeof userFormSchema>;
export type CategoryFormValues = z.infer<typeof categoryFormSchema>;
export type HabitFormValues = z.infer<typeof habitFormSchema>;
export type AchievementFormValues = z.infer<typeof achievementFormSchema>;
export type PostFormValues = z.infer<typeof postFormSchema>;
