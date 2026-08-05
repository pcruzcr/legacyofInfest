"""
Module: registro
System: engine.core
Academic Unit: N/A

AUD-268 — a dónde van los avisos.

El proyecto no configuraba el logging **en ninguna parte**. Sin configuración,
Python instala su manejador de último recurso y escribe todo lo de `WARNING`
para arriba en la consola; y este repositorio tiene 134 llamadas a
`logger.warning`, muchas en rutas normales de juego —un fondo que falta, un
árbol de diálogo que el mapa pide y no existe, el renderizador cayendo a
software—. El jugador veía una pared de mensajes técnicos mientras jugaba.

Por qué no se borran los avisos
--------------------------------
Porque son correctos. Este repositorio lleva un mes cazando defectos que
fallaban **en silencio** —AUD-055, el objeto de Tiled mal escrito que
desaparecía; AUD-127, el diálogo que no se abría; AUD-149, los cuatro enemigos
cuyo daño no llegaba— y la lección de todos fue la misma: callarse es lo que
hace que un defecto dure meses. Los avisos se quedan.

Lo que cambia es el destino: la consola se queda para el jugador, y el registro
completo va a un fichero junto a las partidas, donde no molesta y sigue estando
cuando alguien pregunta «¿por qué no me sale el diálogo?».
"""
from __future__ import annotations

import logging
from pathlib import Path

from src.engine.core.user_settings import user_data_dir

#: Nombre del fichero de registro. Uno solo y se sobreescribe cada arranque: un
#: registro que crece sin límite acaba siendo un fichero de 200 MB que nadie
#: mira, y lo que hace falta casi siempre es *la última partida*.
NOMBRE_DEL_REGISTRO = "legacy_of_infest.log"

#: Marca para no apilar manejadores si `App` se construye dos veces en el mismo
#: proceso, que es lo que hacen las pruebas.
_MARCA = "loi_registro"


def ruta_del_registro(directorio: Path | None = None) -> Path:
    """Dónde vive el registro. Junto a las partidas, no dentro del proyecto."""
    base = directorio if directorio is not None else user_data_dir()
    return Path(base) / NOMBRE_DEL_REGISTRO


def configurar_registro(depurar: bool = False,
                        directorio: Path | None = None) -> Path | None:
    """Manda los avisos al fichero, y a la consola sólo si se piden.

    Devuelve la ruta del registro, o `None` si no se pudo abrir.

    Que no se pueda abrir **no impide jugar**: un directorio de sólo lectura o
    un disco lleno son problemas del entorno, y quedarse sin juego por no poder
    escribir un registro sería el remedio peor que la enfermedad. En ese caso
    los avisos se descartan en silencio, que es exactamente lo que el jugador
    quiere que pase.
    """
    raiz = logging.getLogger()
    raiz.setLevel(logging.DEBUG if depurar else logging.INFO)

    # Se retiran los nuestros de una pasada anterior; los de otro (pytest, una
    # entrega que configure el suyo) no se tocan.
    for viejo in [h for h in raiz.handlers if getattr(h, _MARCA, False)]:
        raiz.removeHandler(viejo)
        viejo.close()

    formato = logging.Formatter(
        "%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    destino: Path | None = None
    try:
        ruta = ruta_del_registro(directorio)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        fichero = logging.FileHandler(ruta, mode="w", encoding="utf-8")
        fichero.setFormatter(formato)
        fichero.setLevel(logging.DEBUG if depurar else logging.INFO)
        setattr(fichero, _MARCA, True)
        raiz.addHandler(fichero)
        destino = ruta
    except (OSError, ValueError):
        # Sin fichero, y sin ruido: ver arriba.
        pass

    if depurar:
        consola = logging.StreamHandler()
        consola.setFormatter(formato)
        consola.setLevel(logging.DEBUG)
        setattr(consola, _MARCA, True)
        raiz.addHandler(consola)
    elif not raiz.handlers:
        # Sin ningún manejador, Python volvería a usar el de último recurso y
        # los avisos reaparecerían en la consola. Un `NullHandler` lo impide.
        nulo = logging.NullHandler()
        setattr(nulo, _MARCA, True)
        raiz.addHandler(nulo)

    return destino
