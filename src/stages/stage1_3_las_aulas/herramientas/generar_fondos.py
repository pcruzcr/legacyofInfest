"""Convierte las fotos del aula real en las 3 capas de parallax del nivel.

Unidad V — Color y transparencia.

TECNICA: PERSPECTIVA ATMOSFERICA.  En el mundo real, cuanto mas lejos esta un
objeto, mas particulas de aire hay entre el y el ojo: pierde SATURACION, pierde
CONTRASTE y se aclara hacia el color del ambiente.  Se reproduce ese efecto
convirtiendo cada pixel a HSV y modificando S y V por separado, algo que en RGB
no se puede hacer sin alterar tambien el tono.

    RGB -> HSV        (ColorTools.rgb_to_hsv)
    S' = S * factor_saturacion
    V' = V * factor_brillo + desplazamiento
    HSV -> RGB        (ColorTools.hsv_to_rgb)

    BG_Far   S*0.25  -> casi gris, se funde con la pared
    BG_Mid   S*0.55
    BG_Near  S*0.85  -> casi el color original

El paso HSV se hace sobre una version reducida (es una conversion por pixel en
Python puro) y despues se reescala.  Como el fondo va desenfocado por estar
lejos, la perdida de resolucion no se nota.
"""
import sys
from pathlib import Path

import pygame

sys.path.insert(0, str(Path.cwd()))

from src.framework.processing.color_tools import ColorTools  # noqa: E402

ANCHO, ALTO = 800, 600
RES_HSV = (320, 240)  # resolucion del paso HSV

CAPAS = [
    # (archivo, capa, factor_saturacion, factor_brillo, desplazamiento_v, alpha)
    # `alpha` es la mezcla final contra un lienzo oscuro: el fondo tiene que
    # leerse como fondo y no competir con el pixel art del primer plano.
    ("aula1.jpg.jpeg", "far", 0.25, 0.55, 0.12, 0.30),
    ("aula2.jpg.jpeg", "mid", 0.55, 0.70, 0.06, 0.34),
    ("aula3.jpg.jpeg", "near", 0.85, 0.85, 0.02, 0.38),
]

# Lienzo de mezcla: gris oscuro CASI NEUTRO.  Se probo con el azul marino del
# motor (15,15,40) y, por ser un azul muy saturado, SUBIA la saturacion final
# (0.136 -> 0.308) y contradecia la perspectiva atmosferica que se busca.
FONDO_MOTOR = (20, 20, 24)

ORIGEN = Path(sys.argv[1])
DESTINO = Path(sys.argv[2])
DESTINO.mkdir(parents=True, exist_ok=True)

pygame.init()
pygame.display.set_mode((ANCHO, ALTO))


def procesar(sup: pygame.Surface, f_sat: float, f_bri: float, desp_v: float) -> pygame.Surface:
    """Aplica la perspectiva atmosferica pixel a pixel via HSV."""
    chico = pygame.transform.smoothscale(sup, RES_HSV)
    salida = pygame.Surface(RES_HSV)
    for y in range(RES_HSV[1]):
        for x in range(RES_HSV[0]):
            r, g, b = chico.get_at((x, y))[:3]
            h, s, v = ColorTools.rgb_to_hsv(r, g, b)
            s = max(0.0, min(1.0, s * f_sat))
            v = max(0.0, min(1.0, v * f_bri + desp_v))
            salida.set_at((x, y), ColorTools.hsv_to_rgb(h, s, v))
    return pygame.transform.smoothscale(salida, (ANCHO, ALTO))


for archivo, capa, f_sat, f_bri, desp_v, alpha in CAPAS:
    ruta = ORIGEN / archivo
    if not ruta.exists():
        print(f"  FALTA: {ruta}")
        continue
    original = pygame.image.load(str(ruta)).convert()
    print(f"{archivo}: {original.get_size()} -> procesando capa '{capa}'...")
    hsv = procesar(original, f_sat, f_bri, desp_v)

    # Mezcla alfa contra el color de fondo del motor:
    #     C_final = alpha * C_foto + (1 - alpha) * C_fondo
    lienzo = pygame.Surface((ANCHO, ALTO))
    lienzo.fill(FONDO_MOTOR)
    resultado = ColorTools.alpha_blend(hsv, lienzo, alpha)

    salida = DESTINO / f"bg_aulas_{capa}.png"
    pygame.image.save(resultado, str(salida))

    # Comparacion de saturacion media, para documentarlo en el README
    def sat_media(s: pygame.Surface) -> float:
        chico = pygame.transform.smoothscale(s, (80, 60))
        total = 0.0
        for y in range(60):
            for x in range(80):
                r, g, b = chico.get_at((x, y))[:3]
                total += ColorTools.rgb_to_hsv(r, g, b)[1]
        return total / 4800.0

    print(f"  -> {salida.name}  saturacion media: "
          f"{sat_media(original):.3f} -> {sat_media(resultado):.3f}")

print("\nListo. Capas en:", DESTINO)
