"""
Module: generar_dataset
System: stage (student assignment)
Academic Unit: Unidad VIII/IX — preparacion del dataset del Vigia.

Construye el dataset etiquetado del clasificador a partir de los sprites
REALES de los enemigos que hay en mi nivel. Dos clases:

    aereo      halcon (Flying), dron (FlyingBomber usa la hoja de vuelo)
    terrestre  paloma y garza (Walker), buitre y quetzal (Shooter)

Las muestras salen de la MISMA tuberia que corre en el juego
=============================================================
Cada muestra se fabrica pintando el sprite sobre un trozo del fondo real y
pasandolo por exactamente las mismas funciones que usa `Vigia` en ejecucion
—desenfoque, umbral de Otsu, inversion, apertura, componentes conectados— y
guardando el parche de la MASCARA que el clasificador recibiria. Las funciones
se importan de `vigia.py`, no se copian, para que no puedan separarse.

Dos intentos anteriores fallaron, y por eso esta asi:

1. *Recortes de pantalla en color.* 92,5% de precision en la prueba y fallaba
   casi todo en ejecucion. En un parche de 32x32 el enemigo ocupa 14x10 px, o
   sea que las HOG las dominaba el fondo: el modelo habia aprendido a separar
   "cielo" de "suelo", y como las muestras aereas salian del cielo y las
   terrestres del suelo, la prueba premiaba ese atajo.

2. *Siluetas sacadas del canal alfa del sprite.* Ya median forma y no fondo,
   pero una silueta perfecta del alfa no se parece a lo que deja Otsu sobre
   una pantalla desenfocada: bordes distintos, y 2 de 7 casos fallaban.

Uso:
    python src/stages/stage3_3_el_patio/generar_dataset.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import pygame  # noqa: E402

AQUI = Path(__file__).resolve().parent
SPRITES = RAIZ / "assets" / "sprites" / "enemies" / "zone3"
FONDOS = RAIZ / "assets" / "backgrounds" / "stage3_3_el_patio"

# (fichero, ancho_fotograma, alto_fotograma) por clase.
HOJAS: dict[str, list[tuple[str, int, int]]] = {
    "aereo": [
        ("enemy_flyinghalcon_walk.png", 14, 10),
        ("enemy_flyinghalcon_hurt.png", 14, 10),
        ("enemy_flyinghalcon_die.png", 14, 10),
        ("enemy_fly_zone3.png", 14, 10),
    ],
    "terrestre": [
        ("enemy_walkerpalom_walk.png", 16, 12),
        ("enemy_walkerpalom_hurt.png", 16, 12),
        ("enemy_walkergarza_walk.png", 16, 12),
        ("enemy_shooterbuitre_walk.png", 12, 12),
        ("enemy_shooterquetzal_walk.png", 12, 12),
        ("enemy_zone3_walk.png", 16, 12),
    ],
}

# Bandas del fondo sobre las que se compone cada clase. Ya no deciden nada
# —solo se guarda la silueta— pero cambian el contraste con el que Otsu corta,
# asi que dan variedad util en los bordes de la mascara. El fondo mide 600 px
# de alto y la ventana de analisis 128, asi que el limite superior de cada
# banda no puede pasar de 600-128.
BANDA_Y = {"aereo": (20, 200), "terrestre": (250, 460)}

VARIANTES = 24  # combinaciones de fondo/escala/espejo por fotograma; muchas se
# descartan porque el sprite no llega a segmentarse sobre ese fondo.


def fotogramas(ruta: Path, fw: int, fh: int) -> list[pygame.Surface]:
    hoja = pygame.image.load(str(ruta)).convert_alpha()
    return [hoja.subsurface(pygame.Rect(i * fw, 0, fw, fh)).copy()
            for i in range(hoja.get_width() // fw)]


def main() -> int:
    pygame.init()
    pygame.display.set_mode((1, 1))
    rng = random.Random(3)  # semilla fija: el dataset es reproducible

    from src.stages.stage3_3_el_patio.vigia import LADO_ANALISIS, Vigia

    vigia = Vigia.__new__(Vigia)  # solo para reutilizar su tuberia
    # El fondo VISIBLE del nivel es la capa `far`. `mid` y `near` existen pero
    # son PNG transparentes desde que el patio pasa a nocturno (una sola
    # pintura, sin planos de parallax), asi que componer sobre `near` daba
    # muestras sobre negro — y el modelo entrenado asi quedo ciego en el juego
    # real. Se compone sobre lo que de verdad se ve.
    fondo = pygame.image.load(str(FONDOS / "bg_stage3_3_el_patio_far.png")).convert()
    total: dict[str, int] = {}

    for clase, hojas in HOJAS.items():
        destino = AQUI / "dataset" / clase
        destino.mkdir(parents=True, exist_ok=True)
        for viejo in destino.glob("*.png"):
            viejo.unlink()
        y0, y1 = BANDA_Y[clase]
        n = 0
        for nombre, fw, fh in hojas:
            ruta = SPRITES / nombre
            if not ruta.exists():
                print(f"  aviso: falta {nombre}, lo salto")
                continue
            for fot in fotogramas(ruta, fw, fh):
                for v in range(VARIANTES):
                    lienzo = pygame.Surface((LADO_ANALISIS, LADO_ANALISIS))
                    bx = rng.randint(0, max(0, fondo.get_width() - LADO_ANALISIS))
                    by = rng.randint(y0, max(y0, min(y1, fondo.get_height() - LADO_ANALISIS)))
                    lienzo.blit(fondo, (0, 0),
                                pygame.Rect(bx, by, LADO_ANALISIS, LADO_ANALISIS))
                    sp = pygame.transform.flip(fot, True, False) if v % 2 else fot
                    escala = (1.0, 1.0, 1.25, 1.5)[v % 4]
                    if escala != 1.0:
                        sp = pygame.transform.scale_by(sp, escala)
                    px = LADO_ANALISIS // 2 - sp.get_width() // 2 + rng.randint(-24, 24)
                    py = LADO_ANALISIS // 2 - sp.get_height() // 2 + rng.randint(-24, 24)
                    lienzo.blit(sp, (px, py))

                    # La misma tuberia del juego, con las funciones del juego.
                    parche = vigia.parche_de(lienzo, (px + sp.get_width() / 2,
                                                      py + sp.get_height() / 2))
                    if parche is None:
                        continue
                    pygame.image.save(parche, str(destino / f"{clase}_{n:03d}.png"))
                    n += 1
        total[clase] = n
        print(f"  {clase:10s} {n} muestras")

    minimo = min(total.values()) if total else 0
    print(f"\nminimo por clase: {minimo} (la norma pide >= 10) -> "
          f"{'OK' if minimo >= 10 else 'INSUFICIENTE'}")
    return 0 if minimo >= 10 else 1


if __name__ == "__main__":
    raise SystemExit(main())
