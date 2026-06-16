from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EventDefinition:
    code: str
    title: str
    category: str
    priority: str
    detection_strategy: str


EVENT_DEFINITIONS: list[EventDefinition] = [
    EventDefinition("fight", "Pelea fisica o agresion", "Violencia y agresiones", "alta", "accion + contexto temporal"),
    EventDefinition("aggression", "Empujones, amenazas o persecucion agresiva", "Violencia y agresiones", "alta", "accion + reglas"),
    EventDefinition("gun", "Arma de fuego", "Armas y objetos peligrosos", "alta", "objeto"),
    EventDefinition("knife", "Cuchillo o punzocortante", "Armas y objetos peligrosos", "alta", "objeto"),
    EventDefinition("suspicious_package", "Mochila o paquete sospechoso abandonado", "Armas y objetos peligrosos", "media", "objeto + permanencia"),
    EventDefinition("fallen_person", "Persona inconsciente, desmayada o inmovil", "Emergencias medicas", "alta", "pose + contexto temporal"),
    EventDefinition("fire", "Incendio", "Emergencias medicas", "alta", "objeto / segmentacion"),
    EventDefinition("smoke", "Humo", "Emergencias medicas", "alta", "objeto / segmentacion"),
    EventDefinition("intrusion", "Ingreso a zona restringida", "Intrusion y accesos no autorizados", "alta", "objeto + zonas"),
    EventDefinition("climbing", "Escalamiento de rejas o muros", "Intrusion y accesos no autorizados", "alta", "accion"),
    EventDefinition("loitering", "Merodeo o permanencia sospechosa", "Conductas sospechosas", "media", "tracking + tiempo"),
    EventDefinition("face_hidden", "Rostro oculto en area sensible", "Conductas sospechosas", "media", "objeto + reglas"),
    EventDefinition("camera_tampering", "Manipulacion de camara", "Conductas sospechosas", "alta", "cambio de escena + objeto"),
    EventDefinition("vandalism", "Vandalismo o dano a mobiliario", "Vandalismo y danos", "media", "accion + objeto"),
    EventDefinition("theft", "Robo o retiro sospechoso de equipo", "Vandalismo y danos", "alta", "accion + tracking"),
    EventDefinition("crowd", "Congestion excesiva de personas", "Riesgos de seguridad general", "baja", "conteo"),
    EventDefinition("running", "Corrida o estampida", "Riesgos de seguridad general", "media", "tracking + velocidad"),
    EventDefinition("blocked_exit", "Salida de emergencia bloqueada", "Riesgos de seguridad general", "media", "objeto + zonas"),
]


DATASET_LABELS: list[str] = [
    "fight",
    "gun",
    "knife",
    "fire",
    "smoke",
    "fallen_person",
    "intrusion",
    "suspicious_package",
    "vandalism",
    "crowd",
    "running",
    "climbing",
    "theft",
    "aggression",
    "loitering",
]


def grouped_events() -> dict[str, list[EventDefinition]]:
    grouped: dict[str, list[EventDefinition]] = {}
    for event in EVENT_DEFINITIONS:
        grouped.setdefault(event.category, []).append(event)
    return grouped
