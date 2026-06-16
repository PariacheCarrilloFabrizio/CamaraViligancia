from roboflow import Roboflow
from ultralytics import YOLO

rf = Roboflow(api_key="wsqnwf87VGownYBh8UUI")
project = rf.workspace("pedros-workspace-ohzku").project("smoking-irsld")
version = project.version(1)

print("Descargando imágenes...")
dataset = version.download("yolov8")
print(f"¡Descarga completada en la carpeta: {dataset.location}!")

# --- 2. ENTRENAMIENTO DE LA INTELIGENCIA ARTIFICIAL ---
print("Iniciando el entrenamiento de YOLOv8...")

# Cargamos el cerebro en blanco (el modelo más rápido y ligero)
model = YOLO('yolov8n.pt')

# Arrancamos el aprendizaje
# OJO: Si tienes una tarjeta de video Nvidia, cambia device='cpu' por device=0
results = model.train(
    data=f"{dataset.location}/data.yaml", 
    epochs=50,       # Cantidad de veces que la IA estudiará las fotos
    imgsz=640,       # Resolución de las imágenes
    batch=16,        # Cuántas imágenes procesa al mismo tiempo
    device='0'     # Usa el procesador por defecto
)

print("¡Entrenamiento finalizado con éxito!")