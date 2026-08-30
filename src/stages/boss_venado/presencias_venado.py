"""Módulo: presencias_venado
Sistema: stages.boss_venado
Descripción: fauna/presencias decorativas del corredor pre-jefe -- patrón
    exacto de src/stages/stage4_1/presencias.py (PresenciaErrante congelada +
    tabla + ventanas de aparición aleatorias), con DOS diferencias deliberadas:
    (1) tramo (1-4 de tramos_venado.Tramo.numero) en vez de fase de 4-1;
    (2) RNG PROPIO (azar.generador(semilla), no random global) -- para que el
    arnés de playtest, que corre a paso fijo y determinista, no vea su
    secuencia de aparición perturbada por cualquier otro consumidor del
    random global, y para que una corrida grabada sea reproducible con la
    misma semilla.

    Regla de oro heredada de stage4_1/stage4_1b (test_no_hay_un_solo_enemigo
    allá, ver invest_2(b)): CERO entidades ECS. Una PresenciaVenado no tiene
    rect de colisión ni damage_on_contact -- es un dato que la escena LEE
    cada cuadro para decidir si dibuja algo, nunca algo que el jugador pueda
    tocar."""
from __future__ import annotations

import math

# CORRECCIÓN frente al Paso 8 de la Tarea 5 tal como está escrito en el
# plan: el borrador importaba `Callable` de `typing`, ya deprecado (ruff
# UP035) -- se usa `collections.abc.Callable`, la convención real de este
# repo (ver sonido.py:24, el mismo mixin que expone `_play_sfx_spatial`).
from collections.abc import Callable
from dataclasses import dataclass, field

from src.engine.core import azar

#: Límites REALES del corredor pre-jefe (0 <= x < ARENA_X0=2480; alto total
#: del mapa = 608px) -- clamp duro: precedente B-035 (el venado se salía de
#: la arena en SEARCH; aunque hoy columna_de_patrullaje() está acotada por
#: columna_centro +- rango_columnas, no debe depender solo de esa
#: aritmética para nunca escaparse del corredor).
LIMITE_X0 = 0.0
LIMITE_X1 = 2480.0
LIMITE_Y0 = 0.0
LIMITE_Y1 = 608.0


def _clamp(valor: float, minimo: float, maximo: float) -> float:
    """Clamp duro compartido por columna_de_patrullaje() y
    fila_de_presencia() -- precedente B-035."""
    return max(minimo, min(maximo, valor))


@dataclass(frozen=True)
class PresenciaVenado:
    """Una figura de fondo que se deja ver un rato dentro de un tramo."""

    id: str
    #: Tramo.numero (1-4) de tramos_venado.py en el que se ve.
    tramo: int
    columna_centro: float
    rango_columnas: float
    periodo_patrullaje: float
    color: tuple[int, int, int]
    alto: int
    #: (mínimo, máximo) segundos hasta la próxima aparición / duración visible.
    espera: tuple[float, float]
    duracion: tuple[float, float]
    alfa: int = 120


PRESENCIAS: tuple[PresenciaVenado, ...] = (
    PresenciaVenado(
        "figura_del_hogar", tramo=1, columna_centro=550.0, rango_columnas=60.0,
        periodo_patrullaje=14.0, color=(30, 26, 20), alto=48,
        espera=(8.0, 15.0), duracion=(4.0, 7.0), alfa=110,
    ),
    PresenciaVenado(
        "sombra_del_carport", tramo=2, columna_centro=1280.0, rango_columnas=40.0,
        periodo_patrullaje=11.0, color=(20, 18, 22), alto=44,
        espera=(9.0, 16.0), duracion=(3.0, 6.0), alfa=100,
    ),
    PresenciaVenado(
        "presencia_del_umbral", tramo=3, columna_centro=1900.0, rango_columnas=80.0,
        periodo_patrullaje=17.0, color=(40, 46, 58), alto=56,
        espera=(7.0, 14.0), duracion=(4.0, 8.0), alfa=90,
    ),
)


def columna_de_patrullaje(presencia: PresenciaVenado, tiempo_total: float) -> float:
    """Posición X de MUNDO de la presencia en este instante -- vaivén
    senoidal alrededor de columna_centro con período propio. Función pura
    (sin pygame): recibe tiempo REAL acumulado, nunca la posición del
    jugador -- mismo patrón que Stage4_1._dibujar_presencias_errantes
    (stage4_1.py:1406-1408: ``avance = (self._tiempo % p.periodo_patrullaje)
    / p.periodo_patrullaje``, usa self._tiempo, no self._player.rect.x)."""
    avance = (tiempo_total % presencia.periodo_patrullaje) / presencia.periodo_patrullaje
    x = presencia.columna_centro + math.sin(avance * math.tau) * presencia.rango_columnas
    return _clamp(x, LIMITE_X0, LIMITE_X1)   # clamp duro: precedente B-035


def fila_de_presencia(presencia: PresenciaVenado) -> float:
    """Posición Y de MUNDO (antes del offset de cámara) de la base superior
    de la silueta -- fila del suelo (560, ver dibujar_fondo en la escena)
    menos la altura de la presencia, pasada por el mismo clamp duro que
    columna_de_patrullaje() (precedente B-035: nunca confiar en que la
    aritmética de origen ya está acotada)."""
    y = 560.0 - presencia.alto
    return _clamp(y, LIMITE_Y0, LIMITE_Y1)   # clamp duro: precedente B-035


@dataclass
class GestorDePresencias:
    """Cuenta hacia la próxima aparición de cada presencia, o hacia que se
    apague la que ya está visible -- mismo mecanismo que
    Stage4_1._actualizar_presencias_errantes (stage4_1.py:1369-1389), con
    RNG propio en vez de random global."""

    semilla: int | None = None
    tramo_actual: int = 1
    #: Tiempo real acumulado (NO la posición del jugador) -- es la base del
    #: vaivén de patrullaje de cada presencia (ver columna_de_patrullaje()
    #: más abajo). Usar la posición del jugador para esto sería un bug: el
    #: período de patrullaje está en SEGUNDOS (11-17s), no en píxeles, y la
    #: fase quedaría congelada cada vez que el jugador deja de moverse en
    #: vez de seguir oscilando -- exactamente el error que evita acumular
    #: tiempo real en vez de espacio recorrido (detectado en la
    #: auto-revisión de este plan contra el patrón real de
    #: stage4_1.py:1406, que usa self._tiempo, no la posición del jugador).
    tiempo_total: float = 0.0
    _azar: object = field(init=False, repr=False)
    _visible: dict = field(default_factory=dict, init=False)
    _proxima: dict = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._azar = azar.generador(self.semilla)

    @property
    def visibles(self) -> dict:
        """{id: segundos_restantes_visible} solo para las que están visibles."""
        return {k: v for k, v in self._visible.items() if v > 0.0}

    def actualizar(self, dt: float) -> None:
        self.tiempo_total += dt
        for p in PRESENCIAS:
            if p.tramo != self.tramo_actual:
                continue
            visible = self._visible.get(p.id, 0.0)
            if visible > 0.0:
                self._visible[p.id] = max(0.0, visible - dt)
                continue
            proxima = self._proxima.get(p.id)
            if proxima is None:
                proxima = self._azar.uniform(*p.espera)
            proxima -= dt
            if proxima <= 0.0:
                self._visible[p.id] = self._azar.uniform(*p.duracion)
                proxima = self._azar.uniform(*p.espera)
            self._proxima[p.id] = proxima


#: Tramo final del Acto 3 (el spec lo describe como x~2200-2480 -- ver §2 y
#: §3.9 del spec: "sombra... en el tramo final del Acto 3"). ARENA_X0 se
#: repite aqui (no se importa de boss_venado_scene para evitar el ciclo de
#: import escena->presencias_venado->escena) -- mismo patron ya usado por
#: ARENA_X0/ARENA_X1 duplicados entre boss_venado.py y boss_venado_scene.py.
SOMBRA_X0 = 2200.0
SOMBRA_X1 = 2480.0   # == ARENA_X0

#: CORRECCIÓN post-revisión de spec (hallazgo del revisor, no del plan): la
#: primera versión de `actualizar()` reenviaba `columna_de_mundo` (la
#: posición del JUGADOR) tal cual a `reproducir_sfx`. `_play_sfx_spatial`
#: (sonido.py:157-161) calcula el pan a partir de `world_x -
#: screen_center_x`, y `screen_center_x` es la cámara centrada en el
#: jugador (camera.py: LERP con `lerp_speed=8.0` sobre el objetivo
#: centrado) -- emitir desde la propia posición del jugador produce
#: siempre un desfase mínimo (el lag del LERP, unas pocas decenas de px),
#: o sea paneo casi nulo y atenuación casi 1.0 (`play_sfx_at`,
#: audio_manager.py:294-321, `atenuacion = 1 - distancia /
#: RADIO_AUDIBLE_EFECTOS` con `RADIO_AUDIBLE_EFECTOS = 2000.0`,
#: audio_manager.py:32). Mismo error que el motor ya documenta y evita en
#: el Gavilán (`_posicion_del_grito`, stage4_1.py:1105-1110): *"un sonido
#: reproducido siempre en el mismo sitio relativo (centrado, sin paneo)...
#: es exactamente lo que vuelve inútil al oído como herramienta de
#: orientación"*.
#:
#: El emisor real es el gazebo del Venado -- el objeto `BossVenado_01`
#: (`type="BossVenado"`) del TMX, verificado con Grep contra
#: `boss_venado.tmx:239` Y su generador (`gen_level_residencias.py:1037`,
#: ambos con `x="3168"`). Con el jugador cruzando la ventana de disparo
#: [SOMBRA_X0, SOMBRA_X1) = x~2200-2480 -- cerca de donde la cámara ya lo
#: sigue centrado --, emitir desde 3168 da una distancia real de varios
#: cientos de píxeles: paneo perceptible a la derecha (el gazebo queda
#: delante, en la dirección de avance) y atenuación bien por debajo de 1.0
#: -- el "bramido lejano, fuera de cámara" que pide el spec, en vez de un
#: sonido que suena pegado al propio jugador.
X_EMISOR_BRAMIDO = 3168.0


class EventoSombraQueCruza:
    """Un solo aviso -- sombra fuera de cámara + bramido espacial -- justo
    antes de la revelación del jefe. Patrón "pez abismal" simplificado
    (stage4_1b.py:333-368: sombra antes de perseguir), pero sin persecución:
    aquí es un evento de puntuación, no una mecánica de miedo sostenida."""

    def __init__(self, reproducir_sfx: Callable[[float], None]) -> None:
        self._reproducir_sfx = reproducir_sfx
        self._disparado = False

    def actualizar(self, columna_de_mundo: float) -> None:
        """``columna_de_mundo`` es la posición del JUGADOR -- decide
        ÚNICAMENTE cuándo se abre la ventana de disparo ([SOMBRA_X0,
        SOMBRA_X1)). El sonido en sí se emite siempre desde
        ``X_EMISOR_BRAMIDO`` (el gazebo del Venado), nunca desde
        ``columna_de_mundo`` -- ver el porqué en el docstring de esa
        constante."""
        if self._disparado:
            return
        if SOMBRA_X0 <= columna_de_mundo < SOMBRA_X1:
            self._disparado = True
            self._reproducir_sfx(X_EMISOR_BRAMIDO)

    def reiniciar(self) -> None:
        """Se llama desde on_enter() -- cada episodio de vida (H-18) merece
        volver a ver/oír el aviso."""
        self._disparado = False
