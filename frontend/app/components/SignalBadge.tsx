"use client";

import type { Signal } from "../types";

interface SignalBadgeProps {
  signal: Signal;
}

const signalConfig: Record<
  Signal,
  { bg: string; text: string; border: string; glow: string; icon: string }
> = {
  Bullish: {
    bg: "bg-signal-bullish/10",
    text: "text-signal-bullish",
    border: "border-signal-bullish/30",
    glow: "glow-green",
    icon: "\u25B2",
  },
  Bearish: {
    bg: "bg-signal-bearish/10",
    text: "text-signal-bearish",
    border: "border-signal-bearish/30",
    glow: "glow-red",
    icon: "\u25BC",
  },
  Neutral: {
    bg: "bg-signal-neutral/10",
    text: "text-signal-neutral",
    border: "border-signal-neutral/30",
    glow: "glow-amber",
    icon: "\u25C6",
  },
};

export default function SignalBadge({ signal }: SignalBadgeProps) {
  const config = signalConfig[signal];

  return (
    <div
      className={`inline-flex items-center gap-2 rounded-md border px-4 py-2 font-semibold tracking-wider uppercase ${config.bg} ${config.text} ${config.border} ${config.glow} signal-pulse`}
    >
      <span className="text-lg">{config.icon}</span>
      <span className="text-sm">{signal}</span>
    </div>
  );
}
