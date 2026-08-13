---
document_id: "LOI-WORLD-016"
title: "Legacy of InFest — Documento de diseño del mundo"
aliases: ["Documento de diseño del mundo", "World Design"]
tags: ["mundo", "diseno", "narrativa"]
description: "4 zonas, 14 escenarios, mapeo de narrativa a jugabilidad"
source: "docs/16_WORLD_DESIGN.md"
date_processed: "2026-08-13"
---

# Legacy of InFest — Documento de diseño del mundo

**ID del documento:** LOI-WORLD-016
**Versión:** 1.1.0
**Estado:** Oficial
**Compatibilidad:** Requiere `03_ARCHITECTURE.md`, `07_STAGE0_DESIGN.md`
**Audiencia:** Profesor, estudiantes, artistas, asistentes de programación con IA

> **AUD-455.** Traduce el documento. Corrige §8: describía "Student Stage
> 1/2/3" como tres escenarios distintos del framework asignados a un
> mismo estudiante — el modelo real, verificado repetidamente en
> `08_SYLLABUS_MAPPING.md` §12, `21_COURSE_SCHEDULE.md` §7, y
> `27_ACADEMIC_RUBRICS.md`, es que cada estudiante desarrolla **un solo**
> Escenario o Jefe a través de tres hitos acumulativos de completitud, no
> tres escenarios separados.

---

## 1. Visión general

Legacy of InFest transcurre en cuatro zonas geográficas distintas, cada una arraigada en un entorno real o culturalmente inspirado en Costa Rica. El mundo se estructura como una progresión lineal de zonas y escenarios, que culmina en una confrontación con el Gran Chamán Paburu en el cementerio sagrado.

Cada zona se subdivide en **cuatro escenarios**. Los escenarios 1–3 son de recorrido y combate. El escenario 4 siempre es una confrontación de jefe o el desafío culminante de esa zona. La excepción es la Zona Final, que sólo tiene dos escenarios — ambos encuentros de jefe.

La narrativa del mundo gira en torno a dos protagonistas — **John** y **Jin** — que llevan reliquias ancestrales (la Pepita de Oro y la Perla) que despiertan a los espíritus de la tierra. Cada espíritu despierto actúa como guardián o antagonista, extraído de la mitología indígena costarricense e imaginería natural.

---

## 2. Estructura del mundo

```
ZONA 1 — Universidad Invenio (campus de jungla)
    Escenario 1-1  La Entrada          (aproximación por montaña de jungla)
    Escenario 1-2  La Soda             (cafetería universitaria, desorden)
    Escenario 1-3  Las Aulas           (aulas universitarias)
    Escenario 1-4  La Residencia       [JEFE: El Venado Sagrado]

ZONA 2 — El Datacenter
    Escenario 2-1  La Planicie         (llanuras entre el campus y el datacenter)
    Escenario 2-2  Entrada y Antenas   (exterior del datacenter, matrices de antenas)
    Escenario 2-3  Las Oficinas        (oficinas interiores)
    Escenario 2-4  El Datacenter       [JEFE: El Rey Terciopelo]

ZONA 3 — Sede Heredia
    Escenario 3-1  La Entrada de Piedra (sendero de piedra hacia el vestíbulo)
    Escenario 3-2  El Hall              (enorme hall universitario)
    Escenario 3-3  El Patio             (patio exterior)
    Escenario 3-4  El Bungaló           [JEFE: El Gavilán Camionero Mascarero]

ZONA FINAL — El Cementerio Sagrado
    Escenario 4-1  La Entrada al Cementerio
    Escenario 4-2  [JEFE FINAL: El Gran Chamán Paburu — 4 fases]
```

---

## 3. Zona 1 — Universidad Invenio

### 3.1 Identidad de la zona

| Propiedad | Valor |
|---|---|
| Ambientación | Campus universitario rodeado de jungla de montaña, Costa Rica |
| Atmósfera | Frondosa, cubierta de vegetación, húmeda. El bosque ancestral se encuentra con la academia moderna. |
| Paleta visual | Verdes profundos, marrones de tierra, ámbar cálido (luz de tarde) |
| Ánimo de BGM | Sonidos ambientales de jungla sobre percusión tensa y rítmica |
| Tema de enemigos | Insectos, animales pequeños, estudiantes desorientados — cosas sacadas de su orden natural |

La zona cuenta la historia de un campus que la jungla ha reclamado poco a poco desde que los espíritus empezaron a agitarse. Enredaderas se cuelan por los pasillos. Animales deambulan por la cafetería. El bosque no ha olvidado que estuvo aquí primero.

---

### 3.2 Escenario 1-1 — La Entrada

**Tipo:** Recorrido
**Longitud:** ~100 metros (625 baldosas de 16px cada una — aproximadamente 3.5 pantallas de desplazamiento)
**Descripción:** Un sendero largo y solitario que serpentea por una jungla montañosa. El protagonista llega a pie. Dosel denso arriba. El sendero se estrecha progresivamente. No hay edificios visibles — sólo árboles, raíces, y roca.

**Relevancia académica:**
- Unidad III: rutas de patrulla de enemigos por curvas de Bézier (serpenteando por la geometría del sendero de jungla)
- Unidad VI: capas de parallax (3–4 planos de profundidad de fondo: cielo, cresta de montaña, dosel, sotobosque)

**Notas de layout:**
- Cambios de elevación suaves usando geometría de plataforma escalonada (escalones de piedra embebidos en la tierra)
- Sin fosos en este escenario — el castigo es sólo el contacto con enemigos
- Checkpoint en el punto medio (tras la sección más angosta del sendero)
- Caídas de un solo sentido de senderos altos a bajos — no se puede volver

**Complemento de enemigos:**

| Enemigo | Cantidad | Comportamiento |
|---|---|---|
| `WalkerInsect` | 6 | Patrulla el sendero, invierte dirección en los bordes |
| `FlyingBird` | 3 | Sobrevuela el sendero en onda senoidal |
| `ShooterFrog` | 2 | Estacionario sobre rocas, lanza proyectiles |

**Rasgos del terreno:**
- Set de baldosas de piedra y tierra (`tileset_jungle_stone.png`)
- Superposición de dosel espeso en primer plano (se renderiza sobre el jugador — capa `FG_Overlay`)
- Tres capas de fondo: gradiente de cielo, silueta de montaña, línea de árboles

**Banner de entrada de escenario:** `"1-1  LA ENTRADA"`
**Límite de tiempo:** 180 segundos
**Disparador de completado:** El arco portal en el borde derecho lleva al Escenario 1-2

---

### 3.3 Escenario 1-2 — La Soda

**Tipo:** Recorrido + combate
**Descripción:** La cafetería universitaria — un espacio interior amplio y caótico. Mesas volteadas. Bandejas dispersas. Los alimentos se han alterado y algunos se volvieron peligrosos. El espacio es de altura media (se ven dos pisos), con un área de mostrador, filas de asientos, y una cocina trasera accesible por una media puerta.

**Relevancia académica:**
- Unidad V: iluminación basada en color (luz cálida de cocina frente a área de comedor fría — tinte HSL aplicado a cada zona)
- Unidad VII: el estudiante usa `FilterTools.adjust_brightness()` para simular el interior tenue tras el caos
- Unidad IV: múltiples capas verticales — baldosas de suelo, geometría de mostrador, vigas de techo

**Notas de layout:**
- Espacio horizontal más amplio que el Escenario 1-1 (~480px)
- Geometría de dos pisos: nivel de suelo (mesas, mostradores) y nivel elevado (repisa de servicio de cocina)
- Una plataforma de un solo sentido separa el suelo de la sección elevada
- Zona de peligro de bandejas proyectil en el mostrador (HazardZone, daño=0.25)
- Checkpoint tras sobrevivir el comedor principal

**Complemento de enemigos:**

| Enemigo | Cantidad | Comportamiento | Notas |
|---|---|---|---|
| `WalkerRaton` | 4 | Patrulla de suelo, más rápido que el walker de jungla | Ratas desplazadas de la cocina |
| `FlyingCucaracha` | 5 | Vuelo errático en onda senoidal | Llenan el espacio a media altura |
| `ShooterCocinero` | 1 | Estacionario tras el mostrador | Lanza alimentos como proyectiles |

**Rasgos del terreno:**
- Set de baldosas de interior (`tileset_cafeteria.png`)
- Baldosas de piso a cuadros (rojo y blanco — dentro de la paleta SNES)
- Luces de techo colgantes (decorativas, capa `Terrain_Detail`)
- Mostrador de cocina como borde superior de plataforma de un solo sentido

**Banner de entrada de escenario:** `"1-2  LA SODA"`
**Límite de tiempo:** 150 segundos

---

### 3.4 Escenario 1-3 — Las Aulas

**Tipo:** Recorrido + combate
**Descripción:** Las aulas universitarias. Un corredor que conecta varias salas, cada una visible a través de puertas. Las salas han sido invadidas: los pupitres están apilados, la pizarra está agrietada, raíces del bosque han roto el piso. El corredor va de izquierda a derecha; las salas laterales son accesibles por puertas abiertas y contienen objetos y peligros.

**Relevancia académica:**
- Unidad VIII: el estudiante aplica `VisionTools.threshold_binary()` para distinguir zonas de "polvo de tiza" (brillantes) de zonas de "sombra de raíz" (oscuras) — dirige una mecánica de luz encendida/apagada
- Unidad VI: animación de puerta con función de easing (las puertas se abren con `ease_out_bounce`)

**Notas de layout:**
- Tres alcobas de aula (salas accesibles, sin desplazamiento, que ramifican del corredor principal)
- El corredor principal mide ~560px de ancho
- Raíces en el piso (sólo visual, `Terrain_Detail`) con zonas de colisión de pinchos embebidas
- La pizarra del aula 2 tiene un mensaje de tutorial escrito (huevo de pascua — lee contenido del curso)

**Complemento de enemigos:**

| Enemigo | Cantidad | Colocación |
|---|---|---|
| `WalkerEstudiante` | 5 | Patrulla el corredor y las salas |
| `FlyingNotebook` | 3 | Papeles voladores con movimiento senoidal |
| `ShooterTiza` | 2 | Estacionarios en los extremos de la pizarra, disparan proyectiles de tiza |

**Objeto especial — pizarra checkpoint:**
Un checkpoint disfrazado de pizarra. Al activarse, una animación de tiza dibuja una marca de verificación en la pizarra. Es el único checkpoint del Escenario 1-3.

**Banner de entrada de escenario:** `"1-3  LAS AULAS"`
**Límite de tiempo:** 150 segundos

---

### 3.5 Escenario 1-4 — La Residencia

**Tipo:** Escenario de jefe
**Descripción:** Un claro residencial boscoso. Muros de piedra ancestrales, cubiertos de musgo. Un área central abierta rodeada de árboles centenarios. Al fondo: la morada del Venado Sagrado — un arco enmarcado en piedra, cubierto de enredaderas. Aquí espera el primer jefe.

**Relevancia académica:**
- Unidad III: el movimiento del jefe durante la Fase 2 sigue un arco de Bézier por la arena
- Unidad VII: la Fase 1 del jefe usa `FilterTools.sobel_edge()` como superposición visual de "aura"

**Layout:**
- Sin desplazamiento horizontal — arena fija (320×224)
- Piso de piedra sólido con 3 plataformas elevadas (para esquivar saltando)
- Entrada del jefe desde la derecha: el venado emerge de detrás del arco de enredaderas

**Jefe:** El Venado Sagrado — ver `17_BOSS_SPEC.md`

**Banner de entrada de escenario:** `"1-4  LA RESIDENCIA"`
**Límite de tiempo:** Ninguno (los escenarios de jefe no tienen cronómetro)

---

## 4. Zona 2 — El Datacenter

### 4.1 Identidad de la zona

| Propiedad | Valor |
|---|---|
| Ambientación | Complejo de datacenter industrial adyacente al campus universitario |
| Atmósfera | Calor opresivo, brillo azul tenue de servidores, zumbido mecánico |
| Paleta visual | Grises acero, azules profundos, naranja caliente (rejillas de calor), luces rojas de advertencia |
| Ánimo de BGM | Zumbido electrónico, ritmo industrial, percusión metálica |
| Tema de enemigos | Serpientes — todos los enemigos de esta zona son a base de serpiente o afines |
| Contexto narrativo | El calor del datacenter lo vuelve el refugio perfecto para las serpientes terciopelo que responden a El Rey Terciopelo |

El datacenter ya era un espacio cálido y cerrado — los servidores generaban calor constante. Cuando los espíritus se agitaron, las serpientes terciopelo migraron aquí y se fusionaron bajo la influencia de El Rey, formando una conciencia colectiva que ahora controla el espacio.

---

### 4.2 Escenario 2-1 — La Planicie

**Tipo:** Recorrido
**Descripción:** Una zona de transición de llanuras abiertas entre el campus universitario y el datacenter. Tierra agrícola — algo de pastizal, algo de tierra despejada, una línea de cerca de alambre de púas. El sendero está expuesto y es ancho.

**Relevancia académica:**
- Unidad II: rango de detección de enemigos demostrado con `vec2_distance` basado en distancia (el espacio abierto hace visibles los cálculos de rango)
- Unidad V: efecto de espejismo de calor con mezcla alfa sobre el suelo (tinte de superficie animado)

**Notas de layout:**
- Terreno plano, ~480px de ancho
- Obstáculos bajos: alambre de púas (sólido a la altura de la rodilla — hay que agacharse para pasar)
- Un hueco en la cerca que se puede saltar o cruzar agachado
- Visual de espejismo de calor: una oscilación de brillo sutil aplicada a las baldosas del suelo vía `FilterTools.adjust_brightness()` con un factor de onda senoidal

**Complemento de enemigos:**

| Enemigo | Cantidad | Comportamiento |
|---|---|---|
| `WalkerSerpientePequena` | 6 | Patrulla de suelo, rápida |
| `ShooterSerpienteArbol` | 3 | Estacionaria en postes de cerca, escupe veneno |
| `FlyingBoa` | 2 | Aérea — onda senoidal |

**Banner de entrada de escenario:** `"2-1  LA PLANICIE"`
**Límite de tiempo:** 160 segundos

---

### 4.3 Escenario 2-2 — Entrada y Antenas

**Tipo:** Recorrido + combate
**Descripción:** La aproximación exterior al datacenter. Un estacionamiento, una caseta de seguridad, y un campo de antenas de comunicación en el techo. El protagonista debe pasar por el nivel de suelo y subir a la matriz de antenas en el techo.

**Relevancia académica:**
- Unidad III: patrulla de enemigos por rutas B-Spline enrollándose en los postes de antena
- Unidad IV: sección de desplazamiento vertical (de abajo hacia arriba) — el bloqueo de cámara cambia de eje

**Notas de layout:**
- El escenario es más ancho y alto de lo típico (320×320 interno — usa una zona de bloqueo de cámara para restringir el desplazamiento horizontal durante la sección vertical)
- Sección de suelo (~200px de ancho): aproximación del estacionamiento, caseta de seguridad
- Sección de escalada vertical: cadena de plataformas tipo escalera por el costado del edificio
- Sección de techo: matriz de antenas — plataformas angostas entre postes

**Bloqueo de cámara de escalada vertical:**
Un objeto `CameraLock` con `lock_x=true, lock_y=false` se activa cuando el jugador llega a la escalera. La cámara entonces sigue sólo el movimiento vertical.

**Complemento de enemigos:**

| Enemigo | Cantidad | Colocación |
|---|---|---|
| `WalkerGuardia` | 2 | Nivel de suelo, caseta de seguridad |
| `FlyingBoa` o `FlyingTerciovolador` | 4 | Patrulla aérea alrededor de las antenas |
| `ShooterSerpienteArbol` o `ShooterVenomoLargo` | 3 | Estacionarios en las plataformas de antena |

**Banner de entrada de escenario:** `"2-2  ENTRADA Y ANTENAS"`
**Límite de tiempo:** 170 segundos

---

### 4.4 Escenario 2-3 — Las Oficinas

**Tipo:** Recorrido + combate
**Descripción:** El interior del datacenter — el piso de oficinas. Cubículos, servidores visibles a través de mamparas de vidrio, gestión de cables en el techo. El piso está cubierto de serpientes. El aire es pesado y cálido. Las luces indicadoras de los servidores parpadean en rojo.

**Relevancia académica:**
- Unidad VII: `FilterTools.canny_edge()` aplicado al fondo produce un efecto visual estilo wireframe (el protagonista "ve" la infestación de serpientes como un mapa de bordes)
- Unidad VIII: `VisionTools.connected_components()` se usa para contar unidades de servidor activas (indicadores LED brillantes) — dirige un indicador de puntuación o densidad

**Notas de layout:**
- Tileset de interior (`tileset_datacenter.png`): piso metálico, mamparas de vidrio, racks de servidor
- Mamparas de vidrio: paredes sólo visuales (sin colisión) — el jugador las atraviesa
- Cableado en el techo: `FG_Overlay` decorativo
- Peligro de suelo: franjas `HazardZone` donde se agrupan las serpientes (daño=0.25)
- Dos ubicaciones de checkpoint: a mitad del campo de cubículos, en la puerta de entrada a la sala de servidores

**Complemento de enemigos:**

| Enemigo | Cantidad | Comportamiento |
|---|---|---|
| `WalkerTerciopelo` | 7 | Patrulla agresiva entre cubículos |
| `ShooterVenomoLargo` | 3 | Escupe veneno de largo alcance desde detrás de mamparas |
| `FlyingTerciovolador` | 2 | Variantes voladoras pequeñas por encima de la altura de las mamparas |

**Banner de entrada de escenario:** `"2-3  LAS OFICINAS"`
**Límite de tiempo:** 150 segundos

---

### 4.5 Escenario 2-4 — El Datacenter

**Tipo:** Escenario de jefe
**Descripción:** La sala de servidores. Una catedral de máquinas. Filas de racks de servidor que llegan hasta el techo. Luces parpadeantes por todas partes. Aire caliente subiendo de las rejillas del suelo. El piso es una masa retorcida de serpientes. En el centro, suspendido entre dos pilares de servidor: El Rey Terciopelo — el espíritu amalgamado.

**Relevancia académica:**
- Unidad IX: clasificación en la Fase 2 del jefe — el colectivo alterna entre tres modos de ataque (agresivo, defensivo, disperso). El estudiante reconoce el modo usando `PatternRecognitionTools.predict()` sobre el estado visual de la superficie del jefe y responde en consecuencia.

**Layout:**
- Arena fija (320×224), sin desplazamiento
- Racks de servidor como paredes laterales (visual y colisión)
- Tres rejillas de suelo como HazardZone (daño=0.25, periódico — activas 2 segundos cada 5 segundos)
- Piso central de la arena: plano con una plataforma baja para saltar sobre los barridos de serpiente

**Jefe:** El Rey Terciopelo — ver `17_BOSS_SPEC.md`

**Banner de entrada de escenario:** `"2-4  EL DATACENTER"`

---

## 5. Zona 3 — Sede Heredia

### 5.1 Identidad de la zona

| Propiedad | Valor |
|---|---|
| Ambientación | Edificio de la sede de Heredia de la Universidad Invenio |
| Atmósfera | Grandeza académica — espacios abiertos amplios, arquitectura de piedra y vidrio |
| Paleta visual | Beige cálido de piedra, sombra interior fría, luz dorada de tarde a través de los tragaluces |
| Ánimo de BGM | Orquestal tenso — algo que caza, paciente, aéreo |
| Tema de enemigos | Aves y criaturas aéreas — el dominio de El Gavilán |

El campus de Heredia se ha vuelto el coto de caza de El Gavilán Camionero Mascarero. Sus techos altos y patios abiertos lo hacen perfecto para depredadores aéreos. La máscara Tilawa le ha dado al gavilán tanto inteligencia como alcance sobrenatural.

---

### 5.2 Escenario 3-1 — La Entrada de Piedra

**Tipo:** Recorrido
**Descripción:** Un largo sendero empedrado que lleva a la entrada principal del edificio de Heredia. Muros de piedra a ambos lados. Arcos arriba. El sendero es ancho y está expuesto — sin cobertura contra ataques aéreos.

**Relevancia académica:**
- Unidad VI: animación de empedrado (cada baldosa de piedra se activa secuencialmente usando lerp cronometrado — un efecto de "despertar" cuando el jugador camina sobre ellas)
- Unidad V: cambio de color de piedra basado en HSL entre zonas soleadas (cálido) y de sombra (frío) al pasar las nubes

**Notas de layout:**
- Sendero plano, ~560px de largo
- Arcos sólo visuales (FG_Overlay)
- Ataques aéreos intermitentes en picada de enemigos `FlyingHalcon` precolocados
- Dos jardineras de piedra elevadas como cobertura (parte superior de plataforma de un solo sentido)

**Complemento de enemigos:**

| Enemigo | Cantidad | Comportamiento |
|---|---|---|
| `WalkerGarza` | 4 | Patrulla el sendero de piedra a pie |
| `FlyingHalcon` | 4 | Onda senoidal rápida, se lanza en picada hacia el jugador |
| `ShooterQuetzal` | 2 | Estacionarios en la parte superior de los arcos, disparan proyectiles de plumas |

**Banner de entrada de escenario:** `"3-1  LA ENTRADA DE PIEDRA"`
**Límite de tiempo:** 160 segundos

---

### 5.3 Escenario 3-2 — El Hall

**Tipo:** Recorrido + combate
**Descripción:** Un hall enorme — techos altos, piso ancho, balcones a ambos lados. Luz natural desde tragaluces arriba. El espacio es vasto y abierto, lo que hace sentir al jugador expuesto. Aves sobrevuelan en círculos. El hall conecta la entrada con los corredores interiores.

**Relevancia académica:**
- Unidad VIII: `VisionTools.watershed_segment()` se usa para identificar "zonas" distintas del hall (zona de entrada, zona central, zona de balcón) — el estudiante usa la clasificación de zona para disparar distintas apariciones de enemigo por zona
- Unidad IV: la pila de capas más compleja del juego: piso, plataformas de balcón, vigas de techo, superposición de tragaluz — 5 capas visibles

**Notas de layout:**
- ~640px de ancho — el escenario más ancho del juego
- Nivel de piso: ancho, pocos obstáculos
- Nivel de balcón: accesible por dos escaleras (plataformas sólidas)
- Techo: indestructible — los proyectiles rebotan (si el disparador está posicionado debajo)
- Rayos de tragaluz: columnas brillantes semitransparentes en posiciones X fijas (sólo visual)

**Complemento de enemigos:**

| Enemigo | Cantidad | Colocación |
|---|---|---|
| `WalkerPalom` | 5 | Nivel de piso — lento, hitbox grande |
| `FlyingHalcon` | 6 | Patrulla aérea — picadas desde la altura del techo |
| `ShooterBuitre` | 2 | Estacionarios en los balcones |

**Banner de entrada de escenario:** `"3-2  EL HALL"`
**Límite de tiempo:** 170 segundos

---

### 5.4 Escenario 3-3 — El Patio

**Tipo:** Recorrido + combate
**Descripción:** Un patio exterior dentro del edificio. Cielo abierto arriba. Vegetación en jardineras. Una fuente en el centro. El suelo es adoquinado. El patio está rodeado de muros del edificio por tres lados — un espacio parcialmente cerrado que se siente como una zona de emboscada.

**Relevancia académica:**
- Unidad VII: `FilterTools.gaussian_blur()` en la capa de cielo simula un efecto nublado — el brillo del cielo dirige la agresividad de los enemigos (cielo brillante = más enemigos voladores activos)
- Unidad III: la animación del arco de agua de la fuente usa un spline Catmull-Rom para la trayectoria de las partículas de agua

**Notas de layout:**
- ~400px de ancho
- Fuente central: visual + parte superior de colisión sólida (plataforma de un solo sentido)
- Cajas de jardinera: obstáculos sólidos bajos (32px de alto) — buenos para agacharse detrás
- Cielo visible en la mitad superior — capa de nubes de parallax en BG_Far

**Complemento de enemigos:**

| Enemigo | Cantidad | Comportamiento |
|---|---|---|
| `WalkerPalom` | 3 | Patrulla de suelo |
| `FlyingHalcon` | 5 | Muy agresivo — detecta a todo el ancho del patio |
| `ShooterQuetzal` | 3 | Desde repisas de ventana del edificio (bordes superiores de la pantalla) |

**Especial de la fuente:** tocar la fuente restaura 0.25 corazones (curación leve). Un uso por activación. Se reactiva en cada reaparición de checkpoint.

**Banner de entrada de escenario:** `"3-3  EL PATIO"`
**Límite de tiempo:** 145 segundos

---

### 5.5 Escenario 3-4 — El Bungaló

**Tipo:** Escenario de jefe
**Descripción:** El piso superior del edificio — un espacio de bungaló alto y abierto con vista panorámica y techo de tragaluz. Arquitectura de piedra y madera. El gavilán se posa aquí. Ésta es su guarida.

**Relevancia académica:**
- Unidad IX: detección de fase de jefe — `PatternRecognitionTools.predict()` clasifica el patrón de vuelo actual del gavilán (picada, círculo, posado) a partir de la distribución visual de su posición en los fotogramas recientes. El jugador usa el patrón predicho para anticipar el siguiente ataque.

**Layout:**
- Arena fija (320×224)
- Vigas de madera como plataformas en tres alturas (baja: Y=192, media: Y=152, alta: Y=112)
- Abertura de tragaluz en el centro superior: el jefe entra y sale por ahí en ciertas fases
- Sin HazardZones — combate puro de plataforma y aire

**Jefe:** El Gavilán Camionero Mascarero — ver `17_BOSS_SPEC.md`

**Banner de entrada de escenario:** `"3-4  EL BUNGALÓ"`

---

## 6. Zona Final — El Cementerio Sagrado

### 6.1 Identidad de la zona

| Propiedad | Valor |
|---|---|
| Ambientación | Un cementerio indígena sagrado en las tierras altas de Costa Rica |
| Atmósfera | Quieta, ancestral, sobrenatural. El aire se siente denso. |
| Paleta visual | Cielo púrpura-negro profundo, piedra pálida, luz verde espectral, resaltes dorados |
| Ánimo de BGM | Percusión ritual, zumbido profundo, silencio puntuado por tambores |
| Función narrativa | El punto de convergencia. Todos los espíritus que John y Jin han derrotado han llevado a este lugar. Paburu espera. |

Esta zona sólo tiene dos escenarios. No hay recorrido — el cementerio mismo ES la confrontación. El Escenario 4-1 es la aproximación por los terrenos del cementerio. El Escenario 4-2 es el encuentro con el jefe final.

---

### 6.2 Escenario 4-1 — La Entrada al Cementerio

**Tipo:** Recorrido + escenario atmosférico previo al jefe
**Descripción:** Un sendero serpenteante por el cementerio sagrado. Lápidas de piedra ancestrales a ambos lados. Cuencos de fuego ceremoniales que proyectan luz en movimiento. El protagonista camina casi en silencio. Los espíritus de los jefes derrotados aparecen como ecos visuales en el fondo — translúcidos, no hostiles, observando.

**Relevancia académica:**
- Unidad V: `ColorTools.apply_tint()` — el brillo espectral verde aplicado a cada superficie de fondo
- Unidad VII: `FilterTools.adjust_brightness()` ligado a la proximidad a los cuencos de fuego — más cerca del fuego = más brillante
- Unidad VIII: `VisionTools.threshold_binary()` se usa para crear un alternador de "visión espectral" — presionar un botón revela una versión de la pantalla filtrada por umbral que muestra marcas de tumba ocultas

**Notas de layout:**
- ~400px de ancho — longitud media
- Sin enemigos (intencional — la atmósfera ES el desafío)
- HazardZone: fisuras de tierra agrietada que pulsan con energía (daño=0.25, periódico)
- Plataformas de cuenco de fuego: pedestales de piedra elevados 32px con sprite de fuego arriba
- Alternador de visión espectral: activado con el botón `LONG_ATTACK` — reemplaza la pantalla con una versión filtrada por umbral durante 3 segundos

**Espíritus en el fondo (sólo visual — capa BG_Mid):**
- Silueta de El Venado Sagrado (astas de venado)
- Silueta de masa enrollada de El Rey Terciopelo
- Silueta de ala de El Gavilán

Son sprites estáticos en la profundidad de parallax BG_Mid — narrativa visual, no entidades.

**Banner de entrada de escenario:** `"4-1  LA ENTRADA AL CEMENTERIO"`
**Límite de tiempo:** Ninguno (ritmo atmosférico — sin presión de tiempo)

---

### 6.3 Escenario 4-2 — El Gran Chamán Paburu

**Tipo:** Escenario de jefe final (4 fases)
**Descripción:** El corazón del cementerio. Un claro circular de piedra con una cabeza de piedra masiva en el centro. Tallas rituales en el piso. Llamas verdes espectrales en el perímetro. La cabeza de piedra abre los ojos.

**Layout:**
- Arena fija (320×224)
- Piso de piedra con círculos rituales tallados (visual)
- Cuatro pilares de llama perimetrales (visual + HazardZone en su base: daño=0.25)
- Sin plataformas — arena plana para máxima flexibilidad de fase
- El jefe ocupa la región centro-superior en la mayoría de las fases

**Jefe:** El Gran Chamán Paburu — ver `17_BOSS_SPEC.md`
**Banner de entrada de escenario:** `"4-2  EL GRAN CHAMÁN PABURU"`

---

## 7. Tabla resumen de zonas

| Zona | Escenarios | Jefe | Ambientación | Unidades académicas principales |
|---|---|---|---|---|
| 1 — Universidad Invenio | 1-1 a 1-4 | El Venado Sagrado | Campus de jungla de montaña | II, III, V, VII |
| 2 — El Datacenter | 2-1 a 2-4 | El Rey Terciopelo | Complejo industrial de servidores | III, V, VII, IX |
| 3 — Sede Heredia | 3-1 a 3-4 | El Gavilán Camionero Mascarero | Edificio universitario urbano | VI, VII, VIII, IX |
| Final — Cementerio | 4-1, 4-2 | El Gran Chamán Paburu | Cementerio sagrado de tierras altas | V, VII, VIII |

---

## 8. Relación con la entrega del estudiante

Cada estudiante desarrolla **un solo** Escenario o Jefe (elegido individualmente en la Clase 1, ver `21_COURSE_SCHEDULE.md` §3, `08_SYLLABUS_MAPPING.md` §12) — no tres escenarios distintos del mundo. La entrega individual puede ser cualquiera de los escenarios de recorrido (X-1 a X-3) o jefes (X-4) de las Zonas 1–3 descritos arriba; la Zona Final es siempre propiedad del profesorado, ya que forma el cierre narrativo compartido de todas las entregas.

El escenario o jefe elegido determina qué unidades académicas demuestra el estudiante de forma más natural (ver la columna "Unidades académicas principales" de §7), aunque las tres Evaluaciones Prácticas exigen cubrir todas las unidades I–IX sin importar cuál se eligió — ver `08_SYLLABUS_MAPPING.md` §12 para el mapeo completo.

---

## 9. Resumen narrativo

| Acto | Evento |
|---|---|
| Prólogo | John y Jin llegan al campus universitario. Llevan la Pepita de Oro (John) y la Perla (Jin). |
| Zona 1 | El bosque despierta a su alrededor. El Venado Sagrado — un ciervo espíritu, huesos ancestrales envueltos en la jungla — se alza para reclamar las reliquias. Derrotado, su espíritu se une a ellos como guía. |
| Zona 2 | El calor del datacenter los atrae. El Rey Terciopelo — miles de serpientes animando un cuerpo decaído — comanda el espacio. Derrotado, su conocimiento del veneno se une a ellos. |
| Zona 3 | Un gavilán enmascarado los caza por la sede de Heredia de la universidad. El Gavilán Camionero Mascarero — potenciado por una máscara Tilawa — guarda el camino hacia Paburu. Derrotado, su vista aérea se une a ellos. |
| Zona Final | El cementerio. Paburu no se esconde. Espera. Cuatro fases. Cuatro formas. La Pepita de Oro y la Perla son la llave — y el peligro. |

---
## 🔗 Documentos relacionados

- [[18_ENEMY_ROSTER.md|Catálogo de enemigos]]
- [[19_NARRATIVE_AND_LORE.md|Narrativa y trasfondo]]
- [[07_STAGE0_DESIGN.md|Diseño de Stage 0]]
