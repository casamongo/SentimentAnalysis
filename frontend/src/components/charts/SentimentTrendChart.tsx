import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { format } from "date-fns";
import type { ScoreHistoryPoint } from "../../types";
import { scoreToColor } from "../../utils/colors";

interface SentimentTrendChartProps {
  data: ScoreHistoryPoint[];
  title?: string;
}

export function SentimentTrendChart({
  data,
  title = "Sentiment Trend",
}: SentimentTrendChartProps) {
  const chartData = data.map((d) => ({
    ...d,
    time: new Date(d.computed_at).getTime(),
    label: format(new Date(d.computed_at), "HH:mm"),
  }));

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-secondary)] p-4">
      <h3 className="mb-4 text-sm font-medium text-[var(--color-text-secondary)]">
        {title}
      </h3>
      {chartData.length === 0 ? (
        <p className="py-8 text-center text-sm text-[var(--color-text-secondary)]">
          No trend data available yet
        </p>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="label"
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              axisLine={{ stroke: "#475569" }}
            />
            <YAxis
              domain={[-1, 1]}
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              axisLine={{ stroke: "#475569" }}
              tickFormatter={(v: number) => v.toFixed(1)}
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
            {/* Zero line */}
            <Area
              type="monotone"
              dataKey={() => 0}
              stroke="#475569"
              strokeDasharray="4 4"
              fill="none"
            />
            <Area
              type="monotone"
              dataKey="score"
              stroke="#3b82f6"
              strokeWidth={2}
              fill="url(#scoreGradient)"
              dot={false}
              activeDot={{ r: 4, fill: "#3b82f6" }}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
