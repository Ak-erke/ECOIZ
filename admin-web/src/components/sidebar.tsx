"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
import { getNavigation } from "@/lib/navigation";

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  const roleLabels = {
    ADMIN: "Админ",
    MODERATOR: "Модератор",
    USER: "Пользователь",
  } as const;
  const navigation = getNavigation(user?.role ?? null);

  return (
    <aside className="sidebar">
      <h1 className="brand">
        ECO<span>IZ</span>
      </h1>
      <p className="sidebar-note">
        Единая админ-панель для модерации, eco-каталога и контроля данных
        платформы.
      </p>
      <nav className="nav-list" aria-label="Навигация админки">
        {navigation.map((item) => {
          const isActive =
            item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`nav-link${isActive ? " active" : ""}`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <strong>{user?.username}</strong>
          <span className="muted">
            {user?.role ? roleLabels[user.role] : ""} · {user?.email}
          </span>
        </div>
        <button type="button" className="ghost-button sidebar-button" onClick={handleLogout}>
          Выйти
        </button>
      </div>
    </aside>
  );
}
