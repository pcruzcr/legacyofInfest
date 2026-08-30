# Auditoría integral — Stage 4-2 «El Gran Shamán Paburu»

**Fecha:** 2026-08-16 · **Alcance:** el stage completo (camposanto + catacumba + jefe de 4 formas)
**Método:** cuatro auditorías paralelas —física/plataformas, bugs funcionales, código/rendimiento y
el jefe— con la escena real ejecutada en headless y en un contexto OpenGL real. **Cada hallazgo
salió de una prueba ejecutada, no de leer el código.** 16 correcciones aplicadas y verificadas
(AUD-480…495), cada una con una prueba que falla sin ella.

---

## 1. Resumen

El stage estaba **más roto de lo que parecía jugando**, y la razón es la misma en casi todos los
casos: cosas que *se ven bien* y no *funcionan*. Tres bugs impedían terminar la partida y ninguno
daba error en consola.

**Lo más grave, en una línea cada uno:**

| | Qué pasaba |
|---|---|
| **Los 10 checkpoints de superficie no existían** | Escritos con `y=FLOOR_Y` (los pies), leídos por el motor como borde superior: la caja quedaba *bajo* el suelo. **0 de 10 se activaban.** Morir devolvía siempre al spawn. |
| **Morir en la catacumba perdía la partida** | El checkpoint guarda su centro y el motor lo aplica como esquina: los pies caían dentro de la losa, el resolutor expulsaba al jugador a x=4112 —fuera de la sala— y caía al vacío sin morir nunca. |
| **El mapa no tenía bordes** | Caminando a la izquierda desde el spawn se salía por x<0 y caía para siempre. Sin muerte, sin respawn: cerrar el juego. |
| **La embestida del venado no podía tocarte** | Nacía 17 px por encima de tu cabeza. 0 impactos en 9 embestidas — y sólo pegaba si **saltabas**, que es lo contrario de su lección. |
| **El Juicio final podía matarte** | Con poca vida, el cierre ceremonial mataba. El diseño dice «se gana siempre; *cómo* se gana es la firma». |

**Y la curva de dificultad iba al revés:** 10,2 → 21,3 → 19,7 → **12,8** de daño por minuto. El acto
final era el segundo más inofensivo de la pelea, porque dos de sus cuatro patrones no podían tocar
a un jugador de pie (la procesión pasaba por encima; CONVERGENCE dejaba siempre los mismos cuatro
pasillos, así que quedarse quieto era la respuesta óptima).

**Estado tras la auditoría:** 130/130 en stage, 100/100 en jefe, TMX validado, 257 pruebas propias
en verde, ruff limpio. Rendimiento holgado: **4,5-5,1 ms por fotograma** (11,5 ms de margen a 60 fps),
y el código propio del stage es menos de 0,7 ms de eso — el resto es el motor.

---

## 2. Bugs corregidos

### CRÍTICOS

**AUD-480 — Los checkpoints de superficie nunca se activaban**
*Repro:* caminar de x=900 a x=3990. *Esperado:* 8 checkpoints. *Actual:* 0.
*Causa:* el generador los emitía con `y=FLOOR_Y` (convención «la y son los pies»), pero el motor
cambió a la semántica nativa de Tiled (`y` = borde superior) — el mismo cambio que ya nos había
enterrado los enemigos (AUD-462). La caja ocupaba 560-592, bajo el suelo; el jugador de pie, 528-560.
*Arreglo:* `y = FLOOR_Y - 48`. **Medido después: 10/10 se activan.**

**AUD-481 — Morir en la catacumba expulsaba del mapa**
*Repro:* pelear, morir contra Paburu, continuar. *Actual:* aparecía en x=4112 (fuera de la sala) y
caía hasta y=31.122 a los 60 s, con la vida llena y sin game-over.
*Causa:* el checkpoint guarda su centro; el motor lo aplica como esquina superior. Los pies caían
16 px dentro de la losa y el resolutor de colisiones lo expulsaba lateralmente hasta el borde.
*Arreglo:* la escena sobrescribe `respawn()` y recoloca siempre en el punto de llegada de la sala.
**Medido: 4/4 muertes seguidas reaparecen dentro.**

**AUD-482 — El mapa no tenía muros de borde**
*Repro:* mantener izquierda 10 s desde el spawn. *Actual:* x=-402, y=4601, cayendo a 500 px/s para
siempre. *Causa:* sin muros laterales y sin plano de muerte (los otros stages del repo sí los tienen).
*Arreglo:* dos sólidos en x=-16 y x=4160. **Medido: 15 s contra cada borde, el jugador se queda dentro.**

**AUD-483 — La embestida del venado pasaba por encima del jugador**
*Actual:* banda de daño en y∈[1225,1251]; tu hurtbox de pie, y∈[1268,1296]. **0 impactos en 9.**
La procesión de ANCIENT_CALL, peor: sus tres pasadas iban todas sobre tu cabeza.
*Causa:* el `-58` venía de la arena vieja de 608 px; con la catacumba, `arena.bottom` es otra cosa.
*Arreglo:* `arena.bottom - 20`, y la procesión a (−20, −70, −120). **Medido: 9/9 impactos, y quedan
33 px de aire para saltarla.**

**AUD-484 — El Juicio final podía matar**
*Actual:* con 1,0 de vida, muerte en t=4,33 s. *Arreglo:* el daño del Juicio nunca baja de 0,5 de
vida. Se gana siempre; la marca del veredicto sigue costando su punto con la barra llena.

### ALTOS

**AUD-485** — Los proyectiles en vuelo sobrevivían al cambio de fase y **dañaban con el jefe
invulnerable** (1,0 medido). Ahora la transición limpia también proyectiles y ánimas.

**AUD-486** — La Pepita **apuntaba al revés**: la línea de mira mostraba el rumbo de la embestida
*anterior* (error angular mediana 129°, máximo 172,8°). Ahora 0,00°.

**AUD-487** — CONVERGENCE dejaba **siempre los mismos cuatro pasillos**: 48 haces, 0 impactos.
Quedarse quieto era óptimo. Ahora el patrón se desplaza por invocación, conservando los pasillos
de ≥120 px. **6 de 24 invocaciones alcanzan a un jugador quieto.**

**AUD-488** — Cargar partida **recortaba la vida de 9 a 5**: el bonus de zona se aplicaba después de
que el motor restaurara la vida guardada. Ahora 9 → 9, y sin curación gratis (3 → 3).

**AUD-489** — La ventana de parry del Juicio era **0,067 s reales**, no los 0,2 declarados: el daño
consumía el juicio antes de que el parry lo viera. Ahora 0,150 s.

**AUD-490** — Dos balsas del pozo se solapaban el **28,9 %** del tiempo y la de arriba **te empujaba
al agua**. Ahora 0,0 %.

### MEDIOS

**AUD-491** — El único checkpoint que funcionaba reaparecía **dentro del pozo**, con el ahogado
encima: 9 → 5 de vida en 10 s sin tocar el mando. Movido a la orilla.
**AUD-492** — El epílogo se jugaba **degradado en el segundo intento** (los custodios no se
despedían). Bandera no reiniciada.
**AUD-493** — Las cadencias que deben acelerarse bajo el 60 % y el 30 % de cada forma **nunca se
activaban** en las Formas 1 y 2: la fracción de vida se medía contra el umbral de entrada y no
contra el tramo. Ahora las cuatro formas recorren 1,00 → 0,00.
**AUD-494** — Proyectiles inmortales: un orbe devuelto con parry **vivía para siempre** (comprobado
a los 120 s con vida declarada de 7 s).
**AUD-495** — El cambio de forma se anunciaba **dos veces** (banner y bloom dobles).

---

## 3. Plataformas

Envolvente de salto medida: **87 px de altura, 90 px/s en suelo, sin salto aéreo, coyote real de
1 fotograma**. Con eso, el techo práctico es un repecho de **80 px (59 % de éxito)**; a 96 px, **0 %**.

- **Los pedestales del círculo II son una trampa visual:** las plataformas a las que apuntan están a
  96 px, o sea **inalcanzables desde ahí** (0 de 136 intentos). Sí se alcanzan por otro lado.
  *Recomendado:* bajarlas de y=400 a y=416.
- **Los 8 nichos y tres plataformas están a exactamente 80 px** — el nivel está construido *en* el
  límite del salto, no *para* él. Con el coyote real de 1 fotograma (el motor no atiende el salto
  desde el aire aunque tenga 6 fotogramas configurados), eso es frustración garantizada.
  *Recomendado:* bajarlos a 64 px.
- **El resorte del camino final no lleva a ninguna parte:** rebota 176 px y la superficie más cercana
  queda 66 px a un lado y 16 px por encima del ápice.
- **La salida derecha del pozo no se lee:** nadando sin pulsar salto, el jugador queda clavado 15 s
  sin progreso. Con salto sale en 0,5 s, pero nada lo enseña. *Recomendado:* una repisa en (848,544).
- `Camino_04` y `Camino_05` **se solapan 48 px** (repisa duplicada).

*No los apliqué* porque los cinco cambian el recorrido y quiero que los juegues antes: son decisiones
de diseño, no bugs.

---

## 4. Código y rendimiento

**Rendimiento: sobra margen.** 4,48 ms por fotograma en el camposanto, 5,10 en combate contra el
Espíritu; p95 de 6,2 ms y **ni un fotograma por encima de 12 ms en 6.000**. Techo ~195 fps. De los
4,07 ms de dibujo, **3,92 son del motor** (post-procesado 1,58, fondo 1,15, luz 0,38); el código
propio del stage cuesta **menos de 0,7 ms**. Sin fugas: 3 minutos de soak, RSS estable.

Lo que sí es real es la **presión de asignación**: 7,3 superficies y 165 KiB por fotograma, de los
que ~148 KiB son del stage — el aura del jefe (72 KiB/frame, reconstruida cada fotograma), el aviso
de casteo y las brasas (13 `.copy()` por fotograma). *Recomendado:* cachear el aura por frame+color
(medido: −88 % de coste) y pre-hornear 8 niveles de brillo para las brasas. **No lo apliqué porque
no hace falta hoy** — hay 11,5 ms libres — y tocar el dibujo del jefe sin necesidad es arriesgarse
por nada. Queda anotado para cuando el presupuesto apriete.

Otros hallazgos anotados y no aplicados: el protocolo de ataque está duplicado en 11 clases (una
base `AtaqueRadial` lo unificaría, pero el parry usa duck typing y el cambio es delicado); el stage
lee dos privados del motor (`_camera._map_w/_map_h`) con un respaldo hardcodeado que sería la tercera
copia del tamaño del mapa; las teclas de depuración (1-4, 0, 9) están **activas en la build normal**
y funcionan incluso durante una cinemática bloqueante.

---

## 5. Lo que quedó pendiente, y qué habría que hacer

1. **Las cinco decisiones de plataformas** de la sección 3 — cambian el recorrido; jugalas primero.
2. **Las teclas de depuración**, que deberían quedar tras una variable de entorno antes de entregar.
3. **El balance de la Forma 4**: con AUD-483 y AUD-487 corregidos, hay que **volver a medir la curva**
   — el objetivo es que el acto final vuelva a ser el pico (≥24 de daño/min contra maniquí quieto).
4. **Tres bugs del motor** que no puedo tocar y conviene contarle al profesor:
   - el coyote time no funciona desde el aire (`PLAYER_COYOTE_FRAMES=6` configurado, 1 fotograma real);
   - las `SinkingPlatform` nunca se hunden: nadie llama a `marcar_pisada()` en producción;
   - `atravesable_desde_abajo` se ignora en las plataformas móviles: las cinco del mapa lo declaran
     y ninguna lo es.
5. **El sorteo se rehace al cargar** una partida (guardado con el círculo II, cargado con el III).
   Rompe «una partida, un círculo», aunque la puerta final evita el softlock.
