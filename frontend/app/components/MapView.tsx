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

const COMMODITY_COLORS: Record<string, string> = {
  Coffee: "#c084fc",
  Sugar: "#f9a8d4",
  Cocoa: "#a78bfa",
  "Orange Juice": "#fb923c",
  Lumber: "#86efac",
  "Palm Oil": "#fcd34d",
};

const DARK_TILE_URL =
  "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";

export default function MapView({ signals }: MapViewProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const [ready, setReady] = useState(false);
  const [showVessels, setShowVessels] = useState(true);
  const [showRegions, setShowRegions] = useState(true);
  const showVesselsRef = useRef(true);
  const showRegionsRef = useRef(true);
  const vesselLayerRef = useRef<L.LayerGroup | null>(null);
  const regionLayerRef = useRef<L.LayerGroup | null>(null);

  const totalVessels = signals.reduce(
    (acc, s) => acc + (s.vessels?.length ?? 0),
    0
  );

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
        center: [10, 20],
        zoom: 2,
        minZoom: 2,
        maxZoom: 6,
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

      // Remove old layer groups
      if (vesselLayerRef.current) {
        map.removeLayer(vesselLayerRef.current);
        vesselLayerRef.current = null;
      }
      if (regionLayerRef.current) {
        map.removeLayer(regionLayerRef.current);
        regionLayerRef.current = null;
      }

      // Clear any remaining circle markers
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

      // Create layer groups
      const regionGroup = L.layerGroup();
      const vesselGroup = L.layerGroup();

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
          );

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

          regionGroup.addLayer(marker);
        }
      }

      // Add vessel markers and route lines
      for (const sig of signals) {
        const routeColor = COMMODITY_COLORS[sig.commodity] ?? "#60a5fa";

        if (!sig.vessels) continue;

        let routeDrawn = false;

        for (const vessel of sig.vessels) {
          // Draw route polyline once per commodity
          if (
            !routeDrawn &&
            vessel.route_coords &&
            vessel.route_coords.length > 1
          ) {
            const routeLine = L.polyline(
              vessel.route_coords.map(
                (c) => [c[0], c[1]] as L.LatLngTuple
              ),
              {
                color: routeColor,
                weight: 1.5,
                opacity: 0.35,
                dashArray: "6,4",
              }
            );
            vesselGroup.addLayer(routeLine);
            routeDrawn = true;
          }

          // Ship icon using a rotated SVG
          const shipIcon = L.divIcon({
            className: "",
            html: `<div style="
              width:24px;height:24px;display:flex;align-items:center;justify-content:center;
              transform:rotate(${vessel.heading}deg);
              filter:drop-shadow(0 0 4px ${routeColor});
            ">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="${routeColor}" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L4 20h3l1.5-4h7l1.5 4h3L12 2zm0 4l3.5 10h-7L12 6z" opacity="0.9"/>
              </svg>
            </div>`,
            iconSize: [24, 24],
            iconAnchor: [12, 12],
          });

          const shipMarker = L.marker(
            [vessel.latitude, vessel.longitude],
            { icon: shipIcon }
          );

          shipMarker.bindPopup(
            `<div style="font-family:monospace;font-size:12px;color:#0a0e1a;min-width:220px">
              <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">
                <span style="font-size:16px">&#x1F6A2;</span>
                <strong style="font-size:13px">${vessel.name}</strong>
              </div>
              <hr style="margin:4px 0;border-color:#ddd"/>
              <div style="display:grid;grid-template-columns:auto 1fr;gap:2px 8px">
                <span style="color:#666">Cargo:</span>
                <span style="font-weight:600;color:${routeColor}">${vessel.cargo}</span>
                <span style="color:#666">Type:</span>
                <span>${vessel.vessel_type}</span>
                <span style="color:#666">MMSI:</span>
                <span>${vessel.mmsi}</span>
                ${vessel.imo ? `<span style="color:#666">IMO:</span><span>${vessel.imo}</span>` : ""}
                <span style="color:#666">Speed:</span>
                <span>${vessel.speed_knots} kn</span>
                <span style="color:#666">Heading:</span>
                <span>${vessel.heading.toFixed(0)}&deg;</span>
                <span style="color:#666">Status:</span>
                <span>${vessel.status}</span>
                <span style="color:#666">Route:</span>
                <span>${vessel.origin_port} &rarr; ${vessel.destination_port}</span>
                ${vessel.eta ? `<span style="color:#666">ETA:</span><span>${vessel.eta}</span>` : ""}
              </div>
              <div style="margin-top:4px;font-size:10px;color:#999">
                Source: ${vessel.source === "simulated" ? "Simulated AIS" : vessel.source}
              </div>
            </div>`
          );

          vesselGroup.addLayer(shipMarker);
        }
      }

      // Store layer groups
      regionLayerRef.current = regionGroup;
      vesselLayerRef.current = vesselGroup;

      // Add layers based on current toggle state (read from refs to avoid stale closure)
      if (showRegionsRef.current) regionGroup.addTo(map);
      if (showVesselsRef.current) vesselGroup.addTo(map);
    }

    addMarkers();
  }, [signals, ready]);

  // Keep refs in sync and toggle region layer visibility
  useEffect(() => {
    showRegionsRef.current = showRegions;
    const map = mapInstanceRef.current;
    if (!map || !regionLayerRef.current) return;
    if (showRegions) {
      regionLayerRef.current.addTo(map);
    } else {
      map.removeLayer(regionLayerRef.current);
    }
  }, [showRegions]);

  // Keep refs in sync and toggle vessel layer visibility
  useEffect(() => {
    showVesselsRef.current = showVessels;
    const map = mapInstanceRef.current;
    if (!map || !vesselLayerRef.current) return;
    if (showVessels) {
      vesselLayerRef.current.addTo(map);
    } else {
      map.removeLayer(vesselLayerRef.current);
    }
  }, [showVessels]);

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
            Global Growing Regions & Vessel Tracking
          </span>
          <span className="text-xs text-text-muted">
            ({signals.reduce((acc, s) => acc + s.regions.length, 0)} regions,{" "}
            {totalVessels} vessels)
          </span>
        </div>
        <div className="flex items-center gap-4 text-[10px]">
          {/* Layer toggles */}
          <button
            onClick={() => setShowRegions(!showRegions)}
            className={`flex items-center gap-1 cursor-pointer transition-opacity ${
              showRegions ? "opacity-100" : "opacity-40"
            }`}
          >
            <span className="inline-block w-2 h-2 rounded-full bg-signal-neutral" />
            Regions
          </button>
          <button
            onClick={() => setShowVessels(!showVessels)}
            className={`flex items-center gap-1 cursor-pointer transition-opacity ${
              showVessels ? "opacity-100" : "opacity-40"
            }`}
          >
            <span className="text-xs">&#x1F6A2;</span>
            Vessels
          </button>
          <span className="w-px h-3 bg-navy-700" />
          {/* Signal colors legend */}
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
        style={{ height: "400px", width: "100%", background: "#0a0e1a" }}
      />
    </div>
  );
}
