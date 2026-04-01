"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
import { Sidebar } from "@/components/sidebar";
import { StatePanel } from "@/components/state-panel";

type AppFrameProps = {
  children: React.ReactNode;
};

export function AppFrame({ children }: AppFrameProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, isLoading, user } = useAuth();

  const isLoginPage = pathname === "/login";

  useEffect(() => {
    if (isLoading) {
      return;
    }

    if (!isAuthenticated && !isLoginPage) {
      router.replace("/login");
      return;
    }

    if (isAuthenticated && isLoginPage) {
      router.replace("/");
      return;
    }

    if (
      user?.role === "MODERATOR" &&
      ["/categories", "/habits", "/achievements"].some((route) =>
        pathname.startsWith(route),
      )
    ) {
      router.replace("/");
    }
  }, [isAuthenticated, isLoading, isLoginPage, pathname, router, user?.role]);

  if (isLoading) {
    return (
      <div className="auth-shell">
        <StatePanel
          title="Загружаем сессию админа"
          description="Проверяем сохраненный вход и уровень доступа."
        />
      </div>
    );
  }

  if (!isAuthenticated && !isLoginPage) {
    return null;
  }

  if (
    user?.role === "MODERATOR" &&
    ["/categories", "/habits", "/achievements"].some((route) =>
      pathname.startsWith(route),
    )
  ) {
    return null;
  }

  if (isLoginPage) {
    return <main>{children}</main>;
  }

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="content">{children}</main>
    </div>
  );
}
