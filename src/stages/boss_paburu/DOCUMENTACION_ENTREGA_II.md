# Documentación de entrega — Evaluación Práctica II

> La «documentación breve» que pide el §8 de la asignación actualizada
> (2026-08-27), en su mismo orden: Descripción → Computación Gráfica →
> Testing. Cada afirmación trae el archivo donde vive, para poder
> **explicar y defender** el trabajo (§7 y §10). El detalle largo está
> en los documentos que se citan; este es el mapa.

---

## 1. Descripción

**Autor.** Alejandro Josué Rodríguez Zamora.

**Nombre.** Stage 4-2 — *El Cementerio Sagrado* y su jefe final,
**El Gran Shamán Paburu** (nivel + jefe en una sola pieza).

**Objetivo.** Cruzar el camposanto de noche, reunir las **Cuatro
Ofrendas** (pavesas de fuego, una por tramo), encender los cuatro
círculos ceremoniales para abrir la Losa del Juicio, y descender a la
catacumba a rendir el juicio ante Paburu: una pelea de **4 formas +
epílogo**.

**Concepto.** Cultura ficticia **tilawa** (lore propio, sin culturas
reales — `GDD.md` §2, `docs/65_EL_LORE_EXTENSO.md`). La tesis del
nivel: *presentarse ante el juez es una decisión* — todo el camposanto
es ida y vuelta, y la única puerta de un solo sentido es el descenso.

**Mecánica principal.** El **rito de las Cuatro Ofrendas**: recoger
pavesas → encenderlas en los círculos (cada uno prende cuatro luces
reales: «la recompensa por explorar es poder ver») → la losa sellada
cede con la cuarta. En el jefe, el **ulti** transforma al portador en
la **Forma del Ánima** (máscara tilawa, 6 s).

**Ejecución.** `jugar_paburu.bat` o
`.venv\Scripts\python.exe main.py --boss boss_paburu`.

---

## 2. Computación Gráfica — dónde y cómo se aplicó cada contenido

### Curvas y modelado

- **Spline de Catmull-Rom** — las ánimas del sello (Forma 1,
  `form1_attacks.py`, clase `SealAnima`): cada luz sube de su marca y
  se curva hacia el centro siguiendo una Catmull-Rom de 4 puntos de
  control (`CurveTools.catmull_rom` del motor). Se eligió Catmull-Rom
  y no Bézier porque **pasa por** sus puntos de control: el ánima
  arranca exactamente en su marca y muere exactamente en el centro.
  El porqué completo, con fórmulas, en `README.md` §4.5.
- **Curvas de Lissajous** — los guardianes espectrales
  (`guardianes.py`): `x = sin(ωx·t+φx)`, `y = sin(ωy·t+φy)` con
  frecuencias **no conmensurables**, así la curva nunca se cierra y el
  vuelo no se memoriza.
- **Tiro parabólico** — `STONE_SPIT` (Forma 1): cinemática integrada
  explícitamente (no una curva pre-muestreada), resolviendo el tiempo
  de vuelo para que el arco sea legible a cualquier distancia
  (`README.md` §4.2).
- **Elipse** — la geometría del sello (SEAL_RX/RY, `README.md` §4.3) y
  los aros de aviso de los ecos.
- **Modelado** — el héroe tilawa es un **muñeco de partes** (capa,
  piernas, torso, brazos, cabeza, bufanda — `tools/gen_heroe_tilawa.py`)
  que compone 9 hojas de animación y su Forma del Ánima con las mismas
  piezas; el **portón** es un arco de medio punto con dovelas, clave y
  enjutas (63 tiles), y el **mausoleo** un dibujo único de 80×128
  rebanado en 40 tiles — modelado primero, retícula después.
  Proporción y escala **medidas**: sprites 32×32, envolvente del salto
  91/104 px, huecos ≤42 px; el mapa entero se organiza contra esos
  números (`DISENO_NIVEL_Y_JEFE.md`).

### Representación de escenas

- **Composición y profundidad por capas**: estrellas (lo más lejano,
  parallax propio) → luna → **nubes que derivan** (parallax 0.28–0.44)
  → fondo → juego → niebla baja. Z-order documentado en `README.md`
  §5.2.
- **Jerarquía visual**: el faro de brasas sobre la boca es la única
  señal cálida al fondo del camino; los cuencos encendidos marcan qué
  círculo ya ardió (los apagados humean — se ve de lejos cuál falta).
- **Navegación**: veladoras-checkpoint como migas de pan, letrero
  «G AGARRARSE» en la tirolesa, mecánica distinta por tramo como
  brújula (regla del ritmo, `DISENO_NIVEL_Y_JEFE.md` §2.6).
- **Cámara**: banda de superficie, **travelling del descenso** (la
  cámara persigue al portador foso abajo y aterriza exactamente en el
  encuadre de la pelea — empalme sin corte, Ronda 16) y encuadre fijo
  del duelo.

### Color y transparencia

- **Paleta intencional**: noche fría (azules, piedra) con el **fuego
  como único acento cálido**, racionado a propósito — farolitos al
  entrar, la boca ardiendo al final (el «racionador de oro/fuego» es
  un test permanente que impide que el acento se derrame).
- **Transparencia real por alfa**: nubes de 12 panzas a alfa 15
  desenfocadas, niebla del camposanto, halos de pavesas y veladoras,
  velos de las ánimas de las tumbas (alfa normal, no aditivo — un blit
  aditivo no sabe dibujar ojos oscuros), jirones verdes del ulti,
  polvo de la apertura de la losa, luces `LightSource` del motor en
  los cuencos.
- **Contraste al servicio del gameplay**: el único ataque parable de
  la Forma 4 es también el más brillante — el color dice qué mirar.

### Texturas

- **Tileset propio** del mapa (`assets/maps/boss_paburu/`), generado y
  versionado por `tools/gen_paburu_tmx.py`: sillería, escombro,
  musgo que solo crece sobre piedra (alfa > 0 — cero píxeles
  flotando), mausoleo y portón rebanados en tiles.
- **Hojas de sprites** 32×32: 9 del héroe + 9 de la Forma del Ánima
  (`assets/sprites/heroe_tilawa/`) + 4 retratos 22×22 del HUD, todas
  cumpliendo las convenciones medidas del motor (pies en fila ~24 en
  cuclillas, caído apoyado en fila 31).
- **Correspondencia textura↔objeto**: las mecánicas del motor van
  **vestidas** por `skins.py` sin tocarlo — las monedas se dibujan
  como pilas de ofrenda, la cerradura como losa de sillería, los
  checkpoints como veladoras.

### Animación

- **Estados del jugador**: 26 estados de `PlayerState` cubiertos con 9
  hojas físicas (idle 4 / walk 8 / jump 4 / fall 3 / crouch 3 /
  ataques 6 y 10 / hurt 4 / die 8), con transiciones del motor.
- **La transformación del ulti**: la Forma del Ánima viste al héroe
  6 s con latido, levitación (+2 px con charco de luz) y corona de
  jirones a 26/s; la muerte lo desviste.
- **Animación ambiental sincronizada**: llamas y humo de los cuencos,
  brasas orbitando al portador, estrellas que titilan con fase propia,
  nueve tumbas con relojes distintos (11–17 s: el camposanto nunca
  repite el mismo segundo), nubes a la deriva.
- **Integración con el gameplay**: la galería rítmica se cruza al
  compás de sus bloques; cada ataque del jefe telegrafia con el cuerpo
  antes de golpear (AUD-477); el sello anima la mecánica estrella de
  la Forma 1.

*Nada de lo anterior se incorporó «para cumplir»: cada recurso tiene
su porqué anotado en el registro de rondas de `PENDIENTES.md`.*

---

## 3. Testing

**Pruebas realizadas.**

- **256 tests automatizados propios** del stage (se ejecutan con
  `pytest tests/ -k paburu`), incluyendo arneses que *juegan* el mapa
  real: un bot que recorre el nivel de punta a punta, caminantes
  geométricos que miden cada salto, el **auditor del respiro del mapa**
  (ningún solape ni roce < 8 px entre piezas, las móviles por su
  carril barrido) y el racionador de color.
- Validadores del profesor: `grade_stage` **130/130**, `grade_boss`
  **100/100**.
- **21 rondas de playtest → corrección** documentadas una a una en
  `PENDIENTES.md` (el ciclo VERSIÓN → PRUEBA → PROBLEMA → CORRECCIÓN →
  NUEVA PRUEBA → MEJORA que pide el §6, con capturas por ronda en
  `capturas_sesion/`).

**Problemas encontrados y correcciones (los emblemáticos).**

- La tirolesa «nunca funcionó»: tres causas apiladas — tecla G nunca
  anunciada (→ letrero), radio de enganche 18 px (→ 30, medido), y un
  **bug del motor** (la gravedad se acumula durante el viaje y hundía
  al jinete ~80 px bajo el cable, colándolo al foso por debajo de la
  losa sellada) → sujeción por re-proyección desde la escena (R18).
- El nadador no salía del pozo tocando el salto (el bot moría ahí a
  los 25 s) → peldaños del brocal (R13).
- Los círculos con `una_vez` se consumían al cruzarlos sin pavesa =
  nivel incompletable → disparadores reutilizables con dedupe (R16).
- Morir re-llama `on_enter` y apagaba el rito entero → estado del rito
  reentrante (R16, cazado por `test_morir_no_apaga_nada`).
- Nueve costuras a 0 px que se leían como piezas incrustadas →
  auditor sistemático + ≥8 px de aire, convertido en test permanente
  (R17).
- El HUD seguía mostrando el retrato del personaje viejo → retratos
  propios inyectados (R14).

**Resultado.** El nivel es completable de punta a punta sin atascos
(verificado por bot y pendiente de la pasada humana final); **13 bugs
del motor** encontrados, reproducidos y documentados en
`BUGS_DEL_MOTOR.md` — 11 ya adoptados por el profesor en el motor v2;
el nº 12 (gravedad en `TirolesaState`) y el nº 13 (el combo cuenta
botonazos, no golpes) pendientes de reportar.

---

## 4. Uso de IA (§7 — para poder defenderlo)

La IA se usó como herramienta de apoyo en depuración, implementación y
auditoría, siempre bajo el ciclo *medir antes de teorizar*: arneses y
capturas primero, cambio después, test permanente al final. Las
decisiones son defendibles con sus porqués escritos: por qué
Catmull-Rom y no Bézier (`README.md` §4.5), por qué radio 30
(medición del enganche en salto), por qué la losa a ras (el escalón de
16 px clavaba al caminante, medido en x=3990), por qué alfa 15 en las
nubes (las elipses duras parecían platillos). El registro completo de
qué se probó y por qué se decidió cada cosa está en `PENDIENTES.md`;
la defensa matemática, en `README.md` §4.

---

## 5. Lista de verificación (§10) — estado

| Punto | Estado |
|---|---|
| El proyecto ejecuta / el nivel carga / el recorrido funciona | ✔ (bot de punta a punta) |
| Colisiones e interacciones | ✔ (256 tests + auditores de respiro y apoyo) |
| Curvas y/o modelado | ✔ (§2 de este doc) |
| Escena, color, transparencia, texturas, animaciones | ✔ (§2) |
| Pruebas / problemas / correcciones | ✔ (§3; 18 rondas) |
| Documentación | ✔ (este documento + los citados) |
| Evidencia | capturas ✔ (`capturas_sesion/`) · **video pendiente (#46)** |
| El estudiante puede explicar y defender | este doc es la chuleta — **requiere la pasada humana** |
