"""
Module: onda_fuente
System: stage (student assignment)
Academic Unit: Unidad II (vectores) + Unidad V (color) + Unidad VI (easing y EventBus).

La Onda de la Fuente: el poder especial del patio. Las monedas no solo suman
en el marcador, tambien cargan la fuente; con una carga lista, la tecla E
suelta una onda expansiva que revienta a los enemigos que alcance.

Por que esta separado del ataque normal del jugador
====================================================
El jugador ya tiene `SHORT_ATTACK`, `LONG_ATTACK` y `DASH` en el mapa de
acciones del motor: cuerpo a cuerpo, corto alcance, uno a uno. La onda es lo
contrario —area, a distancia, con recurso limitado— y sirve justo para lo que
el ataque normal no puede: quitarte de encima al dron mientras trepas la liana
y no puedes ni golpear ni esquivar. Anadirla como poder propio del escenario
no toca `player.py` ni el mapa de acciones del motor, que son del profesor.

La tecla E se lee directa de pygame (`pygame.key.get_pressed()`) en vez de
registrar una accion nueva: registrar una accion obligaria a tocar
`src/engine/input/action_map.py`, y ese archivo no es mio. E esta libre — el
motor solo usa A C D F G J K M P Q R S V W X Z.
"""
from __future__ import annotations

import pygame

from src.engine.utils.math_utils import (
    ease_out_cubic,
    ease_out_quad,
    vec2_distance,
    vec2_normalize,
)
from src.framework.processing.color_tools import ColorTools

TECLA = pygame.K_e

MONEDAS_POR_CARGA = 3
CARGAS_MAX = 3

CLARO = (235, 250, 255)   # blanco-agua, al salir
AZUL = (60, 150, 220)     # azul de la fuente, al disiparse

RADIO_MAX = 140.0
DURACION = 0.55
DANO = 3.0          # la mayoria de enemigos de la zona 3 tienen 2.0 de vida


def _mezcla_hsv(a: tuple[int, int, int], b: tuple[int, int, int],
                t: float) -> tuple[int, int, int]:
    """Interpola dos colores *en HSV*, no en RGB (Unidad V).

    Mezclar en RGB pasa por grises sucios cuando los dos colores tienen tonos
    distintos; en HSV el tono gira y la mezcla mantiene el color vivo todo el
    recorrido, que es justo lo que se quiere en un destello.
    """
    h1, s1, v1 = ColorTools.rgb_to_hsv(*a)
    h2, s2, v2 = ColorTools.rgb_to_hsv(*b)
    return ColorTools.hsv_to_rgb(h1 + (h2 - h1) * t,
                                 s1 + (s2 - s1) * t,
                                 v1 + (v2 - v1) * t)


class Onda:
    """Una onda viva: crece con easing y solo golpea una vez a cada enemigo."""

    def __init__(self, centro: pygame.Vector2, radio_max: float = RADIO_MAX,
                 dano: float = DANO) -> None:
        self.centro = pygame.Vector2(centro)
        self.t = 0.0
        # El Vigia decide estos dos numeros segun lo que haya clasificado:
        # aereo abre el radio, terrestre sube el dano. Por defecto, los de
        # siempre, para que la Onda siga funcionando sin Vigia.
        self.radio_max = radio_max
        self.dano = dano
        self._ya_golpeados: set[int] = set()

    @property
    def viva(self) -> bool:
        return self.t < DURACION

    @property
    def radio(self) -> float:
        """Rapida al salir y frenando al final: `ease_out_cubic`."""
        return self.radio_max * ease_out_cubic(min(self.t / DURACION, 1.0))

    def update(self, dt: float, enemigos) -> int:
        """Avanza la onda y golpea a quien haya entrado. Devuelve los alcanzados."""
        self.t += dt
        radio = self.radio
        alcanzados = 0
        for e in enemigos:
            if id(e) in self._ya_golpeados:
                continue
            pos = getattr(e, "position", None)
            if pos is None:
                continue
            # Unidad II: distancia entre vectores para el alcance del area.
            if vec2_distance(self.centro, pygame.Vector2(pos)) > radio:
                continue
            self._ya_golpeados.add(id(e))
            golpear = getattr(e, "apply_hit", None)
            if golpear is None:
                continue
            # El empujon sale del centro de la onda hacia el enemigo: se
            # normaliza la diferencia para quedarnos solo con la direccion.
            direccion = vec2_normalize(pygame.Vector2(pos) - self.centro)
            origen = self.centro - direccion * 4
            golpear(self.dano, (origen.x, origen.y))
            alcanzados += 1
        return alcanzados

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        avance = min(self.t / DURACION, 1.0)
        radio = int(self.radio)
        if radio <= 1:
            return
        cx = int(self.centro.x - offset.x)
        cy = int(self.centro.y - offset.y)
        # Unidad V: el anillo va del blanco-agua al azul de la fuente segun se
        # expande, y se apaga con `ease_out_quad` para que no corte de golpe.
        alfa = int(230 * (1.0 - ease_out_quad(avance)))
        if alfa <= 0:
            return
        color = _mezcla_hsv(CLARO, AZUL, avance)
        lienzo = pygame.Surface((radio * 2 + 6, radio * 2 + 6), pygame.SRCALPHA)
        centro_local = (radio + 3, radio + 3)
        pygame.draw.circle(lienzo, (*color, alfa), centro_local, radio, 3)
        pygame.draw.circle(lienzo, (*color, alfa // 3), centro_local, max(1, radio - 6), 2)
        surface.blit(lienzo, (cx - radio - 3, cy - radio - 3))


class OndaFuenteController:
    """Cuenta monedas, gasta cargas y mantiene vivas las ondas.

    Se suscribe a `EVENTO_RECOGIDO` igual que `MonedaFxController`: cada moneda
    del nivel suma, y cada `MONEDAS_POR_CARGA` monedas dan una carga.
    """

    def __init__(self, event_bus, vigia=None) -> None:
        from src.framework.stage.interactable_system import EVENTO_RECOGIDO

        # Unidad IX: el resultado del clasificador cambia el poder. Es una de
        # las dos formas observables en que la clasificacion altera el juego.
        self._vigia = vigia

        self._ondas: list[Onda] = []
        self._monedas = 0
        self._cargas = 0
        self._tecla_antes = False
        self._ultimo_alcance = 0
        self._aviso = 0.0
        self._fuente = pygame.font.Font(None, 18)
        # El bus guarda referencias debiles: si no me guardo el metodo, la
        # suscripcion se recoge y el poder deja de cargarse en silencio.
        self._handler = self._on_recogido
        event_bus.subscribe(EVENTO_RECOGIDO, self._handler)

    def _on_recogido(self, **data) -> None:
        if str(data.get("item_id", "")) != "coin":
            return
        self._monedas += 1
        if self._monedas % MONEDAS_POR_CARGA == 0 and self._cargas < CARGAS_MAX:
            self._cargas += 1
            self._aviso = 1.6

    # ── ciclo de vida ──────────────────────────────────────────
    def update(self, dt: float, jugador, enemigos) -> None:
        tecla = bool(pygame.key.get_pressed()[TECLA])
        recien_pulsada = tecla and not self._tecla_antes
        self._tecla_antes = tecla

        if recien_pulsada and self._cargas > 0 and jugador is not None:
            self._cargas -= 1
            radio, dano = RADIO_MAX, DANO
            if self._vigia is not None:
                radio *= self._vigia.multiplicador_radio
                dano += self._vigia.dano_extra
            self._ondas.append(Onda(pygame.Vector2(jugador.position), radio, dano))

        vivos = [e for e in (enemigos or []) if getattr(e, "current_health", 1) > 0]
        for onda in self._ondas:
            self._ultimo_alcance += onda.update(dt, vivos)
        self._ondas = [o for o in self._ondas if o.viva]
        self._aviso = max(0.0, self._aviso - dt)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        for onda in self._ondas:
            onda.draw(surface, offset)
        self._dibujar_cargas(surface)

    def _dibujar_cargas(self, surface: pygame.Surface) -> None:
        """Tres gotas abajo a la izquierda: llenas = cargas disponibles."""
        base_x, base_y = 12, surface.get_height() - 22
        for i in range(CARGAS_MAX):
            x = base_x + i * 16
            lleno = i < self._cargas
            color = (120, 200, 245) if lleno else (70, 80, 95)
            pygame.draw.circle(surface, color, (x, base_y), 6)
            pygame.draw.circle(surface, (20, 30, 45), (x, base_y), 6, 1)
        falta = MONEDAS_POR_CARGA - (self._monedas % MONEDAS_POR_CARGA)
        etiqueta = "E: ONDA" if self._cargas else f"{falta} moneda(s)"
        texto = self._fuente.render(etiqueta, True, (215, 235, 250))
        surface.blit(texto, (base_x + CARGAS_MAX * 16 + 4, base_y - 7))
        if self._aviso > 0:
            aviso = self._fuente.render("!ONDA LISTA!  (E)", True, (255, 240, 140))
            surface.blit(aviso, (surface.get_width() // 2 - aviso.get_width() // 2, 46))

    @property
    def cargas(self) -> int:
        return self._cargas
