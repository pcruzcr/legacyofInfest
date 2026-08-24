---
document_id: "LOI-USER-035"
title: "Legacy of InFest — Manual de Usuario"
aliases: ["User Manual", "Manual de Usuario"]
tags: ["user", "manual", "guide"]
description: "Manual de usuario para jugadores y evaluadores"
source: "docs/35_USER_MANUAL.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Manual de Usuario

**ID del Documento:** LOI-USER-035  
**Versión:** 1.0.0  
**Estado:** Oficial  
**Audiencia:** Usuarios, Jugadores, Evaluadores

> **AUD-455 (2026-08-13).** Cuatro correcciones verificadas contra el
> código real: exigía Python 3.14 cuando el mínimo real es 3.11 (CI corre
> 3.11/3.12/3.13, ver `CLAUDE.md` y `10_LIBRARIES_AND_DEPENDENCIES.md`);
> asignaba `X` a «Agacharse» cuando `X`/`K` es ataque largo y agacharse es
> `↓`/`S` (ver `04_PLAYER_SPEC.md` §3); apuntaba a `assets/audio/`, una
> carpeta que no existe — la música vive en `assets/music/` y los efectos
> en `assets/sfx/` (ver `20_ASSET_BIBLE.md`); y el diagrama del HUD seguía
> mostrando el área de juego a 320×224, la resolución retirada por AUD-451
> — la interna real es 800×600.

---

## 1. ¿Qué es Legacy of InFest?

Es un motor de videojuegos 2D educativo tipo *side-scroller* ambientado en la mitología maya/chol. Combina mecánicas clásicas de acción-plataformas con laboratorios interactivos de procesamiento de imágenes, visión por computadora y reconocimiento de patrones.

## 2. Requisitos del Sistema

| Componente | Especificación |
|---|---|
| Python | 3.11 o superior (CI corre 3.11 / 3.12 / 3.13) |
| Dependencias | Ver `requirements.txt` (~12 paquetes) |
| Disco | ~500 MB (con assets) |
| Sistema | Windows 10+, macOS 12+, Linux con X11 |

## 3. Instalación

```bash
git clone <repo-url>
cd legacy-of-infest
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

Ver `docs/82_ENVIRONMENT_SETUP_GUIDE.md` para instalación detallada y solución de problemas.

## 4. Controles Generales

### 4.1 Jugador

| Tecla | Acción |
|---|---|
| `←` / `→` | Moverse izquierda / derecha |
| `ESPACIO` / `↑` | Saltar |
| `↓` | Agacharse |
| `Z` | Ataque corto |
| `X` | Ataque largo |
| `ESC` | Pausa / menú anterior |
| `ENTER` / `Z` | Confirmar en menús |

### 4.2 Debug (F11)

| Tecla | Acción |
|---|---|
| `F11` | Activar/desactivar la consola de depuración |
| `F4` | Mostrar árbol de módulos cargados |
| `F5` | Mostrar colisiones y hurtboxes |
| `F6` | Mostrar eventos en cola |

## 5. Menú Principal

Al iniciar el juego verás:

1. **Play** — Inicia la partida (Stage 0)
2. **Academic Demos** — Acceso a los 10 laboratorios interactivos
3. **Controls** — Pantalla de controles
4. **Credits** — Créditos

## 6. HUD (Interfaz en Juego)

```
┌──────────────────────────────────────────────────┐
│ ❤ ❤ ❤ ❤ ❤                     ⏱ 01:45     │
│                                                    │
│              [Área de juego 800×600 px]             │
│                                                    │
│                                                    │
│                                                    │
│                                                    │
├──────────────────────────────────────────────────┤
│  ❤ ❤ ❤ ❤ ❤                  SCORE: 1250      │
└──────────────────────────────────────────────────┘
```

| Elemento | Descripción |
|---|---|
| Corazones (arriba) | Salud del jugador |
| Temporizador | Tiempo restante del nivel |
| Corazones (abajo) | Salud del jefe (solo jefes) |
| Puntaje | Puntos acumulados |
| Banner superior | Nombre del stage al entrar |
| Mensajes | Diálogos y notificaciones |

## 7. Stages

El juego incluye múltiples niveles (stages). Cada stage tiene:

- **Zonas** con tilesets, enemigos y desafíos específicos
- **Checkpoints** que guardan tu progreso dentro del nivel
- **Enemigos** caminantes, voladores y disparadores
- **Jefes** con múltiples fases al final de ciertos niveles

### 7.1 Stage 0 — "The Awakening"

Stage de referencia construido por el profesor. Demuestra todas las mecánicas del motor: plataformas, enemigos, jefes (Venado Sagrado), power-ups y transiciones de zona.

## 8. Academic Demos

Desde el menú principal, selecciona **Academic Demos** para acceder a 10 laboratorios interactivos que demuestran conceptos de las Unidades II–IX:

| # | Demo | Unidad | Concepto |
|---|---|---|---|
| 1 | Vector Lab | II | Vectores, persecución |
| 2 | Transform Lab | II/III | Matrices 2D |
| 3 | Curve Editor | III | Bézier, splines |
| 4 | Interpolation Lab | III/IV | Lerp, easing |
| 5 | Color Theory | V | RGB/HSV/HSL |
| 6 | Noise Lab | V/VIII | Ruido procedural |
| 7 | Collision Lab | VI | Colisión AABB |
| 8 | Filter Demo | VII | Filtros de imagen |
| 9 | Vision Demo | VIII | Segmentación |
| 10 | Pattern Demo | IX | ML / clasificación |

### 8.1 Controles Comunes de Demos

| Tecla | Acción |
|---|---|
| `TAB` | Cambiar modo de operación |
| `←` / `→` | Ajustar parámetro principal |
| `↑` / `↓` | Ajustar parámetro secundario |
| `ESPACIO` | Cambiar superficie de origen |
| `F` | Congelar superficie actual |
| `S` | Guardar captura PNG |
| `R` | Reiniciar parámetros |
| `ESC` | Volver al menú de demos |

## 9. Solución de Problemas Comunes

| Problema | Solución |
|---|---|
| "ModuleNotFoundError" | Activar venv y `pip install -r requirements.txt` |
| Ventana no aparece | Verificar display (no WSL headless) |
| FPS bajos | Cerrar otras aplicaciones; reducir la escala de ventana con `LOI_DISPLAY_SCALE=1` (AUD-460: la ventana se crea a interior × escala, así que el factor ahora sí cambia de verdad el tamaño y el coste) |
| Audio no funciona | Verificar `bgm_track` en TMX; la música vive en `assets/music/` y los efectos en `assets/sfx/` |
| Texto borroso | Usar `SDL_HINT_RENDER_SCALE_QUALITY=0` (default en el motor) |

## 10. Archivos de Salida

| Tipo | Ubicación |
|---|---|
| Capturas de demo | `tests/output/demo/` |
| Logs de depuración | Consola (stdout) |
| Tests | `python -m pytest` |


---
## 🔗 Documentos Relacionados

- [[82_ENVIRONMENT_SETUP_GUIDE.md|Environment Setup Guide]]
- [[03_ARCHITECTURE.md|Architecture]]
- [[04_PLAYER_SPEC.md|Player Specification]]
- [[09_HUD_SPEC.md|HUD Specification]]
- [[40_DIALOGUE_SYSTEM.md|Dialogue System]]
