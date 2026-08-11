"""El pulso visual: la imagen late con la música — AUD-425.

Por qué existía el hueco
========================
`docs/62` §C1 listaba seis piezas para el reloj musical y cinco estaban hechas
desde AUD-137: reloj alimentado por la posición de la pista, `bpm`/`compas`
como propiedades de mapa, objetos cuantizados a compás y compensación de
latencia. La sexta —«pulso visual: cámara, escala y luz al compás»— era la
única viva, y AUD-414 la dejó dicha en vez de escondida entre cinco afirmaciones
falsas.

El motivo de que faltara es el de siempre en este repositorio:
`engine/audio/music_clock.py` son 280 líneas que saben exactamente en qué punto
del compás va la música, y **ningún consumidor visual las miraba**. La
información estaba; faltaba enchufarla.

Cómo se sostiene sin marear
===========================
Un latido visual es fácil de hacer mal: si late todo, todo el rato y con la
misma fuerza, deja de ser una acentuación y se convierte en un temblor. Tres
reglas, las tres con su número:

* **Decae, no oscila.** La intensidad es máxima justo cuando entra el pulso y
  cae a cero antes del siguiente. Una senoidal completa daría un balanceo
  constante; esto da un golpe y silencio, que es lo que hace una batería.
* **El primer tiempo del compás pesa más.** `pulso_en_compas == 0` es el que se
  acentúa —lo dice el propio reloj en su docstring— y aquí vale el doble que
  los demás. Sin esa diferencia, un 4/4 se siente como cuatro golpes iguales y
  se pierde el compás.
* **Las amplitudes son deliberadamente pequeñas.** 1,5 px de cámara y un 6 % de
  luz. Se nota sin que nadie sepa por qué se nota, que es la definición de que
  está bien puesto; al doble, un nivel rítmico se vuelve incómodo de jugar.

Un escenario sin `bpm` no tiene reloj musical, así que no late nada: los
diecisiete mapas entregados se ven exactamente igual que antes.
"""
from __future__ import annotations

from typing import Any

__all__ = ["AMPLITUD_CAMARA_PX", "AMPLITUD_LUZ", "intensidad", "offset_de_camara"]

#: Cuánto dura el golpe, en fracción de pulso. 0,35 a 120 BPM son 175 ms.
#:
#: Por debajo de 0,2 el destello es tan corto que a 60 fps puede caer entre dos
#: fotogramas y perderse; por encima de 0,5 el pulso todavía está decayendo
#: cuando entra el siguiente y los golpes se solapan en un temblor continuo.
_DURACION = 0.35

#: Cuánto más pesa el primer tiempo del compás.
_ACENTO = 2.0

#: Desplazamiento vertical máximo de la cámara, en píxeles.
#:
#: Píxel y medio. El juego corre a 320×180 internos, así que 1,5 px es casi un
#: 1 % de la altura: se percibe como un empujón y no como un salto de imagen.
AMPLITUD_CAMARA_PX = 1.5

#: Cuánto sube el brillo ambiental en el golpe, en fracción.
AMPLITUD_LUZ = 0.06


def intensidad(reloj: Any | None) -> float:
    """Cuánto late la imagen **ahora**, de 0 a 1.

    Devuelve 0 sin reloj, que es el caso de todo escenario que no declara
    `bpm`. Es lo que mantiene intactos los mapas que no son rítmicos: no hay
    bandera que apagar ni valor por defecto que recordar — sin música medida,
    no hay latido.
    """
    if reloj is None:
        return 0.0
    try:
        fraccion = float(reloj.fraccion)
        en_compas = int(reloj.pulso_en_compas)
    except (AttributeError, TypeError, ValueError):
        # Un doble de prueba incompleto no puede tumbar el fotograma que
        # decora. Misma regla que el contador de texturas en AUD-413.
        return 0.0

    if fraccion >= _DURACION:
        return 0.0
    # Caída lineal desde 1 en el instante del pulso hasta 0 al final del golpe.
    caida = 1.0 - (fraccion / _DURACION)
    peso = _ACENTO if en_compas == 0 else 1.0
    return min(1.0, caida * peso / _ACENTO)


def offset_de_camara(reloj: Any | None) -> float:
    """Píxeles que la cámara baja en este fotograma. Positivo = hacia abajo.

    Baja y no sube porque el golpe se lee como un impacto contra el suelo: una
    cámara que sube en el pulso se siente como si el mundo flotara.
    """
    return intensidad(reloj) * AMPLITUD_CAMARA_PX


def factor_de_luz(reloj: Any | None) -> float:
    """Multiplicador del brillo ambiental. 1,0 cuando no hay latido."""
    return 1.0 + intensidad(reloj) * AMPLITUD_LUZ
