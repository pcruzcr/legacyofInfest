# Validación de sistemas: qué está implementado, qué se alcanza, qué no existe

**Fecha:** 31 de julio de 2026
**Método:** análisis del árbol de sintaxis sobre todo `src/`, no lectura de
documentación. La documentación de este proyecto ya ha mentido cuatro veces.

---

## La pregunta que se hace, y por qué no es «¿existe?»

Un sistema puede estar en tres estados, y sólo el tercero sirve de algo:

1. **No existe.**
2. **Existe y nadie lo alcanza.** Compila, tiene pruebas, y ningún camino del
   juego llega a él. Es el defecto que este proyecto lleva un mes encontrando:
   la iluminación que no iluminaba un píxel, las trece demos que dibujaban en
   una esquina, el ultimate cuyo medidor nadie incrementaba, el nado sin zona de
   agua.
3. **Existe y se usa.**

Preguntar «¿está implementado?» sólo distingue el 1 del resto. Aquí se cuentan
las **llamadas reales desde el motor**.

---

## Los diez sistemas

| Sistema | Fichero | Usos en el motor | Veredicto |
|---|---|---|---|
| **Guardado** | `engine/core/save_manager.py` | 6 | ✅ en uso |
| **Audio ambiental** | `engine/audio/audio_manager.py` | 8 | ✅ en uso |
| **Speedrun** | `framework/stage/speedrun_mode.py` | 2 | ✅ en uso |
| **Bestiario** | `framework/entities/bestiary.py` | 14 | ✅ en uso |
| **Diálogo** | `framework/ui/dialogue_system.py` | 6 | ⚠️ en uso, **sin una sola prueba** |
| **Cutscenes** | `framework/stage/cutscene_system.py` | 6 | ⚠️ en uso, **sin una sola prueba** |
| **Niebla de guerra** | `framework/vfx/fog_of_war.py` | **0** | ❌ **huérfano** (8 usos en pruebas) |
| **Efecto de agua** | `framework/vfx/water_effect.py` | **0** | ❌ **huérfano** (6 usos en pruebas) |
| **Boss Rush** | `framework/stage/boss_rush_mode.py` | **0** | ❌ **huérfano** (4 usos en pruebas) |
| **Transiciones** | `engine/scene/transitions.py` | **0** | ❌ **duplicado muerto** |

### Los cuatro huérfanos, uno por uno

**`fog_of_war.py`, `water_effect.py`, `boss_rush_mode.py`** — escritos,
documentados (`docs/44_`, `46_`, `47_`) y con pruebas que los ejercitan en
aislamiento. Ningún escenario, ninguna escena y ningún menú los instancia. Un
jugador no puede llegar a ellos por ningún camino.

Son el mismo patrón que el nado: **las pruebas los mantienen verdes y eso
esconde que nadie los usa.** Una prueba unitaria confirma que la pieza funciona;
no confirma que esté enchufada.

**`engine/scene/transitions.py`** es distinto y peor: sus cinco clases
—`BaseTransition`, `FadeTransition`, `WipeTransition`, `SlideTransition`,
`CircleTransition`— tienen **cero usos en todo el repositorio, ni siquiera en
pruebas**. Las transiciones que el juego usa de verdad están en
`engine/scenes/transition_manager.py`, que `SceneManager` sí instancia.

Es exactamente lo que AUD-099 retiró dos veces: **dos implementaciones del
mismo concepto, una viva y una muerta**, y el estudiante que busca «cómo hago
una transición» encuentra la muerta el 50 % de las veces.

### Diálogo y cutscenes: en uso, sin red

Los dos se llaman desde `StageScene` y tienen **cero pruebas**. No están rotos
—el arnés de humo los ejercita al arrancar cada escena— pero son los dos únicos
sistemas vivos del motor sin una sola prueba propia. Cualquier cambio en ellos
se descubre jugando.

---

## Enemigos

```
tipos registrados en el motor : 30
colocados en algún mapa       : 20
nunca colocados               : 10
```

Los diez que nadie ha puesto nunca en un mapa: `FlyingCucaracha`,
`FlyingNotebook`, `FlyingTerciovolador`, `ShooterCocinero`, `ShooterTiza`,
`ShooterVenomoLargo`, `WalkerEstudiante`, `WalkerInsect`, `WalkerRaton`,
`WalkerTerciopelo`.

**No es un defecto del motor: los treinta funcionan.** Es un hueco de contenido,
y tiene una consecuencia concreta: el bestiario del juego **no se puede
completar**, porque hay diez criaturas que ningún jugador puede encontrar. Un
codex con entradas inalcanzables se lee como un fallo aunque no lo sea.

*(Nota: varios estudiantes registran variantes propias con nombres como
`LaSodaWalkerRaton`, así que el tipo base del motor queda sin usar mientras la
criatura sí aparece. Cuenta a medias.)*

### Cajas de daño

Corregidas en AUD-108, en esta misma sesión: diez de doce cuerpos tenían la
hurtbox **fuera** del cuerpo. Ver `57_COLISIONES_Y_DEUDAS_SALDADAS.md`.

---

## Estados

### De enemigo — 13 declarados

Doce se asignan de verdad en algún punto del motor o de las entregas. **`IDLE`
no se asigna nunca**: se lee en tres sitios y no se escribe en ninguno. Un
enemigo nunca está `IDLE`; nace en `PATROL`.

Es menor —nada se rompe— pero significa que un estudiante que consulte el enum
diseñará contando con un estado que su enemigo nunca tendrá.

### Del jugador — 26 declarados

```
alcanzables por transición : 24
bases legítimas            :  2   (AirborneState, _AttackState)
huérfanos                  :  0
```

**Antes de esta sesión eran tres huérfanos.** `SwimmingState` se conectó en
F5.6, y aquí apareció el quinto sistema huérfano del mes:

> **`AirChaseState`** — sprite propio (`player_jump.png`), velocidad de
> animación propia (12,0), valor en el enum `PlayerState.AIR_CHASE`, y una
> lógica completa que lanza al jugador hacia arriba y adelante para seguir al
> enemigo levantado. **Cero transiciones de entrada.**

La forma del código decía para qué era: `enter()` pone `velocity.y = -200` y
suma un golpe al combo, y `AerialAttackState` ya mandaba al remate a partir del
segundo golpe. **Faltaba el primero.** Conectado: el primer golpe aéreo lanza,
el segundo remata.

Y una prueba nueva encontró otro hueco a los diez segundos de escribirse:
`LEDGE_GRAB` tenía hoja de sprites y **no** tenía velocidad de animación, así
que caía al valor por defecto de 10 fps y agarrarse a un borde se veía nervioso.

Esa prueba sustituye a `assert len(PlayerState) == 24`, que además se llamaba
`test_player_state_enum_has_19_values`: el nombre y el número ya no coincidían,
señal de que a alguien le tocó editarla y sólo cambió el número. **Una prueba
que hay que actualizar cada vez que se añade un estado no protege nada; enseña
a editar pruebas.**

---

## Obstáculos, lianas y tirolesas

### Obstáculos: sí, y de sobra

Sin escribir una línea de código, desde Tiled:

`Solid` · `Platform` (atravesable desde abajo) · `HazardZone` · `DeathPit` ·
`LaserZone` (con ciclo y aviso) · `ShockwaveZone` · `RhythmBlock` ·
`SinkingPlatform` · `MovingPlatform` · `WindZone` · `FrictionZone` · `Conveyor`
· `WaterZone` · `LockedDoor` · `Cage` · `Guard` · `Stalker`.

### Lianas y tirolesas: **no había nada, y ahora sí**

Búsqueda sobre todo `src/`: ni `Ladder`, ni `Rope`, ni `Zipline`, ni `Climb`, ni
un solo estado que suspendiera la gravedad. **Cero coincidencias.**

Y no se podían improvisar. Un estudiante intentaría apilar `Solid` estrechos
para simular una cuerda, y lo que consigue es una pared: el jugador queda **al
lado** de la columna, no dentro, y para subir tiene que saltar — que es
exactamente lo que una liana existe para evitar. Trepar necesita tres cosas que
ningún componente daba: suspender la gravedad, movimiento vertical libre, y una
forma de soltarse que no sea caerse.

Implementadas en F5.14:

| Tipo TMX | Componente | Estado | Fuente |
|---|---|---|---|
| `Vine` | `Liana` | `TrepandoState` | DKC (Ropey Rampage), Zelda, Spelunky, Castlevania |
| `Zipline` | `Tirolesa` | `TirolesaState` | DKC, Rayman, Ori |

**La diferencia entre las dos, en una frase:** en la liana *tú* decides la
velocidad; en la tirolesa la decide la pendiente. Por eso una sirve para
descansar y explorar, y la otra para acelerar y comprometerse.

Detalles que se pensaron y quedan escritos en el código:

* **El margen de agarre es generoso.** Con la anchura exacta de la cuerda
  —cuatro píxeles— agarrarse sería puntería, y fallar por uno se lee como que
  el juego no responde.
* **Se agarra con el botón, no automáticamente.** Una liana que te atrapa al
  pasar corriendo convierte un adorno en una trampa.
* **La tirolesa se mide contra el segmento, no contra su caja envolvente.** Un
  cable diagonal tiene una caja enorme y engancharía desde metros por debajo,
  donde el cable no está.
* **Al llegar al final se conserva el impulso.** Frenar en seco desperdicia toda
  la velocidad que el tramo acumuló.
* **Soltarse de la liana da impulso horizontal.** Sin él, saltar te deja caer en
  vertical sobre el mismo sitio y la liana no sirve para cruzar nada.

Y una consecuencia de paso: `Action.MOVE_UP` existía en el mapa de acciones y
**no lo leía nadie**. Pulsar arriba no hacía nada en todo el juego. Ahora sube
por la liana.

---

## Resumen

| | Cuántos | |
|---|---|---|
| Sistemas en uso | 6 de 10 | |
| Sistemas huérfanos | 3 | niebla de guerra, agua (VFX), boss rush |
| Duplicados muertos | 1 | `engine/scene/transitions.py` |
| Sistemas vivos sin pruebas | 2 | diálogo, cutscenes |
| Tipos de enemigo | 30 registrados, 20 usados | |
| Estados de enemigo | 13, uno nunca asignado (`IDLE`) | |
| Estados del jugador | 26, **cero huérfanos** (eran 3) | |
| Obstáculos desde Tiled | 17 tipos | |
| Lianas y tirolesas | **añadidas** | no existía nada |

---

## Lo que recomendaría, por orden

1. **Borrar `engine/scene/transitions.py`.** Cinco clases muertas que compiten
   con las vivas. Es la tercera vez que aparece un duplicado así (AUD-099 quitó
   dos), y cada uno cuesta media hora a quien se lo encuentra.
2. **Decidir sobre los tres huérfanos.** Niebla de guerra, efecto de agua y
   boss rush están escritos y probados. O se enchufan —el laboratorio de
   mecánicas es el sitio natural— o se retiran con su documentación. Mantener
   código vivo que nadie ejecuta es pagar el coste sin cobrar el beneficio.
3. **Escribir pruebas de diálogo y cutscenes.** Son los dos únicos sistemas
   vivos sin red.
4. **Colocar los diez enemigos que nadie ha usado**, o quitarlos del bestiario.
   Un codex que no se puede completar se lee como un fallo.
