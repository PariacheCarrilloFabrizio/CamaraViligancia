# IA Vigilancia

Prototipo de videovigilancia inteligente para un entorno universitario.

El objetivo del proyecto es analizar video en tiempo real mediante Inteligencia Artificial para detectar eventos de riesgo, guardar evidencia y preparar alertas para el area encargada de seguridad o SAE.

Este repositorio es un avance funcional. Aun no representa un sistema final de seguridad, pero ya integra camara, deteccion con modelos YOLO, dashboard web y una primera estructura para eventos como peleas, aglomeraciones y persona caida.

## Idea del proyecto

El sistema busca transformar una camara tradicional en una fuente de analisis inteligente.

Flujo general:

```text
Camara -> Backend Python -> Modelo IA -> Eventos -> Evidencia -> Dashboard web
```

En esta etapa se trabaja con:

- webcam de laptop
- Camo con iPhone
- camaras virtuales
- a futuro, camaras IP/RTSP de videovigilancia

## Estado actual

Actualmente el sistema puede:

- abrir una fuente de video
- usar GPU NVIDIA si esta disponible
- caer automaticamente a CPU si no hay GPU
- detectar personas con YOLO
- cargar un modelo local de peleas en `models/fight/best.pt`
- guardar evidencia por evento
- exponer una API con FastAPI
- mostrar la camara en un dashboard Next.js
- cambiar la camara desde el frontend

Eventos activos por defecto:

- `fight`
- `crowd`
- `fallen_person`

Importante: el modelo de pelea y las reglas actuales son un avance de prototipo. Para una version robusta se necesitan mas datos, pruebas y modelos temporales.

## Estructura del proyecto

```text
ia-vigilancia/
  app/
    alerts.py
    capture.py
    config.py
    detector.py
    event_catalog.py
    event_engine.py
    main.py
    server.py
  dashboard/
    app/
    package.json
  docs/
    training-guide.md
  models/
    README.md
  .env.example
  .gitignore
  environment.yml
  requirements.txt
```

## Librerias principales

Python:

- `opencv-python`: abre camaras, lee frames, dibuja cajas y codifica el stream de video.
- `ultralytics`: permite usar modelos YOLO para deteccion de objetos y el modelo `best.pt`.
- `torch`: ejecuta los modelos de IA en CPU o GPU NVIDIA.
- `fastapi`: crea la API que conecta Python con el dashboard web.
- `uvicorn`: servidor que levanta la API FastAPI.
- `python-dotenv`: lee configuracion desde `.env`.
- `dill`: requerido por algunos modelos YOLO descargados o entrenados para cargarse correctamente.

Frontend:

- `Next.js`: framework web para construir el dashboard.
- `React`: base de componentes de la interfaz.
- `Tailwind CSS`: estilos rapidos y consistentes para el dashboard.
- `Bun`: gestor y runtime usado para instalar dependencias y ejecutar el frontend.

## Configuracion del entorno

Desde la raiz del proyecto:

```powershell
cd C:\Users\Unknown\Documents\GitHub\ia-vigilancia
.\venv\Scripts\activate
pip install -r requirements.txt
```

Si se usa Anaconda:

```powershell
conda create -n ia-vigilancia python=3.11 -y
conda activate ia-vigilancia
pip install -r requirements.txt
```

Crear `.env` a partir de `.env.example`:

```powershell
Copy-Item .env.example .env
```

## Configuracion importante

El archivo `.env` controla camara, modelos y rendimiento.

Valores principales:

```text
CAMERA_SOURCE=0
CAMERA_WIDTH=960
CAMERA_HEIGHT=540
CAMERA_FPS=30
MODEL_PATH=yolov8n.pt
YOLO_CLASSES=0
FIGHT_MODEL_PATH=models/fight/best.pt
INFERENCE_DEVICE=auto
INFERENCE_IMAGE_SIZE=640
DETECTION_INTERVAL=2
ENABLED_EVENTS=fight,crowd,fallen_person
```

Sobre `INFERENCE_DEVICE`:

- `auto`: usa GPU si PyTorch detecta CUDA, si no usa CPU.
- `0`: fuerza la primera GPU NVIDIA.
- `cpu`: fuerza CPU.

Recomendacion para el equipo:

```text
INFERENCE_DEVICE=auto
```

Asi el proyecto se adapta a cada laptop.

## Verificar GPU

Para saber si PyTorch esta usando la GPU:

```powershell
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

Si devuelve `True`, el sistema puede usar la GPU.

Si devuelve `False`, el sistema sigue funcionando en CPU, pero con menos FPS.

## Ejecutar el sistema completo

Forma rapida:

```powershell
.\scripts\dev-web.ps1
```

Esto abre dos terminales:

- una para la API Python
- otra para el dashboard Next.js

Luego abrir:

```text
http://localhost:3000
```

Forma manual:

Terminal 1: backend Python con camara e IA.

```powershell
cd C:\Users\Unknown\Documents\GitHub\ia-vigilancia
.\venv\Scripts\python.exe -m uvicorn server:app --app-dir app --host 127.0.0.1 --port 8000
```

Terminal 2: dashboard web.

```powershell
cd C:\Users\Unknown\Documents\GitHub\ia-vigilancia\dashboard
bun install
bun run dev
```

Abrir:

```text
http://localhost:3000
```

API:

```text
http://localhost:8000/api/health
http://localhost:8000/api/cameras
http://localhost:8000/video_feed
```

## Ejecutar sin web

Para desarrollo rapido, sin Next.js ni navegador:

```powershell
.\scripts\dev-camera.ps1
```

Esto abre la camara en una ventana de OpenCV.

Controles:

- `q`: salir
- `ESC`: salir
- `Ctrl+C`: detener desde terminal

## Selector de camara

El dashboard tiene un selector de camaras.

Desde la web se puede:

- escanear camaras locales
- seleccionar una camara detectada
- escribir manualmente un indice, por ejemplo `0`, `1` o `2`
- escribir una URL RTSP/HTTP para camaras IP futuras

Para Camo:

1. Abrir Camo en el telefono.
2. Abrir Camo Studio en la laptop.
3. Confirmar que se ve la imagen en Camo Studio.
4. Ejecutar backend y dashboard.
5. En el dashboard, presionar `Escanear`.
6. Probar camaras `0`, `1`, `2` hasta encontrar Camo.

## Rendimiento y FPS

Configuracion recomendada:

```text
CAMERA_WIDTH=960
CAMERA_HEIGHT=540
CAMERA_FPS=30
INFERENCE_DEVICE=auto
INFERENCE_IMAGE_SIZE=640
DETECTION_INTERVAL=2
STREAM_JPEG_QUALITY=75
```

Si va lento:

```text
DETECTION_INTERVAL=3
INFERENCE_IMAGE_SIZE=512
CAMERA_WIDTH=640
CAMERA_HEIGHT=360
```

`DETECTION_INTERVAL=2` significa que el sistema no ejecuta IA en todos los frames, sino cada 2 frames. Esto mejora FPS y reduce carga.

La web mantiene la ultima imagen anotada entre detecciones para evitar que las cajas parpadeen. Si quieres maxima precision visual frame por frame, usa:

```text
DETECTION_INTERVAL=1
```

Si quieres mas FPS, usa `2` o `3`.

## Modelos

El modelo base:

```text
yolov8n.pt
```

Detecta objetos generales. Por defecto se usa solo la clase `person` con:

```text
YOLO_CLASSES=0
```

El modelo de pelea:

```text
models/fight/best.pt
```

Si detecta `violence`, el sistema crea un evento `fight`.

Si detecta `non_violence`, no genera alerta.

## Entrenamiento

La guia detallada esta en:

```text
docs/training-guide.md
```

Resumen:

- objetos como cuchillo, humo o fuego se entrenan con fotos etiquetadas con cajas
- acciones como pelea o agresion se entrenan mejor con videos
- para esta fase se puede convertir video a frames y entrenar YOLO
- a futuro, lo ideal para acciones es usar modelos temporales con clips

## Que no se sube a Git

El `.gitignore` evita subir archivos pesados o generados:

- `venv/`
- `dashboard/node_modules/`
- `dashboard/.next/`
- `evidence/`
- `runs/`
- `videos/`
- `test_outputs/`
- `*.pt`
- `*.onnx`
- `*.engine`

Esto no impide ejecutar el proyecto. Las dependencias se reinstalan con `pip install -r requirements.txt` y `bun install`.

Los modelos `.pt` no se suben por Git normal porque pueden pesar mucho. Si el equipo necesita compartir modelos, usar una de estas opciones:

- Google Drive
- OneDrive
- Hugging Face
- Git LFS

## Limitaciones actuales

Este es un prototipo, no un sistema final.

Limitaciones:

- la deteccion de peleas depende de la calidad del modelo `best.pt`
- puede haber falsos positivos
- `fallen_person` todavia requiere mejor modelo o pose estimation
- no hay autenticacion en el dashboard
- no se guardan clips de video, solo evidencia basica
- no hay base de datos historica todavia

## Siguientes pasos

Mejoras recomendadas:

- guardar clips antes y despues de cada evento
- agregar tracking de personas
- entrenar mejor el modelo de pelea con datos propios
- agregar modelos de fuego, humo y cuchillo
- registrar eventos en base de datos
- enviar alertas a SAE
- agregar ubicacion real por camara

## Para exposicion

Mensaje clave:

El proyecto demuestra que una camara comun puede conectarse a un sistema de IA que analiza video en tiempo real, detecta eventos relevantes y los muestra en un dashboard. La version actual es un avance funcional orientado a validar la arquitectura antes de escalar a camaras profesionales y modelos mas especializados.
