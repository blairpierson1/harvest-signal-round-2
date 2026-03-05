"use client";

import type { PriceHistory } from "../types";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  Tooltip,
  YAxis,
} from "recharts";

interface SparklineChartProps {
  history: PriceHistory;
}

const trendColors: Record<string, { stroke: string; fill: string; label: string }> = {
  Uptrend: { stroke: "#22c55e", fill: "rgba(34,197,94,0.15)", label: "text-signal-bullish" },
  Downtrend: { stroke: "#ef4444", fill: "rgba(239,68,68,0.15)", label: "text-signal-bearish" },
  Sideways: { stroke: "#f59e0b", fill: "rgba(245,158,11,0.15)", label: "text-signal-neutral" },
  "N/A": { stroke: "#64748b", fill: "rgba(100,116,139,0.10)", label: "text-text-muted" },
};

const trendArrows: Record<string, string> = {
  Uptrend: "\u2197",
  Downtrend: "\u2198",
  Sideways: "\u2192",
  "N/A": "\u2014",
};

export default function SparklineChart({ history }: SparklineChartProps) {
  const { points, trend_label } = history;
  const colors = trendColors[trend_label] ?? trendColors["N/A"];
  const arrow = trendArrows[trend_label] ?? "\u2014";

  if (points.length === 0) {
    return (
      <div className="mt-3 rounded-md bg-navy-900/40 px-4 py-3 border border-navy-700/30">
        <span className="text-xs text-text-muted">Price history unavailable</span>
      </div>
    );
  }

  const data = points.map((p) => ({ date: p.date, price: p.close }));
  const prices = points.map((p) => p.close);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const padding = (maxPrice - minPrice) * 0.1 || 1;

  return (
    <div className="mt-3 rounded-md bg-navy-900/40 px-4 py-3 border border-navy-700/30">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-text-muted uppercase tracking-widest">
          30-Day Price
        </span>
        <span className={`text-xs font-semibold ${colors.label} flex items-center gap-1`}>
          <span>{arrow}</span>
          {trend_label}
        </span>
      </div>
      <div className="h-16">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
            <defs>
              <linearGradient id={`gradient-${trend_label}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={colors.stroke} stopOpacity={0.3} />
                <stop offset="100%" stopColor={colors.stroke} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <YAxis domain={[minPrice - padding, maxPrice + padding]} hide />
            <Tooltip
              contentStyle={{
                backgroundColor: "#111827",
                border: "1px solid #1e293b",
                borderRadius: "6px",
                fontSize: "11px",
                color: "#f1f5f9",
              }}
              labelStyle={{ color: "#94a3b8", fontSize: "10px" }}
              formatter={(value: number | undefined) => {
                if (value === undefined) return ["N/A", "Price"];
                return [`$${value.toFixed(2)}`, "Price"];
              }}
            />
            <Area
              type="monotone"
              dataKey="price"
              stroke={colors.stroke}
              strokeWidth={1.5}
              fill={`url(#gradient-${trend_label})`}
              dot={false}
              activeDot={{ r: 3, fill: colors.stroke }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
