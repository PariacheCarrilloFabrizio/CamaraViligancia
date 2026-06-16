from dataclasses import dataclass
import cv2
import numpy as np
import time

@dataclass
class Camera:
    source: str
    label: str

def list_available_cameras(limit: int = 5) -> list[Camera]:
    cameras = []
    for i in range(limit):
        # Intentamos con MSMF primero (Mejor compatibilidad en Windows modernos)
        cap = cv2.VideoCapture(i, cv2.CAP_MSMF)
        if not cap.isOpened():
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW) # Respaldo 1
        if not cap.isOpened():
            cap = cv2.VideoCapture(i) # Respaldo 2

        if cap.isOpened():
            # Leer un frame para comprobar que sirve
            ok, frame = cap.read()
            if ok and frame is not None:
                # Si el promedio de píxeles es mayor a 1, no es una pantalla totalmente negra
                if np.mean(frame) > 1.0:
                    cameras.append(Camera(source=str(i), label=f"Cámara {i}"))
            cap.release()
    return cameras

def open_camera(source: str, width: int, height: int, fps: int) -> cv2.VideoCapture:
    if source.isdigit():
        index = int(source)
        # Lista de motores a probar en orden de fiabilidad para Windows
        backends = [cv2.CAP_MSMF, cv2.CAP_DSHOW, cv2.CAP_ANY]
        
        for backend in backends:
            cap = cv2.VideoCapture(index, backend)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                cap.set(cv2.CAP_PROP_FPS, fps)
                
                # Calentamiento: Leer 5 frames para descartar pantallas negras iniciales
                for _ in range(5):
                    ok, frame = cap.read()
                    if ok and frame is not None and np.mean(frame) > 1.0:
                        return cap # ¡Encontramos video real!
                
                # Si llegó aquí, dio pantalla negra. Liberar y probar el siguiente motor.
                cap.release()
                
        # Si el índice solicitado falló por completo, forzar búsqueda de cualquier cámara activa
        print(f"La cámara {source} no responde o envía pantalla negra. Buscando alternativas...")
        for i in range(5):
            if i != index:
                cap = cv2.VideoCapture(i, cv2.CAP_MSMF)
                if cap.isOpened():
                    for _ in range(5):
                        ok, frame = cap.read()
                        if ok and frame is not None and np.mean(frame) > 1.0:
                            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                            return cap
                    cap.release()
    else:
        # Lógica para cámaras IP (RTSP/HTTP) de la UTP o externas
        cap = cv2.VideoCapture(source)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            return cap

    # Retorno de emergencia absoluto si todo falla
    return cv2.VideoCapture(0)