"use client";

import type { PriceTrend } from "../types";

interface PriceTickerProps {
  trend: PriceTrend;
  commodity: string;
}

const commodityUnits: Record<string, string> = {
  Pistachios: "$/lb",
  Figs: "$/lb",
  Olives: "$/lb",
  Dates: "$/lb",
  Citrus: "$/lb",
};

export default function PriceTicker({ trend, commodity }: PriceTickerProps) {
  const unit = commodityUnits[commodity] ?? "";
  const isUp = trend.direction === "up";
  const isDown = trend.direction === "down";

  const directionColor = isUp
    ? "text-signal-bullish"
    : isDown
      ? "text-signal-bearish"
      : "text-text-muted";

  const arrow = isUp ? "\u2191" : isDown ? "\u2193" : "\u2194";

  return (
    <div className="flex items-center gap-3">
      <div className="flex flex-col">
        <span className="text-xs text-text-muted uppercase tracking-widest mb-0.5">
          Price
        </span>
        {trend.current_price !== null ? (
          <div className="flex items-baseline gap-2">
            <span className="text-lg font-bold text-text-primary tabular-nums">
              {trend.current_price.toLocaleString("en-US", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </span>
            <span className="text-xs text-text-muted">{unit}</span>
          </div>
        ) : (
          <span className="text-sm text-text-muted">N/A</span>
        )}
      </div>
      {trend.change_percent !== null && (
        <div
          className={`flex items-center gap-1 rounded-md px-2 py-1 text-xs font-semibold ${directionColor} ${
            isUp
              ? "bg-signal-bullish/10"
              : isDown
                ? "bg-signal-bearish/10"
                : "bg-navy-700"
          }`}
        >
          <span>{arrow}</span>
          <span className="tabular-nums">
            {Math.abs(trend.change_percent).toFixed(2)}%
          </span>
        </div>
      )}
      {trend.source === "estimated" && (
        <span className="text-[10px] text-text-muted italic ml-1 self-end mb-0.5">
          (est.)
        </span>
      )}
    </div>
  );
}
