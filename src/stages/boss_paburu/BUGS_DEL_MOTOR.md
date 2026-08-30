# Hallazgos del motor — reporte para el profesor

**De:** Alejandro · **Fecha:** 2026-08-16
**Origen:** auditoría integral del Stage 4-2 (`boss_paburu`). Todo lo que sigue apareció
trabajando sobre ese nivel, pero **ninguno es del nivel**: son de `src/engine/` o
`src/framework/`, y por eso no los toqué (la regla del repositorio es que ese código no se
modifica desde un stage).

**Cómo leer esto:** cada punto trae *cómo reproducirlo* y *qué se midió*. Todos se
comprobaron ejecutando el juego o un arnés, no leyendo el código. Los cinco primeros
afectan a **cualquier entrega**, no solo a la mía.

---

## 1. CRÍTICO — Un golpe + una cinemática dejan el juego congelado para siempre

**Dónde:** `src/framework/scenes/stage_scene.py` (`update` → `_update_gameplay`) y
`src/framework/stage/collision_system.py` (`update_hitstop`).

**Qué pasa:** cada golpe que conecta congela la simulación 0,05 s poniendo `time_scale` a 0
(hit-stop). Quien lo descongela es `CollisionSystem.update_hitstop`, que vive **dentro** de
`_update_gameplay`. Y `_update_gameplay` no corre cuando una cinemática bloquea:

```python
en_escena = self._actualizar_escenas(dt)
if not self._game_over and not en_escena:
    self._update_gameplay(dt)      # <-- aquí dentro está el drenaje del hit-stop
```

Así que si el jugador está pegando cuando arranca una cinemática, el contador se queda a
medias con el reloj en cero. **No es una pausa larga: no vuelve nunca.**

**Reproducción (medida):** con el hit-stop activo, disparar una escena bloqueante y dejar
correr 10 segundos de juego → `time_scale` sigue en `0.0`, `is_hitstopped` sigue en `True`.
El síntoma visible es la pantalla congelada, a veces partida a medio redibujar porque el
buffer de pyscroll se queda a mitad.

**Por qué importa a todos:** le pasa a cualquier nivel que combine combate y cinemáticas —
que son casi todos los de jefe. En el mío ocurría al pisar el círculo viniendo de pelear.

**El motor ya avisa de la mitad del problema.** El docstring de `update_hitstop` dice, sobre
el caso hermano (alimentarlo con el `dt` escalado): *«the game freezes permanently on the
first landed hit (AUD-001)»*. Este es el mismo cuelgue por el otro lado: no alimentarlo en
absoluto.

**Sugerencia:** sacar `update_hitstop` fuera del `if`, al final de `update`, para que corra
siempre; o ponerle un techo de duración dentro del propio `CollisionSystem`. Yo puse el techo
del lado de mi escena porque no puedo tocar el motor, pero ahí sólo protege a mi nivel.

---

## 2. CRÍTICO — Sin tarjeta gráfica, ninguna escena dibuja su interfaz

**Dónde:** `src/engine/core/app.py`, `_draw`.

**Qué pasa:** en la ruta de GPU, `App` llama a `dibujar_mundo` y a `dibujar_ui` por separado
(AUD-343). En el camino **software** —sin ModernGL instalado, o con el contexto caído— llama
sólo a `escena.draw(...)`, y una `StageScene` que reparte su dibujo entre las dos mitades
nunca ejecuta `dibujar_ui`.

**Reproducción (medida, con SDL dummy y sin GL):** el mundo se dibuja; **el HUD, las
cinemáticas, el minimapa y los subtítulos no aparecen**.

**Por qué importa:** si el proyecto se corrige en una máquina sin GPU o sin ModernGL, la
entrega se ve sin interfaz y parece rota sin serlo.

**Sugerencia:** en la rama software, llamar a `dibujar_mundo` + `dibujar_ui` cuando la escena
las implemente, igual que hace la rama de GL.

---

## 3. ALTO — El coyote time está configurado pero no funciona

**Dónde:** `src/framework/entities/states/airborne.py`.

**Qué pasa:** `settings.PLAYER_COYOTE_FRAMES = 6` (100 ms), y `Player._can_jump()` devuelve
`True` durante esa ventana… pero **ningún estado aéreo llama a `_do_jump`**, así que la
ventana no se puede usar.

**Medido:** coyote real de **1 fotograma** (16,7 ms) frente a los 100 ms configurados.

**Por qué importa:** es de las cosas que más se notan al jugar sin saber por qué. Un salto
pedido 3 fotogramas después de dejar el borde se pierde, y el jugador siente que el mando no
responde. Además, cualquier nivel calibrado suponiendo los 100 ms está más duro de lo que su
autor cree.

**Sugerencia:** llamar a `_handle_grounded_jump_input` desde `AirborneState` mientras el
contador de coyote siga vivo.

---

## 4. ALTO — Las `SinkingPlatform` nunca se hunden

**Dónde:** `src/framework/ecs/systems.py`, `marcar_pisada()`.

**Qué pasa:** la función existe y está probada, pero **no la llama nadie en producción** — la
única llamada del árbol está en `tests/test_ecs.py`. Una `SinkingPlatform` colocada en un TMX
se comporta como una plataforma fija.

**Medido:** de pie sobre una losa hundible con `retraso=0.35`, la altura no cambia en 6,7 s.

**Por qué importa:** es una mecánica documentada que cualquiera puede poner en su mapa
creyendo que funciona. En el mío hay dos y son losas fijas.

---

## 5. ALTO — `atravesable_desde_abajo` se ignora en las plataformas móviles

**Dónde:** `src/framework/ecs/…` (`rects_solidos()`) y `stage_scene.py` (~línea 972), donde
esos rects se suman a `solidos` en vez de a `one_way_rects`.

**Qué pasa:** una `MovingPlatform` que declara `atravesable="true"` **no** es atravesable: el
jugador se golpea la cabeza contra ella desde abajo.

**Medido:** saltando bajo un ascensor declarado atravesable, la cabeza choca a y=510 en vez de
subir a y=440.

**Por qué importa:** la propiedad existe en el esquema y miente. Las cinco plataformas móviles
de mi mapa la declaran.

---

## 6. MEDIO — El respawn coloca al jugador desplazado

**Dónde:** `src/framework/scenes/stage_scene.py`, `respawn` / `set_spawn`.

**Qué pasa:** un `Checkpoint` guarda su **centro**, y al reaparecer se aplica a la vez como
`position` (esquina superior izquierda) y como `rect.center`. El jugador reaparece corrido
media caja.

**Medido en mi nivel:** el checkpoint de la sala del jefe guarda (3984,1280) y el jugador
aparecía con los pies 16 px **dentro** del suelo; el resolutor de colisiones lo expulsaba
lateralmente hasta fuera de la sala, y desde ahí caía al vacío sin morir nunca (y=31.122 a los
60 s, con la vida llena y sin game-over). Partida perdida.

**Sugerencia:** decidir una sola convención (`rect.midbottom = checkpoint` es la habitual) y
aplicarla en un único sitio.

---

## 7. MEDIO — El clima `fog` y `snow` repiten una muestra de 2 segundos

**Dónde:** el sistema de clima, con `sfx_environment_wind_indoor.wav`.

**Qué pasa:** los dos climas reproducen en bucle infinito una muestra de 2,0 s que no está
hecha para loopear. Se oye como un chasquido cada dos segundos.

**Por qué no salta a la vista:** ningún stage del curso usa `fog` ni `snow`, así que sólo lo
oye quien los active. Lo resolví desde mi stage con un ambiente propio de 12 s con loop
perfecto, pero el bug sigue ahí para el siguiente que use esos climas.

---

## 8. MEDIO — El analizador de niveles sobreestima el salto

**Dónde:** `src/framework/stage/level_metrics.py` (`analyse_stage`).

**Qué pasa:** usa `max_gap_with_air_jump = 171 px`, más del doble del alcance real que medí
del jugador. Resultado: **dice que hay plataformas alcanzables que no lo son.**

**Medido:** el salto real llega a 87 px de altura y el techo práctico de un repecho es 80 px
(59 % de éxito); a 96 px, **0 de 136 intentos**. El analizador daba por buenas dos plataformas
de mi mapa a 96 px.

**Por qué importa:** `grade_stage.py` puntúa el diseño con esos números, así que un mapa puede
sacar nota alta con saltos imposibles. Si el juego no tiene salto aéreo, la constante debería
reflejarlo.

---

## 9. BAJO — El HUD muestra el total de fases, no la actual

**Dónde:** `src/engine/ui/hud.py` (~línea 772).

**Qué pasa:** durante toda la pelea el HUD dice «PHASE 4» aunque el jefe esté en la primera.
Pasa igual en los jefes de referencia, así que es del motor y no de una entrega.

---

## 10. BAJO — `sombras_proyectadas` es inusable en mapas grandes

**Dónde:** el sistema de sombras proyectadas.

**Qué pasa:** proyecta una cuña por **cada rect de colisión**. En un mapa cuyos suelos miden
miles de píxeles, eso son polígonos negros que tapan media pantalla. Lo probé y tuve que
apagarlo.

**Sugerencia:** limitar la proyección a rects por debajo de cierto tamaño, o recortarla a la
vista de la cámara.

---

## Nota de migración: la `y` de los objetos del TMX

AUD-455 cambió la convención: la `y` de un objeto pasó de ser **los pies** a ser el **borde
superior** (la semántica nativa de Tiled). El cambio es correcto, pero **los mapas existentes
no se migraron**, y el fallo es silencioso: nada da error, los objetos simplemente quedan
media caja más abajo.

En mi mapa afectó a dos familias sin que nada avisara:
- los **enemigos de suelo** quedaron enterrados su altura entera (invisibles);
- los **checkpoints** quedaron bajo el suelo y **ninguno de los diez se activaba** — morir
  devolvía siempre al spawn del nivel.

Los dos ya están corregidos de mi lado. Lo señalo por si otras entregas del curso arrastran lo
mismo: se detecta comparando `rect.bottom` de la entidad viva con el suelo, no leyendo el TMX
(el XML se ve «bien» en los dos casos).
