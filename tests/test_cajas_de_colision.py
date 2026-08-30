"""
AUD-108 — las cajas de daño tienen que estar **dentro** del cuerpo.

El defecto, medido antes de arreglarlo
======================================
`EnemyBase._build_hurtbox` devuelve un rectángulo en coordenadas locales que
`_update_rects` suma a la posición::

    self.hurtbox = pygame.Rect(
        self.position.x + local.x, self.position.y + local.y,
        local.width, local.height,
    )

Diez de los doce cuerpos distintos del bestiario declaraban un desplazamiento
**sin encoger el tamaño**. `EnemyWalker`, por ejemplo::

    rect del cuerpo : 24 × 28
    _build_hurtbox  : Rect(4, 2, 24, 28)   ← mismo tamaño, desplazado

El resultado no es una caja ajustada al cuerpo: es **el cuerpo entero movido 4
px a la derecha y 2 hacia abajo**. Medido sobre el bestiario completo:

    enemigo            cuerpo              hurtbox en mundo    desalineación
    Walker             (100,72,24,28)      (104,74,24,28)      izq+4 der+4
    Flying             (101,104,20,14)     (107,108,20,14)     izq+6 der+6
    Shooter            (100,76,16,24)      (104,78,24,30)      izq+4 der+12
    Charger            (100,76,28,24)      (104,78,28,24)      izq+4 der+4
    Archer             (100,72,16,28)      (102,76,16,28)      izq+2 arr+4

Qué se siente al jugar
----------------------
En un `Flying` de 20 px de ancho, la caja está 6 px a la derecha: **el 30 % de
su cuerpo visible no se puede golpear** por la izquierda, y hay 6 px de aire a
su derecha que sí golpean. Contra un `Shooter`, la caja sobresale **12 px** por
la derecha: recibes daño de un enemigo que no está ahí.

Y como el desplazamiento es siempre hacia la derecha, atacar desde la izquierda
es sistemáticamente más difícil que desde la derecha, en todo el bestiario, en
los catorce escenarios.

El jugador lo hacía bien desde el principio, y por eso se sabe cuál era la
intención::

    return pygame.Rect(self.rect.x, self.rect.y + off_y, self.rect.width, h)
    #                  ↑ misma x        ↑ sólo recorte vertical  ↑ misma anchura

La invariante que se fija aquí
------------------------------
**Ninguna caja de daño puede salirse del cuerpo que la lleva.** Es comprobable,
vale para los 30 enemigos del bestiario y para los que registren los
estudiantes, y convierte un error de diseño silencioso en una prueba roja.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.entities import entity_factory
from src.framework.entities.enemy_base import EnemyBase
from src.framework.stage.stage_loader import StageLoader

#: Margen de tolerancia, en píxeles.
#:
#: Uno, y no cero: los cuerpos se colocan con `int()` sobre una posición en
#: coma flotante, así que un píxel de diferencia entre el rect y la caja es
#: redondeo y no un error de diseño. Dos ya sería medio dedo del jugador.
TOLERANCIA = 1


def _enemigos():
    entity_factory.ensure_registered()
    for nombre, cls in sorted(StageLoader._entity_registry.items()):
        try:
            e = cls(pygame.Vector2(100, 100))
        except Exception:
            continue
        if isinstance(e, EnemyBase):
            yield nombre, e


@pytest.fixture(scope="module", autouse=True)
def _pg():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 224))
    yield


def _fuera(caja: pygame.Rect, cuerpo: pygame.Rect) -> str:
    partes = []
    if caja.left < cuerpo.left - TOLERANCIA:
        partes.append(f"sobresale {cuerpo.left - caja.left} px por la izquierda")
    if caja.right > cuerpo.right + TOLERANCIA:
        partes.append(f"sobresale {caja.right - cuerpo.right} px por la derecha")
    if caja.top < cuerpo.top - TOLERANCIA:
        partes.append(f"sobresale {cuerpo.top - caja.top} px por arriba")
    if caja.bottom > cuerpo.bottom + TOLERANCIA:
        partes.append(f"sobresale {caja.bottom - cuerpo.bottom} px por abajo")
    return ", ".join(partes)


class TestLasCajasNoSeSalenDelCuerpo:
    def test_ninguna_hurtbox_sale_del_cuerpo(self):
        """La caja que recibe daño tiene que estar donde se ve al enemigo."""
        culpables = []
        for nombre, e in _enemigos():
            e.update(1.0 / 60.0)
            problema = _fuera(e.hurtbox, e.rect)
            if problema:
                culpables.append(
                    f"{nombre}: cuerpo {tuple(e.rect)}, hurtbox "
                    f"{tuple(e.hurtbox)} — {problema}",
                )
        assert not culpables, (
            "estas cajas de daño están fuera del cuerpo que las lleva; el "
            "jugador golpea donde no hay nada y recibe daño donde no hay "
            "enemigo:\n  " + "\n  ".join(culpables)
        )

    def test_ninguna_hitbox_sale_del_cuerpo(self):
        """La caja que hace daño, igual: no puede golpear desde fuera del cuerpo."""
        culpables = []
        for nombre, e in _enemigos():
            e.update(1.0 / 60.0)
            problema = _fuera(e.hitbox, e.rect)
            if problema:
                culpables.append(
                    f"{nombre}: cuerpo {tuple(e.rect)}, hitbox "
                    f"{tuple(e.hitbox)} — {problema}",
                )
        assert not culpables, (
            "estas cajas de golpe están fuera del cuerpo:\n  " + "\n  ".join(culpables)
        )

    def test_ninguna_caja_esta_vacia(self):
        """Una caja de área cero es un enemigo invulnerable e inofensivo."""
        vacias = []
        for nombre, e in _enemigos():
            e.update(1.0 / 60.0)
            for etiqueta, caja in (("hurtbox", e.hurtbox), ("hitbox", e.hitbox)):
                if caja.width <= 0 or caja.height <= 0:
                    vacias.append(f"{nombre}.{etiqueta} = {tuple(caja)}")
        assert not vacias, f"cajas de área cero: {vacias}"

    def test_la_caja_cubre_la_mayor_parte_del_cuerpo(self):
        """Una caja diminuta dentro de un cuerpo grande es igual de injusta.

        Con el 40 % del área basta para no penalizar los diseños que recortan a
        propósito —el Venado expone 30×40 de un cuerpo de 48×48, un 52 %— y
        detecta el caso contrario: una caja tan pequeña que el enemigo parece
        invulnerable.
        """
        pequenas = []
        for nombre, e in _enemigos():
            if nombre == "Shielded":
                continue  # AUD-721: vulnerable sólo por detrás, área pequeña a propósito
            e.update(1.0 / 60.0)
            area_cuerpo = e.rect.width * e.rect.height
            if area_cuerpo <= 0:
                continue
            fraccion = (e.hurtbox.width * e.hurtbox.height) / area_cuerpo
            if fraccion < 0.40:
                pequenas.append(f"{nombre}: la hurtbox cubre el {fraccion:.0%}")
        assert not pequenas, (
            "estas cajas son tan pequeñas que el enemigo parece invulnerable:\n  "
            + "\n  ".join(pequenas)
        )


class TestSimetriaIzquierdaDerecha:
    """Atacar por la izquierda no puede ser más difícil que por la derecha.

    Es la consecuencia que más se nota del defecto y la que ningún estudiante
    habría sabido nombrar: todos los desplazamientos iban hacia la derecha, así
    que el juego entero estaba sesgado a favor de un lado.
    """

    def test_la_caja_esta_centrada_horizontalmente_en_el_cuerpo(self):
        torcidas = []
        for nombre, e in _enemigos():
            # AUD-721 — Shielded es vulnerable sólo por detrás: su hurtbox
            # asimétrica es diseño, no defecto del centrado
            if nombre == "Shielded":
                continue
            e.update(1.0 / 60.0)
            margen_izq = e.hurtbox.left - e.rect.left
            margen_der = e.rect.right - e.hurtbox.right
            if abs(margen_izq - margen_der) > TOLERANCIA:
                torcidas.append(
                    f"{nombre}: {margen_izq} px de margen a la izquierda y "
                    f"{margen_der} a la derecha",
                )
        assert not torcidas, (
            "la caja no está centrada: golpear por un lado es más fácil que por "
            "el otro:\n  " + "\n  ".join(torcidas)
        )
