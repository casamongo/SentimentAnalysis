import { clsx } from "clsx";
import { useDashboardStore } from "../../store";
import type { DashboardMode } from "../../types";

const modes: { value: DashboardMode; label: string }[] = [
  { value: "realtime", label: "Real-Time" },
  { value: "historical", label: "Historical" },
];

export function ModeToggle() {
  const mode = useDashboardStore((s) => s.mode);
  const setMode = useDashboardStore((s) => s.setMode);

  return (
    <div className="flex rounded-lg bg-[var(--color-bg-primary)] p-1">
      {modes.map(({ value, label }) => (
        <button
          key={value}
          onClick={() => setMode(value)}
          className={clsx(
            "rounded-md px-3 py-1 text-xs font-medium transition-colors",
            mode === value
              ? "bg-blue-600 text-white"
              : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]",
          )}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
