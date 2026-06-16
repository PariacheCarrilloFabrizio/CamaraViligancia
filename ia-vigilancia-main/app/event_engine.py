from __future__ import annotations

from dataclasses import dataclass

import cv2

from detector import DetectionBox, DetectionSummary


@dataclass(frozen=True, slots=True)
class EventRecord:
    code: str
    title: str
    priority: str
    detail: str


class EventEngine:
    def __init__(
        self,
        enabled_events: list[str],
        fight_motion_threshold: float,
        fight_frames_required: int,
        crowd_person_threshold: int,
    ) -> None:
        self.enabled_events = set(enabled_events)
        self.fight_motion_threshold = fight_motion_threshold
        self.fight_frames_required = fight_frames_required
        self.crowd_person_threshold = crowd_person_threshold
        self.previous_gray: cv2.typing.MatLike | None = None
        self.fight_streak = 0

    def analyze(self, frame: cv2.typing.MatLike, summary: DetectionSummary) -> list[EventRecord]:
        events: list[EventRecord] = []
        people = [
            detection
            for detection in summary.detections
            if detection.model_source == "base" and detection.class_name == "person"
        ]

        if "crowd" in self.enabled_events and len(people) >= self.crowd_person_threshold:
            events.append(
                EventRecord(
                    code="crowd",
                    title="Aglomeracion detectada",
                    priority="baja",
                    detail=f"{len(people)} personas visibles en la escena",
                )
            )

        frame_height, frame_width = frame.shape[:2]

        if "fallen_person" in self.enabled_events:
            fallen_people = [person for person in people if self._looks_fallen(person, frame_width, frame_height)]
            if fallen_people:
                events.append(
                    EventRecord(
                        code="fallen_person",
                        title="Posible persona en el suelo",
                        priority="alta",
                        detail=f"{len(fallen_people)} region(es) con postura horizontal",
                    )
                )

        if "fight" in self.enabled_events:
            fight_event = self._detect_fight_model(summary)
            if fight_event is None and not summary.fight_model_enabled:
                fight_event = self._detect_possible_fight(frame, people)
            if fight_event is not None:
                events.append(fight_event)

        self.previous_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return events

    def _detect_fight_model(self, summary: DetectionSummary) -> EventRecord | None:
        fight_detections = [
            detection
            for detection in summary.detections
            if detection.model_source == "fight" and self._is_positive_fight_label(detection.class_name)
        ]

        if not fight_detections:
            return None

        best_detection = max(fight_detections, key=lambda detection: detection.confidence)
        return EventRecord(
            code="fight",
            title="Pelea detectada",
            priority="alta",
            detail=(
                f"Modelo entrenado detecto {best_detection.class_name} "
                f"con confianza {best_detection.confidence:.2f}"
            ),
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

    def _looks_fallen(self, person: DetectionBox, frame_width: int, frame_height: int) -> bool:
        if person.area < 18_000:
            return False
        if person.height == 0:
            return False

        aspect_ratio = person.width / person.height
        if aspect_ratio < 1.35:
            return False

        center_x, center_y = person.center
        bottom_ratio = person.y2 / max(frame_height, 1)
        center_ratio = center_y / max(frame_height, 1)
        width_ratio = person.width / max(frame_width, 1)

        if bottom_ratio < 0.72:
            return False
        if center_ratio < 0.62:
            return False
        if width_ratio < 0.25:
            return False

        return True

    def _detect_possible_fight(
        self,
        frame: cv2.typing.MatLike,
        people: list[DetectionBox],
    ) -> EventRecord | None:
        if len(people) < 2:
            self.fight_streak = 0
            return None

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.previous_gray is None:
            return None

        close_pairs = self._count_close_pairs(people)
        motion_score = self._motion_score(gray_frame, people)

        if close_pairs > 0 and motion_score >= self.fight_motion_threshold:
            self.fight_streak += 1
        else:
            self.fight_streak = 0

        if self.fight_streak >= self.fight_frames_required:
            return EventRecord(
                code="fight",
                title="Posible pelea o forcejeo",
                priority="alta",
                detail=(
                    f"Movimiento brusco sostenido con {close_pairs} pareja(s) cercana(s). "
                    f"Puntaje de movimiento: {motion_score:.1f}"
                ),
            )

        return None

    def _count_close_pairs(self, people: list[DetectionBox]) -> int:
        close_pairs = 0
        for index, left_person in enumerate(people):
            left_center_x, left_center_y = left_person.center
            for right_person in people[index + 1 :]:
                right_center_x, right_center_y = right_person.center
                distance_x = abs(left_center_x - right_center_x)
                distance_y = abs(left_center_y - right_center_y)
                width_reference = max(left_person.width, right_person.width)
                height_reference = max(left_person.height, right_person.height)

                if distance_x <= width_reference * 0.9 and distance_y <= height_reference * 0.8:
                    close_pairs += 1
        return close_pairs

    def _motion_score(self, gray_frame: cv2.typing.MatLike, people: list[DetectionBox]) -> float:
        if self.previous_gray is None:
            return 0.0

        frame_delta = cv2.absdiff(gray_frame, self.previous_gray)
        total_motion = 0.0

        for person in people:
            x1 = max(0, person.x1)
            y1 = max(0, person.y1)
            x2 = min(frame_delta.shape[1], person.x2)
            y2 = min(frame_delta.shape[0], person.y2)
            if x2 <= x1 or y2 <= y1:
                continue

            region = frame_delta[y1:y2, x1:x2]
            if region.size == 0:
                continue

            total_motion += float(region.mean())

        return total_motion
