import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { scoreToColor } from "../../utils/colors";
import { SOURCE_DISPLAY_NAMES } from "../../utils/constants";

interface SourceBreakdownChartProps {
  breakdown: Record<string, number>;
}

export function SourceBreakdownChart({ breakdown }: SourceBreakdownChartProps) {
  const data = Object.entries(breakdown)
    .map(([source, score]) => ({
      source: SOURCE_DISPLAY_NAMES[source] ?? source,
      score,
      fill: scoreToColor(score),
    }))
    .sort((a, b) => b.score - a.score);

  if (data.length === 0) {
    return (
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-secondary)] p-4">
        <h3 className="mb-4 text-sm font-medium text-[var(--color-text-secondary)]">
          Source Breakdown
        </h3>
        <p className="py-8 text-center text-sm text-[var(--color-text-secondary)]">
          No source data available
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-secondary)] p-4">
      <h3 className="mb-4 text-sm font-medium text-[var(--color-text-secondary)]">
        Source Breakdown
      </h3>
      <ResponsiveContainer width="100%" height={360}>
        <BarChart data={data} layout="vertical" margin={{ left: 80 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
          <XAxis
            type="number"
            domain={[-1, 1]}
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            axisLine={{ stroke: "#475569" }}
          />
          <YAxis
            type="category"
            dataKey="source"
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            axisLine={{ stroke: "#475569" }}
            width={80}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1e293b",
              border: "1px solid #475569",
              borderRadius: "8px",
              color: "#f8fafc",
              fontSize: "12px",
            }}
            formatter={(value: number) => [value.toFixed(4), "Score"]}
          />
          <Bar dataKey="score" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell key={index} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
