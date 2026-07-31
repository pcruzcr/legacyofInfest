# GDD — El Gran Shaman Paburu
## Stage 4-2 · Boss Final de Legacy of InFest

**Autor:** Alejandro Josué Rodríguez Zamora · **Versión:** 2.0 — diseño cerrado hasta EP3
**Asignación confirmada:** Solo Stage 4-2 (arena del combate). Movesets del profesor = sugerencias; el lore es lo obligatorio.
**Canon base:** `17_BOSS_SPEC` §6, `16_WORLD_DESIGN` §6, `19_NARRATIVE_AND_LORE` §2/§4/§5.4, `20_ASSET_BIBLE`

---

## 1. Pilares de diseño

Tres frases que resuelven cualquier duda futura. Si una idea nueva no sirve a alguna, se descarta.

1. **Paburu no es un enemigo, es un examinador.** Cada ataque pregunta algo. Nada es crueldad gratuita.
2. **La arena recuerda.** El escenario cambia durante el combate y al final cuenta una historia que nadie narró en voz alta.
3. **Ver es el verbo final.** El juego entero trata de observar (La Perla amplifica la percepción). El clímax exige mirar, no reaccionar.

---

## 2. Lore ampliado (autoría propia sobre el canon)

### 2.1 El duelo de Paburu — por qué está roto
El canon dice que Paburu fue "corrompido por un duelo antiguo" y nunca explica cuál. Aquí se define:

Hace siglos, antes de que las reliquias existieran como amenaza, Paburu aplicó **esta misma prueba** a alguien de su propio pueblo: una joven portadora llamada **Kavë**. Paburu la juzgó indigna. Fue severo — más de lo necesario, porque temía equivocarse. Kavë murió en la prueba.

Después descubrió que sí era digna. Que el error fue suyo.

Por eso selló las reliquias y se selló a sí mismo: no para castigar al mundo, sino porque **no confiaba en su propio juicio**. Los siglos de espera no fueron vigilancia — fueron penitencia. Cuando John y Jin llegan, Paburu no está furioso: está **aterrado de volver a equivocarse**.

Esto reescribe el combate entero. Cada forma es un intento de juzgar sin repetir el error:
- **Forma 1 (Piedra):** juzga sin mirar — ojos cerrados, ataques ciegos y mecánicos. Es como juzgó a Kavë.
- **Forma 2 (Máscara):** juzga con la tradición — invoca lo que ya venciste para verificar si fue mérito o suerte.
- **Forma 3 (Reliquia):** deja que las reliquias juzguen por él — se lava las manos. Por eso es aleatoria: ni él sabe qué va a pasar.
- **Forma 4 (Espíritu):** juzga como él mismo, cara a cara. Y ahí hace lo que no hizo con Kavë: **da una oportunidad**.

### 2.2 Las marcas del cementerio
Las marcas grabadas en la piedra del cementerio son **nombres**: cada portador que esperó la prueba y nunca llegó a rendirla, más Kavë al centro. Durante el combate, el ataque "El Sello" las va grabando en el piso de la arena. Al terminar la pelea, el sello está completo y legible.

### 2.3 Los tres espíritus
El venado, la serpiente y el gavilán **fueron los guardianes de Paburu en vida** — los que custodiaban el cementerio junto a él. Llevan siglos esperándolo tanto como él esperó a los portadores. Por eso en la secuencia final se inclinan: no es sumisión, es reencuentro.

---

## 3. La arena — El Cementerio Sagrado

### 3.1 Croquis funcional

```
  ╔══════════════════════════════════════════════════════════╗
  ║   cielo púrpura-negro · luna velada · niebla espectral    ║  BG_Far
  ║                                                           ║
  ║   ▲ silueta      ▲ silueta        ▲ silueta               ║  BG_Mid
  ║    venado         serpiente         gavilán               ║  (los 3 guardianes,
  ║                                                           ║   translúcidos, observan)
  ║                                                           ║
  ║ ┌──┐                                              ┌──┐   ║
  ║ │▓▓│  ═══════[ P L A T A F O R M A ]═══════       │▓▓│   ║  ← plataformas one-way
  ║ │▓▓│              (altura media)                   │▓▓│   ║    (esquivar EYE_BEAM)
  ║ │▓▓│                                               │▓▓│   ║
  ║ │▓▓│         ◆ ZONA DEL SELLO ◆                    │▓▓│   ║  ← el centro: aquí se
  ║ │▓▓│      (las marcas se graban aquí)              │▓▓│   ║    graban las marcas
  ║ └──┘                                              └──┘   ║
  ║ ██████████████████████████████████████████████████████   ║  ← suelo de piedra
  ╚══════════════════════════════════════════════════════════╝
     ▲ refugio                                    ▲ refugio
     izquierdo                                    derecho
     (CONVERGENCE)                                (CONVERGENCE)
```

**Dimensiones:** 800×600 px de pantalla; arena de ~1200×600 px (cámara con leve scroll horizontal, no un mapa largo).

**Elementos:**
| Elemento | Función mecánica | Función narrativa |
|---|---|---|
| Suelo de piedra central | Superficie principal de combate | Donde se graba el sello |
| 2 plataformas one-way (altura media) | Esquivar EYE_BEAM bajo/alto; verticalidad en Forma 4 | Lápidas caídas convertidas en puentes |
| 2 refugios laterales (nichos) | Única cobertura ante CONVERGENCE | Tumbas de los guardianes |
| Cuencos de fuego (4, decorativos + luz) | `LightSystem` — iluminación dinámica | Ritual encendido para la prueba |
| Fondo: siluetas de los 3 espíritus | Ninguna (BG_Mid, parallax) | Testigos; se "activan" en la Forma 2 |

**Paleta canónica (Asset Bible):** cielo púrpura-negro `#1a0d26` · piedra pálida `#c8c3b8` · verde espectral `#00c864` · dorado `#e8b12c` · negro perla `#0d0d14`.

### 3.2 Regla de composición
La arena empieza **vacía y oscura**. Con cada forma se enciende un cuenco de fuego más y aparecen más marcas en el piso. Al llegar a la Forma 4, el escenario está completamente iluminado y el sello es visible. **El escenario se ilumina a medida que Paburu se revela.**

---

## 4. El combate — 4 formas

**Vida total:** 20 corazones (5 por forma). **Vida del jugador:** 5 (según el motor).
Todos los números son punto de partida; se ajustan con playtesting.

---

### FORMA 1 — "La Cabeza de Piedra" (20 → 15)
> *Juzga sin mirar.*

**Visual:** Cabeza colosal de piedra verde precolombina (64×64), semienterrada en el centro. Ojos cerrados. Al comenzar el combate, se abren: verde brillante. Inclinación ±8px como única animación de movimiento.
**Movimiento:** Estática. Toda la presión viene de los patrones.
**Efecto (U-V):** `ColorTools.apply_tint(superficie, (0,120,40))` — tinte verde espectral permanente.

| Patrón | Cada | Descripción | Daño |
|---|---|---|---|
| `STONE_SPIT` | 4 s | Escupe 3 proyectiles de piedra en arco (separación 15°). Trayectorias parabólicas. | 0.5 c/u |
| `EYE_BEAM` | 8 s | Rayo horizontal de ambos ojos, 8px de alto, 200px/s. Telegraph: los ojos brillan 0.5 s antes. Se esquiva subiendo a plataforma o agachándose. | 1.0 |
| **`EL SELLO`** ★ | 10 s | **[Reemplaza GROUND_SLAM]** Paburu no golpea: *reclama*. Emergen 5 columnas de piedra del suelo en posiciones que dibujan un fragmento del sello ceremonial. Telegraph: grietas luminosas 0.8 s antes. Al retraerse dejan **marcas grabadas permanentes** en el piso. | 0.5 |

★ = diseño propio

**Transición 1→2:** La piedra se agrieta. De las grietas emergen las tres siluetas espectrales (venado, serpiente, gavilán) que fluyen hacia el centro y forman la figura de la Forma 2. La cáscara de piedra cae. *Se enciende el primer cuenco de fuego.*

---

### FORMA 2 — "La Máscara Espectral" (15 → 10)
> *Juzga con la tradición.*

**Visual:** Figura espectral alta hecha de energía verde (56×72). Donde iría el rostro: una máscara Tilawa flotante, translúcida.
**Punto débil:** SOLO la máscara (hurtbox 40×40) recibe daño. El cuerpo es invulnerable.
**Movimiento:** Deriva flotante — onda senoidal vertical (amplitud 20px, 0.3 Hz) + desplazamiento horizontal a 40px/s.
**Efecto (U-VII):** `FilterTools.adjust_brightness(máscara, 0.8 + 0.4*sin(t*3))` cada frame — brillo respirante.

| Patrón | Cada | Descripción | Daño |
|---|---|---|---|
| `SPIRIT_WAVE` | 5 s | Onda de energía por el suelo (se esquiva agachándose) O por el techo (se esquiva saltando). **Alterna.** | 0.5 |
| **`EL DUELO DE LOS ECOS`** ★ | 12 s | **[Reemplaza SUMMON_ECHOES]** Invoca **un solo eco**, elegido según el comportamiento del jugador en los últimos 10 s: mucho esquivar → **venado** (embestida veloz); mucho quieto → **serpiente** (ataque de área); mucho saltar → **gavilán** (picada aérea). El eco ejecuta un ataque y se disuelve. | 50% del original |
| `MASK_PULSE` | 7 s | La máscara emite onda circular expansiva. Radio de daño 80px. | 0.75 |

★ **Nota académica (U-IX):** la elección del eco es clasificación de patrones del jugador — se registran contadores de salto/esquive/inmovilidad y se selecciona por umbral. Documentar inline como aplicación de Unidad IX.

**Ecos — decisión de producción:** se diseñan como **siluetas espectrales propias** (formas abstractas verde translúcido, reconocibles por silueta: astas / espiral / alas). Si los sprites de los compañeros están listos a tiempo, se sustituyen; si no, la silueta ya se ve intencional. **Cero dependencias en el camino crítico.**

**Destello espectral (siembra):** Durante esta forma, 2-3 veces, la pantalla parpadea brevemente en visión espectral (`threshold_binary`) de forma automática, sin control del jugador. Dura 0.2 s. Nadie explica qué fue. **Es la siembra de la mecánica de la Forma 4.**

**Transición 2→3:** La máscara se disuelve. La Pepita y La Perla vuelan al arena desde John y Jin. Paburu las atrapa. *Se enciende el segundo cuenco.* El juego **elige aleatoriamente** 3A o 3B.

---

### FORMA 3 — "La Reliquia" (10 → 5) — ALEATORIA
> *Deja que las reliquias juzguen por él.*

Selección aleatoria por sesión (semilla por partida). Dos peleas distintas; el jugador aprende ambas con el tiempo.
**Nota de producción:** implementar una tecla de debug para forzar la forma durante desarrollo y demos.

#### 3A — "La Pepita" (esfera dorada, 32×32) — OFENSIVA
**Movimiento:** Persecución agresiva. `vec2_normalize()` hacia el jugador a 120px/s + jitter aleatorio (±30°) cada 0.5 s.
**Daño por contacto:** 1.0

| Patrón | Descripción | Daño |
|---|---|---|
| `GOLD_RUSH` | Acelera a 240px/s durante 0.8 s, cada 5 s | contacto |
| `GOLD_BURST` | Al cruzar cada corazón: 8 orbes dorados radiales | 0.25 c/u |
| `RICOCHET` | Rebota en paredes y plataformas conservando velocidad | contacto |

**Nota académica (U-II):** `RICOCHET` implementa reflexión vectorial pura: `v = v - 2·(v·n)·n`. Documentar inline.

#### 3B — "La Perla" (esfera negra, 32×32) — DEFENSIVA
**Movimiento:** Orbita el centro de la arena, radio 64px, 0.3 rad/s. Rara vez se acerca.
**Daño por contacto:** 0.5

| Patrón | Descripción | Daño |
|---|---|---|
| `DARK_FIELD` | Coloca zona lenta 48×48 (velocidad del jugador ÷2), dura 8 s, hasta 3 simultáneas | — |
| `PEARL_VOLLEY` | 3 orbes negros lentos hacia el jugador, persisten 6 s | 0.5 c/u |
| `PULL` | Cada 10 s: atracción gravitacional hacia la esfera durante 1 s | — |

**Nota académica (U-II):** `PULL` implementa atracción simplificada: `v += normalize(pos_esfera - pos_jugador) · G · dt`. Documentar inline.

**Transición 3→4:** La esfera se disuelve lentamente. Materializa la figura alta del espíritu. Paburu **mira al jugador durante 3 segundos completos** sin atacar. Luego levanta la mano. *Se encienden los dos cuencos restantes — la arena queda completamente iluminada y el sello es visible en el piso.*

---

### FORMA 4 — "El Espíritu del Shaman" (5 → 0)
> *Juzga cara a cara. Y da la oportunidad que no dio antes.*

**Visual:** Figura espectral alta y delgada (64×80). Túnicas de luz fluida. Rostro antiguo, sereno. Ojos blancos. Manos con luz dorada y perlada alternada.
**Movimiento:** Flotación senoidal vertical (amplitud 32px, 0.2 Hz) + deriva horizontal lenta (20px/s).
**Efecto (U-VII):** `FilterTools.sobel_edge(superficie)` mezclado a alpha 60 — el contorno del espíritu se refuerza con detección de bordes.

| Patrón | Cada | Descripción | Daño |
|---|---|---|---|
| `RELIC_SURGE` | 6 s | Ambas reliquias orbitan a Paburu y estallan: orbes dorados (rápidos, pocos) + negros (lentos, muchos) | 0.5 / 0.25 |
| **`SPIRIT_FORM`** ★ | 10 s | **[Rediseñado]** Paburu se vuelve **invisible e intangible** 2.5 s (antes 1.5). Sigue atacando. **Solo se le puede ver y golpear con la VISIÓN ESPECTRAL activa.** | — |
| `ANCIENT_CALL` | 15 s | Los tres ecos aparecen simultáneamente 3 s, cada uno ejecuta un ataque, se disuelven | 50% |
| `CONVERGENCE` | única, a 2♥ | Ambas reliquias convergen sobre el jugador. Telegraph: 2 s orbitando hacia él. Solo se evita en los refugios laterales. | 2.0 |
| **`EL OFRECIMIENTO`** ★ | única, a 1♥ | **Paburu se detiene por completo. Baja las manos. 3 segundos sin atacar, vulnerable, mirando al jugador.** Si lo golpean: daño normal. Si NO lo golpean: recupera 0.5♥. Sin recompensa mecánica por perdonar. | — |

★ = diseño propio

#### La Visión Espectral (mecánica estrella — U-VIII)
- **Activación:** botón `LONG_ATTACK` (mantener). **Cooldown:** 8 s. **Duración máxima:** 3 s.
- **Efecto:** aplica `VisionTools.threshold_binary()` a la pantalla — el mundo se vuelve blanco y negro de alto contraste, y **el espíritu intangible se hace visible y golpeable**.
- **Costo de diseño:** mientras está activa, la visión distorsionada dificulta leer los otros ataques. Ver a Paburu significa dejar de ver el resto.
- **Justificación narrativa:** es el poder de La Perla — *"amplifica la percepción; quien la porta es atraído hacia la observación"* (lore §4.2). No es un gadget: es la reliquia que Paburu vino a probar.
- **Curva de enseñanza:** destellos automáticos en Forma 2 (siembra) → control del jugador en Forma 4 (examen).

---

### Secuencia de derrota (canon §6.7 + ampliación propia)

1. A 0 de vida, el espíritu **no cae — asciende**.
2. Las reliquias vuelan de vuelta hacia John y Jin.
3. Paburu abre los brazos. **Hold de 4 segundos.**
4. ★ **Los recuerdos:** aparecen los tres ecos, uno por uno, con un frame congelado del momento de su derrota. Cada uno se inclina y se disuelve. *(Aquí es donde entra tu cinemática: no son enemigos, son sus guardianes despidiéndose.)*
5. Paburu devuelve la reverencia.
6. Se disuelve en luz dorada. Las marcas del sello en el piso **brillan una última vez** — los nombres son legibles por un instante, con Kavë al centro.
7. El cementerio queda en silencio. Fade a blanco.
8. → Créditos (integración a cargo del profesor).

---

## 5. Mapeo académico (para la rúbrica)

| Unidad | Dónde se demuestra |
|---|---|
| **II — Transformaciones y vectores** | Arcos de `STONE_SPIT`; reflexión vectorial en `RICOCHET`; atracción gravitacional en `PULL`; rotación/escalado de orbes |
| **III — Curvas** | Trayectorias de ecos y orbes con `CurveTools.bezier` / `catmull_rom`; órbita de las reliquias en `RELIC_SURGE` |
| **IV — Representación de escenas** | 8 capas del TMX, parallax de las siluetas, orden de dibujo, gestión de sprites |
| **V — Color e iluminación** | `ColorTools.apply_tint` (piedra verde); cuencos de fuego con `LightSystem`; cambio de paleta por forma; alpha blending de ecos |
| **VI — Texturas, animación, interpolación** | 11 spritesheets; easings de `math_utils` en transiciones; movimiento senoidal |
| **VII — Procesamiento de imágenes** | `adjust_brightness` respirante en la máscara; `sobel_edge` en el aura del espíritu |
| **VIII — Segmentación** | `threshold_binary` de la Visión Espectral como mecánica jugable |
| **IX — Reconocimiento de patrones** | Selección del eco según comportamiento del jugador en `EL DUELO DE LOS ECOS` |

---

## 6. Producción de assets

### 6.1 Spritesheets (11)
| Archivo | Frames | FPS | Loop | Tamaño |
|---|---|---|---|---|
| `boss_paburu_stone.png` | 4 | 6 | sí | 64×64 |
| `boss_paburu_stone_slam.png` | 8 | 12 | no | 64×64 |
| `boss_paburu_mask.png` | 6 | 10 | sí | 56×72 |
| `boss_paburu_mask_wave.png` | 8 | 12 | no | 56×72 |
| `boss_paburu_gold.png` | 6 | 14 | sí | 32×32 |
| `boss_paburu_black.png` | 6 | 14 | sí | 32×32 |
| `boss_paburu_relic_atk.png` | 10 | 14 | no | 32×32 |
| `boss_paburu_spirit.png` | 8 | 10 | sí | 64×80 |
| `boss_paburu_spirit_surge.png` | 12 | 14 | no | 64×80 |
| `boss_paburu_hurt.png` | 4 | 12 | no | según forma |
| `boss_paburu_transcend.png` | 20 | 8 | no | 64×80 |

### 6.2 Otros assets
- **Proyectiles:** piedra (8×8), orbe dorado (8×8), orbe negro (8×8), onda espectral (32×16)
- **Ecos:** 3 siluetas espectrales propias (~48×48, verde translúcido)
- **Escenario:** tileset del cementerio, fondo BG_Far (cielo), siluetas BG_Mid (3), cuencos de fuego (animados 4f), columnas de `EL SELLO` (16×48), marcas grabadas (variantes)
- **Reliquias:** pepita 8×6, perla 7×7 *(ya definidas en lore §4 — verificar si existen en `assets/`)*

### 6.3 Estrategia de producción
- **Dibujado a mano** (Aseprite / LibreSprite / Piskel): las 11 hojas de Paburu, tileset, cuencos.
- **Generado por código:** auras, orbes, partículas, marcas del sello, efecto Sobel del espíritu. Precedente en el repo: `tools/generate_all_assets.py`. Ventaja doble: menos trabajo manual **y** demuestra unidades del curso.
- **Reutilizado:** revisar `assets/` antes de dibujar nada — el proyecto tiene assets compartidos.

---

## 7. Roadmap de las tres entregas

### EP1 — Prototipo Funcional (15%)
> *Objetivo: que exista y se pueda pelear.*

- [x] `boss_paburu.tmx` con las 8 capas obligatorias + `BossSpawn` + geometría de la arena (suelo, 2 plataformas, 2 refugios) — 8/8 capas; 4 plataformas y 2 nichos
- [x] `boss_paburu_scene.py` heredando de `StageScene`; carga y corre
- [x] `boss_paburu.py` heredando de `BossBase`, con las 4 formas declaradas (aunque solo la 1 esté implementada)
- [x] **Forma 1 completa:** `STONE_SPIT`, `EYE_BEAM`, `EL SELLO` con marcas persistentes
- [x] Barra de vida del boss en el HUD
- [x] Transición 1→2 (aunque la Forma 2 sea placeholder)
- [x] Arte: placeholder aceptable, pero la cabeza de piedra ya con tinte verde (`apply_tint`)

**Evidencia:** coordenadas, transformaciones geométricas, interacción básica, color.

### EP2 — Vertical Slice (15%)
> *Objetivo: que se vea y se sienta como el jefe final.*

- [ ] **Forma 2 completa:** `SPIRIT_WAVE`, `EL DUELO DE LOS ECOS`, `MASK_PULSE`, punto débil en la máscara
- [ ] Brillo respirante de la máscara (`adjust_brightness`)
- [ ] Ecos con siluetas propias + lógica de selección por comportamiento
- [ ] Destellos espectrales de siembra
- [ ] **Arte final de Formas 1 y 2** (spritesheets terminados)
- [ ] Arena con tileset final, cuencos de fuego con `LightSystem`, siluetas de fondo
- [ ] Transiciones 1→2 y 2→3 con animación y easing
- [ ] Marcas del sello acumulándose visiblemente

**Evidencia:** curvas, color, transparencia, texturas, animación, interpolación.

### EP3 — Integración Final (15%)
> *Objetivo: el combate completo, pulido y con el procesamiento de imágenes integrado.*

- [ ] **Forma 3A y 3B completas** (reflexión vectorial + atracción gravitacional documentadas inline)
- [ ] Selección aleatoria + tecla de debug
- [ ] **Forma 4 completa:** `RELIC_SURGE`, `SPIRIT_FORM` invisible, `ANCIENT_CALL`, `CONVERGENCE`, `EL OFRECIMIENTO`
- [ ] **Visión Espectral** funcionando (`threshold_binary` en vivo, cooldown, costo de legibilidad)
- [ ] Aura del espíritu con `sobel_edge`
- [ ] **Secuencia de derrota completa** con los recuerdos de los ecos y el sello brillando
- [ ] Arte final de Formas 3 y 4 + `transcend`
- [ ] Tuning de dificultad con playtesting
- [ ] README del stage documentando qué unidad demuestra cada mecánica

**Evidencia:** PDI, segmentación, reconocimiento de patrones, integración total.

### Regla de gestión
**Cada entrega debe ser jugable y demostrable en 3 minutos.** Si el tiempo aprieta, se recorta alcance, nunca pulido. Orden de sacrificio si hace falta: `EL SELLO` (visual) → `EL DUELO DE LOS ECOS` (simplificar a eco fijo) → **nunca `EL OFRECIMIENTO`** (cuesta poco y es lo único irrepetible).

---

## 8. Estructura de archivos

```
legacyofInfest/
├── src/stages/boss_paburu/
│   ├── __init__.py
│   ├── boss_paburu.py           ← la entidad (4 formas, hereda BossBase)
│   ├── boss_paburu_scene.py     ← la escena (hereda StageScene)
│   └── README.md                ← mapeo mecánica → unidad del curso
├── assets/maps/boss_paburu/
│   ├── boss_paburu.tmx
│   └── (tileset del cementerio)
└── assets/sprites/boss_paburu/
    ├── boss_paburu_*.png        ← las 11 hojas
    ├── ecos/
    └── proyectiles/
```

**Regla inviolable:** no se modifica `src/engine/` ni `src/framework/`. Todo el trabajo son archivos nuevos bajo `boss_paburu`. Si se detecta un bug del framework, se reporta al profesor.

---

## 9. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| El arte consume más tiempo del previsto | Placeholders desde EP1; generación procedural de efectos; reutilizar assets del repo |
| Los sprites de los compañeros no llegan | Ecos con siluetas propias desde el diseño |
| La Visión Espectral resulta confusa al jugar | Siembra en Forma 2; playtest temprano con alguien que no conozca el diseño |
| 4 formas es demasiado alcance | Orden de sacrificio definido en §7; las formas 3A/3B comparten infraestructura |
| Dificultad mal calibrada para una demo de 3 min | Tuning con playtesting; tecla de debug para saltar formas en la presentación |
