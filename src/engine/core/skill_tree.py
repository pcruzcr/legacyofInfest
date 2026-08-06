"""
Module: skill_tree
System: engine.core
Academic Unit: N/A
Description: AUD-293 — el árbol de habilidades: en qué se gastan los puntos de
experiencia.

Lo único que no existía en absoluto
===================================
`docs/87` §3 lo dijo sin rodeos: no había clase de árbol, ni nodos, ni pantalla,
y `ExperienceSystem` repartía puntos que **no se podían gastar en nada** — no
existía un método para ello. Era la última pieza del bucle de progresión que
faltaba entera, no a medio conectar.

Qué hay en el árbol, y qué no
=============================
**Sólo estadísticas.** Las mecánicas —doble salto, dash, parry— las sueltan los
jefes (AUD-238/AUD-294) y ésa es la diferencia que hace legible la progresión:
lo que **puedes hacer** lo abre derrotar a alguien, y lo que **aguantas o
pegas** lo abre jugar. Meter el doble salto en el árbol dejaría al jugador sin
saber por qué a veces la progresión avanza matando y a veces comprando.

Tres ramas, y las tres con tope:

* **Vitalidad** — media pizca de corazón por rango, diez rangos: de 5 a **10
  corazones** y ni uno más. El tope es del diseño, no del árbol: `max_health`
  lo recorta pase lo que pase, así que ni con todas las reliquias del juego
  encima se pasa de diez.
* **Fuerza** — +8 % de daño por rango, cinco rangos: +40 % al final.
* **Ímpetu** — +0,15 s de ultimate por rango, cuatro rangos: de 0,60 s a 1,20 s.

Por qué el coste sube con el rango
==================================
El primer rango de vitalidad cuesta un punto y el décimo cuesta cinco. Con
coste plano, la ruta óptima es siempre la misma —subir a tope la rama más
barata— y el árbol deja de ser una decisión para ser una cuenta. Con coste
creciente, en algún momento sale más a cuenta empezar otra rama, y ahí es donde
el jugador elige.

Y por qué nada de esto toca la física
=====================================
Vida, daño y duración del ultimate no cambian ni un píxel de dónde se puede
saltar. Es deliberado: la invariante 2 dice que las 26 entregas tienen que
seguir funcionando, y un nodo que subiera la altura de salto recalificaría los
dieciséis mapas medidos por `grade_stage`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

#: Techo absoluto de corazones. Lo pidió el diseño y lo aplica `Player`.
CORAZONES_MAXIMOS: float = 10.0


@dataclass(frozen=True)
class NodoDeHabilidad:
    """Un nodo del árbol: qué mejora, cuánto y a cambio de qué."""

    id: str
    nombre: str
    descripcion: str
    #: Cuántas veces se puede subir.
    rangos: int
    #: Cuánto mejora **por rango**. La unidad la decide quien lo consume.
    por_rango: float
    #: Puntos que cuesta el primer rango.
    coste_base: int
    #: Cuánto sube el coste por cada rango ya comprado.
    coste_incremento: int = 0
    #: Nodo que hay que haber empezado antes. Vacío = disponible desde el inicio.
    requiere: str = ""

    def coste_del_rango(self, rango: int) -> int:
        """Lo que cuesta pasar de `rango` a `rango + 1`."""
        return self.coste_base + self.coste_incremento * max(0, rango)


CATALOGO: tuple[NodoDeHabilidad, ...] = (
    NodoDeHabilidad(
        id="vitalidad",
        nombre="Vitalidad",
        descripcion="+½ corazón por rango, hasta 10 corazones.",
        rangos=10, por_rango=0.5, coste_base=1, coste_incremento=0,
    ),
    NodoDeHabilidad(
        id="fuerza",
        nombre="Fuerza",
        descripcion="+8 % de daño por rango.",
        rangos=5, por_rango=0.08, coste_base=2, coste_incremento=1,
    ),
    NodoDeHabilidad(
        id="impetu",
        nombre="Ímpetu",
        descripcion="+0,15 s de ultimate por rango.",
        rangos=4, por_rango=0.15, coste_base=2, coste_incremento=1,
        # Se abre con la fuerza: alargar el ultimate sin pegar más fuerte es
        # alargar un ataque flojo, y el jugador lo compraría sin notarlo.
        requiere="fuerza",
    ),
)

_POR_ID: dict[str, NodoDeHabilidad] = {n.id: n for n in CATALOGO}


def nodo(nodo_id: str) -> NodoDeHabilidad | None:
    return _POR_ID.get(nodo_id)


class ArbolDeHabilidades:
    """Qué rangos lleva comprados esta partida, y qué dan.

    Singleton como el resto del estado de partida —inventario, experiencia,
    puntuación—, y por la misma razón: lo consultan el jugador, el HUD y la
    pantalla del árbol, y pasarlo por parámetro a los tres obligaría a
    enhebrarlo por media docena de constructores que hoy no lo necesitan.
    """

    _instancia: ArbolDeHabilidades | None = None

    def __init__(self) -> None:
        self._rangos: dict[str, int] = {}

    @classmethod
    def get_instance(cls) -> ArbolDeHabilidades:
        if cls._instancia is None:
            cls._instancia = cls()
        return cls._instancia

    @classmethod
    def _reset_instance(cls) -> None:
        cls._instancia = None

    # ── consulta ──────────────────────────────────────────────────
    def rango(self, nodo_id: str) -> int:
        return self._rangos.get(nodo_id, 0)

    def al_maximo(self, nodo_id: str) -> bool:
        n = _POR_ID.get(nodo_id)
        return n is not None and self.rango(nodo_id) >= n.rangos

    def coste(self, nodo_id: str) -> int:
        """Lo que cuesta el siguiente rango. 0 si ya está al máximo."""
        n = _POR_ID.get(nodo_id)
        if n is None or self.al_maximo(nodo_id):
            return 0
        return n.coste_del_rango(self.rango(nodo_id))

    def desbloqueado(self, nodo_id: str) -> bool:
        """¿Se cumple el requisito de este nodo?"""
        n = _POR_ID.get(nodo_id)
        if n is None:
            return False
        return not n.requiere or self.rango(n.requiere) > 0

    def motivo_para_no_comprar(self, nodo_id: str) -> str:
        """Por qué no se puede comprar, en una frase para la pantalla.

        Devuelve cadena vacía si sí se puede. Existe como método y no como
        comentario en la interfaz porque un botón apagado sin explicación es
        la forma más rápida de que alguien concluya que el juego está roto.
        """
        from src.engine.core.experience import ExperienceSystem

        n = _POR_ID.get(nodo_id)
        if n is None:
            return "Ese nodo no existe."
        if self.al_maximo(nodo_id):
            return "Ya está al máximo."
        if not self.desbloqueado(nodo_id):
            requisito = _POR_ID.get(n.requiere)
            return f"Necesitas antes un rango de {requisito.nombre if requisito else n.requiere}."
        coste = self.coste(nodo_id)
        if ExperienceSystem.get_instance().puntos < coste:
            return f"Te faltan puntos: cuesta {coste}."
        return ""

    def puede_comprar(self, nodo_id: str) -> bool:
        return not self.motivo_para_no_comprar(nodo_id)

    # ── compra ────────────────────────────────────────────────────
    def comprar(self, nodo_id: str) -> bool:
        """Sube un rango pagando con puntos de experiencia.

        Todo o nada, como `ExperienceSystem.spend`: si el gasto no cabe, no se
        sube el rango. Cobrar y no dar es peor que no dejar comprar.
        """
        if not self.puede_comprar(nodo_id):
            return False
        from src.engine.core.experience import ExperienceSystem

        if not ExperienceSystem.get_instance().spend(self.coste(nodo_id)):
            return False
        self._rangos[nodo_id] = self.rango(nodo_id) + 1
        return True

    # ── lo que da ─────────────────────────────────────────────────
    def _total(self, nodo_id: str) -> float:
        n = _POR_ID.get(nodo_id)
        return 0.0 if n is None else n.por_rango * self.rango(nodo_id)

    def bonus_corazones(self) -> float:
        """Corazones extra. `Player.max_health` los suma y recorta a 10."""
        return self._total("vitalidad")

    def bonus_dano(self) -> float:
        """Fracción de daño extra. 0,4 = +40 %."""
        return self._total("fuerza")

    def bonus_ultimate(self) -> float:
        """Segundos extra de ultimate."""
        return self._total("impetu")

    # ── persistencia ──────────────────────────────────────────────
    def to_dict(self) -> dict[str, int]:
        return dict(self._rangos)

    def from_dict(self, datos: dict[str, Any] | None) -> None:
        """Restaura los rangos de una partida.

        Se descarta lo que no está en el catálogo y se recorta al máximo de
        cada nodo: una partida editada a mano no debe poder dar veinte
        corazones ni inventar un nodo que el juego no sabe aplicar.
        """
        self._rangos = {}
        for clave, valor in dict(datos or {}).items():
            n = _POR_ID.get(str(clave))
            if n is None:
                continue
            self._rangos[n.id] = max(0, min(int(valor), n.rangos))

    def reset(self) -> None:
        self._rangos = {}
