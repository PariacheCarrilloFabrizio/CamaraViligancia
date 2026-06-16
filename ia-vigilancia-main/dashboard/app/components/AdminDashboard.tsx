"use client";

import { useEffect, useState } from "react";
import {
  Search, ChevronDown, ChevronRight, Video, Server,
  ShieldAlert, Monitor, Activity, Cpu, Camera as CameraIcon
} from 'lucide-react';

type Health = {
  status: string;
  camera_source: string;
  fps: number;
  device: string;
  fight_model_enabled: boolean;
  enabled_events: string[];
  error: string | null;
};

type CameraOption = {
  source: string;
  label: string;
};

type EventItem = {
  code: string;
  title: string;
  priority: string;
  detail: string;
  created_at: string;
  evidence_path: string | null;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function AdminDashboard() {
  const [health, setHealth] = useState<Health | null>(null);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [cameraOptions, setCameraOptions] = useState<CameraOption[]>([]);
  const [selectedSource, setSelectedSource] = useState("0");
  const [manualSource, setManualSource] = useState("");
  const [isSwitchingCamera, setIsSwitchingCamera] = useState(false);
  const [streamVersion, setStreamVersion] = useState(0);

  const [isNvrOpen, setIsNvrOpen] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      try {
        const [healthResponse, eventsResponse] = await Promise.all([
          fetch(`${API_URL}/api/health`, { cache: "no-store" }),
          fetch(`${API_URL}/api/events`, { cache: "no-store" }),
        ]);

        if (!cancelled) {
          const nextHealth = await healthResponse.json();
          setHealth(nextHealth);
          setSelectedSource(nextHealth.camera_source ?? "0");
          setEvents(await eventsResponse.json());
        }
      } catch {
        if (!cancelled) {
          setHealth(null);
          setEvents([]);
        }
      }
    }

    loadData();
    const intervalId = window.setInterval(loadData, 1500);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, []);

  useEffect(() => {
    loadCameras();
  }, []);

  async function loadCameras() {
    try {
      const response = await fetch(`${API_URL}/api/cameras`, { cache: "no-store" });
      setCameraOptions(await response.json());
    } catch {
      setCameraOptions([]);
    }
  }

  async function changeCamera(source: string) {
    const trimmedSource = source.trim();
    if (!trimmedSource) return;

    setIsSwitchingCamera(true);
    try {
      const response = await fetch(`${API_URL}/api/camera`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: trimmedSource }),
      });
      const nextHealth = await response.json();
      setHealth(nextHealth);
      setSelectedSource(trimmedSource);
      setManualSource("");
      setStreamVersion((version) => version + 1);
    } finally {
      setIsSwitchingCamera(false);
    }
  }

  const cameraStatus = health?.status === "running" ? "En vivo" : "Sin conexión";

  return (
    <div className="flex h-screen bg-[#1c1c1c] text-gray-300 font-sans overflow-hidden">

      {/* BARRA LATERAL IZQUIERDA */}
      <aside className="w-80 bg-[#252525] border-r border-[#333] flex flex-col flex-shrink-0">

        <div className="h-14 flex items-center justify-between px-4 border-b border-[#333] bg-[#1e1e1e]">
          <div className="flex items-center">
            <ShieldAlert className="w-5 h-5 text-red-600 mr-2" />
            <h1 className="font-bold text-sm text-gray-100 tracking-wide">SMART WALL UTP</h1>
          </div>
          <span className="text-[10px] bg-[#333] text-gray-400 px-2 py-1 rounded">Chimbote</span>
        </div>

        <div className="p-4 border-b border-[#333] bg-[#1e1e1e]/50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Conexión Manual</span>
            <button
              onClick={loadCameras}
              className="text-[10px] bg-[#333] hover:bg-[#444] text-white px-2 py-1 rounded transition-colors flex items-center"
              type="button"
            >
              <Search className="w-3 h-3 mr-1" /> Escanear
            </button>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              className="w-full bg-[#141414] border border-[#444] text-xs text-gray-300 px-3 py-2 rounded focus:outline-none focus:border-red-600 transition-colors"
              placeholder="Índice o URL"
              value={manualSource}
              onChange={(e) => setManualSource(e.target.value)}
            />
            <button
              className="bg-red-700 hover:bg-red-600 disabled:opacity-50 text-white px-3 py-2 text-xs font-bold rounded transition-colors"
              disabled={!health || isSwitchingCamera || !manualSource.trim()}
              onClick={() => changeCamera(manualSource)}
              type="button"
            >
              Usar
            </button>
          </div>
          {health?.error && (
            <p className="mt-2 text-[10px] text-red-400 bg-red-900/20 p-2 rounded border border-red-900/50">
              {health.error}
            </p>
          )}
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar p-2">
          <div className="flex items-center text-xs py-2 px-1 hover:bg-[#333] cursor-pointer rounded">
            <Server className="w-4 h-4 mr-2 text-blue-400" />
            <span className="font-semibold text-gray-200">Servidor IA Local</span>
          </div>

          <div className="ml-2 mt-1">
            <div
              className="flex items-center text-xs py-1.5 px-1 hover:bg-[#333] cursor-pointer rounded"
              onClick={() => setIsNvrOpen(!isNvrOpen)}
            >
              {isNvrOpen ? <ChevronDown className="w-3.5 h-3.5 mr-1 text-gray-400" /> : <ChevronRight className="w-3.5 h-3.5 mr-1 text-gray-400" />}
              <Monitor className="w-4 h-4 mr-1.5 text-gray-400" />
              <span>Fuentes Disponibles</span>
            </div>

            {isNvrOpen && (
              <div className="ml-5 mt-1 flex flex-col gap-0.5">

                <button
                  onClick={() => changeCamera("0")}
                  className={`flex items-center text-left text-xs py-2 px-3 rounded transition-colors ${selectedSource === "0"
                      ? "bg-red-600/20 border-l-2 border-red-600 text-white font-bold"
                      : "hover:bg-[#333] text-gray-400 border-l-2 border-transparent"
                    }`}
                >
                  <Video className={`w-4 h-4 mr-2 ${selectedSource === "0" ? "text-red-500" : "text-emerald-500"}`} />
                  Cámara Principal
                </button>

                <button
                  onClick={() => changeCamera("1")}
                  className={`flex items-center text-left text-xs py-2 px-3 rounded transition-colors ${selectedSource === "1"
                      ? "bg-red-600/20 border-l-2 border-red-600 text-white font-bold"
                      : "hover:bg-[#333] text-gray-400 border-l-2 border-transparent"
                    }`}
                >
                  <Video className={`w-4 h-4 mr-2 ${selectedSource === "1" ? "text-red-500" : "text-emerald-500"}`} />
                  Biblioteca Norte
                </button>

                <button
                  onClick={() => changeCamera("2")}
                  className={`flex items-center text-left text-xs py-2 px-3 rounded transition-colors ${selectedSource === "2"
                      ? "bg-red-600/20 border-l-2 border-red-600 text-white font-bold"
                      : "hover:bg-[#333] text-gray-400 border-l-2 border-transparent"
                    }`}
                >
                  <Video className={`w-4 h-4 mr-2 ${selectedSource === "2" ? "text-red-500" : "text-emerald-500"}`} />
                  Laboratorio TI
                </button>

                {cameraOptions.filter(cam => !["0", "1", "2"].includes(cam.source)).map((cam) => (
                  <button
                    key={cam.source}
                    onClick={() => changeCamera(cam.source)}
                    className={`flex items-center text-left text-xs py-2 px-3 rounded transition-colors ${selectedSource === cam.source
                        ? "bg-red-600/20 border-l-2 border-red-600 text-white font-bold"
                        : "hover:bg-[#333] text-gray-400 border-l-2 border-transparent"
                      }`}
                  >
                    <Video className={`w-4 h-4 mr-2 ${selectedSource === cam.source ? "text-red-500" : "text-emerald-500"}`} />
                    {cam.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="border-t border-[#333] p-4 bg-[#1e1e1e]">
          <div className="flex items-center text-xs text-gray-400 mb-2">
            <Activity className="w-3.5 h-3.5 mr-2" /> Modelos Activos:
            <span className="ml-1 text-gray-200">{health?.enabled_events?.length ?? 0}</span>
          </div>
          <div className="flex items-center text-xs text-gray-400">
            <Server className="w-3.5 h-3.5 mr-2" /> API:
            <span className="ml-1 text-[10px] text-blue-400 truncate">{API_URL}</span>
          </div>
        </div>
      </aside>

      {/* ÁREA PRINCIPAL */}
      <main className="flex-1 flex flex-col bg-[#141414]">

        <header className="h-14 border-b border-[#333] flex justify-between items-center px-6 bg-[#1e1e1e]">
          <div className="flex items-center gap-4">
            <span className="text-sm font-semibold text-white uppercase tracking-wider">Monitor Principal</span>
            <span className={`text-[10px] font-bold px-2 py-1 rounded border uppercase tracking-wider ${health?.status === "running"
                ? "bg-emerald-900/50 text-emerald-400 border-emerald-800"
                : "bg-red-900/50 text-red-400 border-red-800"
              }`}>
              {cameraStatus}
            </span>
          </div>
          <div className="flex gap-6">
            <div className="flex items-center gap-2">
              <CameraIcon className="w-4 h-4 text-gray-500" />
              <div>
                <p className="text-[9px] text-gray-500 uppercase font-bold">Fuente Activa</p>
                <p className="text-xs font-mono text-gray-200">{selectedSource}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-gray-500" />
              <div>
                <p className="text-[9px] text-gray-500 uppercase font-bold">Aceleración</p>
                <p className={`text-xs font-mono ${health?.device.includes('cuda') ? 'text-emerald-400' : 'text-blue-400'}`}>
                  {health?.device?.toUpperCase() ?? "N/A"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 border-l border-[#333] pl-6">
              <div>
                <p className="text-[9px] text-gray-500 uppercase font-bold">Rendimiento</p>
                <p className="text-sm font-mono font-bold text-white">{health?.fps ?? 0} FPS</p>
              </div>
            </div>
          </div>
        </header>

        <div className="flex-1 flex p-4 gap-4 overflow-hidden">

          <div className="flex-1 bg-black border border-[#333] rounded-lg shadow-2xl relative overflow-hidden flex flex-col">
            <div className="absolute top-3 left-3 z-10 bg-black/70 px-2 py-1 rounded text-[10px] font-mono text-white border border-[#444] flex items-center">
              <span className={`w-1.5 h-1.5 rounded-full mr-2 ${health ? "bg-red-500 animate-pulse" : "bg-gray-500"}`}></span>
              CAM-{selectedSource} | {new Date().toLocaleDateString()}
            </div>

            {health ? (
              <img
                src={`${API_URL}/video_feed?v=${streamVersion}`}
                alt="Stream en vivo de la camara"
                className="w-full h-full object-contain"
              />
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-[#333]">
                <Monitor className="w-24 h-24 mb-4 opacity-20" />
                <p className="text-sm font-bold text-gray-600 uppercase tracking-widest">Señal Perdida</p>
              </div>
            )}
          </div>

          <div className="w-80 bg-[#1e1e1e] border border-[#333] rounded-lg shadow-lg flex flex-col overflow-hidden">
            <div className="h-12 bg-[#252525] border-b border-[#333] flex items-center justify-between px-4">
              <div className="flex items-center">
                <span className="text-xs font-bold text-gray-300 uppercase tracking-widest">Alertas IA</span>
                <span className="ml-2 bg-red-600 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full">{events.length}</span>
              </div>
              <span className="text-[9px] text-gray-500 uppercase font-bold">Tiempo Real</span>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-2 custom-scrollbar">
              {events.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center px-4">
                  <ShieldAlert className="w-10 h-10 text-gray-700 mb-3" />
                  <p className="text-xs font-bold text-gray-500 uppercase">Sin eventos</p>
                  <p className="text-[10px] text-gray-600 mt-1">El perímetro se encuentra seguro y bajo monitoreo constante.</p>
                </div>
              ) : (
                events.map((event) => (
                  <div
                    key={`${event.code}-${event.created_at}-${event.detail}`}
                    className={`border p-3 rounded shadow-sm ${event.priority === "alta"
                        ? "bg-[#2a1717] border-red-900/50"
                        : event.priority === "media"
                          ? "bg-[#2a2417] border-yellow-900/50"
                          : "bg-[#172a21] border-emerald-900/50"
                      }`}
                  >
                    <div className="flex justify-between items-start mb-1.5">
                      <span className={`text-xs font-bold ${event.priority === "alta"
                          ? "text-red-400"
                          : event.priority === "media"
                            ? "text-yellow-400"
                            : "text-emerald-400"
                        }`}>
                        {event.title}
                      </span>
                      <span className="text-[10px] text-gray-500 font-mono">
                        {event.created_at.split(' ')[1] || event.created_at}
                      </span>
                    </div>
                    <p className="text-[10px] text-gray-400 leading-relaxed mb-2">{event.detail}</p>
                    <div className="flex justify-between items-center mt-2 pt-2 border-t border-black/20">
                      <span className="text-[9px] uppercase font-bold text-gray-500">Prioridad:</span>
                      <span className={`text-[9px] uppercase font-bold px-1.5 rounded ${event.priority === "alta" ? "bg-red-900/50 text-red-300" : "bg-gray-800 text-gray-400"
                        }`}>
                        {event.priority}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>
      </main>

    </div>
  );
}