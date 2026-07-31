# Stage 2.1 - Distrito Central: Oficinas

Escenario del proyecto Legacy of InFest - Zona 2 (Distrito Central), area de oficinas.
Nivel horizontal de recorrido y combate, sin jefe.

## Contenido
- Dimensiones: 200 x 38 tiles (3200 x 608 px)
- Piso con colision y paredes en ambos bordes
- 9 enemigos: 4 Walker, 2 Charger, 3 Brute (dificultad creciente izq -> der)
- Spawn del jugador a la izquierda, salida (NextTrigger) al final
- Fondos parallax (skyline nocturno) e iluminacion de ambiente

## Archivos
- stage2_1_oficinas.tmx  : el mapa (Tiled)
- stage2_1_oficinas.py   : la escena (subclase de StageScene)
- tileset_oficinas.png   : tileset 16x16
- __init__.py            : modulo Python
Fondos en: assets/backgrounds/oficinas/

## Como ejecutar
.\.venv\Scripts\activate
python main.py --stage stage2_1_oficinas

## Controles
Mover: A/D o flechas | Saltar: Espacio/W | Ataque: Z o X | Dash: Shift

## Autor
Saul - Zona 2 (Distrito Central: Oficinas)
