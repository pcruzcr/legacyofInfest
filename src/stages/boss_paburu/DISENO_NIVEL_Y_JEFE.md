# Stage 4-2 · El Cementerio de Paburu — diseño de nivel y de jefe

**Documento vivo.** Aquí se decide qué se construye y por qué; el GDD (`GDD.md`)
guarda el lore y `DISENO_CEMENTERIO.md` el razonamiento original del cementerio.
Cuando este documento y el código se contradigan, manda el código y se corrige
aquí — la regla del repositorio (`CLAUDE.md` §5).

**Última actualización:** 2026-08-16 · AUD-461 (la capa del jefe viaja por la
ruta de GPU: intro, guardianes y ronda por fin visibles con moderngl), la
señal del círculo sorteado (§2.2) y **la pasada de dirección de arte**:
noche real en vez de crepúsculo, los cuatro círculos con geometría propia y
las mecánicas del motor con piel del camposanto (AUD-462…466). Detalle en §7
y en `PENDIENTES.md`.

**La decisión de color, escrita para no volver a discutirla.** El camposanto
es de NOCHE: `start_hour = night` (tinte azul lunar 170,185,238), luz de
camino 0.50 y sala 0.42→0.68 por forma. Estuvo dos meses en `dusk`, que tiñe
la imagen entera de ocre rosado por el color grading — el «color caca» de dos
playtests seguidos no era el arte ni el tileset: era la hora. Y hasta AUD-463
ninguno de esos números llegaba a la pantalla, porque el reloj del mundo
sobrescribía la luz de la escena cada fotograma; ahora la Sala del Juicio
manda sobre su propia luz y del reloj sólo hereda tinte, bloom, clima y el
latido del compás.

---

## 0. La tesis: por qué este nivel puede ganar

Tres principios salieron de la investigación de diseño de jefes, y el nivel
los cumple o los va a cumplir:

1. **El ataque-firma es el gancho de memoria.** Las mejores peleas se
   describen por UN momento que hubo que aprender. El nuestro ES
   **EL OFRECIMIENTO** (§3.7, implementado): el cierre ritual de la pelea,
   con raíz folclórica real y sus dos salidas con test.
2. **La arena escala con el jefe.** No basta con que el jefe cambie de fase:
   el espacio debe cambiar con él. Nuestro sellado ya lo hace (los muros); las
   formas 3 y 4 lo llevan más lejos (§3.5, §3.6) hasta que en CONVERGENCE el
   **nivel entero es el arma**.
3. **El ritmo premia, nunca castiga.** La lección Hi-Fi Rush contra
   NecroDancer: atacar a compás da bonificación; fallar el compás no quita
   nada. Con «Judgment of the Ancestors» declarando su BPM en el mapa (§2.6),
   el nivel late — pero nadie necesita oído para terminarlo.

**Y la carta que nadie más tiene: el ritual es mecánica.** La estructura viene
del Juego de los Diablitos de Boruca (Patrimonio Cultural Inmaterial de Costa
Rica, 2017) — la lucha ritual, la caída de los danzantes, el llamado que los
resucita, el cierre ceremonial — pero **el juego no la nombra**: el lore usa
Tilawa, cultura ficticia a propósito, y `19_NARRATIVE` prohíbe importar
culturas reales por nombre. La estructura se adapta al lore existente sin
cambiarle una coma: los tres guardianes del camposanto **ya son** el venado,
la serpiente y el gavilán — los jefes que el jugador venció, custodios de
Paburu en vida. Ellos caen y el llamado de Paburu (`ANCIENT_CALL`, ya
declarado) los levanta: no pueden morir dos veces. Y el cierre es el juicio
(`EL_OFRECIMIENTO`, ya declarado). Nada de esto pide tecnología nueva ni
lore nuevo: pide que lo que ya existe signifique algo.

---

## 1. Estado medido (no aspiracional)

| Qué | Valor | Cómo se verifica |
|---|---|---|
| Mapa | 4160×672 px (260×42 tiles de 16) | `gen_paburu_tmx.py` lo regenera entero |
| Nota del calificador | **130/130 (100 %)** en stage y **100/100** en boss — media del árbol: 79,0 % | `scripts/grade_stage.py` / `grade_boss.py` |
| Validación TMX | limpia, 0 errores | `scripts/validate_tmx.py` |
| Pruebas propias | 17 (cementerio) + 17 (escena/jefe/guardado) | `pytest -k paburu` |
| Formas del jefe con ataques | **4 de 4** — la pelea completa, con su ceremonia de cierre | F1-F2 en arnés; F3 `test_forma3_paburu.py`; F4 `test_forma4_paburu.py`; el ARCO entero `test_pelea_completa_paburu.py` — 52 tests propios en 5 arneses |
| Vida del jugador aquí | 9 (5 base + 4 de zona) | `VIDA_EXTRA_ZONA_4`, sin tocar `settings` |
| Música | `bgm_paburu.ogg` — **«Judgment of the Ancestors»**, composición propia | la escena la resuelve por extensión |

---

## 2. Diseño de nivel

### 2.1 El recorrido, tramo por tramo

```
x=0        480      864         1440        2016   2240        2816  3040        3616        4160
|—spawn————|—POZO———|—CÍRCULO I—|—CÍRCULO II—|—————|—CÍRC. III—|—————|—CÍRC. IV——|——PUERTA——→|
            agua     864-1440    1440-2016          2240-2816         3040-3616    trampa final
            fondo    (se tocan: muro con muro)      galería           último
            y=624                                   intermedia        círculo
```

* **El pozo (480–864).** Agua con `WaterZone`; el Ahogado arrastra hacia
  abajo. Cruce alternativo por arriba: cinco piezas de parkour (dos pasarelas
  + tres balsas `MovingPlatform` de ejes alternados). La opción doble es
  deliberada: el agua es la ruta segura y lenta; el parkour, la rápida y
  castigable. **Ronda 13:** cada orilla lleva su *peldaño del brocal* — un
  escalón de escombro sumergido a 32 px bajo la lámina — porque salir del
  agua exigía SOSTENER el salto (tocándolo no se salía nunca, medido con el
  bot: moría ahí a los 25 s) y eso no lo descubre nadie.
* **Cuatro círculos ceremoniales.** `EventTrigger`s (`PABURU_CIRCULO_01..04`)
  con el disparador **metido 64 px** dentro de la arena, para que al sellarse
  los muros el jugador quede siempre dentro. En el lore son la plaza del
  ritual: donde los guardianes danzaron en vida, la tierra recuerda.
* **El foso del final (la entrada física).** Si el jugador cruza los cuatro
  círculos sin pisar el sorteado, el camino desemboca en un foso que cae a la
  catacumba (`PABURU_CIRCULO_PUERTA`, excluido del sorteo). Nadie se queda
  sin jefe — y nadie "se saltó" nada: llegó por la entrada principal.

### 2.1b La catacumba: LA SALA DEL JUICIO (decisión de Alejandro, 2026-08-14; rediseñada el mismo día tras la crítica visual)

La pelea ya no ocurre en el círculo pisado: **el círculo abre la tierra y
baja al jugador a la catacumba** (el TMX creció de 672 a 1312 px de alto).
Tres razones de diseño, las tres con test:

1. **Justicia.** Paburu **cura al portador al recibirlo** («EL JUEZ CURA AL
   PORTADOR»): la pelea de 4 formas queda calibrada contra la barra llena
   para todos. Un tribunal que remata heridos no prueba nada (lore §128).
2. **Reintento sin fricción.** Checkpoint dentro de la cámara + reentrada
   que reinvoca al jefe fresco, cura y **no repite la cinemática**.
3. **Arena diseñada**, cerrada por roca real del mapa — sin muros invisibles.

**La arquitectura (v2 — la primera versión era una caja con repisas clonadas
y se rechazó por eso).** No es una excavación: es un CUARTO de cementerio,
como las cámaras mortuorias reales. Dos espacios con jerarquía:

* **La antecámara** (derecha, 160 px, techo bajo): donde desemboca el foso.
  Se aterriza sobre un montículo de escombro —siglos de derrumbes por el
  mismo agujero—, con una hornacina vacía enfrente y el checkpoint. La
  llegada tiene umbral: caés, te levantás, y cruzás **el arco roto**.
* **La Sala del Juicio** (izquierda, 640 px): bóveda escalonada con su clave
  de arco en lo alto; el **columbario** en filas con dintel a ambos lados de
  la franja del sello (que queda lisa: ahí dibuja el jefe, y el suelo de esa
  franja es de **losas grabadas** — el círculo ritual estaba abajo desde
  siempre); dos **capillas laterales en silueta** que dicen que hay más
  cripta detrás de la pared.

**Ninguna plataforma repite altura, ancho ni apoyo** — cada una es un mueble
del cuarto: dos repisas de cripta sobre ménsulas contra el muro oeste
(1200/1136), dos **columnas rotas de alturas distintas** cuyo capitel es el
escalón (1216/1152), el **puente de arco** sobre el sello (1088), y dos
ménsulas sueltas (1136/1232). Dos rutas de escalada con ritmos distintos:
la oeste sube por las repisas; la este, por ménsulas y capitel.

**La atmósfera del motor, encendida** (antes el mapa no declaraba ninguna):
**atardecer congelado** (`start_hour=dusk`, `day_length=0` — el manual del
motor recomienda exactamente eso para arenas: la luz no cambia a mitad de
pelea, y el ocre del crepúsculo deja VER la luna del parallax), niebla,
**ceniza flotando** (la quema ritual del lore), viñeta 0.32, bloom 0.55.
Las **sombras proyectadas se probaron y se apagaron**: proyectan una cuña
por rect de colisión, y con suelos de 4.000 px eran polígonos negros
tapando media pantalla — decisión tomada mirando capturas del juego real,
no el preview. Nota medida: el calificador pasó de 80,0 % a **91,5 %
(119/130)** con este rediseño.

**Tercera pasada visual (mismo día, tras la crítica «parece hecho por
alguien sin experiencia» — capturas del juego corriendo, no del preview):**

* El campo de lápidas del fondo medía hasta 96 px de alto por 32 de ancho:
  **perfil de edificios**. Ahora 1-3 tiles, remates alternando piedra y
  cruz, segunda fila más BAJA y rala (lo lejano se ve menos, no más).
* **Cada tramo construye sus plataformas distinto**: la entrada las apoya
  en cuerpos de tumba, las galerías en ménsulas de arco, el camino final en
  frontones de mausoleo. Y **cada círculo tiene emblema**: I cruces, II
  obeliscos, III templo roto, IV mausoleos — «me tocó el de los obeliscos»
  es lo que convierte un sitio en un lugar.
* La pared de la Sala pasó de mampostería marrón (indistinguible de la
  roca) a **silueta en sombra con nichos enmarcados**: el cuarto se lee por
  contraste. Y detrás del jefe, **el retablo**: dos pilastras, su arco y la
  hornacina vacía — el trono que Paburu no ocupa. El ojo ancla donde pasa
  la pelea.
* La cámara en superficie se **clava a la banda del camposanto** (y ≤ 72):
  el mapa alto ya no arrastra media pantalla de tierra maciza al encuadre.
* Bug real encontrado por captura: `_forzar_forma` ponía la vida del
  segmento y el jefe caía en cascada a la Forma 4 en un fotograma.

Los cuatro círculos de la superficie quedan como el ritual de la plaza —
decorado, enemigos, sorteo — y todos desembocan en la misma Sala.

### 2.2 El sorteo

`Cementerio.leer(tmx, semilla)` elige **un** círculo por partida
(reproducible con semilla, uniforme ±25 % medido a 2000 tiradas). Solo el
sorteado invoca; los otros tres son teatro — hasta la Forma 4, donde dejan de
serlo (§3.6). Por eso `BossPaburu` no aparece en ningún TMX: colocarlo fijaría
justo lo que el diseño quiere impredecible.

**La señal (R2-8, 2026-08-16).** El playtest enseñó que un sorteo invisible
se siente arbitrario («me volvió a tirar a Paburu»): funcionaba, pero no se
LEÍA. Ahora el círculo elegido se anuncia solo: brasas que suben desde su
emblema y un halo que respira al ras de la losa — la tierra de ESE círculo
está viva, los otros tres quedan fríos. Es información diegética, no interfaz:
se ve desde lejos, el jugador decide si entra sabiendo, y al descender se
apaga (abajo manda la sala). Deterministas por círculo (un `Random` sembrado
con su nombre) para que las pruebas miren posiciones concretas; blits
aditivos en el mundo, con el porqué técnico documentado en el código
(`test_senal_circulo_paburu.py`, 5 pruebas).

### 2.3 El ritual sembrado en el recorrido (nuevo, P0)

La investigación es unánime: el camino al jefe debe **anunciarlo**. El
recorrido pasa a contar el ritual del camposanto —la danza de los custodios,
la caída, el llamado— antes de que el jugador sepa que lo está viendo:

* **Máscaras en la verja.** Tiles de detalle: máscaras brunca colgadas en los
  tramos de verja, una por círculo, mirando al camino. Coste: 2-3 tiles nuevos
  en el tileset propio.
* **El altar del llamado.** Un mausoleo pequeño antes del círculo I con el
  cuerno ceremonial tallado — el instrumento cuyo son levanta a los
  guardianes en la pelea (§3.4, `ANCIENT_CALL`). Quien vuelva a pasar tras
  ganar, entiende.
* **`MessageTrigger_Once` de lore** (2-3, cortos): «Aquí bailaron tres días» ·
  «Los custodios danzan aún» — frases que solo cierran sentido al final.
* **`Cutscene` TMX de entrada**: encuadre lento del camposanto al cruzar la
  verja, sin tocar Python. Presentación del espacio = respeto por el espacio.

### 2.4 Mecánicas del motor: en uso y a incorporar

**En uso:** `WaterZone` · `MovingPlatform` ×5 rutas distintas ·
`SinkingPlatform` · `RhythmBlock` · `Zipline` · `Spring` · `Vine` ·
`EventTrigger` · `Light` (braseros + farol) · `Checkpoint` ×2.

**A incorporar** (todas existen en el motor; prioridad en §6):

| Mecánica | Uso aquí | Por qué gana puntos |
|---|---|---|
| `bpm`/`compas` + pulso (F6) | declarar el BPM de «Judgment of the Ancestors»; cámara y brillo laten | el nivel entero respira con música compuesta por el equipo — nadie más tendrá eso |
| `RhythmBlock` con `patron` | la ruta parkour alta del pozo pasa a patrón musical (`"x.x."`) | ritmo como **ruta opcional**, no como peaje (lección Hi-Fi Rush) |
| `sombras_proyectadas` | las lápidas proyectan sombra de los braseros | ES el nivel nocturno del juego; profundidad visual gratis |
| `Guard` (cono de visión) | un vigilante espectral en la galería III: rodearlo, pasarlo agachado, o pelear | sigilo opcional = una decisión más por sala |
| `Door` + `Key` + `Chest` + `BreakableBlock` | mausoleo cerrado; la llave tras una lápida rompible; dentro, lore + vida | recompensa la curiosidad sin ser obligatorio |
| `Objective` | «Cruza el camposanto» (kind=llegar) | intención visible en HUD; el calificador lo puntúa |
| `Slope` | la cuesta al círculo IV y el borde este del pozo | mata dos deudas del calificador con una mecánica |

### 2.5 Deudas señaladas por el calificador

1. **Checkpoints a 3.303 px** → tercero entre II y III (~x 2100).
2. **Repecho de 480 px en el pozo** → `Slope` o escalón (§2.4).
3. **1 balsa sin ruta desde el spawn** → revisar rango o darle escalón.

### 2.6 La regla del ritmo (decisión de diseño)

Con `bpm` declarado, el motor cuantiza `RhythmBlock` al compás y late la
cámara (AUD-425: sin `bpm`, nada cambia — los demás niveles no se ven
afectados). La regla que adoptamos, y que se defiende en la presentación:
**el compás abre rutas y da espectáculo; jamás cierra el camino principal.**
La ruta a nivel de suelo nunca exige oído.

---

## 3. Diseño de jefe — El Gran Shamán Paburu

### 3.1 La pelea en una frase

Un tribunal en cuatro actos: Paburu **juzga** al jugador con instrumentos cada
vez más personales — la piedra que no mira, la máscara de la tradición, las
reliquias delegadas, y su propio espíritu, cara a cara. Y debajo del tribunal,
el ritual: el forastero que entra al camposanto debe ser puesto a prueba.

### 3.2 Las cuatro formas (tabla de fases real, `set_phases`)

| # | Forma | Vida | Tamaño | Movimiento | Patrones | Estado |
|---|---|---|---|---|---|---|
| 1 | LA CABEZA DE PIEDRA | 20→15 | 64×64 | estática | `STONE_SPIT` `EYE_BEAM` `EL_SELLO` | **implementada** |
| 2 | LA MÁSCARA ESPECTRAL | 15→10 | 56×72 | flotante | `SPIRIT_WAVE` `DUELO_DE_ECOS` `MASK_PULSE` | **implementada** |
| 3 | LA RELIQUIA (3A/3B) | 10→5 | 32×32 | persecución / órbita | *se inyectan al sortear* | **implementada** |
| 4 | EL ESPÍRITU DEL SHAMAN | 5→0 | 64×80 | `spirit_float` | `RELIC_SURGE` `SPIRIT_FORM` `ANCIENT_CALL` `CONVERGENCE` `EL_OFRECIMIENTO` | **implementada** |

Hilo de identidad entre formas: **la máscara es siempre el punto débil**
(×2,5). Cambia todo lo demás; eso no. La transición limpia proyectiles (el
jugador debe poder mirar) pero conserva las marcas de EL SELLO.

### 3.3 Forma 1 — implementada

Piedra que escupe (parable), rayo ocular telegrafiado, EL SELLO (columnas que
graban marcas persistentes). El parry devuelve proyectiles con más daño del
que traían.

### 3.4 Forma 2 — implementada, con los guardianes pendientes

Tres ataques, tres respuestas: **SPIRIT_WAVE** se salta · **MASK_PULSE** solo
daña el borde del anillo (castiga la media distancia, premia pelear pegado al
punto débil; no parable a propósito) · **DUELO_DE_ECOS** se para (devueltos
pegan doble; lentos porque la ventana de parry es 0,2 s).

**Los guardianes pelean — implementado (2026-08-14, tarea #37; medido: 8
ecos en 40 s, daño combinado jefe+ronda 5,5/9 contra un maniquí quieto —
la misma presión total que el jefe solo, porque los i-frames absorben los
solapes; lo vigila `tests/test_guardianes_paburu.py`):**

Los tres guardianes son los espíritus del **venado, la serpiente y el
gavilán** — los jefes que el jugador ya venció, custodios de Paburu en vida
(GDD §41). Que peleen a su lado no es un añadido: es lo que el lore dice que
son. Y cada uno ataca con **el eco de su firma**, así la pelea final cita el
viaje entero del jugador:

* **El venado** — embestida fantasmal horizontal a media altura, recta y
  telegrafiada: se salta (eco de su CHARGE).
* **La serpiente** — orbe sinuoso que serpentea hacia el jugador, lento:
  se para con parry (eco del Rey Terciopelo).
* **El gavilán** — picada diagonal desde arriba, anunciada por la sombra en
  el suelo: se esquiva lateral (eco de su DIVE).

Reglas de presión: cadencia ≥6 s por guardián, escalonados entre sí y lejos
de MASK_PULSE. Moderado, no imposible — restricción explícita de diseño.

**El arte de los espíritus (rehecho 2026-08-14 tras la crítica «se ven
horribles»):** la primera hoja eran tres siluetas inventadas — bultos que no
se parecían a nadie, y un espíritu que no se reconoce no cuenta nada. Ahora:
el **venado se destila del sprite real** de su jefe (recolor espectral por
luminancia + jirones + halo); la **serpiente y el gavilán se dibujan a mano**
porque sus hojas resultaron ser tarjetas de relleno (se verificó mirando los
PNG) — la serpiente sobre una espina senoidal con los rombos de la
terciopelo y la cabeza en cresta, y el gavilán frontal con cinco plumas-dedo
por ala, cola en abanico y **la máscara ceremonial como lo más luminoso del
cuerpo**: el lore dice que esa máscara es la que después busca a Paburu
(§19 5.3) — el espíritu del gavilán es la máscara volando. Matices por
identidad: verde de monte, violeta de terciopelo, cian de cielo.

**No pueden morir; caen.** Ya están muertos: devolverle el orbe a la
serpiente con parry (o golpear a un guardián en su ventana) lo **tumba** —
se apaga unos segundos — y **el llamado de Paburu lo levanta**. Es la
estructura ritual (la caída y el llamado) contada con los personajes del
lore, sin tocarlo. Mecánicamente: una ventana de alivio que el jugador
aprende a fabricar; narrativamente: el anticipo de `ANCIENT_CALL` (§3.6) y
de la inclinación final — los que pelean contra ti son los mismos que al
final se despiden con respeto.

### 3.5 Forma 3 — LA RELIQUIA, aleatoria 3A/3B (tarea #31)

`relic_variant = random.choice(["gold", "black"])` — ya cableado. Cada partida
ve **una** de dos peleas; la rejugabilidad es el argumento del sorteo entero.

* **3A · La Pepita (gold) — persecución.** Pequeña (32×32), rápida, caza al
  jugador: embestidas en ráfaga con rebote en los muros del círculo, estela
  breve, pausa de vulnerabilidad tras 3 embestidas. Lección: moverse sin
  dejar de mirar.
* **3B · La Perla (black) — órbita.** Orbita un centro que se desplaza; el
  peligro es el anillo, no el centro. Radios que contraen/expanden con
  `suave()`, púas telegrafiadas, ventana de daño cuando la órbita se detiene.
  Lección: leer el ritmo, entrar y salir.
* **La arena escala (principio §0.2):** al entrar la Forma 3 se activan las
  plataformas interiores del círculo (dos cornisas laterales que en F1-F2 eran
  decorado): la reliquia domina el suelo, el jugador gana la vertical.

Técnica: los patrones se **inyectan** en `attack_patterns` al sortear (la
lista nace vacía a propósito) y `_patrones_de_la_fase()` los recoge sin tocar
el planificador.

### 3.6 Forma 4 — EL ESPÍRITU (implementada 2026-08-14, tarea #32)

| Patrón | Diseño |
|---|---|
| `RELIC_SURGE` | las DOS reliquias vuelven como satélites breves — la que no salió en F3 **debuta aquí**: nadie ve todo en una partida, todos lo ven todo en dos |
| `SPIRIT_FORM` | Paburu se desdobla; el gemelo espejo repite el último ataque con retardo de medio compás |
| `ANCIENT_CALL` | el llamado: levanta a los guardianes caídos y los tres cruzan la arena en procesión coreografiada (Lissajous ya implementado) — pasillos de esquive, no muro |
| `CONVERGENCE` | **el nivel es el arma, visto desde abajo**: los cuatro círculos del camposanto se abren sobre la catacumba y sus haces de luz caen dentro de la cámara — la plaza del ritual dispara a través de la tierra |
| `EL_OFRECIMIENTO` | el final ritual (§3.7) |

**Cómo quedó implementada (form4_attacks.py, 10 tests propios):**

* El Espíritu **flota** (vaivén senoidal 32 px @0,2 Hz, escala ×1,2 real vía
  AUD-257) y no es trampa de contacto. Su movimiento vive en `_post_update`
  junto al reloj de ataques — se midió que la máquina de estados heredada
  (RETREAT/HURT) les robaba el cuerpo a las formas libres y las dejaba
  caminando por el suelo; el arreglo curó también a la Forma 3.
* `RELIC_SURGE` trae **las dos** reliquias como satélites (órbitas de radio
  y sentido opuestos); `SPIRIT_FORM` refleja al gemelo que repite la ola
  desde el otro lado; `ANCIENT_CALL` **levanta a los custodios caídos** y
  ordena la procesión — tres pasadas a tres alturas, escalonadas 0,45 s,
  coreografiadas por la escena vía evento del bus; `CONVERGENCE` deja caer
  cuatro haces secuenciales desde la bóveda con pasillos garantizados
  (≥120 px, con test).
* **EL_OFRECIMIENTO está declarado en la fase pero fuera de la rotación** —
  sin método `_attack_` a propósito (y con test que lo impide): es la
  ceremonia. A cero de vida el Espíritu no muere: se alza invulnerable, los
  custodios se arrodillan, la sala se vacía, y a los 1,6 s lanza el
  **Juicio** — un anillo con el telegraph más largo de la pelea (2,2 s,
  anillos ámbar colapsando hacia el juez). Parry → «EL CAMPOSANTO TE
  ABSUELVE»; recibido → UN golpe y «JUZGADO — Y AUN ASÍ, EN PIE».
  `boss.absuelto` guarda la marca para el final. Las dos salidas, con test.

Herramientas nuevas del motor que esta forma usa: **`escala` de fase real**
(AUD-257 — el espíritu crece al bajar de vida: 1.0 → 1.15 → 1.3) y **fases
`invulnerable`** para la puesta en escena del cierre — siempre con algo que
hacer, nunca pausa vacía.

### 3.7 EL OFRECIMIENTO — el ataque-firma (implementado 2026-08-14)

El cierre adapta la estructura ritual —la caída colectiva y el fuego del
juicio—, **sin fase oculta ni vida sorpresa** (la investigación es clara: la fase extra no anunciada frustra;
el cierre ceremonial corto, no):

1. Al llegar a 0 la vida de la Forma 4, Paburu no muere: la arena se apaga,
   los tres guardianes se arrodillan, y suena el cuerno ceremonial — largo,
   solo.
2. Paburu se alza una última vez (fase `invulnerable`, ~10 s, escala 1.3) y
   **ofrece el juicio**: un único ataque total, telegrafiado con el compás de
   la canción, que cruza la arena entera.
3. **Parry** en la ventana → el juicio se vuelve contra él: final limpio,
   «el camposanto te absuelve» — el fuego del juicio se vuelve contra el
   juez, no contra el forastero.
4. Sin parry (esquivado o recibido) → Paburu cae igual, pero el jugador queda
   con 1 punto menos y la marca del juicio en la pantalla final. Se gana
   siempre; **cómo** se gana es la firma.

Un solo intercambio, aprendible en una partida, imposible de olvidar. Ese es
el momento que se cuenta al jurado — y al amigo.

**El EPÍLOGO (implementado tras la revisión exhaustiva — era la mejora A):**
el veredicto ya no mata en seco. Abre seis segundos coreografiados donde la
SALA responde al resultado antes de que ningún texto lo diga:

1. **La luz da el veredicto** — absuelto, la sala amanece hasta plena luz y
   los braseros arden altos; juzgado, la penumbra vuelve y los fuegos se
   achican. Dos finales visuales distintos, medidos en test.
2. **Los custodios se despiden** (GDD §204, por fin): venado, serpiente y
   gavilán, uno a uno con 0,6 s entre reverencias — se inclinan y se
   disuelven hacia ARRIBA. No es derrota: es reencuentro.
3. **El Espíritu asciende** 90 px con el smoothstep de todo el stage y se
   disuelve en **doce ánimas** que suben con deriva propia.
4. El mensaje final según la marca: «LA MÁSCARA DESCANSA» (absuelto) o
   «EL JUICIO QUEDÓ GRABADO» — y recién entonces la muerte real y el cierre
   del motor. `boss.absuelto` por fin tiene su pago en pantalla.

Cuatro tests propios (`TestElEpilogo`): despedida completa antes de la
muerte, la luz de cada veredicto, la disolución en ánimas.

**LOS SFX PROPIOS (implementados — era la mejora B):** tres muestras
recicladas cubrían quince ataques y el Juicio final sonaba al rayo ocular
de la Forma 1. Cinco sonidos sintetizados en `tools/gen_paburu_sfx.py`
(deterministas: senos, envolventes smoothstep, espectros inarmónicos para
la piedra — Unidad VI aplicada al audio) viven en `assets/sfx/bosses/`:

| Muestra | Momento | Carácter |
|---|---|---|
| `paburu_llamado` | ANCIENT_CALL y el arranque del epílogo | cuerno ceremonial 108 Hz, armónicos 2:3:4, vibrato tardío |
| `paburu_juicio` | la pregunta final se lanza | sub-grave 55→38 Hz que crece, batido desafinado encima |
| `paburu_custodio_cae` | parry que tumba a un guardián; los tres al arrodillarse | tercera menor descendente, casi un suspiro |
| `paburu_absolucion` | veredicto CON parry | do-mi-sol-do escalonado: la sala amanece también al oído |
| `paburu_sello` | EL SELLO (F1) y veredicto SIN parry | campana de piedra inarmónica — la marca queda grabada |

El cableado no toca el motor: el `SoundBank` carga todo `assets/sfx/` por
nombre de archivo, y la escena inyecta su reproductor en el jefe
(`boss.reproducir_sfx = _sfx_propio` en `_invocar_a_paburu`; `play_sfx`
respeta mute y volúmenes del usuario). El veredicto SUENA distinto según
cómo terminó — la misma regla que la luz. Seis tests (`test_sfx_paburu`):
contrato nombre↔archivo (un typo sería silencio invisible), inyección, y
los tres momentos con la muestra correcta.

### 3.8 Decisiones de producto

* **`skill_drop`: ninguno.** Es el jefe final; la recompensa es el final y la
  marca (o su ausencia). Un objeto lo abarataría.
* **Balance de referencia:** pelea a 20 golpes; jugador con 9 de vida. F2
  medida: 5,5 de daño a jugador quieto en 40 s — meta: ≤ mitad en movimiento.
  Cada forma más corta e intensa que la anterior (los umbrales 20/15/10/5 ya
  lo imponen).
* **Cuantización al compás (P2, estrella si da tiempo):** los inicios de
  telegrafiado de F4 alineados al compás vía `RelojMusical`. Espectáculo
  gratis; la equidad no cambia (los cooldowns mandan).

---

## 4. Verificación

| Suite | Qué sostiene |
|---|---|
| `test_cementerio_paburu.py` (17) | sorteo, círculos, disparadores, pozo, muros, puerta |
| `test_guardado_y_cadena[boss_paburu]` | la vida de zona no pisa el guardado |
| `test_audio_wiring` | sonidos emitidos vs lista de espera |
| `test_guia_del_motor` / inventario | las 4 especies documentadas (82 tipos) |
| **Por escribir** (#33) | arnés de las 4 formas: daño/duración por forma, transiciones, 3A y 3B por semilla, caída/levantamiento de guardianes, EL OFRECIMIENTO con y sin parry |

---

## 5. Fuentes de la investigación

* Principios de jefes (telegrafiado, fases, arena, ataque-firma):
  gamedesignskills.com, gamedeveloper.com («3 Elements That Every Great Boss
  Fight Needs», «Boss Battle Design and Structure»), game-wisdom.com.
* Ritmo que premia y no castiga: análisis de Hi-Fi Rush (frostilyte.ca) y
  Crypt of the NecroDancer (Game Design Deep Dive, gamedeveloper.com).
* Juego de los Diablitos de Boruca (Cagrúv rójc): Wikipedia es, UCR
  (ucr.ac.cr), Ministerio de Cultura y Juventud (mcj.go.cr), Delfino.cr,
  fases del juego según José Luis Amador (joseluisamador.info) — Tumbazón,
  resurrección por caracola, cacería y quema del toro.

---

## 6. AUDITORÍA FINAL (2026-08-14) — hallazgos PAB-NN

Con la disciplina del repositorio: cada hallazgo con evidencia ejecutada, y
cada uno o corregido con test o justificado con su porqué.

| ID | Hallazgo | Estado |
|---|---|---|
| PAB-01 | **Softlock de carga**: guardar en la catacumba y cargar reconstruía la sala sellada SIN jefe (el sorteo y `sellado` no persisten) — de reiniciar el juego | **CORREGIDO**: la reentrada dentro de la cámara rearma la pelea (jefe fresco, cura, sin cinemática). Test propio |
| PAB-02 | Brecha de checkpoints: 2.555 px | **CORREGIDO a 5 checkpoints** (spawn, pozo, galería I, galería II, catacumba): ningún tramo de superficie supera ~1.000 px. La vara de 500 px del calificador queda corta A PROPÓSITO: más densidad trivializa a los moradores — densidad vs tensión es una decisión, no un olvido |
| PAB-03 | **Cero coleccionables**: nada premiaba la curiosidad | **CORREGIDO**: el circuito del Mausoleo del Juicio — lápida falsa rompible → LA LLAVE DEL JUICIO → puerta sellada → cofre con vasija de corazón — más la Ofrenda de los Deudos en la plataforma alta del ascensor. Coleccionables 10/10 |
| PAB-04 | La máquina de estados heredada (RETREAT) robaba el cuerpo de las formas flotantes: Reliquia y Espíritu caminaban por el suelo | **CORREGIDO**: el movimiento de formas libres vive con el reloj de ataques, en el hook que corre en todos los estados. Test de flotación |
| PAB-05 | El arco completo no tenía verificación de punta a punta | **CORREGIDO**: `test_pelea_completa_paburu.py` mata al jefe con cadencia humana (1 golpe/s) a través de los 4 umbrales reales, en las DOS variantes y las DOS salidas del Ofrecimiento |
| PAB-07 | **Los TRES ataques de la Forma 1 rotos en producción**: `arena.py` conservó la geometría de la arena original (800×608 en el origen) a través de DOS rediseños — EL SELLO emergía en la superficie a 700 px de la pelea, el rayo moría al primer fotograma (cota `y≤608` con la pelea en y≈1200) y las piedras «tocaban suelo» al nacer. Invisible para los tests porque contaban lanzamientos, no posiciones | **CORREGIDO** en la revisión exhaustiva post-auditoría: `arena.py` reescrito a la geometría de la Sala + guardián de sincronía TMX↔constantes que revienta si el generador mueve la catacumba. Medido: rayo vive 3,1 s, piedras 3,1 s, sello emerge en y=1257, la F1 vuelve a hacer 5,5 de daño en 40 s |
| PAB-06 | Los arneses bajaban por el atajo de depuración: el cableado del bus real (foso → evento → descenso) no tenía guardián | **CORREGIDO**: E2E por `INTERACT_TRIGGER_FIRED` — la puerta desciende, el círculo no sorteado queda inerte |

**El arco, medido** (maniquí que golpea 1/s, ambas variantes):

| Variante | Arco total | F1 | F2 | F3 | F4+cierre | Daño recibido | Final |
|---|---|---|---|---|---|---|---|
| gold (Pepita) | 40 s | 8 s | 7 s | 18 s | 8 s | 5,0 / 9 | absuelto |
| black (Perla) | 38 s | 8 s | 7 s | 16 s | 8 s | 3,5 / 9 | absuelto |

La forma central es la más larga (las ventanas de la Reliquia mandan el
ritmo) y el cierre es corto — la curva que el diseño pedía. Un jugador real
tarda más y recibe menos: el maniquí no esquiva nada.

**Batería final:** 52 tests propios · validador TMX 0 errores · calificador
130/130 (100 %) · ruff limpio en todo el alcance del CI · suites del motor
que tocan el stage (guardado en cadena, humo de escenas, audio, inventarios
de documentación) en verde.

---

## 7. Hoja de ruta priorizada

La lista maestra tras la revisión exhaustiva (2026-08-14). Lo tachado del
P0 original ya vive en §3; lo del calificador (checkpoint 3, pozo, balsa,
mausoleo con llave/cofre) también está hecho y medido en §6.

**Hecho tras la revisión:**

| Mejora | Trabajo | Tarea |
|---|---|---|
| A | ~~El Epílogo del Juicio: despedidas, luz-veredicto, ascensión~~ **hecho** | #32 ✓ |
| B | ~~SFX propios: llamado, juicio, caída, absolución, sello (§3.7)~~ **hecho** | #40 ✓ |
| C | ~~BPM de «Judgment of the Ancestors»~~ **hecho**: 136 BPM medidos con librosa (los tres tercios del .ogg coinciden; intervalo 0,4436 s ± 0,0095). `bpm`/`compas` en el mapa → `RelojMusical` montado, la luz late al pulso (AUD-425, medido en escena), y los 3 RhythmBlocks de la Galería I pasan a `patron «xxx.»` con desfases 0/1/2 — la ola recorre los bloques a un pulso de distancia. Postmortem incluido: el primer intento («xxx.xxx.» con desfases 0/2/4) tenía período real 4 y dos bloques parpadeaban juntos; ahora hay test que lo impide (`test_ritmo_paburu`, 5) | #41 ✓ |
| D | ~~Poses por forma~~ **hecho**: 6 hojas nuevas (`gen_paburu_art_formas.py`, post-procesado del idle — retroceso+destello, casteo, ventana). Corrige de paso un defecto real: el framework mapea HURT a la clave literal «hurt» y golpear a la Máscara mostraba frames de la cabeza de piedra. Ahora: `mask_hurt`/`spirit_hurt` (retroceso que decae), `mask_cast`/`spirit_cast` (armadas por el PLANIFICADOR — todo patrón las hereda; ojos al blanco, boca goteando luz / oro ritual encendido), y `gold_open`/`black_open` — la ventana del motor HECHA VISIBLE (el estado que multiplica el daño ×4 no puede ser secreto; la Perla se agrieta en CLARO: negro apagado sobre cementerio negro no existe). Guardián anti-autoengaño: diferencia media por píxel ≥6 entre pose e idle (el primer `mask_cast` era indistinguible y todo estaba «en verde»). Tests `test_poses_paburu` (5) | #42 ✓ |

**Pendiente, en orden:**

| Mejora | Trabajo | Tarea |
|---|---|---|
| — | ~~Guion de la intro~~ **hecho**: auditoría post-catacumba. El movimiento salió ileso (alturas relativas al ancla — no había PAB-07). El guion sí estaba roto: «las marcas bajo sus pies» y «el del centro es Kavë» señalaban el círculo de la superficie; ahora señalan el columbario de la Sala, y el giro de Kavë mejoró con la mudanza (su nombre NO está en los nichos porque no murió esperando: fue juzgada — la diferencia exacta que atormenta a Paburu). Tildes y la ë verificadas glifo a glifo contra la fuente. Tests `test_intro_paburu` (2, con E2E de la cinemática entera en la catacumba) | #43 ✓ |
| — | ~~Skin de mecánicas del motor~~ **hecho a la medida de lo posible**: `skins.py` subclasea `DrawingSystem` (patrón `intro.py`/`CutsceneAction`, cero framework) y la escena instala `DibujoDelCamposanto` — puerta de mausoleo (sillería + dintel + cerradura de oro), verja de hierro, arca de reliquias (madera + flejes de oro, pariente del pectoral). Recogibles conservan `icon_color` (AUD-234). LÍMITE documentado con motivo: las mecánicas del ECS (balsas, bloques rítmicos, resortes) se dibujan en un punto fijo post-luz sin hook — duplicar `dibujar_ui` sería un fork frágil y sobrepintar desde `Scene.draw` cae encima del HUD. Mitigado: los bloques rítmicos ya laten con la canción (C). Tests `test_skins_paburu` (3: instalación, distinción por píxel, contrato) | #44 ✓ |
| — | ~~Ritual sembrado~~ **hecho**: el recorrido ANUNCIA el rito. (1) Máscaras de los tres guardianes colgadas de la verja (tiles 65-67, fila 9 del atlas; rotan por vano — venado/serpiente/gavilán, los rostros que bajan a pelear en la F2). (2) El altar del llamado con la caracola muda (tiles 68-70) a la SALIDA del pozo — el orden del rito en la geografía: el agua, el llamado, la prueba; postmortem: el primer intento lo puso en el «claro» del camino final que de claro no tenía nada (mausoleo IV + resorte), visto en zoom de captura real. (3) Cuatro `MessageTrigger_Once` que siembran lo que se juega después. (4) `Cutscene` TMX de entrada (punto, al empezar): fundido+temblor, corta a propósito y SIN órdenes de cámara (lección PAB-07). (5) El vigilante espectral del camino final: `Guard` del motor (cono+alerta); el castigo lo cablea la escena — ser visto convoca una picada de gavilán con respiro de 5 s, sigilo opcional. BONUS: el guardián de tests cazó la fuga «MascaraBrunca»/«Guardián de máscara brunca» (cultura real en TMX y bestiario) → renombrado a Tilawa en identificadores y textos visibles; la investigación real sigue citada solo aquí (§referencias). Tests `test_ritual_paburu` (5) + arneses con `_apagar_cinematicas` (la entrada bloqueante corría el reloj de los arneses de combate) | #45 ✓ |
| — | Playtest humano + rendimiento (F11); el jugador prueba, el código ajusta | #46 |
| — | ~~El aviso de lore tapaba la entrada del jefe~~ **hecho** (AUD-475): `hide()` de la caja al descender | R2-4 ✓ |
| — | ~~«Los murciélagos no van por el mapa»~~ **hecho** (AUD-476): `SineFlight` rebota a ±96 px del origen; ahora el ancla viaja (305 px medidos) y baja hacia el jugador al detectarlo, sin el picado que se rechazó | R2-5 ✓ |
| — | ~~Falta saber CUÁNDO ataca el jefe~~ **hecho** (AUD-477): anillo que colapsa sobre el jefe mientras `_pose_cast_t` vive — un tell del cuerpo, común a las cuatro formas, que se calla en el epílogo. El BALANCE de los ataques sigue pendiente de una partida | R2-9 (legibilidad) ✓ |
| — | ~~Las plataformas «demasiado genéricas»~~ **hecho** (AUD-472): el nivel se apoyaba en UNA cornisa estampada 40 veces. Cuatro familias de mueble en el tileset (sarcófago volcado, viga del techo hundido, costillar, plañidera caída), 12 tiles nuevos, repartidas por tramo y por círculo. En un cementerio no hay cornisas: hay cosas que quedaron ahí | AUD-472 ✓ |
| — | ~~Población: segundo recorte~~ **hecho** (AUD-473): 12 → 8. Cada especie conserva su mejor momento y pierde los ecos | AUD-473 ✓ |
| — | ~~Los ecos se mueven~~ **hecho** (AUD-474): galope del venado, aleteo del gavilán, latido y rombos girando del orbe | AUD-474 ✓ |
| — | ~~EL CUELGUE tras un golpe~~ **hecho** (AUD-467): el hit-stop (0,05 s con `time_scale` a 0 por golpe conectado) se drena dentro de `_update_gameplay`, que NO corre durante una cinemática. Golpe + escena = reloj en cero para siempre (medido: 10 s después seguía en 0,0). La escena lo drena cuando sabe que el padre no lo hará. Reportable al profesor | AUD-467 ✓ |
| — | ~~El ahogado salía del pozo~~ **hecho** (AUD-468): en alerta `EnemyFlying` persigue en X y sigue la Y; ahora la escena le inyecta el rect de su agua y vuelve dentro tras cada movimiento. Caza en el pozo, no fuera | AUD-468 ✓ |
| — | ~~«Una luz en el personaje»~~ **hecho** (AUD-469): había DOS — el farol del stage y el foco que el MOTOR pega al jugador en `_update_lighting`. Las dos apagadas; `LUZ_CAMINO` 0.50→0.58 y los charcos los ponen los cuencos de fuego, que se ven | AUD-469 ✓ |
| — | ~~La población de enemigos~~ **hecho** (AUD-470): 19 → 12. Los recortes anteriores contaban los que se VEÍAN, con once enterrados; cada tramo conserva una pregunta y pierde las repeticiones | AUD-470 ✓ |
| — | ~~Los ecos de los guardianes «muy toscos»~~ **hecho** (AUD-471): eran primitivas opacas (elipse, círculo, rombo). Ahora superficies con alfa sumando luz, tres capas y silueta reconocible: cornamenta de tres puntas, cuerpo con los rombos de la Terciopelo, alas de cinco plumas con la máscara ceremonial encendida. Telegrafiados rehechos: el carril del venado dice la ALTURA, el aro del orbe dice DÓNDE | AUD-471 ✓ |
| — | ~~AUD-461 — la capa del jefe muere en la ruta de GPU~~ **hecho** (2026-08-16): `App` no llama a `draw()` en una escena con ruta de GPU (AUD-343/371) y toda la capa del stage —intro, guardianes, ataques de la ronda, ecos del vigilante— vivía en un override de `draw()`. En la máquina real (moderngl) la intro corría invisible (leída como congelamiento, R2-3), y la ronda de la F2 golpeaba sin dibujarse (parte del «todo horrible» de R2-9). Reproducido y verificado en un contexto GL real (Mesa), pasada a pasada: la LUZ siempre estuvo bien. La capa ahora se reparte entre `dibujar_ui` (GPU, tras la luz) y `dibujar_mundo` (software/arneses). Tests `test_capa_gl_paburu` (4, todas fallan contra el código viejo) | R2-1 ✓ |
| — | ~~Señal del círculo sorteado (§2.2)~~ **hecho** (2026-08-16): brasas + halo solo en el elegido; se apagan al descender. Tests `test_senal_circulo_paburu` (5) | R2-8 ✓ |
| — | ~~Los moradores estaban enterrados~~ **hecho** (AUD-462): el motor cambió la convención del TMX en AUD-455 (la `y` es el borde SUPERIOR, no los pies) y este generador seguía escribiendo `FLOOR_Y`: las 11 máscaras y sukias tenían el cuerpo entero bajo tierra. `SOBRE_EL_SUELO()` en el generador; guardián medido sobre la escena viva, no sobre el XML | AUD-462 ✓ |
| — | ~~«Color caca»: la hora y la luz robada~~ **hecho** (AUD-463): `dusk` teñía todo de ocre (el motor aplica el tinte de la hora a la imagen entera) → `night`; y `_aplicar_hora` sobrescribía la penumbra de la escena cada fotograma, así que las rampas del nivel no existían → la escena manda sobre su luz y conserva del reloj lo que sí quiere. `MIN_AMBIENTE` 0.45→0.12 con motivo escrito | AUD-463 ✓ |
| — | ~~Cuatro avisos de lore eran dos de más~~ **hecho** (AUD-464): la caja del motor tapa un tercio de pantalla; quedan dos, de una línea, donde el jugador ya está parado mirando algo | AUD-464 ✓ |
| — | ~~«Ese poder azul raro»~~ **hecho** (AUD-465): eran los marcadores de posición del motor para `BloqueRitmico` (lila), `PlataformaMovil` (gris) y `Resorte` (amarillo). `skins.py` decía que no se podían sustituir sin forkear el framework; AUD-461 dio el hook (`dibujar_ui` ya sobrescrito) y ahora la piel se dibuja encima: losa grabada, madera atada, bronce con cuñas. Tests `test_piel_mecanicas_paburu` (4) | AUD-465 ✓ |
| — | ~~Los cuatro círculos eran la misma pieza~~ **hecho** (AUD-466): `muebles_del_circulo` devolvía las mismas seis medidas para los cuatro — simetría heredada de cuando la pelea ocurría arriba. Ahora `PERFILES_DE_CIRCULO`: cornisas largas y bajas (I), pedestales estrechos (II), galería corrida con apoyo descentrado (III), tejados escalonados (IV). Postmortem: subir también los aleros rompía la cadena del analizador hasta la catacumba (124/130); los aleros se nivelan y la variedad vive en las cornisas | AUD-466 ✓ |
| — | ~~Las marcas del sello se acumulaban sin tope~~ **hecho** (AUD-496): `SelloDeSuelo.engrave` añadía una rotación por invocación y ninguna salía nunca, así que al llegar a Paburu la pantalla se llenaba de rayas verdes. `MARCAS_MAXIMAS = 4`, en cola | AUD-496 ✓ |
| — | ~~Los custodios seguían en las Formas 3 y 4~~ **hecho** (AUD-497): el lore dice que la Danza de los Custodios es el acto de la **Forma 2**, y aparecían también en la 3 y machacaban en la 4. Ahora su presencia es exclusiva de `FORM_MASK`; en la 4 sólo cuando `ANCIENT_CALL` los convoca explícitamente (procesión u ofrecimiento), y el guard va DESPUÉS del bloque que los arrodilla para no romper el ofrecimiento. Medido: F2 presencia=1,0 · F3 y F4 presencia=0,0 | AUD-497 ✓ |
| — | ~~EL CUELGUE DEL MURCIÉLAGO, por fin~~ **hecho** (AUD-498): tercer reporte del mismo congelamiento («la música siguió sonando pero el juego en freeze»). No era el hit-stop en sí ni AUD-467/479 — es que **el bucle del motor deja de llamar a la escena**: `pasos_fijos()` acumula el delta ESCALADO, con el hit-stop la escala vale 0, el acumulador no crece y el generador devuelve **cero pasos**, así que `scene_manager.update` no corre y nadie drena el contador. Abrazo mortal. AUD-467/479 no podían funcionar porque ambos viven en `update()`. Reproducido con el bucle real: 180 fotogramas, 0 pasos. El arreglo toma el latido prestado de `dibujar_ui` (que sí corre siempre) y drena con tiempo real sólo cuando `clock.dt == 0`. Tests `test_reloj_atascado_paburu` (3, fallan sin el arreglo). Bug BLOQUEANTE del motor: afecta a cualquier entrega | AUD-498 ✓ |

| — | ~~#50 — el portador con rostro~~ **hecho** (Ronda 14): el héroe del concept de Alejandro como personaje jugable de ESTE stage — hojas propias en `assets/sprites/heroe_tilawa/` (talladas por `tools/gen_heroe_tilawa.py` como muñeco de partes: capa, bufanda, correaje, vendas, melena) + swap de `_sprite_frames` en la escena. Cero motor; `assets/sprites/player` intocado porque lo regenera el script del profesor. La Forma del Ánima (#49) se talla sobre el héroe. Detalle en `PENDIENTES.md` Ronda 14 | #50 ✓ |
| — | ~~La ronda 13 del playtest (2026-08-17)~~ **hecha entera** — detalle en `PENDIENTES.md` (Ronda 13): mecate con agarre REAL (`TrepandoState` auto al caer al foso; ARRIBA/ABAJO/SALTO mandan, resbala a 70 px/s sin tocar nada), fuera la liana huérfana de la entrada, resorte al bolsillo del otro lado del foso (4048, -700 — el bolsillo era una trampa medida), peldaños del brocal en el pozo (la salida ya no exige sostener el salto), solapes visuales fuera (`Camino_04/05` fundidas, `Losa_Hundible_02` → 2968), ofrendas dibujadas como pila de monedas, letrero «G AGARRARSE» junto a la tirolesa, **LAS NUBES** que derivan (D-01·K) y **LA FORMA DEL ÁNIMA** (#49: el ulti viste la máscara tilawa 6 s — verde ánima, jamás dorada; cero mecánica). Verificado con bot geométrico de punta a punta sin atascos y 18 tests nuevos | R13 ✓ |
| — | ~~El sorteo cortaba el nivel~~ **hecho** (D-01 fase A): el disparador de un círculo mide 416 px pegados al suelo, así que el sorteo no elegía dónde te atrapaban sino **dónde terminaba el nivel** (33/47/66/85 %, media 57 %). La tirolesa (3840), el resorte (3952) y la puerta (4000) quedaban detrás del corte en las CUATRO partidas posibles: contenido intacto e inalcanzable. Ahora la catacumba se entra por su boca, al final del camino, bajando por el **mecate del sepulturero** (`Vine` de 736 px) — y se baja cuando uno decide. Los círculos conservan sus perfiles y sus muebles; pierden la trampa. Hallazgo del motor por el camino: **ningún sistema dibuja las lianas**. Tests `test_acceso_catacumba_paburu` (7) | D-01·A ✓ |

**Aceptado con motivo (no son tareas):** el «PHASE 4» del HUD muestra el
TOTAL de fases (rareza del motor, `hud.py`, igual en los otros jefes);
`sombras_proyectadas` apagado (postmortem en el generador); el ritmo quedó en 8/8: la
posición celeste del NextTrigger metía 1.353 px fantasma en la cadena de
checkpoints (`analyse_checkpoints` incluye la salida y ordena por (x, y));
ahora está enterrado en la losa de la antecámara, hay 12 checkpoints con
hueco máximo de 480 px (incluido el del foso, a media caída del descenso
de 704 px) y los pedestales del círculo II aportan el salto exigente que
la geometría pedía — la única pareja de SÓLIDOS saltables (las cornisas
one-way no cuentan para el analizador). Guardián: `test_nota_paburu`.
