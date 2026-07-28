"""
Module: seasons
System: framework.stage
Academic Unit: Unidad VI — Color y composición

Estaciones: una capa fina encima del ciclo día/noche.

F2.2 — por qué esto es tan corto
--------------------------------
La estación no necesita un sistema propio. Lo que hace una estación en un juego
2D es tres cosas, y las tres ya existen:

1. **Teñir la paleta.** El ciclo día/noche ya multiplica la escena por un color
   (`LightSystem.ambient_color`); la estación multiplica ese color otra vez.
2. **Sugerir un clima.** `WeatherSystem` ya sabe llover y nevar; la estación
   sólo dice cuál es el clima por defecto si el mapa no lo declara.
3. **Cambiar las partículas del aire.** `AmbientParticleSystem` ya tiene cinco
   tipos; la estación elige uno.

Construir un "sistema de estaciones" con su propia lógica de render habría sido
duplicar tres cosas que funcionan. Este módulo es una tabla y dos funciones, y
eso es exactamente lo que debe ser.

Nota de diseño: las estaciones **no se avanzan solas**. Un escenario dura
minutos; que cambiara de invierno a primavera a mitad sería ruido, no
ambientación. La estación es una propiedad del mapa, como el clima.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Estacion:
    """Lo que una estación aporta al escenario."""

    #: Multiplicador de color sobre el tinte de la hora, de 0 a 1 por canal.
    #: Un invierno frío baja el rojo; un otoño lo sube y baja el azul.
    tinte: tuple[float, float, float]
    #: Clima por defecto si el mapa no declara `climate`.
    clima: str
    #: Partículas de aire por defecto, y su ritmo.
    particulas: tuple[str, float]
    #: Ajuste del brillo ambiente. El invierno es más pálido y luminoso por la
    #: nieve; el otoño, más apagado.
    factor_luz: float


ESTACIONES: dict[str, Estacion] = {
    "spring": Estacion(
        tinte=(0.97, 1.00, 0.95),      # verde muy leve
        clima="clear",
        particulas=("spores", 12.0),
        factor_luz=1.00,
    ),
    "summer": Estacion(
        tinte=(1.00, 0.98, 0.90),      # dorado
        clima="clear",
        particulas=("dust", 10.0),
        factor_luz=1.08,
    ),
    "autumn": Estacion(
        tinte=(1.00, 0.90, 0.78),      # ámbar
        clima="rain",
        particulas=("leaves", 14.0),
        factor_luz=0.94,
    ),
    "winter": Estacion(
        tinte=(0.92, 0.96, 1.00),      # azul pálido
        clima="snow",
        particulas=("ash", 8.0),       # ceniza gris pasa por nieve fina
        factor_luz=1.02,
    ),
}

#: Cuando el mapa no declara estación. `None` no es una opción aquí: un
#: escenario sin estación es simplemente uno de verano, y tener un cuarto caso
#: "sin estación" duplicaría cada rama de la escena.
POR_DEFECTO = "summer"


def estacion(nombre: object) -> Estacion:
    """Devuelve la estación pedida, o la de por defecto si no se reconoce.

    No lanza. Un nombre mal escrito en Tiled tiene que producir un aviso y un
    escenario jugable, no un error de carga: el estudiante que escribe
    `invierno` en vez de `winter` necesita ver su nivel para darse cuenta.
    """
    clave = str(nombre or "").strip().lower()
    return ESTACIONES.get(clave, ESTACIONES[POR_DEFECTO])


def es_valida(nombre: object) -> bool:
    return str(nombre or "").strip().lower() in ESTACIONES


#: Coeficientes de luma ITU-R BT.601, los mismos que usa el bloom.
_LUMA = (0.299, 0.587, 0.114)


def _normalizar(tinte: tuple[float, float, float]) -> tuple[float, float, float]:
    """Reescala un tinte para que no cambie el brillo, sólo el tono.

    F2.2 — el defecto que esto corrige
    ----------------------------------
    El tinte del otoño era (1,00, 0,90, 0,78): multiplicadores menores que uno
    en dos canales, así que además de dar color **quitaba luz**. Al aplicar
    otoño a Stage 0, la prueba de jugabilidad nocturna cayó de 44 % a 23 % de
    píxeles distinguibles al atardecer, por debajo del mínimo. Y el suelo de
    `MIN_AMBIENTE` no lo detenía, porque ese suelo protege el **escalar** de
    brillo y la pérdida venía por el color.

    Dos maneras de oscurecer una escena y un solo freno es un mal diseño. Aquí
    el tinte pasa a ser puramente cromático —se divide por su propia
    luminancia, así que el canal dominante sube en vez de bajar los otros— y
    `factor_luz` queda como la única perilla de brillo de una estación. Cada
    cosa la controla exactamente un número.
    """
    luma = sum(c * k for c, k in zip(tinte, _LUMA, strict=True))
    if luma <= 0:
        return (1.0, 1.0, 1.0)
    return (tinte[0] / luma, tinte[1] / luma, tinte[2] / luma)


def aplicar_tinte(
    color: tuple[int, int, int], est: Estacion,
) -> tuple[int, int, int]:
    """Combina el tinte de la hora con el de la estación.

    Los dos son multiplicadores, así que se componen sin más. Es la razón de
    que la estación pueda ser una capa tan fina: no compite con la hora, la
    modula. El de la estación se normaliza primero, para que aporte tono y no
    oscuridad — ver `_normalizar`.
    """
    factores = _normalizar(est.tinte)
    return (
        max(0, min(255, round(color[0] * factores[0]))),
        max(0, min(255, round(color[1] * factores[1]))),
        max(0, min(255, round(color[2] * factores[2]))),
    )
