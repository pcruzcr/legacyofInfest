"""
Module: guardianes
System: stages.boss_paburu
Academic Unit: II (vectores), VI (interpolación y movimiento paramétrico)
Description: Los tres guardianes espectrales de Paburu — venado, serpiente
             y gavilán (GDD §2.3).

POR QUÉ EXISTE
Estaban pintados DENTRO de `bg_paburu_mid.png`. Un fondo es una imagen
estática, así que quedaban clavados en el cielo: tres siluetas inmóviles,
del mismo tamaño y a la misma altura, repartidas por la franja de arriba.
Se leían como calcomanías pegadas al vidrio.

El lore §2.3 dice otra cosa: son los guardianes que acompañaron a Paburu en
vida y **llevan siglos esperándolo**, tanto como él esperó a los portadores.
Eso no lo comunica una silueta quieta. Acá cada uno tiene su propia deriva,
su propio ritmo y su propio desfase.

CÓMO SE MUEVEN (Unidad VI)
Trayectoria de Lissajous: dos senos de frecuencia distinta, uno por eje.

    x(t) = cx + Ax · sen(ωx · t + φx)
    y(t) = cy + Ay · sen(ωy · t + φy)

Cuando ωx y ωy no son múltiplos enteros entre sí, la curva **no se cierra**:
el recorrido tarda muchísimo en repetirse y el ojo nunca le encuentra el
patrón. Con un solo seno por eje, o con frecuencias proporcionales, se vería
un vaivén de péndulo — que es justo el aspecto mecánico que se quería
evitar.

El alfa también respira, con un tercer período distinto: aparecen y se
desvanecen sin sincronizarse entre ellos ni consigo mismos.
"""
from __future__ import annotations

import math
from pathlib import Path

import pygame

HOJA = Path("assets/backgrounds/paburu/paburu_guardianes.png")
CELDA_W, CELDA_H = 160, 120


class Guardian:
    """Un espíritu a la deriva sobre el cementerio.

    `base` es su centro; se mueve alrededor sin alejarse nunca de ahí, para
    que la composición de la arena no se desarme.
    """

    __slots__ = ("frame", "bx", "by", "ax", "ay", "wx", "wy", "px", "py",
                 "alpha_base", "alpha_amp", "w_alpha", "t")

    def __init__(self, frame: pygame.Surface, base: tuple[int, int],
                 amp: tuple[float, float], omega: tuple[float, float],
                 fase: tuple[float, float], alpha: tuple[int, int],
                 w_alpha: float) -> None:
        self.frame = frame
        self.bx, self.by = base
        self.ax, self.ay = amp
        self.wx, self.wy = omega
        self.px, self.py = fase
        self.alpha_base, self.alpha_amp = alpha
        self.w_alpha = w_alpha
        self.t = 0.0

    def update(self, dt: float) -> None:
        self.t += dt

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2,
             presencia: float = 1.0) -> None:
        """`presencia` va de 0 (no están) a 1 (materializados del todo).

        La maneja la escena según la forma del boss: en la Forma 1 los
        guardianes NO están. Aparecen recién con la Máscara, que es cuando
        Paburu se decide a llamarlos (GDD §2.1: la Forma 2 "juzga con la
        tradición — invoca lo que ya venciste"). Tenerlos siempre en el
        cielo gastaba la aparición: si están desde el primer segundo, que
        después bajen a pelear no sorprende a nadie.
        """
        if presencia <= 0.01:
            return
        x = self.bx + math.sin(self.t * self.wx + self.px) * self.ax
        y = self.by + math.sin(self.t * self.wy + self.py) * self.ay
        a = self.alpha_base + self.alpha_amp * (
            0.5 + 0.5 * math.sin(self.t * self.w_alpha)
        )
        self.frame.set_alpha(int(max(0, min(255, a * presencia))))
        surface.blit(
            self.frame,
            (int(x - CELDA_W / 2 - offset.x), int(y - CELDA_H / 2 - offset.y)),
        )


def cargar() -> list[Guardian]:
    """Los tres guardianes con sus parámetros. [] si falta la hoja.

    Los valores están elegidos para que ninguno comparta frecuencia con
    otro: si dos coincidieran, se moverían a la par y volverían a leerse
    como un adorno repetido.

    El venado va más lento y más tenue —es el más lejano—, el gavilán más
    rápido y más brillante. La serpiente deriva más en horizontal que en
    vertical, que es como se mueve una serpiente.
    """
    if not HOJA.exists():
        return []
    hoja = pygame.image.load(str(HOJA)).convert_alpha()
    frames = [
        hoja.subsurface(pygame.Rect(i * CELDA_W, 0, CELDA_W, CELDA_H)).copy()
        for i in range(3)
    ]
    # El alfa se mide sobre la hoja YA compuesta con su halo, así que
    # bajarlo apaga el resplandor junto con el cuerpo. Con los valores del
    # primer intento (26-44) las figuras quedaban planas otra vez: se
    # movían, pero habían perdido lo espectral. Estos las devuelven a la
    # presencia que tenían horneadas en el fondo, sin taparlo.
    #        base         amplitud    frecuencia      fase       alfa      ω alfa
    datos = (
        ((132, 238), (26.0, 14.0), (0.21, 0.33), (0.0, 1.7), (52, 22), 0.24),
        ((402, 188), (38.0, 11.0), (0.17, 0.41), (2.1, 0.4), (64, 26), 0.31),
        ((668, 198), (22.0, 20.0), (0.29, 0.19), (1.2, 2.6), (78, 30), 0.19),
    )
    return [Guardian(f, *d) for f, d in zip(frames, datos)]
