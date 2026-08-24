"""
Module: polifonia
System: engine.audio
Academic Unit: N/A
Description: AUD-280 — cuántas veces puede sonar el mismo efecto a la vez.

El problema, que se oye antes de entenderse
-------------------------------------------
`SoundBank.play()` llamaba a `Sound.play()` sin contar nada. Cinco enemigos que
mueren en el mismo fotograma —lo normal al soltar un ataque en área— disparaban
cinco veces el mismo fichero **en fase**. Sumar cinco copias idénticas de una
onda no suena «más»: suena distinto. Multiplica la amplitud por cinco, satura
el bus y produce el chasquido característico del recorte digital, y además roba
cinco de los ocho canales que pygame reserva por defecto, así que el siguiente
sonido —el del golpe del jugador, el que importa— se queda sin canal y no suena.

El resultado es exactamente el contrario del que se busca: la escena más
intensa es la que peor se oye.

Las dos reglas, y por qué son dos
---------------------------------
**Refuerzo dentro de la ventana.** Dos disparos del mismo sonido separados por
menos de 40 ms el oído no los separa: los integra en un solo evento. Así que la
segunda petición no abre voz nueva, **sube la que ya suena**. Es lo que hace que
cinco muertes simultáneas se oigan como una muerte grande en vez de como cinco
muertes recortadas.

**Tope de voces pasada la ventana.** Cinco muertes repartidas en dos segundos sí
son cinco eventos y deben oírse los cinco, pero no hacen falta veinte voces del
mismo sonido vivas a la vez. Tres es suficiente para que se note la densidad sin
comerse el bus.

Esto es lógica pura a propósito
-------------------------------
No toca el mezclador. Recibe el instante y la duración, y devuelve qué hacer;
`SoundBank` es quien habla con pygame. Se separa por la misma razón que
`mixer_buses`: **un módulo de audio que necesita altavoces para probarse no se
prueba**, y en CI no hay altavoces. Aquí se puede fijar por prueba que cinco
muertes en el mismo fotograma producen una voz y cuatro refuerzos, que es la
afirmación que interesa.
"""
from __future__ import annotations

from dataclasses import dataclass, field

#: Voces simultáneas del **mismo** sonido. Distintos sonidos no compiten aquí.
MAX_VOCES_POR_SONIDO: int = 3

#: Por debajo de esta separación, dos disparos del mismo sonido son un evento.
#:
#: 40 ms es algo más de dos fotogramas a 60 fps. Por debajo de ~30 ms el oído
#: deja de resolver dos ataques del mismo timbre como sucesos separados; por
#: encima de ~60 ms empieza a oírse el eco, que es peor que la saturación
#: porque suena a fallo del motor y no a estruendo.
VENTANA_DE_REFUERZO: float = 0.04

#: Cuánto sube la voz viva por cada repetición que se calla.
#:
#: Multiplicativo y pequeño. Cinco muertes dan 1,12⁴ = 1,57, que el tope de
#: `REFUERZO_MAXIMO` recorta: el objetivo es que se note la multitud, no que la
#: multitud sea lo único que se oiga.
REFUERZO: float = 1.12

#: Techo del refuerzo acumulado, en veces sobre el volumen pedido.
REFUERZO_MAXIMO: float = 1.5


@dataclass(frozen=True)
class Decision:
    """Qué hacer con una petición de reproducción.

    `ganancia` sólo tiene sentido con `refuerza`: es el factor **absoluto**
    sobre el volumen con el que arrancó la voz viva, no un incremento. Se
    devuelve absoluto porque `Channel.set_volume` también lo es, y convertir
    entre incrementos y absolutos en el sitio equivocado es cómo un sonido
    acaba subiendo sin techo.
    """

    accion: str  # "suena" | "refuerza" | "calla"
    ganancia: float = 1.0

    @property
    def suena(self) -> bool:
        return self.accion == "suena"


@dataclass
class _Voz:
    inicio: float
    fin: float
    ganancia: float = 1.0


@dataclass
class ControlDeVoces:
    """Decide, sin tocar el mezclador, si un sonido puede volver a sonar."""

    maximo: int = MAX_VOCES_POR_SONIDO
    ventana: float = VENTANA_DE_REFUERZO
    refuerzo: float = REFUERZO
    refuerzo_maximo: float = REFUERZO_MAXIMO
    _voces: dict[str, list[_Voz]] = field(default_factory=dict)

    def pedir(self, nombre: str, ahora: float, duracion: float) -> Decision:
        """¿Suena, refuerza a la que ya suena, o se calla?

        `duracion` es lo que dura el fichero. Con ella las voces caducan solas y
        no hace falta que nadie avise de que un canal terminó — un «avísame al
        acabar» es justo la clase de cabo suelto que deja el contador subido
        para siempre y silencia un sonido a partir de la tercera vez.
        """
        vivas = self._vivas(nombre, ahora)

        if vivas:
            ultima = vivas[-1]
            if ahora - ultima.inicio < self.ventana:
                ultima.ganancia = min(
                    ultima.ganancia * self.refuerzo, self.refuerzo_maximo,
                )
                return Decision("refuerza", ultima.ganancia)
            if len(vivas) >= self.maximo:
                return Decision("calla")

        # Una duración no positiva —un fichero que no se pudo medir— se trata
        # como una voz de la propia ventana: sin esto caducaría en el acto y el
        # tope no contaría nada.
        fin = ahora + (duracion if duracion > 0.0 else self.ventana)
        vivas.append(_Voz(inicio=ahora, fin=fin))
        self._voces[nombre] = vivas
        return Decision("suena")

    def voces_vivas(self, nombre: str, ahora: float) -> int:
        """Para el overlay de depuración y para las pruebas."""
        return len(self._vivas(nombre, ahora))

    def limpiar(self) -> None:
        self._voces.clear()

    def _vivas(self, nombre: str, ahora: float) -> list[_Voz]:
        vivas = [v for v in self._voces.get(nombre, ()) if v.fin > ahora]
        if vivas:
            self._voces[nombre] = vivas
        else:
            self._voces.pop(nombre, None)
        return vivas
