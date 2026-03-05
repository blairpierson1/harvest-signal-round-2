"use client";

import type { Confidence } from "../types";

interface ConfidenceMeterProps {
  confidence: Confidence;
}

const confidenceConfig: Record<
  Confidence,
  { bars: number; color: string; label: string }
> = {
  High: { bars: 3, color: "bg-signal-bullish", label: "HIGH" },
  Medium: { bars: 2, color: "bg-signal-neutral", label: "MED" },
  Low: { bars: 1, color: "bg-text-muted", label: "LOW" },
};

export default function ConfidenceMeter({ confidence }: ConfidenceMeterProps) {
  const config = confidenceConfig[confidence];

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-text-muted uppercase tracking-widest">
        Confidence
      </span>
      <div className="flex items-end gap-0.5">
        {[1, 2, 3].map((bar) => (
          <div
            key={bar}
            className={`w-1.5 rounded-sm transition-all ${
              bar <= config.bars ? config.color : "bg-navy-700"
            }`}
            style={{ height: `${bar * 5 + 4}px` }}
          />
        ))}
      </div>
      <span className="text-xs font-semibold text-text-secondary">
        {config.label}
      </span>
    </div>
  );
}
