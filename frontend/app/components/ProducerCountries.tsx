"use client";

import { useState } from "react";
import type { ProducerCountry, WeatherRisk } from "../types";

interface ProducerCountriesProps {
  producers: ProducerCountry[];
}

const riskStyles: Record<WeatherRisk, { bg: string; text: string; border: string; dot: string }> = {
  Normal: {
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    border: "border-emerald-500/20",
    dot: "bg-emerald-400",
  },
  Watch: {
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    border: "border-amber-500/20",
    dot: "bg-amber-400",
  },
  Alert: {
    bg: "bg-red-500/10",
    text: "text-red-400",
    border: "border-red-500/20",
    dot: "bg-red-400",
  },
};

function RiskBadge({ risk }: { risk: WeatherRisk }) {
  const style = riskStyles[risk] ?? riskStyles.Normal;
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider ${style.bg} ${style.text} ${style.border} border`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${style.dot}`} />
      {risk}
    </span>
  );
}

export default function ProducerCountries({ producers }: ProducerCountriesProps) {
  const [expanded, setExpanded] = useState(false);

  if (!producers || producers.length === 0) return null;

  return (
    <div className="mt-1">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-xs text-text-muted hover:text-accent-blue transition-colors cursor-pointer"
      >
        <span
          className={`transition-transform duration-200 ${expanded ? "rotate-90" : ""}`}
        >
          &#9654;
        </span>
        {expanded ? "Hide" : "Show"} top producers
      </button>

      {expanded && (
        <div className="mt-3 space-y-2">
          {producers.map((p) => (
            <div
              key={p.country}
              className="flex items-center justify-between rounded-md bg-navy-900/50 px-3 py-2.5 border border-navy-700/30"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-text-primary truncate">
                      {p.country}
                    </span>
                    <span className="text-[10px] text-text-muted whitespace-nowrap">
                      {p.share_percent}%
                    </span>
                  </div>
                  <div className="text-[10px] text-text-muted mt-0.5 flex gap-3">
                    <span>{p.temperature_avg}°C</span>
                    <span>{p.precipitation_sum}mm</span>
                    <span>{p.relative_humidity}% RH</span>
                  </div>
                </div>
              </div>
              <div className="flex flex-col items-end gap-1 flex-shrink-0 ml-2">
                <RiskBadge risk={p.weather_risk} />
                {p.weather_risk !== "Normal" && (
                  <span className="text-[9px] text-text-muted max-w-[160px] text-right truncate" title={p.risk_detail}>
                    {p.risk_detail}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
