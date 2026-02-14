import { useDashboardStore } from "../../store";
import { ModeToggle } from "../dashboard/ModeToggle";

export function Header() {
  const selectedTicker = useDashboardStore((s) => s.selectedTicker);

  return (
    <header className="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-bg-secondary)] px-6 py-3">
      <div className="text-sm text-[var(--color-text-secondary)]">
        {selectedTicker ? (
          <span>
            Tracking: <strong className="text-[var(--color-text-primary)]">{selectedTicker}</strong>
          </span>
        ) : (
          "Select a stock to begin"
        )}
      </div>
      <ModeToggle />
    </header>
  );
}
