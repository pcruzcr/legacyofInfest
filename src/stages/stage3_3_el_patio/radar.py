"""
Module: radar
System: stage (student assignment)
Academic Unit: Unidad IV (representacion de escena) + II (cambio de coordenadas).

Camara de rastreo: un cuadro en la columna izquierda, justo debajo de las
barras de vida, que ensena el trozo de nivel que viene DELANTE del jugador, dibujado como esquema —terreno, enemigos, monedas,
checkpoints y la salida— en vez de como pixeles del juego.

Por que no reutiliza el minimapa del motor
===========================================
`src/engine/ui/minimap.py` existe y `StageScene` ya lo pinta, pero resuelve
otro problema: es redondo, cubre el mapa ENTERO a la vez y solo marca puntos
(jugador, enemigos, checkpoints) sobre las zonas ya exploradas. En un mapa de
2400x896 eso deja el nivel reducido a una mancha de 110 px donde no se
distingue el relieve, que es justo lo que hace falta saber aqui: si lo que
viene es suelo, un foso o la subida del muro. Este radar es cuadrado, sigue al
jugador con una ventana movil y dibuja la FORMA del terreno.

Tampoco se toca el minimapa del motor para adaptarlo: es codigo del profesor y
lo usan las otras 25 entregas.

La ventana va adelantada `ADELANTO` px en la direccion en que mira el jugador:
un radar centrado en uno mismo ensena donde ya se ha estado, que no sirve de
nada.
"""
from __future__ import annotations

import pygame

LADO = 132          # lado del cuadro, en pixeles de pantalla
# Columna izquierda, justo debajo del HUD del motor: retrato en (15,15,60,60),
# barra de vida en (15,80,60,12) y estamina en (15,94,60,12), o sea que la
# franja de arriba termina en y=106. El radar arranca en 114 y el panel del
# Vigia va debajo, en 272.
POS_X = 10
POS_Y = 114
VENTANA = 640       # cuantos pixeles de mundo entran en el cuadro
ADELANTO = 170      # cuanto se adelanta la ventana hacia donde se mira

FONDO = (10, 18, 32, 190)
BORDE = (90, 170, 220)
SUELO = (74, 116, 88)
PLATAFORMA = (250, 214, 120)
ENEMIGO = (255, 70, 70)
MONEDA = (255, 190, 70)
CHECKPOINT = (255, 230, 110)
SALIDA = (120, 240, 160)
JUGADOR = (90, 200, 255)


class Radar:
    """Dibuja un esquema movil del nivel bajo el HUD de la izquierda."""

    def __init__(self, datos, salida: tuple[float, float]) -> None:
        self._solidos = list(getattr(datos, "collision_rects", []) or [])
        self._unidireccionales = list(getattr(datos, "one_way_rects", []) or [])
        self._checkpoints = [
            pygame.Vector2(getattr(c, "x", 0), getattr(c, "y", 0))
            for c in (getattr(datos, "checkpoints", []) or [])
        ]
        self._salida = pygame.Vector2(salida)
        self._mapa = getattr(datos, "map_pixel_size", (0, 0))
        self._datos = datos
        self._mirada = 1.0          # 1 derecha, -1 izquierda
        self._ultimo_x = 0.0
        self._fuente = pygame.font.Font(None, 16)

    # -- utilidades ---------------------------------------------
    def _ventana(self, jugador) -> pygame.Rect:
        """Trozo de mundo que se muestra, adelantado hacia donde se mira."""
        cx = jugador.position.x + ADELANTO * self._mirada
        cy = jugador.position.y
        v = pygame.Rect(0, 0, VENTANA, VENTANA)
        v.center = (int(cx), int(cy))
        # Sin salirse del mapa: si no, media ventana queda en negro y el
        # jugador aparece pegado al borde sin entender por que.
        ancho, alto = self._mapa
        if ancho and v.width < ancho:
            v.x = max(0, min(v.x, ancho - v.width))
        if alto and v.height < alto:
            v.y = max(0, min(v.y, alto - v.height))
        return v

    @staticmethod
    def _a_cuadro(punto, ventana: pygame.Rect, origen: tuple[int, int]):
        """Mundo -> pixeles del cuadro (Unidad II: cambio de sistema)."""
        k = LADO / ventana.width
        return (int(origen[0] + (punto[0] - ventana.x) * k),
                int(origen[1] + (punto[1] - ventana.y) * k))

    # -- ciclo de vida ------------------------------------------
    def update(self, jugador) -> None:
        if jugador is None:
            return
        x = jugador.position.x
        if abs(x - self._ultimo_x) > 0.5:
            self._mirada = 1.0 if x > self._ultimo_x else -1.0
            self._ultimo_x = x

    def draw(self, surface: pygame.Surface, jugador) -> None:
        if jugador is None:
            return
        ventana = self._ventana(jugador)
        k = LADO / ventana.width
        ox, oy = POS_X, POS_Y

        cuadro = pygame.Surface((LADO, LADO), pygame.SRCALPHA)
        cuadro.fill(FONDO)

        def pinta(rect, color):
            if not rect.colliderect(ventana):
                return
            x = (rect.x - ventana.x) * k
            y = (rect.y - ventana.y) * k
            pygame.draw.rect(cuadro, color,
                             (int(x), int(y), max(1, int(rect.width * k)),
                              max(1, int(rect.height * k))))

        for r in self._solidos:
            pinta(r, SUELO)
        for r in self._unidireccionales:
            pinta(r, PLATAFORMA)

        def punto(pos, color, radio=2):
            if not ventana.collidepoint(int(pos[0]), int(pos[1])):
                return
            x = int((pos[0] - ventana.x) * k)
            y = int((pos[1] - ventana.y) * k)
            pygame.draw.circle(cuadro, color, (x, y), radio)

        for c in self._checkpoints:
            punto((c.x, c.y), CHECKPOINT, 2)
        for m in (getattr(self._datos, "recogibles", []) or []):
            r = getattr(m, "rect", None)
            if r is not None:
                punto(r.center, MONEDA, 2)
        for e in (getattr(self._datos, "entity_list", []) or []):
            if getattr(e, "current_health", 1) > 0:
                punto((e.position.x, e.position.y), ENEMIGO, 3)
        punto((self._salida.x, self._salida.y), SALIDA, 4)

        # El jugador va de ultimo para que nada lo tape, y con un anillo
        # alrededor porque en 132 px un punto de 3 px se pierde entre el resto.
        px, py = self._a_cuadro((jugador.position.x, jugador.position.y),
                                ventana, (0, 0))
        pygame.draw.circle(cuadro, JUGADOR, (px, py), 3)
        pygame.draw.circle(cuadro, JUGADOR, (px, py), 6, 1)

        surface.blit(cuadro, (ox, oy))
        pygame.draw.rect(surface, BORDE, (ox, oy, LADO, LADO), 1)
        rotulo = self._fuente.render("RADAR", True, BORDE)
        surface.blit(rotulo, (ox, oy + LADO + 3))
        flecha = "->" if self._mirada > 0 else "<-"
        f = self._fuente.render(flecha, True, JUGADOR)
        surface.blit(f, (ox + LADO - f.get_width(), oy + LADO + 3))
