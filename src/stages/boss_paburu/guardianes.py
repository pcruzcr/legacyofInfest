# Autor: Alejandro Josué Rodríguez Zamora
# Stage 4-2 «El Gran Shamán Paburu» — Legacy of InFest
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

#: El orden de la hoja y de `cargar()`: quién es cada frame.
NOMBRES = ("venado", "serpiente", "gavilan")


def suavizado(t: float) -> float:
    """Smoothstep 3t² − 2t³ (Unidad VI)."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


class Guardian:
    """Un espíritu a la deriva sobre el cementerio.

    `base` es su centro; se mueve alrededor sin alejarse nunca de ahí, para
    que la composición de la arena no se desarme.

    Desde la Forma 2 además PELEA (DISENO_NIVEL_Y_JEFE.md §3.4): la escena le
    pide su posición para lanzar el eco de su firma, y el parry devuelto lo
    puede TUMBAR. Un guardián no muere —ya está muerto—: cae, se apaga, y el
    llamado de Paburu lo levanta pasado `_caido` segundos. La caída es la
    única ventana que el jugador puede fabricarse contra la ronda, y por eso
    cuesta un parry, no un golpe.
    """

    __slots__ = (
        "_caida_total",
        "_caido",
        "_desp_retraso",
        "_desp_t",
        "alpha_amp",
        "alpha_base",
        "ax",
        "ay",
        "bx",
        "by",
        "frame",
        "nombre",
        "px",
        "py",
        "t",
        "w_alpha",
        "wx",
        "wy",
    )

    def __init__(self, frame: pygame.Surface, base: tuple[int, int],
                 amp: tuple[float, float], omega: tuple[float, float],
                 fase: tuple[float, float], alpha: tuple[int, int],
                 w_alpha: float, nombre: str = "") -> None:
        self.frame = frame
        self.bx, self.by = base
        self.ax, self.ay = amp
        self.wx, self.wy = omega
        self.px, self.py = fase
        self.alpha_base, self.alpha_amp = alpha
        self.w_alpha = w_alpha
        self.t = 0.0
        self.nombre = nombre
        self._caido = 0.0        # segundos que le quedan en el suelo
        self._caida_total = 1.0  # para dibujar la caída proporcional
        self._desp_t: float | None = None   # la despedida, si empezó
        self._desp_retraso = 0.0

    # ── El combate ──────────────────────────────────────────────
    def reubicar(self, base: tuple[float, float]) -> None:
        """Mueve el centro de deriva. La escena lo llama al sellar la arena.

        Las bases de `cargar()` son de la vista de 800 px alrededor del
        origen del mapa: en el cementerio la pelea ocurre en el círculo
        sorteado —a 900, a 2300, a 3300 px— y sin reubicarlos los tres
        espíritus quedaban fuera de pantalla exactamente durante la única
        parte del nivel en la que importan.
        """
        self.bx, self.by = base

    def pos(self) -> pygame.Vector2:
        """La posición actual de la deriva (centro del sprite), en mundo."""
        x = self.bx + math.sin(self.t * self.wx + self.px) * self.ax
        y = self.by + math.sin(self.t * self.wy + self.py) * self.ay
        if self._caido > 0.0:
            # Caído se hunde hacia el suelo de su franja del cielo.
            y += 46.0 * suavizado(1.0 - self._caido / self._caida_total)
        return pygame.Vector2(x, y)

    @property
    def esta_caido(self) -> bool:
        return self._caido > 0.0

    def tumbar(self, segundos: float = 6.0) -> None:
        """Lo saca de la ronda un rato. El llamado lo levanta solo."""
        self._caido = max(self._caido, segundos)
        self._caida_total = max(segundos, 0.001)

    def levantar(self) -> None:
        """El llamado de Paburu (ANCIENT_CALL lo usará explícitamente)."""
        self._caido = 0.0

    # ── La despedida (GDD §204: el epílogo del juicio) ──────────
    #: Duraciones de la reverencia y de la disolución.
    REVERENCIA = 0.9
    DISOLUCION = 0.8

    def despedirse(self, retraso: float = 0.0) -> None:
        """El custodio se inclina y se disuelve. No es derrota: es
        reencuentro (GDD §41) — esperaron siglos para esto."""
        if self._desp_t is None:
            self._desp_t = 0.0
            self._desp_retraso = retraso
            self._caido = 0.0        # de rodillas no: en pie para inclinarse

    @property
    def se_despidio(self) -> bool:
        return (self._desp_t is not None
                and self._desp_t - self._desp_retraso
                >= self.REVERENCIA + self.DISOLUCION)

    def _despedida_fase(self) -> tuple[float, float]:
        """(reverencia 0..1, disolución 0..1) del momento actual."""
        if self._desp_t is None:
            return 0.0, 0.0
        t = self._desp_t - self._desp_retraso
        if t <= 0.0:
            return 0.0, 0.0
        rev = min(1.0, t / self.REVERENCIA)
        dis = min(1.0, max(0.0, (t - self.REVERENCIA) / self.DISOLUCION))
        return rev, dis

    def update(self, dt: float) -> None:
        self.t += dt
        if self._caido > 0.0:
            self._caido = max(0.0, self._caido - dt)
        if self._desp_t is not None:
            self._desp_t += dt

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
        if presencia <= 0.01 or self.se_despidio:
            return
        p = self.pos()
        rev, dis = self._despedida_fase()
        if rev > 0.0:
            # La reverencia: baja la cabeza —el cuerpo entero, a esta
            # escala— con el mismo smoothstep de todo el stage; después la
            # disolución se lo lleva hacia arriba, no hacia abajo: se van
            # al reencuentro, no al suelo.
            p.y += 14.0 * suavizado(rev) - 30.0 * suavizado(dis)
        a = self.alpha_base + self.alpha_amp * (
            0.5 + 0.5 * math.sin(self.t * self.w_alpha)
        )
        if self._caido > 0.0:
            # Caído se apaga a un cuarto: sigue ahí —no murió—, pero el
            # jugador VE que lo sacó de la ronda. Sin esta señal, tumbar a
            # un guardián no se sentiría como nada.
            a *= 0.25
        if dis > 0.0:
            a *= max(0.0, 1.0 - dis)
        self.frame.set_alpha(int(max(0, min(255, a * presencia))))
        surface.blit(
            self.frame,
            (int(p.x - CELDA_W / 2 - offset.x), int(p.y - CELDA_H / 2 - offset.y)),
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
    return [Guardian(f, *d, nombre=n)
            for f, d, n in zip(frames, datos, NOMBRES, strict=False)]
