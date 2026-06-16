from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import cv2

from event_engine import EventRecord


@dataclass(slots=True)
class EvidenceManager:
    directory: Path
    cooldown_seconds: int
    enabled: bool = True
    _last_saved_at: dict[str, datetime] | None = None

    def __post_init__(self) -> None:
        if self.enabled:
            self.directory.mkdir(parents=True, exist_ok=True)
        self._last_saved_at = {}

    def save_event_evidence(self, frame: cv2.typing.MatLike, event: EventRecord) -> Path | None:
        if not self.enabled:
            return None

        now = datetime.now()
        last_saved_at = self._last_saved_at.get(event.code)
        if last_saved_at is not None:
            elapsed = now - last_saved_at
            if elapsed < timedelta(seconds=self.cooldown_seconds):
                return None

        event_directory = self.directory / event.code
        event_directory.mkdir(parents=True, exist_ok=True)
        filename = f"{event.code}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
        output_path = event_directory / filename
        cv2.imwrite(str(output_path), frame)
        self._last_saved_at[event.code] = now
        return output_path
