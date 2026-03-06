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

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

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
        link.integrity =
          "sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=";
        link.crossOrigin = "anonymous";
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

      // Clear all non-tile layers (markers, polylines, port markers)
      map.eachLayer((layer: L.Layer) => {
        if (!(layer instanceof L.TileLayer)) {
          map.removeLayer(layer);
        }
      });

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

          // Look up producer share for this region's country
          const producer = sig.producers.find(
            (p) => p.country === region.country
          );
          const shareLine = producer
            ? `<strong>${escapeHtml(producer.share_percent.toFixed(1))}%</strong> of global production<br/>`
            : "";

          marker.bindPopup(
            `<div style="font-family:monospace;font-size:12px;color:#0a0e1a;min-width:180px">
              <strong>${escapeHtml(sig.commodity)}</strong> - ${escapeHtml(region.region_name)}<br/>
              <span style="color:${color};font-weight:bold">${escapeHtml(sig.signal)}</span><br/>
              <hr style="margin:4px 0;border-color:#ddd"/>
              ${shareLine}
              Temp: ${escapeHtml(region.temperature_avg.toFixed(1))}&deg;C<br/>
              Rain: ${escapeHtml(region.precipitation_sum.toFixed(1))}mm<br/>
              Humidity: ${escapeHtml(region.relative_humidity.toFixed(0))}%<br/>
              <em>${escapeHtml(region.condition_summary)}</em>
            </div>`
          );
        }

        // Draw shipping lane polyline if coordinates are available
        if (
          sig.shipping &&
          sig.shipping.origin_lat !== null &&
          sig.shipping.origin_lon !== null &&
          sig.shipping.destination_lat !== null &&
          sig.shipping.destination_lon !== null
        ) {
          const laneColor = color;
          const polyline = L.polyline(
            [
              [sig.shipping.origin_lat, sig.shipping.origin_lon],
              [sig.shipping.destination_lat, sig.shipping.destination_lon],
            ],
            {
              color: laneColor,
              weight: 2,
              opacity: 0.5,
              dashArray: "6, 8",
            }
          ).addTo(map);

          const rateLabel =
            sig.shipping.rate_usd !== null
              ? `$${escapeHtml(sig.shipping.rate_usd.toLocaleString())} / ${escapeHtml(sig.shipping.container_type)}`
              : "Rate N/A";

          polyline.bindPopup(
            `<div style="font-family:monospace;font-size:12px;color:#0a0e1a;min-width:180px">
              <strong>${escapeHtml(sig.commodity)}</strong> Shipping Lane<br/>
              <span style="color:${laneColor};font-weight:bold">${escapeHtml(sig.shipping.route)}</span><br/>
              <hr style="margin:4px 0;border-color:#ddd"/>
              ${escapeHtml(sig.shipping.origin_port)} &#x2192; ${escapeHtml(sig.shipping.destination_port)}<br/>
              ${rateLabel}
            </div>`
          );

          // Add port markers (small diamonds at origin/destination)
          for (const port of [
            { lat: sig.shipping.origin_lat, lon: sig.shipping.origin_lon, label: sig.shipping.origin_port },
            { lat: sig.shipping.destination_lat, lon: sig.shipping.destination_lon, label: sig.shipping.destination_port },
          ]) {
            L.circleMarker([port.lat, port.lon], {
              radius: 4,
              fillColor: "#38bdf8",
              color: "#0ea5e9",
              weight: 1.5,
              opacity: 0.9,
              fillOpacity: 0.7,
            }).addTo(map);
          }
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
          <span className="flex items-center gap-1">
            <span className="inline-block w-3 border-t border-dashed border-sky-400" />
            Shipping
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
