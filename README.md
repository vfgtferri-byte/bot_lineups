# Bot de Vessel Schedules para puertos de África

Bot en Python (sin dependencias externas obligatorias) para recopilar información de `vessel schedule` desde páginas públicas de puertos africanos.

## ¿Tengo que importarlo en Visual Studio Code?

No es obligatorio, pero **sí es lo más cómodo**.

- Puedes ejecutarlo desde cualquier terminal (VS Code, CMD, PowerShell, bash, etc.).
- En VS Code solo tienes que abrir la carpeta del proyecto y correr comandos en la terminal integrada.

---

## 1) Dónde ejecutar el bot

Ejecuta el bot **dentro de la carpeta del proyecto** (donde está `vessel_schedule_bot.py`).

Ejemplo de ruta:

```bash
/workspace/bot_lineups
```

Comprueba que estás en la carpeta correcta:

```bash
pwd
```

En Windows:

```powershell
cd C:\ruta\a\bot_lineups
```

---

## 2) Cómo abrirlo en VS Code

1. Abre VS Code.
2. `File` → `Open Folder...`
3. Selecciona la carpeta del proyecto (`bot_lineups`).
4. Abre terminal integrada: `Terminal` → `New Terminal`.
5. Ejecuta los comandos desde esa terminal.

---

## 3) Cómo ejecutarlo (rápido)

### Opción A: salida JSON

```bash
python vessel_schedule_bot.py --config ports_africa.json --output data/schedules.json --format json
```

### Opción B: salida CSV

```bash
python vessel_schedule_bot.py --config ports_africa.json --output data/schedules.csv --format csv
```

### Limitar pruebas a pocos puertos

```bash
python vessel_schedule_bot.py --config ports_africa.json --limit 2
```

---

## 4) Configurar puertos reales

Edita `ports_africa.json` y reemplaza las URLs de ejemplo por URLs/endpoints oficiales.

Archivo base incluido:

- Port of Mombasa
- Port of Durban
- Port of Tanger Med

Si un puerto tiene API JSON oficial, usa `"method": "json"`.

---

## 5) Ver resultados

- Si usas JSON: revisa `data/schedules.json`
- Si usas CSV: revisa `data/schedules.csv`

---

## 6) Errores comunes

- **`No se pudo extraer ... 403`**: el sitio bloquea scraping o hay proxy/firewall.
- **Sin resultados**: la URL no contiene tabla/JSON de schedules o cambió el formato.
- **`python` no encontrado**: instala Python 3 y usa `python3` si aplica.

---

## Funcionalidad

- Carga puertos desde `ports_africa.json`.
- Consume fuentes HTML o JSON.
- Extrae y normaliza campos frecuentes:
  - `vessel_name`, `voyage`, `eta`, `etd`, `terminal`, `status`
- Exporta salida en JSON o CSV.

## Nota legal

Respeta siempre los términos de uso/robots de cada sitio. Si existe API oficial, úsala primero.
