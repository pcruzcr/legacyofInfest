# Autor: Alejandro Josué Rodríguez Zamora
# Stage 4-2 «El Gran Shamán Paburu» — Legacy of InFest
"""
Module: skins
System: stages.boss_paburu
Academic Unit: V (color y paleta)
Description: El arte propio de las mecánicas del motor en el camposanto
             (tarea #44).

POR QUÉ EXISTE
El circuito del mausoleo usa las piezas del motor —cofre, puerta, jaula,
llave— y el motor las dibuja como rectángulos planos de color genérico.
Su propia documentación lo asume temporal: «el estudiante lo sustituye
por su arte cuando lo tenga» (`drawing_system.py`). Este es ese arte: en
un nivel con dirección visual fuerte, un cofre marrón de catálogo delata
que la pieza no pertenece al lugar.

CÓMO — SIN TOCAR EL FRAMEWORK
`DrawingSystem` es un atributo de la escena (`self._drawing`), así que se
SUBCLASEA aquí y la escena instala la variante — el mismo patrón que
`intro.py` usa con `CutsceneAction`. Solo se redefine
`_draw_interactables`; todo lo demás (mapa, entidades, HUD) sigue siendo
del motor. Los recogibles conservan su `icon_color` del catálogo (AUD-234
existe justamente para distinguirlos) — solo cambia el MARCO de lo que se
dibuja, no su información.

EL LÍMITE, DOCUMENTADO (la otra mitad de #44)
Las mecánicas del ECS —balsas (`PlataformaMovil`), bloques rítmicos,
resortes— NO se pueden skinear desde el stage sin costos inaceptables:
`dibujar_mecanicas_ecs` es una función de módulo llamada en un punto fijo
de `dibujar_ui` (post-luz, pre-HUD, AUD-242) sin ningún hook. Las dos
vías posibles se descartaron con motivo: duplicar `dibujar_ui` en la
escena es un fork que se rompe con cada cambio del motor; sobrepintar
desde `Scene.draw` cae ENCIMA del HUD (violación de orden z que se ve en
cuanto una balsa cruza bajo la barra del jefe). Se acepta el dibujo del
motor para esa familia — mitigado porque los bloques rítmicos ya laten
con la canción (mejora C), que es identidad más fuerte que un tinte.

LA PALETA es la del tileset del camposanto (piedra caliza y oro Tilawa),
no colores nuevos: las piezas deben leerse como talladas por las mismas
manos que la Sala.
"""
from __future__ import annotations

from typing import Any

import pygame

from src.framework.stage.drawing_system import DrawingSystem

# Piedra del camposanto y oro ritual (mismas familias que el tileset).
PIEDRA_HI = (200, 195, 184)
PIEDRA = (156, 150, 138)
PIEDRA_DK = (96, 92, 84)
PIEDRA_NEGRA = (44, 42, 40)
ORO = (232, 177, 44)
ORO_DK = (150, 112, 30)
MADERA = (94, 70, 46)
MADERA_DK = (58, 44, 30)


class DibujoDelCamposanto(DrawingSystem):
    """El `DrawingSystem` del motor con las piezas del mausoleo talladas."""

    def _draw_interactables(
        self, surface: pygame.Surface, sistema: Any, offset: pygame.Vector2,
    ) -> None:
        """Mismo contrato que el original; cambia solo el pincel.

        Los disparadores siguen sin dibujarse (son invisibles a propósito)
        y los recogibles conservan `icon_color` — con un remate de brillo
        para que la llave del juicio se lea como metal y no como ficha.
        """
        from src.engine.core.inventory import get_inventory
        inventario = get_inventory()

        for objeto in getattr(sistema, "recogibles", ()):
            if objeto.recogido:
                continue
            r = objeto.rect.move(-offset.x, -offset.y)
            # LAS OFRENDAS («los coins», playtest de Alejandro dos veces:
            # «se ven como cuadros y no como monedas reales» y «te dije de
            # los coins y no me dijiste nada»). El motor las pinta como
            # rectángulo redondeado del color del catálogo; aquí son lo
            # que el mapa dice que son: una ofrenda — un montoncito de
            # monedas dejado a los muertos, no una ficha de arcade.
            if objeto.item_id == "coin":
                surface.blit(self._pila_de_ofrenda(), r.topleft)
                continue
            defn = inventario.get_def(objeto.item_id)
            color = defn.icon_color if defn is not None else ORO
            pygame.draw.rect(surface, color, r, border_radius=3)
            pygame.draw.rect(surface, PIEDRA_NEGRA, r, 1, border_radius=3)
            # El brillo: una esquina de luz, como en las reliquias.
            pygame.draw.line(surface, (255, 250, 230),
                             (r.left + 2, r.top + 2), (r.left + 5, r.top + 2))

        for cerradura in getattr(sistema, "cerraduras", ()):
            r = cerradura.rect.move(-offset.x, -offset.y)
            # LA LOSA DEL JUICIO (D-01·D): la única cerradura ACOSTADA del
            # nivel — tapa la boca del foso a ras de piso. Se reconoce por
            # la proporción: una puerta es alta, una losa es ancha.
            if r.w > r.h * 2:
                if not cerradura.abierta:
                    self._losa_del_juicio(surface, r)
                # Abierta no se dibuja NADA: el hueco del foso ES la
                # información, y un marco flotando sobre un agujero se
                # lee como un bug de dibujado.
                continue
            if cerradura.abierta:
                # Abierta queda el MARCO de piedra: el hueco se ve
                # atravesable, que es la información que importa.
                pygame.draw.rect(surface, PIEDRA_DK, r, 2)
                continue
            if cerradura.clase == "jaula":
                self._verja(surface, r)
            else:
                self._puerta_de_mausoleo(surface, r)

        for cofre in getattr(sistema, "cofres", ()):
            r = cofre.rect.move(-offset.x, -offset.y)
            self._arca_de_reliquias(surface, r, cofre.abierto)

    # ── Las piezas ──────────────────────────────────────────────
    _ofrenda_cacheada: pygame.Surface | None = None

    @classmethod
    def _pila_de_ofrenda(cls) -> pygame.Surface:
        """La pila de monedas, 16×16, tallada una vez.

        Tres monedas tumbadas, dos encima y una parada al frente con su
        canto: la silueta de «alguien dejó esto aquí». El destello va en
        el oro claro del tileset para que el bloom de la GPU lo bendiga
        igual que a los cuencos — estas SÍ deben brillar: son lo único
        del decorado que se puede recoger.
        """
        if cls._ofrenda_cacheada is not None:
            return cls._ofrenda_cacheada
        s = pygame.Surface((16, 16), pygame.SRCALPHA)
        ORO_VIVO = (240, 170, 72)
        ORO_LUZ = (255, 226, 148)
        ORO_SOMBRA = (150, 112, 30)
        BORDE = (52, 36, 14)

        def moneda_tumbada(cx: int, cy: int) -> None:
            pygame.draw.ellipse(s, BORDE, (cx - 3, cy - 1, 7, 4))
            pygame.draw.ellipse(s, ORO_SOMBRA, (cx - 3, cy - 1, 7, 3))
            pygame.draw.ellipse(s, ORO_VIVO, (cx - 2, cy - 1, 5, 2))

        # La base: tres tumbadas; encima dos; el brillo lo pone la parada.
        for cx, cy in ((4, 13), (9, 14), (12, 12)):
            moneda_tumbada(cx, cy)
        for cx, cy in ((6, 11), (11, 10)):
            moneda_tumbada(cx, cy)
        # La moneda parada, con la espiral tilawa insinuada.
        pygame.draw.circle(s, BORDE, (6, 7), 4)
        pygame.draw.circle(s, ORO_VIVO, (6, 7), 3)
        pygame.draw.circle(s, ORO_SOMBRA, (6, 7), 3, 1)
        s.set_at((6, 6), ORO_LUZ)
        s.set_at((5, 7), ORO_SOMBRA)
        s.set_at((7, 8), ORO_SOMBRA)
        # El destello que la delata desde lejos.
        s.set_at((11, 9), ORO_LUZ)
        cls._ofrenda_cacheada = s
        return s

    def _losa_del_juicio(self, surface: pygame.Surface,
                         r: pygame.Rect) -> None:
        """La tapa de piedra sobre la boca: sillería a ras de piso con
        las juntas marcadas. Las cuatro marcas del progreso las pinta la
        escena encima (ella conoce el rito; esta piel no)."""
        pygame.draw.rect(surface, PIEDRA_DK, r)
        pygame.draw.rect(surface, PIEDRA_NEGRA, r, 1)
        pygame.draw.line(surface, PIEDRA,
                         (r.left + 1, r.top + 1), (r.right - 2, r.top + 1))
        for x in range(r.left + 12, r.right - 4, 12):
            pygame.draw.line(surface, PIEDRA_NEGRA,
                             (x, r.top + 3), (x, r.bottom - 2))

    def _puerta_de_mausoleo(self, surface: pygame.Surface,
                            r: pygame.Rect) -> None:
        """Losa de piedra con dintel y cerradura de oro: se abre con LA
        llave, y el ojo tiene que ir directo a dónde entra."""
        pygame.draw.rect(surface, PIEDRA_DK, r)
        pygame.draw.rect(surface, PIEDRA_NEGRA, r, 2)
        # El dintel: una franja clara arriba, como los arcos de la Sala.
        pygame.draw.rect(surface, PIEDRA,
                         (r.left + 2, r.top + 2, r.width - 4, 5))
        pygame.draw.line(surface, PIEDRA_HI,
                         (r.left + 2, r.top + 2), (r.right - 3, r.top + 2))
        # Juntas de sillería: la puerta está TALLADA, no pintada.
        for y in range(r.top + 12, r.bottom - 6, 9):
            pygame.draw.line(surface, PIEDRA_NEGRA,
                             (r.left + 3, y), (r.right - 4, y))
        # La cerradura de oro, a la altura de la mano.
        cx, cy = r.centerx, r.top + r.height * 2 // 3
        pygame.draw.rect(surface, ORO, (cx - 3, cy - 3, 6, 6))
        pygame.draw.rect(surface, ORO_DK, (cx - 3, cy - 3, 6, 6), 1)
        pygame.draw.line(surface, PIEDRA_NEGRA, (cx, cy), (cx, cy + 2))

    def _verja(self, surface: pygame.Surface, r: pygame.Rect) -> None:
        """La jaula, en el idioma de la verja del camposanto: barrotes
        con remate, no una caja gris."""
        pygame.draw.rect(surface, PIEDRA_NEGRA, r, 2)
        pygame.draw.rect(surface, PIEDRA_DK,
                         (r.left, r.top, r.width, 4))
        pygame.draw.rect(surface, PIEDRA_DK,
                         (r.left, r.bottom - 4, r.width, 4))
        for x in range(r.left + 6, r.right - 2, 8):
            pygame.draw.line(surface, (70, 68, 78),
                             (x, r.top + 3), (x, r.bottom - 3), 2)
            surface.set_at((x, r.top + 5), PIEDRA_HI)   # el brillo del hierro

    def _arca_de_reliquias(self, surface: pygame.Surface, r: pygame.Rect,
                           abierta: bool) -> None:
        """El cofre como arca: madera oscura, flejes de oro y greca — el
        pariente mueble del pectoral del Espíritu."""
        if abierta:
            pygame.draw.rect(surface, MADERA_DK, r, border_radius=2)
            pygame.draw.rect(surface, PIEDRA_NEGRA, r, 2, border_radius=2)
            # Vacía y a oscuras: ya dio lo suyo.
            pygame.draw.rect(surface, (20, 16, 14),
                             (r.left + 3, r.top + 3, r.width - 6,
                              r.height - 6))
            return
        pygame.draw.rect(surface, MADERA, r, border_radius=2)
        pygame.draw.rect(surface, MADERA_DK, r, 2, border_radius=2)
        # La tapa, con su borde de luz.
        pygame.draw.line(surface, PIEDRA_HI,
                         (r.left + 2, r.top + 2), (r.right - 3, r.top + 2))
        pygame.draw.line(surface, MADERA_DK,
                         (r.left + 2, r.centery), (r.right - 3, r.centery), 2)
        # Flejes de oro y el broche: la greca del Asset Bible en mueble.
        for fx in (r.left + 4, r.right - 6):
            pygame.draw.line(surface, ORO, (fx, r.top + 2),
                             (fx, r.bottom - 3), 2)
        pygame.draw.rect(surface, ORO,
                         (r.centerx - 2, r.centery - 2, 5, 5))
        pygame.draw.rect(surface, ORO_DK,
                         (r.centerx - 2, r.centery - 2, 5, 5), 1)
