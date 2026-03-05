"use client";

import { useEffect, useState, useCallback } from "react";
import dynamic from "next/dynamic";
import type { DashboardResponse, CommoditySignal } from "../types";
import CommodityCard from "./CommodityCard";

const MapView = dynamic(() => import("./MapView"), { ssr: false });

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Dashboard() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchSignals = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_URL}/api/signals`);
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      const result: DashboardResponse = await response.json();
      setData(result);
      setLastRefresh(new Date());
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch signal data"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSignals();

    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchSignals, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchSignals]);

  const signalCounts = data?.signals.reduce(
    (acc: Record<string, number>, s: CommoditySignal) => {
      acc[s.signal] = (acc[s.signal] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <div className="min-h-screen bg-navy-950">
      {/* Header */}
      <header className="border-b border-border-subtle bg-navy-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <span className="text-2xl">&#x1F33E;</span>
                <h1 className="text-xl font-bold tracking-wider text-text-primary">
                  HARVEST<span className="text-accent-cyan">SIGNAL</span>
                </h1>
              </div>
              <div className="hidden sm:block h-6 w-px bg-navy-700 mx-2" />
              <span className="hidden sm:block text-xs text-text-muted uppercase tracking-widest">
                Soft Commodity Weather Intelligence
              </span>
            </div>

            <div className="flex items-center gap-4">
              {/* Signal Summary */}
              {signalCounts && (
                <div className="hidden md:flex items-center gap-3 text-xs">
                  {signalCounts["Bullish"] ? (
                    <span className="flex items-center gap-1 text-signal-bullish">
                      <span className="inline-block w-2 h-2 rounded-full bg-signal-bullish" />
                      {signalCounts["Bullish"]} Bull
                    </span>
                  ) : null}
                  {signalCounts["Bearish"] ? (
                    <span className="flex items-center gap-1 text-signal-bearish">
                      <span className="inline-block w-2 h-2 rounded-full bg-signal-bearish" />
                      {signalCounts["Bearish"]} Bear
                    </span>
                  ) : null}
                  {signalCounts["Neutral"] ? (
                    <span className="flex items-center gap-1 text-signal-neutral">
                      <span className="inline-block w-2 h-2 rounded-full bg-signal-neutral" />
                      {signalCounts["Neutral"]} Neut
                    </span>
                  ) : null}
                </div>
              )}

              {/* Refresh Button */}
              <button
                onClick={fetchSignals}
                disabled={loading}
                className="flex items-center gap-2 rounded-md border border-navy-700 bg-navy-800 px-3 py-1.5 text-xs text-text-secondary hover:bg-navy-700 hover:text-text-primary transition-all disabled:opacity-50 cursor-pointer"
              >
                <span className={loading ? "animate-spin" : ""}>&#x21BB;</span>
                Refresh
              </button>

              {/* Status Indicator */}
              <div className="flex items-center gap-2">
                <span
                  className={`inline-block w-2 h-2 rounded-full ${
                    error
                      ? "bg-signal-bearish"
                      : loading
                        ? "bg-signal-neutral animate-pulse"
                        : "bg-signal-bullish"
                  }`}
                />
                <span className="text-xs text-text-muted">
                  {error ? "ERROR" : loading ? "LOADING" : "LIVE"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        {/* Last Updated */}
        {lastRefresh && (
          <div className="mb-6 flex items-center gap-2 text-xs text-text-muted">
            <span>Last updated:</span>
            <span className="text-text-secondary">
              {lastRefresh.toLocaleString("en-US", {
                dateStyle: "medium",
                timeStyle: "medium",
              })}
            </span>
            <span className="text-text-muted">&#x2022;</span>
            <span>Auto-refresh: 5min</span>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="mb-6 rounded-lg border border-signal-bearish/30 bg-signal-bearish/10 p-4">
            <div className="flex items-center gap-2">
              <span className="text-signal-bearish font-bold">&#x26A0;</span>
              <span className="text-sm text-signal-bearish font-medium">
                Connection Error
              </span>
            </div>
            <p className="mt-1 text-xs text-text-secondary">{error}</p>
            <p className="mt-1 text-xs text-text-muted">
              Make sure the backend API is running at {API_URL}
            </p>
          </div>
        )}

        {/* Map - always render at top when we have data */}
        {data && data.signals.length > 0 && (
          <MapView signals={data.signals} />
        )}

        {/* Loading State */}
        {loading && !data && (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div
                key={i}
                className="rounded-lg border border-border-subtle bg-surface-elevated p-6 animate-pulse"
              >
                <div className="flex justify-between mb-4">
                  <div className="h-6 w-24 rounded bg-navy-700" />
                  <div className="h-8 w-20 rounded bg-navy-700" />
                </div>
                <div className="h-16 rounded bg-navy-700/50 mb-4" />
                <div className="h-4 w-3/4 rounded bg-navy-700/30 mb-2" />
                <div className="h-4 w-1/2 rounded bg-navy-700/30" />
              </div>
            ))}
          </div>
        )}

        {/* Signal Cards - 2x3 grid */}
        {data && (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {data.signals.map((signal) => (
              <CommodityCard key={signal.commodity} data={signal} />
            ))}
          </div>
        )}

        {/* Footer Info */}
        <footer className="mt-12 border-t border-border-subtle pt-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs text-text-muted">
            <div className="flex flex-col gap-1">
              <p>
                <span className="text-text-secondary font-medium">
                  Signal Methodology:
                </span>{" "}
                Weather-driven supply risk analysis using 7-day rolling
                conditions from growing regions.
              </p>
              <p>
                Drought/heat stress &#x2192; Bullish (supply risk) | Excess
                rainfall &#x2192; Bearish (harvest disruption) | Normal &#x2192;
                Neutral
              </p>
            </div>
            <div className="flex flex-col items-end gap-1">
              <p>
                Weather:{" "}
                <span className="text-accent-cyan">Open-Meteo API</span>
              </p>
              <p>
                Prices:{" "}
                <span className="text-accent-cyan">Yahoo Finance</span>
              </p>
              <p>
                Shipping:{" "}
                <span className="text-accent-cyan">Freightos</span>
              </p>
              <p>
                News:{" "}
                <span className="text-accent-cyan">NewsAPI</span>
              </p>
            </div>
          </div>
        </footer>
      </main>
    </div>
  );
}
