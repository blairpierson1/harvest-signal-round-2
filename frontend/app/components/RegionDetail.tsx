"use client";

import type { RegionWeather } from "../types";

interface RegionDetailProps {
  regions: RegionWeather[];
}

export default function RegionDetail({ regions }: RegionDetailProps) {
  return (
    <div className="mt-4 border-t border-border-subtle pt-4">
      <h4 className="text-xs font-semibold text-text-muted uppercase tracking-widest mb-3">
        Growing Regions
      </h4>
      <div className="grid gap-2">
        {regions.map((region) => (
          <div
            key={`${region.region_name}-${region.country}`}
            className="flex items-center justify-between rounded-md bg-navy-900/50 px-3 py-2"
          >
            <div className="flex flex-col">
              <span className="text-sm font-medium text-text-primary">
                {region.region_name}
              </span>
              <span className="text-xs text-text-muted">{region.country}</span>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <div className="flex flex-col items-end">
                <span className="text-text-muted">Temp</span>
                <span className="text-text-secondary font-medium tabular-nums">
                  {region.temperature_avg.toFixed(1)}°C
                </span>
              </div>
              <div className="flex flex-col items-end">
                <span className="text-text-muted">Rain</span>
                <span className="text-text-secondary font-medium tabular-nums">
                  {region.precipitation_sum.toFixed(1)}mm
                </span>
              </div>
              <div className="flex flex-col items-end">
                <span className="text-text-muted">RH</span>
                <span className="text-text-secondary font-medium tabular-nums">
                  {region.relative_humidity.toFixed(0)}%
                </span>
              </div>
              <div className="hidden sm:flex flex-col items-end min-w-24">
                <span className="text-text-muted">Status</span>
                <span className="text-accent-cyan text-right">
                  {region.condition_summary}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
