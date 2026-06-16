from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import cv2
import torch

os.environ.setdefault("MPLCONFIGDIR", str(Path(".cache/matplotlib").resolve()))

from ultralytics import YOLO


@dataclass(slots=True)
class DetectionBox:
    model_source: str
    class_id: int
    class_name: str
    confidence: float
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        return max(0, self.x2 - self.x1)

    @property
    def height(self) -> int:
        return max(0, self.y2 - self.y1)

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def center(self) -> tuple[int, int]:
        return (self.x1 + self.width // 2, self.y1 + self.height // 2)


@dataclass(slots=True)
class DetectionSummary:
    annotated_frame: cv2.typing.MatLike
    labels: list[str]
    detection_count: int
    detections: list[DetectionBox]
    fight_model_enabled: bool = False


class YOLODetector:
    def __init__(
        self,
        model_path: str,
        confidence_threshold: float,
        tracked_classes: list[int] | None,
        fight_model_path: str | None = None,
        fight_confidence_threshold: float | None = None,
        inference_device: str = "auto",
        image_size: int = 640,
    ) -> None:
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.tracked_classes = tracked_classes
        self.class_names = self.model.names
        self.fight_model = None
        self.fight_model_path = fight_model_path
        self.fight_confidence_threshold = fight_confidence_threshold or confidence_threshold
        self.device = self._resolve_device(inference_device)
        self.image_size = image_size
        self.use_half_precision = self.device != "cpu"

        if fight_model_path:
            path = Path(fight_model_path)
            if path.exists():
                self.fight_model = YOLO(str(path))
            else:
                print(f"Aviso: no se encontro el modelo de peleas en {fight_model_path}. Se usara solo YOLO base.")

    def detect(self, frame: cv2.typing.MatLike) -> DetectionSummary:
        results = self.model.predict(
            source=frame,
            conf=self.confidence_threshold,
            classes=self.tracked_classes,
            device=self.device,
            imgsz=self.image_size,
            half=self.use_half_precision,
            verbose=False,
        )
        result = results[0]
        labels: list[str] = []
        detections: list[DetectionBox] = []
        fight_detections: list[DetectionBox] = []

        if result.boxes is not None:
            for box in result.boxes:
                detections.append(self._box_to_detection(box, self.class_names, "base"))

        labels.extend(f"{detection.class_name} ({detection.confidence:.2f})" for detection in detections)
        annotated_frame = frame.copy()

        if self.fight_model is not None:
            fight_results = self.fight_model.predict(
                source=frame,
                conf=self.fight_confidence_threshold,
                device=self.device,
                imgsz=self.image_size,
                half=self.use_half_precision,
                verbose=False,
            )
            fight_result = fight_results[0]

            if fight_result.boxes is not None:
                for box in fight_result.boxes:
                    detection = self._box_to_detection(box, self.fight_model.names, "fight")
                    fight_detections.append(detection)
                    detections.append(detection)

        positive_fight_detections = [
            detection for detection in fight_detections if self._is_positive_fight_label(detection.class_name)
        ]
        for detection in detections:
            if detection.model_source != "base":
                continue
            if any(self._overlaps(detection, fight_detection) for fight_detection in positive_fight_detections):
                continue
            self._draw_detection(
                annotated_frame,
                detection,
                label=f"{detection.class_name} {detection.confidence:.2f}",
                color=(255, 0, 0),
            )

        for detection in positive_fight_detections:
            labels.append(f"fight:{detection.class_name} ({detection.confidence:.2f})")
            self._draw_detection(
                annotated_frame,
                detection,
                label=f"{detection.class_name} {detection.confidence:.2f}",
                color=(255, 255, 0),
            )

        return DetectionSummary(
            annotated_frame=annotated_frame,
            labels=labels,
            detection_count=len(labels),
            detections=detections,
            fight_model_enabled=self.fight_model is not None,
        )

    def _box_to_detection(self, box, class_names, model_source: str) -> DetectionBox:
        class_id = int(box.cls.item())
        confidence = float(box.conf.item())
        class_name = class_names[class_id]
        x1, y1, x2, y2 = [int(value) for value in box.xyxy[0].tolist()]

        return DetectionBox(
            model_source=model_source,
            class_id=class_id,
            class_name=class_name,
            confidence=confidence,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
        )

    def _draw_detection(
        self,
        frame: cv2.typing.MatLike,
        detection: DetectionBox,
        label: str,
        color: tuple[int, int, int],
    ) -> None:
        cv2.rectangle(frame, (detection.x1, detection.y1), (detection.x2, detection.y2), color, 2)
        label_origin = (detection.x1, max(20, detection.y1 - 8))
        cv2.putText(
            frame,
            label,
            label_origin,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
            cv2.LINE_AA,
        )

    def _is_positive_fight_label(self, class_name: str) -> bool:
        normalized_name = class_name.lower().replace("_", " ").replace("-", " ")
        negative_terms = (
            "no fight",
            "non fight",
            "no violence",
            "non violence",
            "no violent",
            "non violent",
            "normal",
            "no pelea",
            "sin pelea",
            "no violencia",
            "sin violencia",
        )

        if any(term in normalized_name for term in negative_terms):
            return False

        positive_terms = ("fight", "violence", "violent", "pelea", "agresion", "aggression")
        return any(term in normalized_name for term in positive_terms)

    def _overlaps(self, left: DetectionBox, right: DetectionBox) -> bool:
        intersection_x1 = max(left.x1, right.x1)
        intersection_y1 = max(left.y1, right.y1)
        intersection_x2 = min(left.x2, right.x2)
        intersection_y2 = min(left.y2, right.y2)
        intersection_width = max(0, intersection_x2 - intersection_x1)
        intersection_height = max(0, intersection_y2 - intersection_y1)
        intersection_area = intersection_width * intersection_height
        smaller_area = max(1, min(left.area, right.area))

        return intersection_area / smaller_area >= 0.55

    def _resolve_device(self, requested_device: str) -> str:
        normalized_device = requested_device.strip().lower()
        if normalized_device == "auto":
            return "0" if torch.cuda.is_available() else "cpu"
        return requested_device
