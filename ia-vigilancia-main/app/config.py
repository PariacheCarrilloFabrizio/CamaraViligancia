from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _parse_int_list(value: str) -> list[int]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    return [int(item) for item in items]


@dataclass(slots=True)
class Settings:
    camera_source: str
    prompt_camera_selection: bool
    camera_scan_limit: int
    camera_width: int
    camera_height: int
    camera_fps: int
    model_path: str
    confidence_threshold: float
    tracked_classes: list[int] | None
    fight_model_path: str | None
    fight_confidence_threshold: float
    inference_device: str
    inference_image_size: int
    detection_interval: int
    stream_jpeg_quality: int
    enabled_events: list[str]
    fight_motion_threshold: float
    fight_frames_required: int
    crowd_person_threshold: int
    window_name: str
    save_evidence: bool
    evidence_dir: str
    evidence_cooldown_seconds: int

    @classmethod
    def from_env(cls) -> "Settings":
        raw_classes = os.getenv("YOLO_CLASSES", "0").strip()
        tracked_classes = _parse_int_list(raw_classes) if raw_classes else None
        raw_events = os.getenv("ENABLED_EVENTS", "fight,crowd,fallen_person").strip()
        enabled_events = [item.strip() for item in raw_events.split(",") if item.strip()]
        fight_model_path = os.getenv("FIGHT_MODEL_PATH", "models/fight/best.pt").strip()

        return cls(
            camera_source=os.getenv("CAMERA_SOURCE", "0"),
            prompt_camera_selection=os.getenv("PROMPT_CAMERA_SELECTION", "true").lower() == "true",
            camera_scan_limit=int(os.getenv("CAMERA_SCAN_LIMIT", "5")),
            camera_width=int(os.getenv("CAMERA_WIDTH", "960")),
            camera_height=int(os.getenv("CAMERA_HEIGHT", "540")),
            camera_fps=int(os.getenv("CAMERA_FPS", "30")),
            model_path=os.getenv("MODEL_PATH", "yolov8n.pt"),
            confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.55")),
            tracked_classes=tracked_classes,
            fight_model_path=fight_model_path or None,
            fight_confidence_threshold=float(os.getenv("FIGHT_CONFIDENCE_THRESHOLD", "0.45")),
            inference_device=os.getenv("INFERENCE_DEVICE", "auto"),
            
            # OPTIMIZACIÓN 1: Reducimos la resolución de análisis de 640 a 416 (Menos carga a la CPU)
            inference_image_size=int(os.getenv("INFERENCE_IMAGE_SIZE", "416")),
            
            # OPTIMIZACIÓN 2: Cambiamos el intervalo de 2 a 6. 
            # La IA procesará 1 de cada 6 cuadros, liberando mas del 80% del procesador.
            detection_interval=max(1, int(os.getenv("DETECTION_INTERVAL", "6"))),
            
            stream_jpeg_quality=int(os.getenv("STREAM_JPEG_QUALITY", "75")),
            enabled_events=enabled_events,
            fight_motion_threshold=float(os.getenv("FIGHT_MOTION_THRESHOLD", "18.0")),
            fight_frames_required=int(os.getenv("FIGHT_FRAMES_REQUIRED", "6")),
            crowd_person_threshold=int(os.getenv("CROWD_PERSON_THRESHOLD", "6")),
            window_name=os.getenv("WINDOW_NAME", "IA Vigilancia - Deteccion"),
            save_evidence=os.getenv("SAVE_EVIDENCE", "true").lower() == "true",
            evidence_dir=os.getenv("EVIDENCE_DIR", "evidence"),
            evidence_cooldown_seconds=int(os.getenv("EVIDENCE_COOLDOWN_SECONDS", "10")),
        )