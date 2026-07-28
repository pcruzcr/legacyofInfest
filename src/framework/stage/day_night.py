"""
Module: day_night
System: framework.stage
Academic Unit: Unidad VI — Interpolación y color

Reloj de mundo: hora del día, y qué le hace a la luz.

F2.1 — por qué esto no existía
------------------------------
Antes de esta fase el escenario tenía un brillo ambiente fijo, declarado en el
TMX. Un nivel se veía igual a los tres minutos que al primer segundo. Eso es
correcto para un prólogo corto, pero deja fuera la característica que más
cambia la sensación de un mundo por menos código: que el tiempo pase.

Lo que hace este módulo es traducir una hora —un número de 0 a 24— a tres
cosas: cuánta luz ambiente hay, de qué color es esa luz, y cuánto realce
(bloom) conviene. La escena las aplica; aquí no se toca ni un píxel.

La interpolación es el contenido de la Unidad VI, así que el archivo está
escrito para poder leerse: las paradas de color son una tabla explícita y la
mezcla es una interpolación lineal entre las dos paradas que rodean la hora
actual. Sin trucos.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LuzDelDia:
    """Cómo se ve el mundo a una hora concreta."""

    #: Multiplicador del `ambient_light` del escenario, de 0 a 1.
    factor_ambiente: float
    #: Tinte de la luz. Se multiplica sobre la escena, así que (255,255,255)
    #: significa "sin teñir".
    color: tuple[int, int, int]
    #: Cuánto sumar al bloom base. De noche el realce se nota más porque hay
    #: menos luz de fondo con la que competir.
    bloom_extra: float


#: Paradas del ciclo, en horas. Entre dos paradas se interpola linealmente.
#:
#: Los valores están elegidos para que **el juego siga siendo jugable a las
#: 3 de la madrugada**. La noche se comunica con el **color** —azul frío frente
#: al blanco del mediodía— más que con la falta de luz.
#:
#: Los tramos nocturnos se subieron de 0,35 a 0,52 tras medirlos en Stage 0.
#: El factor se multiplica por el `ambient_light` del mapa, que allí vale 0,70,
#: así que 0,35 daba un ambiente aplicado de 0,245 y un brillo de pantalla de
#: 12,7 sobre 255: el jugador no veía a los enemigos. Con 0,52 y el suelo de
#: `StageScene.MIN_AMBIENTE` la noche queda en 25, frente a los 45 del
#: mediodía. Sigue siendo media pantalla más oscura, y se puede jugar.
PARADAS: tuple[tuple[float, LuzDelDia], ...] = (
    (0.0,  LuzDelDia(0.52, (165, 180, 235), 0.14)),   # madrugada cerrada
    (5.0,  LuzDelDia(0.58, (185, 190, 235), 0.12)),   # antes del alba
    (7.0,  LuzDelDia(0.72, (255, 190, 150), 0.08)),   # amanecer, cálido
    (10.0, LuzDelDia(1.00, (255, 250, 240), 0.00)),   # mañana
    (14.0, LuzDelDia(1.00, (255, 255, 250), 0.00)),   # mediodía
    (18.0, LuzDelDia(0.80, (255, 175, 130), 0.06)),   # tarde dorada
    (20.0, LuzDelDia(0.66, (235, 165, 175), 0.11)),   # ocaso
    (22.0, LuzDelDia(0.55, (170, 185, 238), 0.14)),   # noche
    (24.0, LuzDelDia(0.52, (165, 180, 235), 0.14)),   # empalma con 0.0
)

HORAS_POR_DIA = 24.0


def _mezclar(a: LuzDelDia, b: LuzDelDia, t: float) -> LuzDelDia:
    """Interpolación lineal entre dos paradas. `t` va de 0 (a) a 1 (b)."""
    return LuzDelDia(
        factor_ambiente=a.factor_ambiente + (b.factor_ambiente - a.factor_ambiente) * t,
        color=(
            round(a.color[0] + (b.color[0] - a.color[0]) * t),
            round(a.color[1] + (b.color[1] - a.color[1]) * t),
            round(a.color[2] + (b.color[2] - a.color[2]) * t),
        ),
        bloom_extra=a.bloom_extra + (b.bloom_extra - a.bloom_extra) * t,
    )


def luz_a_las(hora: float) -> LuzDelDia:
    """Devuelve la luz correspondiente a una hora cualquiera.

    La hora se normaliza al rango [0, 24), así que 25.5 es la 1:30 y -1 son
    las 23:00. Es deliberado: un reloj que acumula segundos acabará pasándose
    de 24 y no tiene sentido que eso sea un error.
    """
    hora = hora % HORAS_POR_DIA
    for i in range(len(PARADAS) - 1):
        h0, luz0 = PARADAS[i]
        h1, luz1 = PARADAS[i + 1]
        if h0 <= hora <= h1:
            tramo = h1 - h0
            t = 0.0 if tramo <= 0 else (hora - h0) / tramo
            return _mezclar(luz0, luz1, t)
    return PARADAS[-1][1]   # inalcanzable con las paradas actuales


class RelojDeMundo:
    """Avanza la hora del juego y responde qué luz toca.

    La duración de un día se mide en **segundos reales**, no en horas
    simuladas: `duracion_dia = 300` significa que el ciclo completo dura cinco
    minutos de partida. Es la unidad en la que piensa quien diseña un nivel.

    `duracion_dia = 0` congela el reloj en su hora inicial, que es como se
    comporta un escenario que no quiere ciclo. Se distingue de "no declarado"
    en la escena, no aquí.
    """

    def __init__(self, hora_inicial: float = 12.0, duracion_dia: float = 0.0) -> None:
        self._hora = hora_inicial % HORAS_POR_DIA
        self._duracion_dia = max(0.0, duracion_dia)

    @property
    def hora(self) -> float:
        return self._hora

    @property
    def congelado(self) -> bool:
        return self._duracion_dia <= 0.0

    @property
    def duracion_dia(self) -> float:
        return self._duracion_dia

    def update(self, dt: float) -> None:
        if self.congelado:
            return
        self._hora = (self._hora + HORAS_POR_DIA * dt / self._duracion_dia) % HORAS_POR_DIA

    def luz(self) -> LuzDelDia:
        return luz_a_las(self._hora)

    def etiqueta(self) -> str:
        """Hora en formato HH:MM, para el HUD y para depurar."""
        horas = int(self._hora)
        minutos = int((self._hora - horas) * 60)
        return f"{horas:02d}:{minutos:02d}"

    #: Nombres de los tramos, para que un estudiante pueda escribir
    #: `start_hour = dusk` en Tiled en vez de buscar el número.
    MOMENTOS: dict[str, float] = {
        "dawn": 7.0,
        "morning": 10.0,
        "noon": 12.0,
        "afternoon": 16.0,
        "dusk": 19.0,
        "night": 22.0,
        "midnight": 0.0,
    }

    @classmethod
    def hora_desde_texto(cls, valor: object, por_defecto: float = 12.0) -> float:
        """Acepta un nombre de momento, un número, o `HH:MM`."""
        if valor is None:
            return por_defecto
        texto = str(valor).strip().lower()
        if not texto:
            return por_defecto
        if texto in cls.MOMENTOS:
            return cls.MOMENTOS[texto]
        if ":" in texto:
            partes = texto.split(":", 1)
            try:
                return (int(partes[0]) + int(partes[1]) / 60.0) % HORAS_POR_DIA
            except ValueError:
                return por_defecto
        try:
            return float(texto) % HORAS_POR_DIA
        except ValueError:
            return por_defecto
