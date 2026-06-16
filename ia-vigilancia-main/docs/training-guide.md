# Guia paso a paso para entrenar modelos

Esta guia esta pensada para integrantes del equipo que no necesariamente programan. La meta es que puedan preparar datos, entrenar un modelo y entregar un archivo `best.pt` usable en el sistema.

## 1. Primero: fotos o videos

Depende del tipo de evento.

Usa fotos cuando el evento sea un objeto visible:

- cuchillo
- arma
- fuego
- humo
- mochila abandonada
- extintor
- casco, mascara o pasamontanas

Usa videos cuando el evento sea una accion:

- pelea
- agresion
- persecucion
- persona cayendo
- persona corriendo
- escalamiento
- vandalismo
- robo

Para peleas, lo mejor es video, porque una pelea no se entiende bien en una sola foto. El modelo necesita ver movimiento, distancia entre personas y continuidad en el tiempo. Si solo se usan fotos, puede confundir abrazos, personas conversando cerca o deportes con peleas.

## 2. Que entrenaremos primero

No intenten entrenar toda la lista del proyecto al mismo tiempo. Para esta etapa, enfoquense en pocos eventos:

- `fight`
- `no_fight`
- `fallen_person`
- `fire`
- `smoke`
- `knife`

Los eventos como `intrusion`, `loitering`, `blocked_exit` o `suspicious_package` se resuelven mejor con reglas, zonas, tracking y tiempo. No son solamente "detectar una cosa".

## 3. Preparar el entorno

Cada persona debe tener el proyecto instalado.

Desde la raiz del repo:

```powershell
cd C:\Users\Unknown\Documents\GitHub\ia-vigilancia
.\venv\Scripts\activate
pip install -r requirements.txt
```

Verifica que YOLO funcione:

```powershell
yolo checks
```

Si se usara GPU NVIDIA:

```powershell
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

Si devuelve `False`, igual se puede entrenar en CPU, pero sera mucho mas lento.

## 4. Entrenar objetos con fotos

Este camino sirve para `knife`, `fire`, `smoke`, `gun`, `mask`, etc.

### 4.1 Recolectar imagenes

Cantidad recomendada para empezar:

- minimo: 100 imagenes por clase
- mejor: 300 a 1000 imagenes por clase
- incluir ejemplos negativos sin el objeto

Ejemplo para `knife`, `fire`, `smoke`:

```text
datasets/security-objects/
  raw/
    knife/
    fire/
    smoke/
    negatives/
```

Las imagenes deben variar:

- buena luz y poca luz
- cerca y lejos
- distintos angulos
- distintos fondos
- imagenes de campus o ambientes parecidos

### 4.2 Etiquetar imagenes

Herramientas recomendadas:

- Roboflow
- CVAT
- Label Studio

Para cada imagen deben dibujar una caja alrededor del objeto.

Ejemplo:

- si hay un cuchillo, dibujar caja solo alrededor del cuchillo
- si hay humo, dibujar caja alrededor de la zona visible de humo
- si hay fuego, dibujar caja alrededor de la llama

No etiqueten objetos dudosos. Si no se ve claro, es mejor no usar esa imagen.

### 4.3 Exportar en formato YOLO

Al exportar, elijan formato:

```text
YOLOv8 / YOLO format
```

La carpeta final deberia quedar asi:

```text
datasets/security-objects/
  images/
    train/
    val/
  labels/
    train/
    val/
  data.yaml
```

El archivo `data.yaml` debe parecerse a esto:

```yaml
path: datasets/security-objects
train: images/train
val: images/val
names:
  0: knife
  1: fire
  2: smoke
```

### 4.4 Entrenar modelo de objetos

Con GPU:

```powershell
yolo detect train model=yolov8n.pt data=datasets/security-objects/data.yaml imgsz=640 epochs=80 batch=8 device=0
```

Con CPU:

```powershell
yolo detect train model=yolov8n.pt data=datasets/security-objects/data.yaml imgsz=512 epochs=50 batch=2 device=cpu
```

Si sale error por memoria:

```powershell
yolo detect train model=yolov8n.pt data=datasets/security-objects/data.yaml imgsz=512 epochs=80 batch=4 device=0
```

### 4.5 Resultado

Al terminar, YOLO genera una carpeta parecida a:

```text
runs/detect/train/weights/
  best.pt
  last.pt
```

El archivo importante es:

```text
best.pt
```

Ese archivo se copia a:

```text
models/security-objects/best.pt
```

## 5. Entrenar peleas con videos

Para `fight`, lo ideal es usar videos. Hay dos caminos:

- camino simple: convertir videos en frames y entrenar YOLO con cajas
- camino correcto a futuro: entrenar un modelo de accion con clips

Para este proyecto, empezaremos con el camino simple porque es mas facil para el equipo.

## 6. Peleas camino simple: video a frames

### 6.1 Recolectar videos

Necesitan dos carpetas:

```text
datasets/fight-videos/
  fight/
  no_fight/
```

Videos `fight`:

- peleas simuladas
- forcejeos
- empujones agresivos
- golpes o patadas simuladas

Videos `no_fight`:

- personas conversando cerca
- personas abrazandose
- juegos
- deportes
- personas caminando rapido
- grupos sin violencia

Esto es muy importante. Si no hay buenos `no_fight`, el modelo va a marcar cualquier movimiento como pelea.

### 6.2 Reglas de grabacion

Para grabar ejemplos propios:

- usar la camara en un angulo parecido al prototipo
- grabar de 5 a 15 segundos por ejemplo
- no grabar rostros sensibles si no es necesario
- evitar videos reales violentos sin permisos
- preferir escenas simuladas y controladas
- nombrar archivos claramente

Ejemplos:

```text
fight_001.mp4
fight_002.mp4
no_fight_hug_001.mp4
no_fight_talking_001.mp4
```

### 6.3 Extraer frames del video

Crear carpeta:

```text
datasets/fight-frames/
  raw/
    fight/
    no_fight/
```

Extraer frames con Python/OpenCV o con una herramienta visual. Recomendacion: 2 a 5 frames por segundo, no todos los frames.

Comando sugerido si se agrega un script mas adelante:

```powershell
python tools\extract_frames.py --input datasets\fight-videos --output datasets\fight-frames\raw --fps 3
```

Si todavia no existe ese script, una persona del equipo debe convertir los videos con una herramienta como VLC, FFmpeg o Roboflow.

### 6.4 Etiquetar frames

Para YOLO, deben etiquetar cajas.

Hay dos formas:

Opcion A: caja alrededor de la pelea completa.

- clase: `violence`
- caja: zona donde ocurre la pelea

Opcion B: caja alrededor de las personas involucradas.

- clase: `violence`
- caja: personas que participan en la pelea

Para `no_fight`, hay dos opciones:

- no poner ninguna caja
- o entrenar tambien clase `non_violence`

Para este proyecto, si usan el modelo actual de pelea, conviene mantener:

```text
0: non_violence
1: violence
```

### 6.5 Estructura final

```text
datasets/fight-yolo/
  images/
    train/
    val/
  labels/
    train/
    val/
  data.yaml
```

Ejemplo de `data.yaml`:

```yaml
path: datasets/fight-yolo
train: images/train
val: images/val
names:
  0: non_violence
  1: violence
```

### 6.6 Entrenar modelo de pelea YOLO

Con GPU:

```powershell
yolo detect train model=yolov8n.pt data=datasets/fight-yolo/data.yaml imgsz=640 epochs=80 batch=8 device=0
```

Con CPU:

```powershell
yolo detect train model=yolov8n.pt data=datasets/fight-yolo/data.yaml imgsz=512 epochs=40 batch=2 device=cpu
```

### 6.7 Usar el modelo entrenado

Cuando termine, copiar:

```text
runs/detect/train/weights/best.pt
```

a:

```text
models/fight/best.pt
```

Luego en `.env`:

```text
FIGHT_MODEL_PATH=models/fight/best.pt
FIGHT_CONFIDENCE_THRESHOLD=0.45
```

## 7. Peleas camino correcto a futuro: clips

El camino mas correcto para pelea es entrenar con clips completos, no solo frames.

La idea:

- cada muestra es un video corto de 2 a 5 segundos
- el clip completo tiene etiqueta `fight` o `no_fight`
- el modelo aprende movimiento, no solo apariencia

Estructura:

```text
datasets/fight-clips/
  train/
    fight/
    no_fight/
  val/
    fight/
    no_fight/
```

Este camino requiere un modelo de accion, como SlowFast, X3D, Video Swin o un clasificador temporal. Es mas fuerte, pero tambien mas dificil de implementar. Por eso queda como fase siguiente.

## 8. Como saber si el modelo sirve

No basta con entrenar y ver que "funciona una vez".

Prueben con:

- videos nuevos que el modelo no vio
- camara real del proyecto
- personas sentadas
- personas abrazandose
- personas corriendo
- personas moviendose cerca sin pelear
- escenas con poca luz

Comando de validacion:

```powershell
yolo detect val model=models/fight/best.pt data=datasets/fight-yolo/data.yaml device=0
```

Comando para probar con video:

```powershell
yolo detect predict model=models/fight/best.pt source=videos/test_fight/pelea_01.mp4 conf=0.45 device=0
```

Comando para probar con webcam:

```powershell
yolo detect predict model=models/fight/best.pt source=0 conf=0.45 device=0
```

Si no tienen GPU:

```powershell
yolo detect predict model=models/fight/best.pt source=0 conf=0.45 device=cpu
```

## 9. Que debe entregar cada equipo

Para cada modelo entrenado, entregar:

- archivo `best.pt`
- archivo `data.yaml`
- lista de clases
- cantidad de imagenes o clips usados
- ejemplos de falsos positivos
- ejemplos de falsos negativos
- capturas de resultados
- recomendacion de confianza minima

Ejemplo:

```text
Modelo: fight
Clases: non_violence, violence
Datos: 420 imagenes train, 110 imagenes val
Confianza recomendada: 0.45
Problema detectado: confunde deportes con pelea
Archivo final: models/fight/best.pt
```

## 10. Reglas para no contaminar el dataset

Eviten:

- usar la misma escena en train y val
- etiquetar imagenes dudosas
- entrenar solo con videos de internet
- entrenar solo con peleas y casi nada de `no_fight`
- usar imagenes muy borrosas sin sentido
- mezclar nombres de clases, por ejemplo `fight`, `violence`, `pelea` para lo mismo

Mantengan nombres estables:

```text
fight / violence
no_fight / non_violence
fallen_person
fire
smoke
knife
```

## 11. Recomendacion final

Para la exposicion, expliquen esto:

- objetos se entrenan con fotos etiquetadas con cajas
- acciones se entrenan mejor con videos o clips
- para esta fase usamos YOLO como avance rapido
- para una version robusta se debe pasar a modelos temporales y tracking
- el modelo siempre debe probarse con la camara real del campus
