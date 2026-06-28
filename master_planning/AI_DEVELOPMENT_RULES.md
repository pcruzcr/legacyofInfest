# AI DEVELOPMENT RULES (v3 - Full Alignment)

## R1: SIGNATURES EXACTAS
Coincide con 22_API_CONTRACTS.md exactamente.
Mismos parametros, tipos, orden, defaults.
Si no esta en contratos, no existe.

## R2: MODULE DOCSTRING
Module, System, Academic Unit, Description en cada .py.

## R3: TYPE HINTS
Python 3.14+ en toda funcion publica.

## R4: NO BARE EXCEPT
except: y except Exception: sin manejo prohibidos.

## R5: NO MAGIC NUMBERS
Importar todo numero de settings.py.

## R6: ASSET LOADING NUNCA CRASHEA
Fallback graceful con placeholder. WARNING log.

## R7: PLACEHOLDER VISUAL COLORS
Player: blue(0,120,255) 20x32. Walker: red(200,0,0) 24x28.
Flying: orange(255,150,0) 20x14. Shooter: purple(150,0,200) 16x24.
Checkpoint inactive: gray(120,120,120) 16x32. Active: gold(255,215,0) 16x32.
Floor: dark gray(60,60,60) 16x16 + border.
Background: dark navy (15,15,40) nunca negro.

## R8: CAMERA OFFSET
Screen = World - camera.offset en TODO entity.draw().

## R9: ONE COMMIT PER TICKET
Formato: [SCOPE] type: description - T#.#

## R10: FORBIDDEN CALLS
Stage code: NO pygame except Surface, NO cv2/scipy/sklearn/skimage/numpy/joblib.

## R11: DEFERRED WORK -> KNOWN_GAPS.md
Todo TODO/NotImplementedError con entrada [GAP-NNN].

## R12: NO MODIFICAR COMPLETED MODULES
DoD cumplido = no tocar sin aprobacion.

## R13: NO STUDENT CODE MODIFICATION
No modificar src/stages/, student_templates/ despues de creados.

## R14: TEST + VISUAL GATE
Toda fase requiere AMBOS gates. Visual gate fallida = fase NO completa.

## R15: GIT HYGIENE
feature/phase-N branches. No force-push a main.

## R16: DOCUMENT PRECEDENCE
22_API_CONTRACTS -> sintaxis. 23_DATA_SCHEMAS -> datos.
Narrative docs -> comportamiento. 25_ROADMAP -> orden.
28_DECISION_LOG -> arquitectura. 33_SCOPE -> QUE construir AHORA.

## R17: STAGE API CONTRACT
Todo BaseScene subclass DEBE tener:
STAGE_ID: str (match folder name)
STAGE_NAME: str (display name)
ZONE: int (1-4)
TIME_LIMIT: int (seconds, 0=no timer)
BGM_TRACK: str (filename without extension)

Engine descubre stages escaneando src/stages/ para subfolders con BaseScene subclass.
SceneRegistry usa STAGE_ORDER fijo. Stages faltantes = skip silencioso.

## R18: OPENCODE PRIMARY
OpenCode reemplaza Cline como herramienta AI primaria.
