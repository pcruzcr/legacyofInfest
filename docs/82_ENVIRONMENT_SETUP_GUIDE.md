---
document_id: "LOI-SETUP-032"
title: "Legacy of InFest — Guía de instalación del entorno"
aliases: ["Guía de instalación del entorno", "Environment Setup Guide"]
tags: ["setup", "entorno", "guia"]
description: "Instalación paso a paso de la máquina y solución de problemas"
source: "docs/82_ENVIRONMENT_SETUP_GUIDE.md"
date_processed: "2026-08-12"
---

# Legacy of InFest — Guía de instalación del entorno

**ID del documento:** LOI-SETUP-032
**Versión:** 1.1.0
**Estado:** Oficial
**Relacionado con:** `10_LIBRARIES_AND_DEPENDENCIES.md`, `23_DATA_SCHEMAS.md`
**Audiencia:** Profesor, estudiantes (incorporación en la primera clase)

> **AUD-455.** Esta versión sustituye a la anterior, que estaba íntegramente en
> inglés (con un resumen en español al final que remitía al lector de vuelta al
> inglés para la solución de problemas — la sección que más se necesita en una
> guía de instalación) y citaba seis documentos que no existen en este
> repositorio (`81_RISK_REGISTER.md`, `77_SYLLABUS_ALIGNMENT_AUDIT.md`,
> `25_IMPLEMENTATION_ROADMAP.md`, `29_GIT_WORKFLOW_AND_STANDARDS.md`,
> `24_TEST_PLAN.md`, `51_IMPLEMENTATION_AUDIT.md`), exigía Python 3.14+ cuando
> `pyproject.toml` pide `>=3.11` y la matriz de CI llega hasta 3.13, y describía
> un flujo de ramas `student/<assignment_id>` / `main` que no es el de este
> repositorio (`prod`, `pprod`, `dev` — ver `CONTRIBUTING.md`, AUD-168). También
> decía que `python main.py` imprimía un mensaje de scaffolding en una
> supuesta "Fase 0"; hoy `main.py` arranca el juego completo directamente.

---

## 1. Propósito

`10_LIBRARIES_AND_DEPENDENCIES.md` cubre la instalación en unas pocas líneas.
Este documento es la **guía operativa paso a paso** que sigue un estudiante
durante la incorporación de la primera clase: instrucciones por plataforma,
herramientas que no son de Python (Tiled, VS Code) y una tabla de solución de
problemas con los fallos más comunes de instalación.

---

## 2. Lista de requisitos previos

Antes de empezar, confirma que tienes:

- [ ] Acceso al repositorio (lo da el profesor)
- [ ] Git instalado y configurado (`git --version` funciona; `git config user.name`/`user.email` están puestos)
- [ ] Acceso de administrador/sudo en tu máquina (hace falta para algunas instalaciones de abajo)
- [ ] Al menos 2 GB de espacio libre en disco

---

## 3. Paso 1 — Instalar Python

El proyecto exige **Python 3.11 o superior** (`requires-python = ">=3.11"` en
`pyproject.toml`). La matriz de integración continua (`.github/workflows/ci.yml`)
prueba **3.11, 3.12 y 3.13** — cualquier versión de esa matriz es una elección
segura. Una versión más nueva (3.14+) puede funcionar, pero no es la que se
verifica en cada cambio del repositorio, así que si algo falla de forma rara,
lo primero que hay que descartar es esa diferencia de versión.

### 3.1 Windows

1. Descarga el instalador desde [python.org/downloads](https://python.org/downloads) — versión 3.11, 3.12 o 3.13.
2. Ejecuta el instalador. **Marca "Add Python to PATH"** en la primera pantalla — es el fallo de instalación más común cuando se olvida.
3. Verifica: abre una terminal nueva (PowerShell o símbolo del sistema) y ejecuta:
   ```
   python --version
   ```
   Salida esperada: `Python 3.1x.x`.

### 3.2 macOS

1. Recomendado: usa [Homebrew](https://brew.sh):
   ```bash
   brew install python@3.12
   ```
2. Verifica:
   ```bash
   python3 --version
   ```

### 3.3 Linux (basado en Debian/Ubuntu)

```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip
python3.12 --version
```

Si tu distribución no tiene todavía el paquete, usa el PPA [deadsnakes](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa) (Ubuntu) o compílalo desde el código fuente según las instrucciones de python.org.

---

## 4. Paso 2 — Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd legacyofInfest
```

Sustituye `<url-del-repositorio>` por la URL real que te dé el profesor.

---

## 5. Paso 3 — Crear y activar un entorno virtual

**Trabaja siempre dentro de un entorno virtual.** Esto aísla las dependencias del proyecto de tu Python del sistema y de otros proyectos.

### 5.1 Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Si aparece un error de política de ejecución, abre PowerShell como administrador una vez y ejecuta:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Luego reintenta la activación.

### 5.2 macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 5.3 Confirmar la activación

El prompt de la terminal debería mostrar `(.venv)` al principio de la línea. Confírmalo con:

```bash
which python    # macOS/Linux
where python    # Windows
```

La salida debe apuntar **dentro** de la carpeta `.venv` del proyecto, no a una ubicación del Python del sistema.

---

## 6. Paso 4 — Instalar las dependencias

Con el entorno virtual activo, la instalación recomendada (la única que documenta `CLAUDE.md`) es la que incluye también las herramientas de desarrollo:

```bash
pip install -e ".[dev]"
```

Esto instala el motor más `pytest`, `ruff` y `mypy`. Si sólo necesitas ejecutar
el juego, sin las herramientas de desarrollo:

```bash
pip install -r requirements.txt
```

`requirements.txt` se mantiene sincronizado a mano con la tabla
`[project.dependencies]` de `pyproject.toml` (lo vigila
`scripts/check_dependency_sync.py`), y hoy instala: `pygame-ce`, `numpy`,
`pydantic`, `orjson`, `scipy`, `opencv-python`, `scikit-image`,
`scikit-learn`, `Pillow`, `pytmx`, `pyscroll`, `joblib`, `matplotlib`.

Hay además tres grupos de extras opcionales, que el juego detecta en tiempo de
importación y para los que existe una ruta de repliegue si faltan:

```bash
pip install -e ".[accel]"       # numba (JIT) + ModernGL (post-proceso por GPU)
pip install -e ".[scripting]"   # lupa — comportamientos de enemigo en Lua
pip install -e ".[audiotools]"  # pydub — conversión de audio fuera de línea
```

**Tiempo de instalación esperado:** 2–5 minutos según la conexión (OpenCV y scikit-learn son los paquetes más grandes).

### 6.1 Verificar la instalación

```bash
python -c "import pygame; print(pygame.version.ver)"
python -c "import cv2; print(cv2.__version__)"
python -c "import numpy; print(numpy.__version__)"
python -c "import sklearn; print(sklearn.__version__)"
python -c "import skimage; print(skimage.__version__)"
python -c "import matplotlib; print(matplotlib.__version__)"
```

Cada línea debe imprimir un número de versión, sin `ModuleNotFoundError` ni `ImportError`. Si alguna falla, ve a §10, Solución de problemas.

---

## 7. Paso 5 — Instalar Tiled (editor de mapas)

**Es una aplicación aparte, no un paquete de pip.** Hace falta sólo si tu tarea es un **Stage** (un escenario); las tareas de jefe pueden no necesitarlo.

1. Descárgalo de [mapeditor.org](https://www.mapeditor.org/) — gratis y de código abierto.
2. Instálalo para tu plataforma (instalador estándar en Windows/macOS; gestor de paquetes o AppImage en Linux).
3. Abre `student_templates/stage_template/stage_template.tmx` para confirmar que Tiled abre correctamente los ficheros del proyecto.

---

## 8. Paso 6 — Configurar VS Code (editor recomendado)

1. Instala [VS Code](https://code.visualstudio.com/).
2. Instala la extensión **Python** (de Microsoft) desde el panel de extensiones.
3. Abre la carpeta del repositorio clonado: `Archivo → Abrir carpeta...` → selecciona `legacyofInfest/`.
4. Selecciona el intérprete de Python correcto: `Ctrl+Shift+P` (o `Cmd+Shift+P` en macOS) → `Python: Select Interpreter` → elige el que está dentro de `.venv/`.
5. Confirma que la barra de estado, abajo a la izquierda, muestra el intérprete de `.venv`, no un Python del sistema.

### 8.1 Extensiones recomendadas (opcionales)

| Extensión | Para qué sirve |
|---|---|
| Pylance | Comprobación de tipos y autocompletado (encaja con las anotaciones de tipo de `22_API_CONTRACTS.md`) |
| GitLens | Visibilidad del historial de git, útil para seguir el flujo de ramas de `CONTRIBUTING.md` |
| Even Better TOML / YAML | Resaltado de sintaxis para `pyproject.toml` y la cabecera de los documentos (`23_DATA_SCHEMAS.md` §7) |

---

## 9. Paso 7 — Ejecutar la aplicación

```bash
python main.py
```

Esto arranca el flujo completo de escenas (Splash → Título → Historia → Stage 0). `main.py` también acepta:

```bash
python main.py --stage stage1_2_la_soda    # lanza un escenario concreto
python main.py --boss boss_rey             # lanza un jefe concreto
python main.py --debug                     # muestra los avisos del motor en consola
python main.py --semilla 12345             # arranca con una semilla fija, para repetir una partida
```

Si no aparece ninguna ventana (sin error, sin ventana), ve a §10.6 más abajo.

---

## 10. Solución de problemas

### 10.1 `ModuleNotFoundError: No module named 'cv2'`

**Causa:** `opencv-python` no se instaló, o no estás dentro del entorno virtual activado.
**Arreglo:**
```bash
# Confirma que el venv está activo (ver §5.3) y luego:
pip install opencv-python
```
Si sigue fallando en Linux, pueden faltar librerías del sistema:
```bash
sudo apt install libgl1 libglib2.0-0
```

### 10.2 `pygame-ce` entra en conflicto con `pygame`

**Causa:** tener los dos paquetes instalados a la vez produce ambigüedad al importar.
**Arreglo:**
```bash
pip uninstall pygame
pip install pygame-ce
```
Verifica siempre con `python -c "import pygame; print(pygame.version.ver)"`; si tienes dudas, `pip show pygame-ce` confirma que el paquete correcto está instalado.

### 10.3 `pip install -r requirements.txt` falla en scikit-learn o scipy (error de compilación)

**Causa:** falta una rueda (`wheel`) precompilada para tu combinación de plataforma/versión de Python, y se cae a compilar desde el código fuente, lo que exige un compilador de C.
**Arreglo:**
- **Windows:** instala ["Build Tools for Visual Studio"](https://visualstudio.microsoft.com/visual-cpp-build-tools/), o más sencillo, usa una versión de Python con ruedas ya disponibles (comprueba en [PyPI](https://pypi.org/project/scikit-learn/#files) qué versiones tienen rueda).
- **macOS:** `xcode-select --install` para las herramientas de compilación de línea de comandos.
- **Linux:** `sudo apt install build-essential python3-dev`

### 10.4 Tiled: el fichero TMX no abre / "Invalid Tileset Reference"

**Causa:** el `.tmx` referencia un tileset por una ruta relativa que no coincide con tu copia local.
**Arreglo:** confirma que el fichero del tileset (por ejemplo, `tileset_stage0.png`, ver `20_ASSET_BIBLE.md`) existe en la ruta relativa esperada desde la ubicación del `.tmx` (`assets/tilesets/`). Si moviste el `.tmx` fuera de su carpeta original, la ruta relativa de Tiled se rompe — mantén los ficheros `.tmx` dentro de su carpeta designada en `src/stages/`.

### 10.5 PowerShell: "running scripts is disabled on this system"

**Causa:** la política de ejecución de Windows bloquea el script de activación del venv (§5.1).
**Arreglo:** repite la instrucción `Set-ExecutionPolicy` de §5.1.

### 10.6 `python main.py` se ejecuta sin error pero no aparece ninguna ventana

**Causa habitual (sobre todo en Linux, WSL o entornos sin pantalla/remotos):** no hay servidor de vídeo disponible, o SDL está usando por defecto un controlador incompatible con tu entorno.
**Arreglo:**
- Confirma que estás en una máquina con pantalla real (no un servidor sin cabeza / un entorno de CI — esos deben ejecutar las pruebas con `pytest`, exportando antes `SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy` y `PYGAME_HIDE_SUPPORT_PROMPT=1`, tal como indica `CLAUDE.md`, en vez de lanzar la aplicación con ventana).
- En WSL2, confirma que WSLg está activo (Windows 11) o que hay un servidor X (por ejemplo VcXsrv) corriendo y `DISPLAY` bien configurado.

### 10.7 VS Code muestra errores de importación aunque `pip install` funcionó

**Causa:** VS Code apunta al intérprete de Python equivocado (el del sistema en vez de `.venv`).
**Arreglo:** repite el paso 4 de §8 (`Python: Select Interpreter`) y confirma que está seleccionada la ruta de `.venv`.

### 10.8 La carga de `joblib`/un modelo falla con un aviso o error de versión

**Causa:** desajuste de versión de scikit-learn entre el momento en que se guardó un `.pkl` y el momento en que se carga.
**Arreglo:** el modelo de referencia ya no se distribuye como `.pkl` (AUD-587): el laboratorio lo entrena en tu máquina desde `assets/datasets/sample_dataset.npz`, así que este desajuste no puede venir del modelo de referencia. Si te pasa con un modelo propio, bórralo y reentrena en tu entorno (`pip install -e ".[dev]"` primero, para que no haya deriva de versión local).

---

## 11. Referencia rápida del flujo de trabajo diario

Una vez completada la instalación, el arranque típico de una sesión es:

```bash
cd legacyofInfest
source .venv/bin/activate      # macOS/Linux
# o
.venv\Scripts\Activate.ps1     # Windows PowerShell

git pull

python main.py                 # ejecutar el juego
pytest                         # ejecutar las pruebas
```

Al terminar la sesión:

```bash
git add <ficheros concretos>
git commit -m "AUD-NNN: qué se arregló, en lenguaje llano"   # ver CONTRIBUTING.md
git push
deactivate                      # sale del entorno virtual
```

El flujo real de ramas de este repositorio (`prod`, `pprod`, `dev`, y ramas
`fix/`, `feat/`, `docs/` partiendo de `dev`) está en `CONTRIBUTING.md` — no
existe una rama `main` (AUD-168).

---

## 12. Lista de verificación (fin de la instalación)

La instalación del entorno está completa cuando **todo** esto es cierto:

- [ ] `python --version` muestra 3.11 o superior
- [ ] El prompt de la terminal muestra `(.venv)` al trabajar en el proyecto
- [ ] Las seis líneas de verificación de importación de §6.1 funcionan
- [ ] Tiled se abre (sólo para tareas de tipo Stage)
- [ ] VS Code muestra el intérprete de `.venv` seleccionado, sin errores de importación en el editor
- [ ] `python main.py` se ejecuta sin excepción y abre la ventana del juego
- [ ] `git status` dentro del repositorio muestra la rama esperada, según el flujo de `CONTRIBUTING.md`

---

## Documentos relacionados

- [[10_LIBRARIES_AND_DEPENDENCIES.md]]
- [[23_DATA_SCHEMAS.md]]
- `../CONTRIBUTING.md`
- `../CLAUDE.md`
