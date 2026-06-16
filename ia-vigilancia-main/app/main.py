from __future__ import annotations

from pathlib import Path

import cv2

from alerts import EvidenceManager
from capture import choose_video_source, open_camera
from config import Settings
from detector import YOLODetector
from event_engine import EventEngine
from event_catalog import EVENT_DEFINITIONS


def main() -> None:
    settings = Settings.from_env()
    detector = YOLODetector(
        model_path=settings.model_path,
        confidence_threshold=settings.confidence_threshold,
        tracked_classes=settings.tracked_classes,
        fight_model_path=settings.fight_model_path,
        fight_confidence_threshold=settings.fight_confidence_threshold,
        inference_device=settings.inference_device,
        image_size=settings.inference_image_size,
    )
    event_engine = EventEngine(
        enabled_events=settings.enabled_events,
        fight_motion_threshold=settings.fight_motion_threshold,
        fight_frames_required=settings.fight_frames_required,
        crowd_person_threshold=settings.crowd_person_threshold,
    )
    evidence_manager = EvidenceManager(
        directory=Path(settings.evidence_dir),
        cooldown_seconds=settings.evidence_cooldown_seconds,
        enabled=settings.save_evidence,
    )
    selected_camera = choose_video_source(
        default_source=settings.camera_source,
        prompt_user=settings.prompt_camera_selection,
        scan_limit=settings.camera_scan_limit,
    )

    camera = open_camera(
        selected_camera.source,
        width=settings.camera_width,
        height=settings.camera_height,
        fps=settings.camera_fps,
    )

    print("Iniciando vigilancia inteligente...")
    print("Controles: enfoca la ventana de video y presiona 'q' o 'ESC' para salir.")
    print(
        f"Fuente: {selected_camera.label} | "
        f"Modelo: {settings.model_path} | "
        f"Modelo pelea: {settings.fight_model_path or 'desactivado'} | "
        f"Confianza minima: {settings.confidence_threshold:.2f} | "
        f"Clases: {settings.tracked_classes or 'todas'}"
    )
    print(f"Catalogo de eventos objetivo cargado: {len(EVENT_DEFINITIONS)} eventos.")
    print(f"Eventos activos en esta prueba: {', '.join(settings.enabled_events)}")

    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                print("No se pudo leer un frame de la camara. Finalizando.")
                break

            summary = detector.detect(frame)
            events = event_engine.analyze(frame, summary)

            overlay_frame = summary.annotated_frame
            for index, event in enumerate(events):
                y_position = 30 + index * 30
                cv2.putText(
                    overlay_frame,
                    f"[{event.priority.upper()}] {event.title}",
                    (10, y_position),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (0, 0, 255),
                    2,
                    cv2.LINE_AA,
                )

                saved_path = evidence_manager.save_event_evidence(frame, event)
                if saved_path is not None:
                    print(f"Evento detectado: {event.code} | {event.detail}")
                    print(f"Evidencia guardada en {saved_path}")

            cv2.imshow(settings.window_name, overlay_frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                print("Salida solicitada por teclado.")
                break

    except KeyboardInterrupt:
        print("Proceso detenido con Ctrl+C.")
    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("Recursos liberados correctamente.")


if __name__ == "__main__":
    main()
