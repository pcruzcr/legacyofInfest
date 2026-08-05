"""AUD-278 — la luz atravesaba las paredes.

El defecto
==========
`LightSystem.render` pega el degradado de cada foco sobre la máscara de
ambiente y ya está. La geometría del nivel **no participa**: una antorcha al
otro lado de un muro de tres metros ilumina igual que si el muro no existiera,
y un pasillo con una luz al fondo se ve entero aunque haya una columna en
medio.

Se nota sobre todo de noche, que es cuando `ambient_light` baja y los focos son
lo único que hay: el jugador ve un halo perfectamente redondo pintado sobre una
pared maciza.

Cómo se resuelve
----------------
Proyección de silueta, que es lo que hace cualquier motor 2D con luces: desde
el foco, cada rectángulo tapa una cuña: se toman sus dos esquinas extremas
—las que abarcan el mayor ángulo visto desde la luz— y se alargan hacia fuera
hasta salir del alcance del foco. Lo que queda dentro de esa cuña, no se
ilumina.

**Apagado por defecto**, y no por prudencia genérica: cuesta una proyección por
foco y por obstáculo, y el reporte 87 §11 lo dejó anotado como «viable, con
coste; hay que medirla antes de encenderla por defecto». La propiedad de mapa
la enciende quien la quiera.

La rejilla de AUD-276 es lo que lo hace barato: sólo se proyectan los
rectángulos que caen dentro del alcance del foco, no los miles del mapa.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.vfx.sombras_proyectadas import ProyectorDeSombras, silueta_de


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


class TestLaSilueta:
    def test_un_bloque_a_la_derecha_da_dos_esquinas(self) -> None:
        bloque = pygame.Rect(200, 100, 40, 40)

        a, b = silueta_de(pygame.Vector2(0, 120), bloque)

        assert a != b

    def test_las_esquinas_son_del_bloque(self) -> None:
        bloque = pygame.Rect(200, 100, 40, 40)
        esquinas = {(200, 100), (240, 100), (200, 140), (240, 140)}

        a, b = silueta_de(pygame.Vector2(0, 120), bloque)

        assert (a.x, a.y) in esquinas
        assert (b.x, b.y) in esquinas

    def test_desde_dentro_no_hay_silueta(self) -> None:
        """Un foco dentro de un muro no proyecta: no hay «detrás»."""
        bloque = pygame.Rect(0, 0, 100, 100)

        assert silueta_de(pygame.Vector2(50, 50), bloque) is None

    def test_la_silueta_cambia_con_la_posicion_del_foco(self) -> None:
        bloque = pygame.Rect(200, 100, 40, 40)

        desde_izquierda = silueta_de(pygame.Vector2(0, 120), bloque)
        desde_arriba = silueta_de(pygame.Vector2(220, 0), bloque)

        assert desde_izquierda != desde_arriba


class TestLaSombraSeDibuja:
    def test_detras_del_bloque_queda_a_oscuras(self) -> None:
        mascara = pygame.Surface((800, 600), pygame.SRCALPHA)
        mascara.fill((255, 255, 255, 255))
        proyector = ProyectorDeSombras()

        proyector.proyectar(
            mascara, pygame.Vector2(100, 300), 400.0,
            [pygame.Rect(300, 200, 40, 200)], pygame.Vector2(0, 0))

        # Justo detrás del bloque, en la línea del foco.
        assert mascara.get_at((420, 300))[:3] == (0, 0, 0)

    def test_delante_del_bloque_sigue_iluminado(self) -> None:
        mascara = pygame.Surface((800, 600), pygame.SRCALPHA)
        mascara.fill((255, 255, 255, 255))
        proyector = ProyectorDeSombras()

        proyector.proyectar(
            mascara, pygame.Vector2(100, 300), 400.0,
            [pygame.Rect(300, 200, 40, 200)], pygame.Vector2(0, 0))

        assert mascara.get_at((200, 300))[:3] == (255, 255, 255)

    def test_sin_obstaculos_no_toca_nada(self) -> None:
        mascara = pygame.Surface((800, 600), pygame.SRCALPHA)
        mascara.fill((255, 255, 255, 255))

        ProyectorDeSombras().proyectar(
            mascara, pygame.Vector2(100, 300), 400.0, [], pygame.Vector2(0, 0))

        assert mascara.get_at((420, 300))[:3] == (255, 255, 255)

    def test_lo_que_esta_fuera_del_alcance_no_proyecta(self) -> None:
        """Un muro a mil píxeles de una antorcha de cien no tapa nada."""
        mascara = pygame.Surface((800, 600), pygame.SRCALPHA)
        mascara.fill((255, 255, 255, 255))

        ProyectorDeSombras().proyectar(
            mascara, pygame.Vector2(100, 300), 80.0,
            [pygame.Rect(600, 200, 40, 200)], pygame.Vector2(0, 0))

        assert mascara.get_at((700, 300))[:3] == (255, 255, 255)


class TestApagadoPorDefecto:
    def test_stage_data_lo_declara_apagado(self) -> None:
        import dataclasses

        from src.framework.stage.stage_loader import StageData

        por_nombre = {f.name: f.default for f in dataclasses.fields(StageData)}
        assert por_nombre["sombras_proyectadas"] is False

    def test_ningun_mapa_entregado_lo_enciende(self) -> None:
        from pathlib import Path

        raiz = Path(__file__).resolve().parents[1]
        con_prop = [
            p.name for p in (raiz / "assets" / "maps").rglob("*.tmx")
            if 'name="sombras_proyectadas"' in p.read_text(
                encoding="utf-8", errors="replace")
        ]
        assert not con_prop, f"ya lo usaban: {con_prop}"

    def test_el_sistema_de_luz_sabe_recibirlas(self) -> None:
        from src.framework.vfx.lighting import LightSystem

        assert hasattr(LightSystem, "set_obstaculos")
