# Guía para dibujar el arte de Paburu a mano

Para reemplazar el arte generado por dibujo propio. Mientras respetes esto,
el juego carga los PNG nuevos sin tocar una línea de código.

## 1. Las hojas y sus tamaños

Cada archivo es una **tira horizontal**: los frames pegados uno al lado del
otro, sin márgenes ni separación. El ancho total es `frames × ancho`.

| Archivo | Frames | Frame | Lienzo total | FPS |
|---|---|---|---|---|
| `boss_paburu_stone.png` | 4 | 64×64 | 256×64 | 6 |
| `boss_paburu_hurt.png` | 4 | 64×64 | 256×64 | 12 |
| `boss_paburu_stone_slam.png` | 8 | 64×64 | 512×64 | 12 |
| `boss_paburu_stone_crack.png` | 8 | 64×64 | 512×64 | — |
| `boss_paburu_stone_proyectil.png` | 3 | 8×8 | 24×8 | — |
| `boss_paburu_mask.png` | 6 | 56×72 | 336×72 | 10 |
| `boss_paburu_gold.png` | 6 | 32×32 | 192×32 | 14 |
| `boss_paburu_black.png` | 6 | 32×32 | 192×32 | 14 |
| `boss_paburu_spirit.png` | 8 | 64×80 | 512×80 | 10 |

Van en **`assets/sprites/boss_paburu/`** con esos nombres exactos. Si cambia
el nombre o el tamaño de frame, hay que actualizar `FORM_SHEETS` en
`boss_paburu.py`.

## 2. Reglas del archivo

- **PNG con transparencia real (RGBA).** Fondo transparente, no blanco ni
  magenta. Lo que quede opaco es la silueta del boss.
- **Sin antialias.** Un borde suavizado a 64 px se ve como suciedad. En el
  editor: lápiz duro, 1 px, opacidad 100%.
- **Sin escalar.** Dibujá directo a 64×64. Si dibujás a 512 y reducís, el
  resultado queda borroso y con colores intermedios.
- Los frames se leen de izquierda a derecha, empezando en x=0.

## 3. La restricción que NO se puede romper

En la Forma 1, **los ojos tienen que quedar en las filas 38 a 41** del
frame de 64 px (contando desde arriba, empezando en 0).

De ahí sale el `EYE_BEAM`: el rayo nace en la fila 38 y mide 8 px de alto,
o sea ocupa 530..538 en coordenadas de mundo. Eso está calibrado contra el
hurtbox del jugador:

```
jugador de pie    → hurtbox y 532..560  → el rayo lo toca      (6 px de solape)
jugador agachado  → hurtbox y 542..560  → pasa por encima      (4 px de aire)
jugador en one-way→ hurtbox y 452..480  → pasa por debajo
```

Los márgenes son de 4 a 6 px. **Si subís los ojos, el rayo deja de pegarle
a un jugador de pie. Si los bajás, ya no se puede esquivar agachándose.**

Referencia de la anatomía actual (en coordenadas locales al frame de 64×64,
definidas en `boss_paburu.py`):

| Rasgo | Fila | Constante |
|---|---|---|
| Ojos | 38 | `EYE_DY = 38` |
| Boca | 52 | `MOUTH_DY = 52` |
| Cuencas (overlay del telegraph) | x 11-19 y 45-53, filas 38-41 | `EYE_BOXES` |

Si querés mover los ojos, cambiá `EYE_DY` y volvé a verificar los tres
casos de arriba. No es opcional: ya rompió el ataque una vez.

## 4. Flujo recomendado

1. Abrí el PNG actual de `assets/sprites/boss_paburu/` en la app.
2. Ponelo en una capa de fondo al 30% de opacidad como referencia de
   proporciones y de la línea de los ojos.
3. Dibujá encima en una capa nueva.
4. Borrá la capa de referencia y exportá con el mismo nombre, encima.
5. Corré el juego. Si la hoja está mal formada, `load_sheet` no la carga y
   vuelven los rectángulos grises — eso te avisa sin crashear.

## 5. Paleta

Sacada del Asset Bible (GDD §3.1). No hace falta respetarla al píxel, pero
mantener la familia hace que las cuatro formas se lean como un personaje.

| Color | Hex | Uso |
|---|---|---|
| Púrpura-negro | `#1a0d26` | fondo del cementerio |
| Piedra pálida | `#c8c3b8` | piedra a la luz |
| Verde espectral | `#00c864` | ojos, sello, energía |
| Dorado | `#e8b12c` | La Pepita, corona |
| Negro perla | `#0d0d14` | La Perla |

Rampa de la piedra verde que usa el generador, de sombra a luz:

```
#0e1612  #18261d  #243629  #324837  #425a45  #567056  #708a6c
```

## 6. Volver al arte generado

Los generadores siguen ahí y son deterministas. Si querés descartar un
dibujo y volver al punto de partida:

```
python tools/gen_paburu_art.py          # Forma 1
python tools/gen_paburu_art_formas.py   # Formas 2-4
```

Sobrescriben los PNG con lo mismo que había. No hay pérdida silenciosa:
lo que dibujes vos se pierde si corrés esto, así que guardá una copia de
tus versiones antes.
