# Los 185 jefes históricos frente a nuestro `BossBase`

**Fuente analizada:** `md jefes.md` — dossier GDD del Top 200 de **jefes**.
**Motor:** Legacy of InFest v1.x — `BossBase` + `BossKit`.
**Fecha:** 31 de julio de 2026.
**Relacionados:** `53_…` (49 niveles) y `54_…` (Top 200 de niveles).

> **Ojo: este fichero no es el de antes.** El anterior `md jefes.md` (96 KB)
> contenía análisis de **niveles** pese al nombre. Éste (350 KB) sí es el
> dossier de **jefes**, con otra plantilla: tipología de jefe, telegrafiado,
> cajas de colisión, micro-bucles de combate y fases. Es material distinto y
> mucho más pertinente, porque la Asignación 02 del curso es diseñar un jefe.

---

## El recuento, y por qué esta vez es una buena noticia

```
bloques de análisis : 185
duplicados          :   0   ← a diferencia del dossier de niveles
juegos distintos    : 127
```

Y el reparto que decide todo:

| Grupo | Jefes | % |
|---|---|---|
| **2D — utilizables en nuestro motor** | **113** | **61 %** |
| 3D | 72 | 39 % |

Compárese con el dossier de niveles, donde sólo el 30 % era 2D y el 63 % era
tridimensional. **Aquí la proporción se invierte.** No es casualidad: un
combate de jefe es una arena cerrada con patrones, fases y telegrafiado, y ese
problema de diseño se resolvió magistralmente en dos dimensiones y se sigue
resolviendo así. Hollow Knight aporta 7, Cuphead 5, Hades 4, Dead Cells 4,
Shovel Knight 3, Castlevania 5 entre sus entregas, Metroid 5, Mario 4.

**Traducción práctica: de este dossier se puede usar el 61 %, contra el 30 %
del de niveles.** Es, con diferencia, el documento más aprovechable de los tres
que has traído.

---

## Lo que `BossKit` ya resuelve, y encaja exactamente

Antes de las tablas conviene decir qué hay, porque es más de lo que parece. El
`BossKit` no es un esqueleto: es un vocabulario de diseño de jefes.

```python
@dataclass
class BossAttack:
    name: str
    windup: float = 0.6      # el aviso
    active: float = 0.2      # el golpe
    recover: float = 0.8     # la ventana de castigo
    reach / min_range / max_range
    cooldown: float = 1.5
    phases: tuple[int, ...] = ()
    def is_readable(self) -> bool: ...   # ¿el aviso da tiempo a reaccionar?

@dataclass
class WeakPoint:
    offset / size
    multiplier: float = 2.5
    phases: tuple[int, ...] = ()

@dataclass
class SummonWave:
    species_id / count / max_alive / cooldown / phases / spawn_offsets
```

Las tres secciones centrales de cada análisis del dossier —**telegrafiado**,
**cajas de colisión y puntos débiles**, y **fases con válvulas de escape**— son
literalmente `windup`, `WeakPoint` y `BossPhase`. El `AttackScheduler` elige
ataque por distancia y fase, respeta enfriamientos y no repite el mismo dos
veces seguidas. `clamp_to_arena` mantiene al jefe dentro. `BOSS_PHASE_CHANGED`
y `BOSS_ATTACK` salen al bus de eventos.

Esto no es una coincidencia feliz: `BossKit` se construyó leyendo esta misma
literatura. Lo que sigue es cuánto de la biblioteca cubre.

---

## A. Se pueden hacer hoy con el kit tal cual (9 familias, ~60 jefes)

| Familia del dossier | Ejemplos | Cómo se hace hoy |
|---|---|---|
| **Fases por umbral de vida** | Drácula, Bowser, Hades, Nightmare King Grimm | `BossPhase(health_threshold=…)`. Es la columna vertebral del kit. |
| **Ataques con aviso, golpe y castigo** | Dark Souls, Shovel Knight, Blasphemous | `BossAttack(windup, active, recover)`. `is_readable()` verifica que el aviso da tiempo. |
| **Selección de ataque por distancia** | Prácticamente todos los duelos (24 del dossier) | `min_range` / `max_range` + `AttackScheduler`. |
| **Puntos débiles que hay que buscar** | Titan Souls (el núcleo de cristal), Mother Brain, Kraid | `WeakPoint` con `multiplier` y `phases`. |
| **Puntos débiles que cambian por fase** | Mega Man Robot Masters, Wall of Flesh | `WeakPoint(phases=(1,2))`. Ya lo contempla. |
| **Invocación de esbirros con tope** | The Collector, Baroness Von Bon Bon, The Furies | `SummonWave(count, max_alive)`. El tope es la parte que casi nadie recuerda y ya está. |
| **Patrones de proyectil** (26 menciones) | Cuphead, Ikaruga, Enter the Gungeon | `Projectile` de `enemy_shooter` + el arco del jugador (F4.2) los reutiliza. |
| **Jefes en varias partes del cuerpo** | Seven Force, Dr. Kahl's Robot, colas y cabezas | Varios `WeakPoint` con `offset` distinto sobre el mismo jefe. |
| **Arena acotada** | Todas | `set_arena_bounds` + `clamp_to_arena`. |

Sobre la última: la arena acotada existe **porque un jefe se salió del mapa**
(AUD-061). Es la clase de detalle que sólo aparece jugando.

---

## B. Baratas: entre una tarde y dos días (8)

| Mecánica | De dónde | Qué falta | Coste |
|---|---|---|---|
| **Contraataque / *parry* del jefe** (12 menciones) | Sekiro, Katana ZERO, Metal Gear Rising | `ParryState` del jugador ya existe. Falta que el jefe tenga un ataque marcado como «parriable» y una reacción al ser desviado. | 4 h |
| **Teletransporte del jefe** (6) | Death (Castlevania), Agahnim, The Time Keeper | Un `BossAttack` cuyo despacho cambie `position`. | 2 h |
| **Fase de invulnerabilidad temporal** | Nosk, Metal Sonic, muchos | `is_vulnerable` ya existe en el planificador; falta exponerlo como propiedad de fase. | 3 h |
| **Ralentización del tiempo en el golpe final** (2) | Metal Gear Rising, Katana ZERO | `Clock.time_scale` ya existe y ya se usa para el *hit-stop*. | 1 h |
| **Ondas de choque periódicas con refugio** | Inside (Onda de Choque) | Un `HazardZone` que se enciende a intervalos, más refugios que lo bloqueen. Misma pieza que los láseres del doc 54. | 4 h |
| **Marea o muro que avanza y empuja** | Terraria (Wall of Flesh), Ori (huida del Ginso) | Scroll forzado + `DeathPit` móvil. Ya está en la lista del doc 54. | 1 día |
| **Clones y espejos del jugador** (4) | SA-X (Metroid Fusion), Badeline (Celeste), Richter | Un jefe que use los mismos ataques del jugador. El framework no lo impide; es trabajo de la clase del estudiante. | 1 día |
| **Cambio de tamaño / crecimiento** (11 «gigante») | Baby Bowser, Grim Matchstick, Mega Satan | Escalar el sprite y el `rect` por fase. Los `WeakPoint` ya se recalculan con `rect_for()`. | 1 día |

---

## C. Proyecto de curso (5)

| Mecánica | De dónde | Por qué cuesta |
|---|---|---|
| **Escalada sobre el propio jefe** | Shadow of the Colossus (4 jefes), Titan Souls | El jefe deja de ser un obstáculo y pasa a ser **terreno**: sus `WeakPoint` tendrían que ser plataformas con colisión, y hace falta estamina de agarre. Es el concepto más ambicioso del dossier y también el más memorable. |
| **Sigilo contra un jefe que no se puede matar** (7 menciones) | E.M.M.I. (Metroid Dread), SA-X, Nemesis | Requiere el estado de alerta y el perseguidor invulnerable del doc 54. Si esos dos se hacen, esto sale casi solo. |
| ***Bullet hell* denso** (6) | Ikaruga, Enter the Gungeon, Binding of Isaac | Cientos de proyectiles a la vez. Nuestro `Projectile` es un objeto por bala; a 300 balas habría que pasar a arreglos NumPy, que es exactamente lo que ya hace `AmbientParticleSystem`. Hay precedente en casa. |
| **Inversión de gravedad como única mecánica** | VVVVVV (Gravitron) | `gravity_multiplier` admite negativo, pero un jefe entero construido sobre eso exige revisar animaciones, salto y cámara. |
| **Patrones sincronizados con la música** | Just Shapes & Beats, Crypt of the NecroDancer | Hay que leer el compás del audio y disparar en él. `pygame.mixer` no da análisis espectral; se resolvería con una pista de tiempos escrita a mano junto al tema. |

---

## D. No aplican (2 familias)

| Familia | Ejemplos | Por qué |
|---|---|---|
| **3D** | 72 de 185 | Elden Ring, Bloodborne, Sekiro, God of War, NieR, Devil May Cry. Misma razón de siempre: no hay cámara tridimensional. |
| **Ruptura de la cuarta pared por *hardware*** | Psycho Mantis (pide cambiar el mando de puerto), Undertale (corrompe la interfaz), Pony Island | No es que el motor no pueda: es que **no debe**. Un juego educativo que simula que el ordenador del estudiante falla enseña la lección equivocada, y en un aula con treinta máquinas produce treinta llamadas a soporte. Vale la pena mencionarlo en clase como diseño y no implementarlo. |

---

## Lo que este dossier dice de nuestras entregas

Aquí es donde el documento deja de ser teórico. La rúbrica de
`scripts/grade_boss.py` mide diez cosas, y las cuatro que más se suspendieron
esta semana son exactamente las cuatro que el dossier repite en cada análisis:

| Casilla de la rúbrica | Cuántos jefes la suspenden | Qué dice el dossier |
|---|---|---|
| `telegraph_state` | 2 de 4 | «Señales Visuales y Auditivas» es una de las cinco secciones **de todos y cada uno** de los 185 análisis. |
| `phase_transitions` | 2 de 4 | «Válvulas de Escape / Fases» — también en los 185. |
| `attack_patterns` | 2 de 4 | El Rey Terciopelo tiene un ataque implementado y la rúbrica no lo ve porque no se llama `attack` ni está declarado en la fase. |
| `hp_thresholds` | 2 de 4 (sólo 1 umbral) | Los duelos del dossier tienen 2–3 fases; ninguno tiene una. |

**No es coincidencia.** La rúbrica que escribimos y este dossier miden lo
mismo, porque describen el mismo oficio. Un estudiante que lea tres análisis de
Hollow Knight antes de diseñar su jefe sube su nota sin que nadie le explique
la rúbrica.

Y hay un caso concreto que conviene repartir: **The Collector** de Hollow
Knight. Invoca esbirros desde frascos, con tope de población, y el jugador
puede romper los frascos en el aire antes de que toquen el suelo. Eso es
`SummonWave(count, max_alive)` más un proyectil destructible: dos piezas que ya
existen, combinadas de una forma que ninguna de nuestras cuatro entregas
intentó.

---

## Resumen

| | Jefes | Veredicto |
|---|---|---|
| **Se hacen hoy con el kit tal cual** | ~60 (9 familias) | `BossPhase`, `BossAttack`, `WeakPoint`, `SummonWave` |
| **Una tarde o dos días** | 8 mecánicas | Parry, teletransporte, invulnerabilidad por fase, cámara lenta, ondas, muro que avanza, clones, cambio de tamaño |
| **Proyecto de curso** | 5 mecánicas | Escalar al jefe, sigilo, *bullet hell*, gravedad invertida, ritmo musical |
| **Fuera** | 72 en 3D + 3 de cuarta pared | Cámara, y criterio pedagógico |

**La conclusión:** este es el dossier más aprovechable de los tres. El 61 % es
directamente utilizable, el `BossKit` ya habla su vocabulario —aviso, golpe,
castigo, fase, punto débil, invocación con tope— y lo que falta son ocho
mecánicas baratas, no un motor nuevo.

---

## Tres recomendaciones

1. **Repartirlo antes de la Práctica II.** Es material de la Asignación 02 tal
   cual está. Las cinco secciones de cada análisis se corresponden casi uno a
   uno con las casillas de `grade_boss.py`, y las cuatro que más se suspendieron
   —telegrafiado, fases, patrones de ataque y umbrales— son las que el dossier
   explica en cada una de sus 185 entradas.

2. **Añadir el *parry* del jefe.** Cuatro horas. `ParryState` ya existe en el
   jugador y no tiene con qué practicar: hoy el desvío no cambia nada en ningún
   jefe. Doce análisis del dossier giran sobre eso, y es la mecánica que
   convierte un saco de golpes en un duelo.

3. **Dar `WeakPoint` como ejemplo obligatorio.** De las cuatro entregas de
   jefes, sólo el Venado usa puntos débiles, y es el que saca 100. Ocho jefes
   del dossier —Titan Souls, Mother Brain, Kraid, los Robot Masters— están
   construidos enteros sobre esa idea, y en nuestro kit es un `dataclass` de
   cinco campos.

---

## Cómo se comprobó

```bash
# Recuento del fichero y reparto 2D/3D
grep -c "^# Análisis" "md jefes.md"      # 185 bloques, 0 duplicados, 127 juegos

# Lo que BossKit ofrece de verdad
grep -n "^class \|^@dataclass" src/framework/entities/boss_kit.py

# Las notas reales de las cuatro entregas de jefes
python scripts/grade_boss.py src/stages/<jefe>
```
