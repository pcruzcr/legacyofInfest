"""
Los cinco actos del 4-1: la tabla que hace que el fondo avance con el jugador.

Por qué es una tabla y no cinco `if`
=====================================
El diseño (`docs/niveles/15_DISENO_4_1_EL_CEMENTERIO.md` §1) define cada acto
por **cinco parámetros a la vez**: braseros encendidos, luna, clima, fondo y
peligros. Escrito como condicionales, cambiar «la luna del acto III» obliga a
buscar en cinco sitios y a acertar en los cinco. Escrito como tabla, el diseño
y el código son el mismo objeto: se lee de arriba abajo como la tabla del
documento, y una prueba puede recorrerla y comprobar que sube monótonamente.

La regla del acto (§1 del diseño): entre actos **no cambia el esquema de
control ni se introduce una mecánica nueva**. Sólo cambia lo que se ve. Por eso
aquí no hay nada que toque al jugador: ni daño, ni velocidad, ni entradas.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Acto:
    """Un acto: lo que el jugador ve cuando llega a este tramo."""

    numero: int
    nombre: str
    #: Primera baldosa del tramo. La escena compara la `x` del jugador.
    desde_baldosa: int
    #: Clima del `WeatherSystem`. Los cuatro valores son los que el motor
    #: conoce (`clear`, `rain`, `snow`, `fog`, `storm`); ninguno es inventado.
    clima: str
    #: Partículas de ambiente: `(tipo, ritmo)`. `spores` es el único efecto del
    #: motor que sale en verde — (150, 255, 130) — y es exactamente la «luz
    #: espectral verde» que el lore le pone al cementerio (§3.4).
    particulas: tuple[str, float]
    #: La luna, del §2 del diseño: baja y crece con el avance.
    luna_y: int
    luna_radio: int
    #: Cuántas siluetas de espíritu se ven en el fondo. Son los vencidos —
    #: venado, Rey Terciopelo, Gavilán— y por canon «no atacan: testifican».
    espiritus: int
    #: Si la Cegua es visible en este acto, y a qué distancia (0 = no está).
    #: Nunca es una entidad: no tiene colisión, ni IA, ni recibe daño.
    cegua: float
    #: Relámpagos por minuto. Cero fuera de la tormenta.
    rayos_por_minuto: float
    #: Luz ambiente del acto. Baja con la noche y sube en el umbral, cuando
    #: los doce braseros arden.
    ambiente: float


#: Los cinco actos, en el orden en que se juegan. Los tramos son de 20
#: baldosas sobre un mapa de 100 — la misma partición que usa el generador.
ACTOS: tuple[Acto, ...] = (
    Acto(1, "LA ENTRADA", 0, "fog", ("ash", 6.0),
         luna_y=60, luna_radio=15, espiritus=0, cegua=0.0,
         rayos_por_minuto=0.0, ambiente=0.46),
    Acto(2, "EL SENDERO DE LOS NOMBRES", 20, "fog", ("spores", 12.0),
         luna_y=110, luna_radio=30, espiritus=1, cegua=0.0,
         rayos_por_minuto=0.0, ambiente=0.44),
    Acto(3, "LA NIEBLA QUE RESPIRA", 40, "fog", ("spores", 18.0),
         luna_y=170, luna_radio=45, espiritus=2, cegua=0.35,
         rayos_por_minuto=4.0, ambiente=0.42),
    Acto(4, "LA TORMENTA", 60, "storm", ("spores", 24.0),
         luna_y=230, luna_radio=60, espiritus=3, cegua=0.7,
         rayos_por_minuto=14.0, ambiente=0.40),
    Acto(5, "EL UMBRAL", 80, "clear", ("spores", 8.0),
         luna_y=300, luna_radio=80, espiritus=3, cegua=1.0,
         rayos_por_minuto=0.0, ambiente=0.58),
)


def acto_en(baldosa_x: float) -> Acto:
    """El acto que corresponde a esa columna del mapa.

    Se recorre al revés y se devuelve el primero que ya empezó. Así añadir un
    acto es añadir una fila, y no hay ningún umbral escrito dos veces.
    """
    for acto in reversed(ACTOS):
        if baldosa_x >= acto.desde_baldosa:
            return acto
    return ACTOS[0]
