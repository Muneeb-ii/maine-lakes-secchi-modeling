import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { MapPin, X } from "lucide-react";
import { API_URL } from "../../lib/constants";
import { parseLakeSearchResponse } from "../../lib/contracts";

const DEFAULT_CENTER = [44.35, -69.2];
const DEFAULT_ZOOM = 7;
const FOCUSED_ZOOM = 12;

function hasLocation(lake) {
  return typeof lake?.latitude === "number" && typeof lake?.longitude === "number";
}

function formatCoordinates(lake) {
  if (!hasLocation(lake)) return "";
  return `${lake.latitude.toFixed(4)}, ${lake.longitude.toFixed(4)}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function markerIcon(isCurrent) {
  return L.divIcon({
    className: `lake-map-pin ${isCurrent ? "lake-map-pin-current" : ""}`,
    html: `<span></span>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
    popupAnchor: [0, -9],
  });
}

export function LakeMapPicker({
  isOpen,
  initialLake,
  currentLakeId,
  onClose,
  onSelectLake,
}) {
  const mapRef = useRef(null);
  const mapNodeRef = useRef(null);
  const markerLayerRef = useRef(null);
  const popupHandlersRef = useRef(new Map());
  const [lakes, setLakes] = useState([]);
  const [status, setStatus] = useState("");
  const [selectedLakeId, setSelectedLakeId] = useState("");

  const focusLake = useMemo(() => {
    if (hasLocation(initialLake)) return initialLake;
    return lakes.find((lake) => lake.midasId === currentLakeId && hasLocation(lake));
  }, [currentLakeId, initialLake, lakes]);

  useEffect(() => {
    if (!isOpen) return;
    let cancelled = false;

    async function loadLocations() {
      try {
        setStatus("Loading lake map…");
        const res = await fetch(`${API_URL}/lakes/locations`);
        const payload = await res.json();
        if (!res.ok) {
          throw new Error("Lake locations could not be loaded.");
        }
        const parsed = parseLakeSearchResponse(payload).filter(hasLocation);
        if (!cancelled) {
          setLakes(parsed);
          setStatus("");
        }
      } catch (error) {
        if (!cancelled) {
          setLakes([]);
          setStatus(error.message || "Lake locations could not be loaded.");
        }
      }
    }

    loadLocations();
    return () => {
      cancelled = true;
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return undefined;
    const onKeyDown = (event) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (!isOpen || !mapNodeRef.current || mapRef.current) return;

    const startCenter = hasLocation(focusLake)
      ? [focusLake.latitude, focusLake.longitude]
      : DEFAULT_CENTER;
    const map = L.map(mapNodeRef.current, {
      center: startCenter,
      zoom: hasLocation(focusLake) ? FOCUSED_ZOOM : DEFAULT_ZOOM,
      scrollWheelZoom: true,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);

    markerLayerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;

    const timer = window.setTimeout(() => map.invalidateSize(), 80);
    return () => {
      window.clearTimeout(timer);
      popupHandlersRef.current.clear();
      map.remove();
      mapRef.current = null;
      markerLayerRef.current = null;
    };
  }, [focusLake, isOpen]);

  useEffect(() => {
    const map = mapRef.current;
    const layer = markerLayerRef.current;
    if (!isOpen || !map || !layer) return;

    popupHandlersRef.current.clear();
    layer.clearLayers();

    lakes.forEach((lake) => {
      const buttonId = `lake-map-select-${lake.midasId}`;
      const marker = L.marker([lake.latitude, lake.longitude], {
        icon: markerIcon(lake.midasId === currentLakeId),
        title: `${lake.lakeName} ${lake.midasId}`,
      });
      const areaLine =
        typeof lake.areaAcres === "number"
          ? `<p class="lake-map-popup-meta">${lake.areaAcres.toLocaleString(undefined, {
              maximumFractionDigits: 1,
            })} acres</p>`
          : "";
      marker.bindPopup(`
        <div class="lake-map-popup">
          <p class="lake-map-popup-title">${escapeHtml(lake.lakeName)}</p>
          <p class="lake-map-popup-meta">${escapeHtml(lake.midasId)} · ${escapeHtml(formatCoordinates(lake))}</p>
          ${areaLine}
          <button type="button" id="${buttonId}" class="lake-map-popup-button">Select lake</button>
        </div>
      `);
      marker.on("popupopen", () => {
        const button = document.getElementById(buttonId);
        const handler = async () => {
          setSelectedLakeId(lake.midasId);
          try {
            await Promise.resolve(onSelectLake(lake.midasId, lake.lakeName));
            onClose();
          } finally {
            setSelectedLakeId("");
          }
        };
        if (button) {
          button.addEventListener("click", handler);
          popupHandlersRef.current.set(buttonId, { button, handler });
        }
      });
      marker.on("popupclose", () => {
        const registered = popupHandlersRef.current.get(buttonId);
        if (registered) {
          registered.button.removeEventListener("click", registered.handler);
          popupHandlersRef.current.delete(buttonId);
        }
      });
      marker.addTo(layer);
    });
  }, [currentLakeId, isOpen, lakes, onClose, onSelectLake]);

  useEffect(() => {
    const map = mapRef.current;
    if (!isOpen || !map || !hasLocation(focusLake)) return;
    map.setView([focusLake.latitude, focusLake.longitude], FOCUSED_ZOOM, {
      animate: true,
    });
  }, [focusLake, isOpen]);

  if (!isOpen) return null;

  return createPortal(
    <div className="lake-map-layer" role="dialog" aria-modal="true" aria-label="Choose a lake from the map">
      <div className="lake-map-scrim" aria-hidden onClick={onClose} />
      <section className="lake-map-modal">
        <div className="flex items-start justify-between gap-3 border-b border-slate-200 pb-3">
          <div>
            <p className="claro-kicker">
              <MapPin className="h-4 w-4" aria-hidden />
              Lake map
            </p>
            <h2 className="mt-1 text-xl font-semibold leading-snug text-slate-950">
              Choose a lake by location
            </h2>
          </div>
          <button type="button" className="claro-icon-button" onClick={onClose} aria-label="Close lake map">
            <X className="h-5 w-5" aria-hidden />
          </button>
        </div>
        <div className="relative mt-4">
          <div ref={mapNodeRef} className="lake-map-canvas" />
          {status && (
            <div className="lake-map-status" role="status">
              {status}
            </div>
          )}
          {selectedLakeId && (
            <div className="lake-map-status" role="status">
              Loading selected lake…
            </div>
          )}
        </div>
      </section>
    </div>,
    document.body
  );
}
