from __future__ import annotations

import json
import threading
import time
import os
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any
import uuid
import concurrent.futures
from ultralytics import YOLO 

import cv2
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from supabase import create_client, Client

from alerts import EvidenceManager
from capture import list_available_cameras, open_camera
from config import Settings
from detector import YOLODetector
from event_engine import EventEngine, EventRecord

# --- CONFIGURACIÓN DE SUPABASE ---
SUPABASE_URL = "https://mwdpanztvxlkefxnpoox.supabase.co"
SUPABASE_KEY = "AQUI_PEGA_TU_LLAVE"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# ---------------------------------

class CameraRuntime:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.detector = YOLODetector(
            model_path=settings.model_path,
            confidence_threshold=settings.confidence_threshold,
            tracked_classes=settings.tracked_classes,
            fight_model_path=settings.fight_model_path,
            fight_confidence_threshold=settings.fight_confidence_threshold,
            inference_device=settings.inference_device,
            image_size=settings.inference_image_size,
        )
        self.event_engine = EventEngine(
            enabled_events=settings.enabled_events,
            fight_motion_threshold=settings.fight_motion_threshold,
            fight_frames_required=settings.fight_frames_required,
            crowd_person_threshold=settings.crowd_person_threshold,
        )
        self.evidence_manager = EvidenceManager(
            directory=Path(settings.evidence_dir),
            cooldown_seconds=settings.evidence_cooldown_seconds,
            enabled=settings.save_evidence,
        )
        
        self.smoking_model = YOLO("models/smoking/best.pt")
        
        self.events: deque[dict[str, Any]] = deque(maxlen=30) 
        
        self.latest_frame: bytes | None = None
        self.latest_fps = 0.0
        self.running = False
        self.error: str | None = None
        self.lock = threading.Lock()
        self.thread: threading.Thread | None = None
        
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.is_detecting = False

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3)
        self.thread = None

    def switch_camera(self, source: str) -> dict[str, Any]:
        self.stop()
        with self.lock:
            self.latest_frame = None
        self.latest_fps = 0.0
        self.error = None
        self.settings.camera_source = source
        self.start()
        return self.health()

    def _ai_task(self, frame_copy: cv2.typing.MatLike) -> None:
        """Tarea pesada de YOLO aislada del video en vivo"""
        try:
            summary = self.detector.detect(frame_copy)
            detected_events = self.event_engine.analyze(frame_copy, summary)
            if detected_events:
                self._record_events(frame_copy, detected_events)
                
            smoking_results = self.smoking_model(frame_copy, conf=0.45, verbose=False)[0]
            
            for box in smoking_results.boxes:
                cls_id = int(box.cls[0])
                label = smoking_results.names[cls_id]
                
                # OJO: Cambia "smoking" por el nombre exacto que le diste a la etiqueta en Roboflow si es distinto
                if label == "smoking" or label == "fumar":
                    smoking_event = EventRecord(
                        code="infraction_smoking",
                        title="Infracción: Persona fumando",
                        priority="media",
                        detail="Se detectó el uso de cigarrillos en zona no autorizada."
                    )
                    self._record_events(frame_copy, [smoking_event])
                    break # Salimos del bucle para no lanzar 100 alertas de la misma persona
                    
        except Exception as e:
            print(f"[ERROR IA]: Falló el procesamiento: {e}")
        finally:
            self.is_detecting = False

    def _capture_loop(self) -> None:
        camera = None
        fps_frames = 0
        last_fps_at = time.perf_counter()

        try:
            camera = open_camera(
                self.settings.camera_source,
                width=self.settings.camera_width,
                height=self.settings.camera_height,
                fps=self.settings.camera_fps,
            )
            self.error = None

            while self.running:
                ok, frame = camera.read()
                if not ok:
                    time.sleep(0.01)
                    continue

                if not self.is_detecting:
                    self.is_detecting = True
                    self.executor.submit(self._ai_task, frame.copy())

                encoded_frame = self._encode_frame(frame)
                
                fps_frames += 1
                now = time.perf_counter()
                if now - last_fps_at >= 1:
                    self.latest_fps = fps_frames / (now - last_fps_at)
                    fps_frames = 0
                    last_fps_at = now

                with self.lock:
                    self.latest_frame = encoded_frame

        except Exception as exc:
            self.error = str(exc)
            self.running = False
        finally:
            if camera is not None:
                camera.release()

    def _record_events(self, frame: cv2.typing.MatLike, events: list[EventRecord]) -> None:
        for event in events:
            saved_path = self.evidence_manager.save_event_evidence(frame, event)
            
            web_path = None
            if saved_path:
                filename = Path(saved_path).name
                web_path = f"evidences/{filename}"

            try:
                supabase.table("events").insert({
                    "code": f"{event.code}-{uuid.uuid4().hex[:6]}",
                    "title": event.title,
                    "priority": event.priority,
                    "detail": event.detail,
                    "evidence_path": web_path
                }).execute()
                print(f"[SUPABASE] Alerta '{event.title}' guardada en la base de datos.")
            except Exception as e:
                print(f"[SUPABASE ERROR] No se pudo guardar en DB: {e}")

    def _encode_frame(self, frame: cv2.typing.MatLike) -> bytes:
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), self.settings.stream_jpeg_quality]
        ok, buffer = cv2.imencode(".jpg", frame, encode_params)
        if not ok:
            return b""
        return buffer.tobytes()

    def get_events(self) -> list[dict[str, Any]]:
        try:
            response = supabase.table("events").select("*").order("created_at", desc=True).limit(30).execute()
            return response.data
        except Exception as e:
            print(f"[SUPABASE ERROR] Error al leer eventos: {e}")
            return []

    def health(self) -> dict[str, Any]:
        return {
            "status": "running" if self.running else "stopped",
            "camera_source": self.settings.camera_source,
            "fps": round(self.latest_fps, 1),
            "device": self.detector.device,
            "fight_model_enabled": self.detector.fight_model is not None,
            "enabled_events": self.settings.enabled_events,
            "error": self.error,
        }

    def frame_stream(self):
        while True:
            with self.lock:
                frame = self.latest_frame

            if frame is None:
                time.sleep(0.05)
                continue

            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            time.sleep(0.01)


settings = Settings.from_env()
runtime = CameraRuntime(settings)


class CameraSelection(BaseModel):
    source: str


app = FastAPI(title="IA Vigilancia API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.evidence_dir, exist_ok=True)
app.mount("/evidences", StaticFiles(directory=settings.evidence_dir), name="evidences")

@app.on_event("startup")
def start_camera() -> None:
    runtime.settings.camera_source = "0" 
    runtime.start()

@app.get("/api/health")
def health() -> dict[str, Any]:
    return runtime.health()

@app.get("/api/cameras")
def cameras() -> list[dict[str, str]]:
    return [
        {"source": camera.source, "label": camera.label}
        for camera in list_available_cameras(settings.camera_scan_limit)
    ]

@app.post("/api/camera")
def select_camera(selection: CameraSelection) -> dict[str, Any]:
    return runtime.switch_camera(selection.source)

@app.get("/api/events")
def events() -> list[dict[str, Any]]:
    return runtime.get_events()

@app.get("/api/events.ndjson")
def events_ndjson() -> StreamingResponse:
    def stream_events():
        last_payload = ""
        while True:
            payload = json.dumps(runtime.get_events(), ensure_ascii=True)
            if payload != last_payload:
                last_payload = payload
                yield payload + "\n"
            time.sleep(1)
    return StreamingResponse(stream_events(), media_type="application/x-ndjson")

@app.get("/video_feed")
@app.get("/api/video_feed")
def video_feed() -> StreamingResponse:
    return StreamingResponse(
        runtime.frame_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)