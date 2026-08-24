"""
Module: integridad
System: engine.core
Academic Unit: N/A
Description: AUD-295 — firma de los ficheros JSON que el juego escribe.

Lo primero, porque si no esto promete lo que no da
==================================================
**Esto no defiende de un estudiante que quiera alterar su tiempo de speedrun.**
El *salt* vive en el código, y el código lo leen las veintiséis personas de las
que teóricamente defendería: quien quiera saltárselo abre este fichero, copia
tres líneas y regenera la firma. Cualquier esquema con la clave en el cliente
tiene ese techo, y no hay forma de subirlo sin un servidor.

Lo que sí da, que no es poco:

* **Detecta corrupción.** Un guardado interrumpido a mitad, un disco con un
  sector malo, un `orjson` que escribió medio fichero. Hoy eso se leía como
  datos válidos y el juego cargaba una partida a medias sin decir nada.
* **Detecta la edición casual.** Abrir `speedrun.json`, poner `0.5` y volver a
  entrar. No es el ataque sofisticado: es el que de verdad ocurre en un aula.
* **Lo deja anotado.** Un fichero que no cuadra se registra, y eso convierte
  «juraría que tenía más monedas» en una línea que se puede mirar.

Cómo se firma
=============
HMAC-SHA256 sobre el JSON **canónico** —claves ordenadas, sin la propia firma—
y el resultado va dentro del mismo objeto, en `_firma`. Un fichero sin `_firma`
se acepta: son los que escribió el juego antes de AUD-295, y rechazarlos sería
borrarle la partida a todo el mundo por una mejora.

HMAC y no un `sha256(salt + datos)` a secas porque el segundo es vulnerable a
extensión de longitud, y aunque aquí no cambie el resultado práctico, enseñar
la versión mala en un repositorio del que copian veintiséis personas sí importa.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any

import orjson

logger = logging.getLogger(__name__)

#: Clave con la que se firma. Está en el código y eso es una decisión, no un
#: descuido: ver la cabecera del módulo. Cambiarla invalida todas las firmas
#: existentes, y esos ficheros pasarán a leerse como «sin firma» — se aceptan,
#: se vuelven a firmar al guardar, y nadie pierde nada.
_CLAVE: bytes = b"legacy-of-infest/AUD-295/integridad-de-datos-locales"

#: Nombre del campo donde vive la firma dentro del propio JSON.
CAMPO_FIRMA: str = "_firma"


def _canonico(datos: dict[str, Any]) -> bytes:
    """Los datos sin su firma, en bytes estables.

    `OPT_SORT_KEYS` importa: sin él, dos volcados del mismo diccionario pueden
    ordenar las claves distinto y producir firmas distintas para datos
    idénticos. Un verificador que falla la mitad de las veces es peor que
    ninguno, porque enseña a ignorar el aviso.
    """
    limpio = {k: v for k, v in datos.items() if k != CAMPO_FIRMA}
    return orjson.dumps(limpio, option=orjson.OPT_SORT_KEYS)


def firmar(datos: dict[str, Any]) -> dict[str, Any]:
    """Devuelve una copia de `datos` con su firma dentro."""
    firmado = dict(datos)
    firmado[CAMPO_FIRMA] = hmac.new(
        _CLAVE, _canonico(datos), hashlib.sha256).hexdigest()
    return firmado


def verificar(datos: Any) -> bool:
    """¿Cuadra la firma de estos datos?

    Devuelve `True` también cuando **no hay firma**. Es deliberado: los
    ficheros anteriores a AUD-295 no la tienen, y tratarlos como alterados
    borraría la partida de todo el que actualice. Quien quiera distinguir los
    dos casos tiene `esta_firmado`.
    """
    if not isinstance(datos, dict):
        return False
    guardada = datos.get(CAMPO_FIRMA)
    if not isinstance(guardada, str):
        return True
    esperada = hmac.new(_CLAVE, _canonico(datos), hashlib.sha256).hexdigest()
    # `compare_digest` y no `==`: comparar cadenas termina en el primer byte
    # distinto y filtra por tiempo cuánto acertaste. Aquí da igual —el atacante
    # tiene la clave delante— pero es lo que hay que escribir en el fichero del
    # que se copia.
    return hmac.compare_digest(guardada, esperada)


def esta_firmado(datos: Any) -> bool:
    return isinstance(datos, dict) and isinstance(datos.get(CAMPO_FIRMA), str)


def volcar(datos: dict[str, Any], *, indentado: bool = True) -> bytes:
    """Serializa **firmando**. Sustituto directo de `orjson.dumps`."""
    opciones = orjson.OPT_INDENT_2 if indentado else 0
    return orjson.dumps(firmar(datos), option=opciones)


def cargar(crudo: bytes | str, *, origen: str = "") -> dict[str, Any] | None:
    """Lee y verifica. `None` si el JSON está roto **o la firma no cuadra**.

    Devolver `None` y no lanzar: quien llama a esto ya sabe qué hacer sin
    datos —empezar de cero, enseñar la pantalla vacía— y no sabría qué hacer
    con una excepción a mitad de la carga de una partida.
    """
    try:
        datos = orjson.loads(crudo)
    except (orjson.JSONDecodeError, ValueError, TypeError):
        logger.warning("integridad: %s no es JSON válido", origen or "el fichero")
        return None
    if not isinstance(datos, dict):
        return None
    if not verificar(datos):
        logger.warning(
            "integridad: la firma de %s no cuadra — el fichero se escribió a "
            "medias o alguien lo editó. Se ignora.", origen or "el fichero")
        return None
    return datos
