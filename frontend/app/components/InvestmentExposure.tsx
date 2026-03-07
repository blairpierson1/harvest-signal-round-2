"use client";

import type { InvestmentSecurity } from "../types";

interface InvestmentExposureProps {
  securities: InvestmentSecurity[];
}

const typeBadgeColors: Record<string, string> = {
  ETF: "bg-accent-blue/15 text-accent-blue border-accent-blue/30",
  REIT: "bg-purple-500/15 text-purple-400 border-purple-500/30",
  Stock: "bg-signal-bullish/15 text-signal-bullish border-signal-bullish/30",
  Futures: "bg-signal-neutral/15 text-signal-neutral border-signal-neutral/30",
};

export default function InvestmentExposure({
  securities,
}: InvestmentExposureProps) {
  if (!securities || securities.length === 0) return null;

  return (
    <div className="mb-3">
      <span className="text-xs text-text-muted uppercase tracking-widest block mb-2">
        Investment Exposure
      </span>
      <div className="space-y-2">
        {securities.map((sec) => {
          const badgeColor =
            typeBadgeColors[sec.type] ??
            "bg-navy-700/50 text-text-secondary border-navy-600/50";

          return (
            <div
              key={sec.ticker}
              className="rounded-md bg-navy-900/40 px-3 py-2.5 border border-navy-700/30"
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <a
                    href={`https://finance.yahoo.com/quote/${encodeURIComponent(sec.yahoo_finance_symbol || sec.ticker)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm font-bold text-accent-cyan hover:underline"
                  >
                    {sec.ticker}
                  </a>
                  <span
                    className={`text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded border ${badgeColor}`}
                  >
                    {sec.type}
                  </span>
                </div>
                {sec.current_price !== null && sec.current_price !== undefined && (
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs text-text-secondary font-medium tabular-nums">
                      ${sec.current_price.toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </span>
                    {sec.change_percent !== null &&
                      sec.change_percent !== undefined && (
                        <span
                          className={`text-[11px] font-semibold tabular-nums ${
                            sec.change_percent > 0
                              ? "text-signal-bullish"
                              : sec.change_percent < 0
                                ? "text-signal-bearish"
                                : "text-text-muted"
                          }`}
                        >
                          {sec.change_percent > 0 ? "+" : ""}
                          {sec.change_percent.toFixed(2)}%
                        </span>
                      )}
                  </div>
                )}
              </div>
              <p className="text-[11px] text-text-secondary leading-relaxed">
                <span className="text-text-muted">{sec.name}</span>
                {" — "}
                {sec.description}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
