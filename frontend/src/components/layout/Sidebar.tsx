import { NavLink } from "react-router-dom";
import { BarChart3, Clock, Home, Settings } from "lucide-react";
import { clsx } from "clsx";

const NAV_ITEMS = [
  { to: "/", icon: Home, label: "Dashboard" },
  { to: "/historical", icon: Clock, label: "Historical" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

export function Sidebar() {
  return (
    <aside className="flex w-64 flex-col border-r border-[var(--color-border)] bg-[var(--color-bg-secondary)]">
      <div className="flex items-center gap-2 p-6">
        <BarChart3 className="h-6 w-6 text-blue-400" />
        <h1 className="text-lg font-bold text-[var(--color-text-primary)]">
          Sentiment
        </h1>
      </div>

      <nav className="flex-1 space-y-1 px-3">
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-blue-600/20 text-blue-400"
                  : "text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-card)] hover:text-[var(--color-text-primary)]",
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
