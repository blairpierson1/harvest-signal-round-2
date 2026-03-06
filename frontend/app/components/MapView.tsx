"use client";

import { useEffect, useRef, useState } from "react";
import type { CommoditySignal, Signal } from "../types";

interface MapViewProps {
  signals: CommoditySignal[];
}

const SIGNAL_COLORS: Record<Signal, string> = {
  Bullish: "#22c55e",
  Bearish: "#ef4444",
  Neutral: "#f59e0b",
};

const DARK_TILE_URL =
  "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";

export default function MapView({ signals }: MapViewProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined" || !mapRef.current) return;
    if (mapInstanceRef.current) return; // already initialized

    let cancelled = false;

    async function initMap() {
      const L = await import("leaflet");

      // Import leaflet CSS
      if (!document.querySelector('link[href*="leaflet.css"]')) {
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
        document.head.appendChild(link);
      }

      if (cancelled || !mapRef.current) return;

      const map = L.map(mapRef.current, {
        center: [30, 45],
        zoom: 4,
        minZoom: 3,
        maxZoom: 8,
        zoomControl: true,
        attributionControl: false,
        scrollWheelZoom: true,
      });

      L.tileLayer(DARK_TILE_URL, {
        subdomains: "abcd",
        maxZoom: 19,
      }).addTo(map);

      mapInstanceRef.current = map;
      setReady(true);
    }

    initMap();

    return () => {
      cancelled = true;
    };
  }, []);

  // Add markers when signals data changes and map is ready
  useEffect(() => {
    if (!ready || !mapInstanceRef.current || !signals.length) return;

    async function addMarkers() {
      const L = await import("leaflet");
      const map = mapInstanceRef.current;
      if (!map) return;

      // Clear existing markers
      map.eachLayer((layer: L.Layer) => {
        if ((layer as L.CircleMarker).getRadius) {
          map.removeLayer(layer);
        }
      });

      // Re-add tile layer if it was removed
      let hasTile = false;
      map.eachLayer((layer: L.Layer) => {
        if (layer instanceof L.TileLayer) hasTile = true;
      });
      if (!hasTile) {
        L.tileLayer(DARK_TILE_URL, {
          subdomains: "abcd",
          maxZoom: 19,
        }).addTo(map);
      }

      // Add region markers for each commodity
      for (const sig of signals) {
        const color = SIGNAL_COLORS[sig.signal];

        for (const region of sig.regions) {
          const marker = L.circleMarker(
            [region.latitude, region.longitude],
            {
              radius: 7,
              fillColor: color,
              color: color,
              weight: 2,
              opacity: 0.9,
              fillOpacity: 0.5,
            }
          ).addTo(map);

          marker.bindPopup(
            `<div style="font-family:monospace;font-size:12px;color:#0a0e1a;min-width:180px">
              <strong>${sig.commodity}</strong> - ${region.region_name}<br/>
              <span style="color:${color};font-weight:bold">${sig.signal}</span><br/>
              <hr style="margin:4px 0;border-color:#ddd"/>
              Temp: ${region.temperature_avg.toFixed(1)}&deg;C<br/>
              Rain: ${region.precipitation_sum.toFixed(1)}mm<br/>
              Humidity: ${region.relative_humidity.toFixed(0)}%<br/>
              <em>${region.condition_summary}</em>
            </div>`
          );
        }
      }
    }

    addMarkers();
  }, [signals, ready]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  return (
    <div className="mb-6 rounded-lg border border-border-subtle bg-surface-elevated overflow-hidden">
      <div className="px-4 py-3 border-b border-border-subtle flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-text-primary tracking-wide">
            Middle East Growing Regions
          </span>
          <span className="text-xs text-text-muted">
            ({signals.reduce((acc, s) => acc + s.regions.length, 0)} regions tracked)
          </span>
        </div>
        <div className="flex items-center gap-3 text-[10px]">
          <span className="flex items-center gap-1">
            <span className="inline-block w-2 h-2 rounded-full bg-signal-bullish" />
            Bullish
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-2 h-2 rounded-full bg-signal-bearish" />
            Bearish
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-2 h-2 rounded-full bg-signal-neutral" />
            Neutral
          </span>
        </div>
      </div>
      <div
        ref={mapRef}
        style={{ height: "320px", width: "100%", background: "#0a0e1a" }}
      />
    </div>
  );
}
