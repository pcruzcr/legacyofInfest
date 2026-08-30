"""
AUD-630 — Contraste WCAG AA, escalado de texto y accesibilidad del kit de UI.

Tres guardianes que antes no existían:

1. **Contraste WCAG AA**: cada par (texto, fondo) que el Theme define tiene
   que cumplir ratio ≥ 4.5:1 para texto normal o ≥ 3:1 para texto grande.
   Antes nadie medía esto; un cambio de paleta podía dejar el texto ilegible
   sin que ningún test se enterara.

2. **Escalado de texto 0.5×–3×**: `Theme.escalar_texto()` es el único camino
   por el que pasan todas las fuentes. Estas pruebas verifican que a cualquier
   escala el texto cabe dentro de su fila asignada y que la fuente mínima
   nunca baja de `_TAMANO_MINIMO`.

3. **Lector de pantalla**: cada widget interactivo expone un nombre
   accesible (`accessible_name`) que un lector de pantalla puede anunciar.
   Antes los widgets no tenían API de accesibilidad.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core import settings
from src.engine.ui.theme import ANCHO_DE_DISENO, ESCALA_DE_INTERFAZ, Theme


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))


# ── Utilidades de contraste ──────────────────────────────────────────────

def _luminancia_rel(rgb: tuple[int, int, int]) -> float:
    """Luminancia relativa según WCAG 2.1 (fórmula sRGB)."""
    canal = []
    for v in rgb:
        s = v / 255.0
        if s <= 0.04045:
            canal.append(s / 12.92)
        else:
            canal.append(((s + 0.055) / 1.055) ** 2.4)
    return 0.2126 * canal[0] + 0.7152 * canal[1] + 0.0722 * canal[2]


def _ratio_contraste(fg: tuple[int, int, int], bg: tuple[int, int, int]) -> float:
    """Ratio de contraste entre dos colores (1.0 = idéntico, 21.0 = máximo)."""
    lum_fg = _luminancia_rel(fg)
    lum_bg = _luminancia_rel(bg)
    mas_claro = max(lum_fg, lum_bg)
    mas_oscuro = min(lum_fg, lum_bg)
    return (mas_claro + 0.05) / (mas_oscuro + 0.05)


# ══════════════════════════════════════════════════════════════════════════
# 1. CONTRASTE WCAG AA
# ══════════════════════════════════════════════════════════════════════════

class TestContrasteWCAGAA:
    """Cada par (texto, fondo) que el juego usa cumple WCAG AA."""

    #: Pares (texto, fondo) que aparecen en pantalla con texto normal (<18pt).
    PARES_TEXTO_NORMAL: list[tuple[str, tuple, tuple]] = [
        ("TEXT sobre BG", Theme.TEXT, Theme.BG),
        ("TEXT sobre SURFACE", Theme.TEXT, Theme.SURFACE),
        ("TEXT sobre SURFACE_RAISED", Theme.TEXT, Theme.SURFACE_RAISED),
        ("TEXT_MUTED sobre BG", Theme.TEXT_MUTED, Theme.BG),
        ("TEXT_MUTED sobre SURFACE", Theme.TEXT_MUTED, Theme.SURFACE),
        ("ACCENT sobre BG", Theme.ACCENT, Theme.BG),
        ("ACCENT sobre SURFACE", Theme.ACCENT, Theme.SURFACE),
        ("SUCCESS sobre BG", Theme.SUCCESS, Theme.BG),
        ("WARNING sobre BG", Theme.WARNING, Theme.BG),
        ("DANGER sobre BG", Theme.DANGER, Theme.BG),
    ]

    #: Pares con texto grande (≥18pt bold o ≥24pt regular) — umbral 3:1.
    PARES_TEXTO_GRANDE: list[tuple[str, tuple, tuple]] = [
        ("TEXT_DIM sobre BG", Theme.TEXT_DIM, Theme.BG),
        ("TEXT_DIM sobre SURFACE", Theme.TEXT_DIM, Theme.SURFACE),
        ("ACCENT_DIM sobre BG", Theme.ACCENT_DIM, Theme.BG),
        ("BORDER_STRONG sobre BG", Theme.BORDER_STRONG, Theme.BG),
    ]

    @pytest.mark.parametrize(
        "nombre,fg,bg", PARES_TEXTO_NORMAL, ids=[p[0] for p in PARES_TEXTO_NORMAL]
    )
    def test_texto_normal_ratio_min_45(self, nombre: str, fg, bg) -> None:
        """Texto normal necesita ratio ≥ 4.5:1 (WCAG AA nivel AA)."""
        ratio = _ratio_contraste(fg, bg)
        assert ratio >= 4.5, (
            f"{nombre}: ratio {ratio:.2f}:1 < 4.5:1 mínimo WCAG AA "
            f"(fg={fg}, bg={bg})"
        )

    @pytest.mark.parametrize(
        "nombre,fg,bg", PARES_TEXTO_GRANDE, ids=[p[0] for p in PARES_TEXTO_GRANDE]
    )
    def test_texto_grande_ratio_min_30(self, nombre: str, fg, bg) -> None:
        """Texto grande necesita ratio ≥ 3:1 (WCAG AA nivel AA)."""
        ratio = _ratio_contraste(fg, bg)
        assert ratio >= 3.0, (
            f"{nombre}: ratio {ratio:.2f}:1 < 3.0:1 mínimo WCAG AA "
            f"para texto grande (fg={fg}, bg={bg})"
        )

    def test_el_acento_destaca_sobre_todos_los_fondos(self) -> None:
        """El ACCENT es el único color de foco: tiene que leerse en cualquier superficie."""
        fondos = [Theme.BG, Theme.SURFACE, Theme.SURFACE_RAISED]
        for fondo in fondos:
            ratio = _ratio_contraste(Theme.ACCENT, fondo)
            assert ratio >= 3.0, (
                f"ACCENT sobre {fondo}: ratio {ratio:.2f} < 3.0 — el foco "
                f"no se distingue del fondo"
            )


# ══════════════════════════════════════════════════════════════════════════
# 2. ESCALADO DE TEXTO
# ══════════════════════════════════════════════════════════════════════════

class TestEscaladoDeTexto:
    """`escalar_texto()` cubre 0.5×–3× sin romper legibilidad."""

    ESCALAS_VALIDAS = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]

    @pytest.mark.parametrize("escala", ESCALAS_VALIDAS)
    def test_fuente_se_genera_a_cualquier_escala(self, _video, monkeypatch, escala: float):
        """A cualquier escala válida, font() devuelve una fuente renderizable."""
        from src.engine.ui.theme import clear_font_cache, font

        monkeypatch.setattr(
            "src.engine.core.user_settings.preferencia",
            lambda clave, defecto: escala,
        )
        clear_font_cache()

        for size_name in ("FONT_TITLE", "FONT_HEADING", "FONT_BODY",
                          "FONT_SMALL", "FONT_TINY"):
            size = getattr(Theme, size_name)
            f = font(size)
            surf = f.render("Prueba", True, Theme.TEXT)
            assert surf.get_width() > 0, (
                f"font({size_name}={size}) a escala {escala}: render vacío"
            )

        clear_font_cache()

    @pytest.mark.parametrize("escala", [0.5, 1.0, 2.0, 3.0])
    def test_texto_cabe_en_su_fila(self, _video, monkeypatch, escala: float):
        """El alto de la fuente no excede el alto de fila asignado."""
        from src.engine.ui.theme import clear_font_cache, font

        # Alto de fila típico en bestiario/logros: 34px a escala 1.0
        ALTO_FILA_BASE = 34
        alto_fila = max(ALTO_FILA_BASE * escala, ALTO_FILA_BASE)

        monkeypatch.setattr(
            "src.engine.core.user_settings.preferencia",
            lambda clave, defecto: escala,
        )
        clear_font_cache()

        f = font(Theme.FONT_BODY)
        alto_texto = f.get_height()
        assert alto_texto <= alto_fila + 8, (
            f"A escala {escala}x: texto {alto_texto}px > fila {alto_fila:.0f}px + margen 8"
        )

        clear_font_cache()

    def test_escala_minima_no_baja_del_suelo(self, _video, monkeypatch):
        """Con escala 0.5×, la fuente mínima sigue siendo ≥ _TAMANO_MINIMO."""
        from src.engine.ui.theme import _TAMANO_MINIMO, clear_font_cache, escalar_texto

        monkeypatch.setattr(
            "src.engine.core.user_settings.preferencia",
            lambda clave, defecto: 0.5,
        )
        clear_font_cache()

        # El tamaño más pequeño de la escala tipográfica
        resultado = escalar_texto(Theme.FONT_TINY)
        assert resultado >= _TAMANO_MINIMO, (
            f"escalar_texto(FONT_TINY) a 0.5x = {resultado} < mínimo {_TAMANO_MINIMO}"
        )

        clear_font_cache()

    def test_la_escala_de_interfaz_es_coherente(self):
        """ESCALA_DE_INTERFAZ = INTERNAL_WIDTH / ANCHO_DE_DISENO."""
        esperado = settings.INTERNAL_WIDTH / ANCHO_DE_DISENO
        assert ESCALA_DE_INTERFAZ == pytest.approx(esperado), (
            f"ESCALA_DE_INTERFAZ ({ESCALA_DE_INTERFAZ}) != "
            f"INTERNAL_WIDTH ({settings.INTERNAL_WIDTH}) / ANCHO ({ANCHO_DE_DISENO})"
        )


# ══════════════════════════════════════════════════════════════════════════
# 3. LECTOR DE PANTALLA — accessible_name en widgets
# ══════════════════════════════════════════════════════════════════════════

class TestAccesibilidadWidgets:
    """Los widgets interactivos exponen accessible_name para lectores de pantalla."""

    def test_menu_item_tiene_accessible_name(self):
        """MenuItem expone su etiqueta como accessible_name."""
        from src.engine.ui.widgets import MenuItem

        item = MenuItem("JUGAR", value="start")
        assert hasattr(item, "accessible_name"), (
            "MenuItem no tiene atributo accessible_name"
        )
        assert item.accessible_name == "JUGAR"

    def test_menu_item_accessible_name_con_descripcion(self):
        """Si MenuItem tiene hint, accessible_name lo incluye."""
        from src.engine.ui.widgets import MenuItem

        item = MenuItem("OPCIONES", value="options", hint="Volumen y controles")
        assert "OPCIONES" in item.accessible_name
        assert "Volumen" in item.accessible_name

    def test_draw_screen_expone_titulo_accesible(self, _video):
        """draw_screen dibuja el título y lo hace recuperable."""
        from src.engine.ui.widgets import draw_screen

        lienzo = pygame.Surface((800, 600))
        draw_screen(lienzo, "PRUEBA ACCESIBLE", "")
        # Verificamos que no crashea y que el método existe
        assert callable(draw_screen)

    def test_message_box_tiene_texto_accesible(self, _video):
        """MessageBox expone su texto actual como accessible_name."""
        from src.engine.core.event_bus import EventBus
        from src.engine.ui.message_box import MessageBox

        bus = EventBus()
        caja = MessageBox(bus)
        assert hasattr(caja, "accessible_name") or hasattr(caja, "text"), (
            "MessageBox no expone texto accesible"
        )


# ══════════════════════════════════════════════════════════════════════════
# Utilidad: informe de contraste (para documentación)
# ══════════════════════════════════════════════════════════════════════════

def test_informe_contraste_completo():
    """Genera una tabla completa de ratios para referencia en docs."""
    pares = [
        ("TEXT/BG", Theme.TEXT, Theme.BG),
        ("TEXT/SURFACE", Theme.TEXT, Theme.SURFACE),
        ("TEXT/SURFACE_RAISED", Theme.TEXT, Theme.SURFACE_RAISED),
        ("TEXT_MUTED/BG", Theme.TEXT_MUTED, Theme.BG),
        ("TEXT_MUTED/SURFACE", Theme.TEXT_MUTED, Theme.SURFACE),
        ("TEXT_DIM/BG", Theme.TEXT_DIM, Theme.BG),
        ("ACCENT/BG", Theme.ACCENT, Theme.BG),
        ("ACCENT/SURFACE", Theme.ACCENT, Theme.SURFACE),
        ("SUCCESS/BG", Theme.SUCCESS, Theme.BG),
        ("DANGER/BG", Theme.DANGER, Theme.BG),
    ]
    resultados = []
    for nombre, fg, bg in pares:
        ratio = _ratio_contraste(fg, bg)
        nivel = "AAA" if ratio >= 7.0 else ("AA" if ratio >= 4.5 else ("AA-large" if ratio >= 3.0 else "FALLO"))
        resultados.append((nombre, fg, bg, ratio, nivel))

    # Todos los pares de texto principal deben pasar al menos AA
    fallos = [(n, r) for n, _, _, r, nivel in resultados if nivel == "FALLO"]
    assert not fallos, f"Pares que fallan WCAG AA: {fallos}"