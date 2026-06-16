# IA Vigilancia Dashboard

Dashboard inicial en Next.js y Tailwind para el prototipo de videovigilancia inteligente.

## Ejecutar con Bun

Desde esta carpeta:

```powershell
bun install
bun run dev
```

Luego abre:

```text
http://localhost:3000
```

## Nota

El dashboard espera que la API de Python este corriendo en:

```text
http://localhost:8000
```

Si necesitas cambiar esa URL, crea `dashboard/.env.local` con:

```text
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Comando recomendado para levantar la API desde la raiz del repo:

```powershell
uvicorn server:app --app-dir app --reload --host 127.0.0.1 --port 8000
```
