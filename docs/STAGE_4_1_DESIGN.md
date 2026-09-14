# STAGE 4-1 — DISEÑO «LA ENTRADA AL CEMENTERIO SAGRADO» (AUD-814 + AUD-815 + AUD-816)

Documento de diseño del rebuild. Todo lo descrito existe en runtime y tiene
prueba o captura que lo demuestra (ver `docs/STAGE_4_1_AUDIT.md`); lo que no
se pudo cumplir se declara en §10, no se esconde.

AUD-815 (reconstrucción audiovisual): F4 incendiado por rayos con fin de
lluvia y persecución de la sombra; F5 con nubes que tapan la luna;
F6 camino de antorchas con templo de diez pasos; diálogos con retrato y
voz; transiciones anticipadas; aviso de salto en el primer vértice.

AUD-816 (reconstrucción visual estructural): pies exactamente sobre la
masa visual del suelo (tiles densos desde la fila 0 + sombra de
contacto); siluetas por grupos en vez de franjas punteadas; F2 duotono
verde-gris (ya no B&N); lluvia por capas con salpicadura; niebla
estratificada en F6; hitos por fase (mausoleo, costillar, gran quemado,
gran cruz, arco); tumbas variadas; diálogo final de Paburu.

## 1. Fantasía del jugador

> «Estoy entrando a un cementerio» → «Algo cambió» → «Esto ya no parece un
> cementerio» → «Algo me está observando» → «La tormenta oculta algo» →
> «¿Qué acaba de pasar?» → «No puedo ver nada» → «Ya no tengo miedo. Algo
> acaba de despertar.»

## 2. Estructura: seis espacios, no seis filtros

Cada fase tiene entrada, zona de exploración, landmark, fondo propio de
tres planos parallax, evento, transición y salida. Las dimensiones
(960×40, secciones de 160) derivan de esa necesidad, no del mapa anterior.

| Fase | Espacio | Color | Clima | Sonido |
|---|---|---|---|---|
| 1 | Cementerio de Tilarán | pleno | despejado | brisa + pájaros |
| 2 | Bosque del Venado | B&N | lluvia | lluvia de bosque |
| 3 | Osamentas de la Serpiente | grises | tormenta | tormenta + viento |
| 4 | Bosque talado del Halcón | sepia ámbar | lluvia | lluvia + aves |
| 5 | Planicie de los Muertos | nocturno azul | despejado | grillos + canto |
| 6 | Camino a Paburu | pleno + verde | niebla | solemnidad |

La transición F1→F2 (y todas) combina lluvia, luz, saturación gradual,
sonido, partículas y fondo: nunca un interruptor.

## 3. Protagonistas y espíritus

Jhon y Jin, guiados por los espíritus (cutscene inicial con voces
antiguas y referencia a Paburu). Venado (observación, apariciones
previas), Serpiente (tormenta, fondo que repta), Halcón (silencio, sombras,
gritos aislados). Cada uno: presencia → diálogo → altar (usar) →
ascensión con luz, sonido y mensaje → flag persistente.

## 4. Terror psicológico

Sin enemigos ni jumpscares: anticipación (apariciones, silueta F1, ojos
F2), silencio súbito + shake 14/0.45 s, sonido direccional (gritos y
crujidos fuera de cuadro), movimiento periférico (serpiente, sombras,
animal F2), oscuridad lunar con nubes, espacios vacíos. Regla: «algo está
aquí» sin que se pueda combatir.

## 4b. F4: incendio y persecución (AUD-815)

Tres rayos prenden tres piras en orden (cols 500/522/544); con la tercera
la lluvia CESA (pasa a despejado + brasas + crepitación) y empieza la
caza: una sombra grande sigue al jugador (acelera, se detiene, embiste con
shake + golpe). La captura llega a mitad de fase: silencio, la sombra
desaparece y habla el Halcón. El bosque incendiado son llamas, humo y tres
focos naranjas con parpadeo: nunca un filtro sobre el bosque verde.

## 5. La luna (F5)

La visibilidad depende de la luna: `_ambiente_base` oscila 0.45–0.75 con
periodo de 8 s (luz real del motor) y los muertos sólo se dibujan con luz
alta. AUD-815: las nubes tapan la luna por rachas (ciclo 16 s, la luz cae
un 65 %) y los muertos patrullan en procesión. Límite honesto: el suelo
global del motor (0.45) impide la oscuridad total; la fase va de penumbra
a noche clara, no a negro.

## 6. El camino (F6)

Niebla real, esporas verdes, 13 grietas con luz apagada: cada ~90 px
caminados encienden la más cercana con sonido posicional. AUD-815: cuatro
antorchas en orden (cols 830/860/890/920) con llama, humo, luz cálida y
aparición del espíritu correspondiente; al llegar (col 940) el templo
responde en diez pasos (mensajes, llamarada, temblor, voz de Paburu,
portal abierto) hacia `boss_paburu`. Terror → solemnidad. Paburu aparece
como silueta parcial (nunca completa) cuando los tres espíritus
ascendieron.

## 7. Despertar y puerta causal

`VENADO + SERPIENTE + HALCÓN liberados = PABURU puede despertar`
(estado derivado, no texto). El `WarpZone` final exige la llave
`paburu_despertado`: sin las tres liberaciones el portal duerme y lo
dice. Destino: `boss_paburu`. No hay `NextTrigger`: una salida automática
anularía la causalidad.

## 8. Easter egg

Lápidas del campanero (col 44) y la maestra (col 50): visibles, con
diálogo Jhon/Jin, integradas al camino. Ubicación documentada aquí y en
`docs/niveles/13_STAGE_4_1.md` §4.

## 9. Audio y música

Seis músicas y seis ambientes propios (sintetizados para el nivel,
`tools/generar_stage41_audio.py`), progresión voces→lluvia→bosque→
tormenta→aves→silencio→canto→solemnidad, transiciones con crossfade. El
silencio de la F4 para música y ambiente 6 s (diseño, no fallo).

## 10. Lo que este diseño NO pide (descope honesto)

- **2.5D / Y-depth**: el motor no tiene ese sistema; el pasillo lateral no
  lo necesita. Profundidad = 5 planos (3 parallax + mundo + frente).
- **Oscuridad total lunar**: vetada por el suelo global de luz (ver §5).
- **Cimas caminando sin saltar**: la cara empinada es muro por diseño del
  motor; las rampas se suben a pie, el vértice se corona saltando (aviso
  en el primer repiso, P0 verificado con bot de recorrido completo).
- **Paburu combatible aquí**: el jefe vive en `boss_paburu`; el 4.1
  entrega presencia, despertar y transición causal, no el combate.
- **Retrato de Jin**: el repo no trae arte de Jin; sus nodos muestran
  hablante sin retrato (mejor que un retrato ajeno). P3 de arte.
