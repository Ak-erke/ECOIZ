"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";

import { useAuth } from "@/components/auth-provider";
import { isMockMode } from "@/lib/config";
import { loginSchema, type LoginFormValues } from "@/lib/validation";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const mockMode = isMockMode();
  const defaultCredentials = mockMode
    ? {
        email: "akmaral@ecoiz.app",
        password: "admin123",
      }
    : {
        email: "admin@ecoiz.app",
        password: "admin123",
      };
  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: defaultCredentials,
  });

  async function onSubmit(values: LoginFormValues) {
    try {
      await login(values);
      router.replace("/");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Не удалось войти. Попробуй еще раз.";
      setError("root", { message });
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <p className="auth-kicker">Доступ в админку ECOIZ</p>
        <h1 className="auth-title">Вход в пространство модерации</h1>
        <p className="muted">
          {mockMode
            ? "Тестовые данные уже подставлены для проверки интерфейса."
            : "Включен live-режим backend. Используй seeded admin-аккаунт для входа."}
        </p>

        <form className="form-shell" onSubmit={handleSubmit(onSubmit)}>
          <label className="field">
            <span>Email</span>
            <input type="email" {...register("email")} />
            {errors.email ? (
              <p className="field-error">{errors.email.message}</p>
            ) : null}
          </label>

          <label className="field">
            <span>Пароль</span>
            <input type="password" {...register("password")} />
            {errors.password ? (
              <p className="field-error">{errors.password.message}</p>
            ) : null}
          </label>

          {errors.root ? (
            <p className="error-message">{errors.root.message}</p>
          ) : null}

          <p className="form-status muted">
            {isDirty
              ? "Есть несохраненные изменения в форме входа."
              : mockMode
                ? "Тестовые данные готовы."
                : "Данные live-админа готовы."}
          </p>

          <div className="button-row">
            <button
              type="submit"
              className="primary-button"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Входим..." : "Войти"}
            </button>
            <button
              type="button"
              className="ghost-button"
              onClick={() => reset(defaultCredentials)}
            >
              Сбросить
            </button>
          </div>
        </form>

        <div className="auth-hint">
          <strong>{mockMode ? "Тестовые аккаунты" : "Аккаунт live-backend"}</strong>
          {mockMode ? (
            <>
              <p className="muted">`akmaral@ecoiz.app / admin123`</p>
              <p className="muted">`nurdana@ecoiz.app / moderator123`</p>
            </>
          ) : (
            <>
              <p className="muted">`admin@ecoiz.app / admin123`</p>
              <p className="muted">`moderator@ecoiz.app / moderator123`</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
