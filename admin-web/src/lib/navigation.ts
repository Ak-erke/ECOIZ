import type { AdminAppRole } from "@/lib/types";

const navigation = [
  { href: "/", label: "Панель" },
  { href: "/users", label: "Пользователи" },
  { href: "/activities", label: "Активности" },
  { href: "/categories", label: "Категории" },
  { href: "/habits", label: "Каталог активностей" },
  { href: "/achievements", label: "Ачивки" },
  { href: "/posts", label: "Посты" },
] as const;

export function getNavigation(role?: AdminAppRole | null) {
  if (role === "MODERATOR") {
    return navigation.filter((item) =>
      ["/", "/users", "/activities", "/posts"].includes(item.href),
    );
  }

  return navigation;
}
