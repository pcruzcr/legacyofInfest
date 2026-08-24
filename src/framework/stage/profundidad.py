"""
Module: profundidad
System: framework.stage
Academic Unit: IV (dibujado, proyección)

AUD-277 — el 2.5D: escala por profundidad.

Qué es, y qué no
================
No es 3D, y conviene decirlo antes que nada porque la hoja de ruta las mezcla.
`docs/62` C2 lo dejó decidido con su razón: la tubería GL de 479 líneas **no es
un scene graph** —no hay materiales, ni culling, ni mallas— y si algún día hace
falta 3D de verdad el camino es portar a Godot, no ampliar esto.

2.5D sí es viable, y es esto: una entidad se dibuja más pequeña cuanto más «al
fondo» esté, con una escala sacada de su posición vertical en el mapa. Con eso,
un pasillo con tres filas de plataformas deja de leerse como un plano y pasa a
leerse como un espacio con profundidad.

**Sin tocar la física.** Ésa es la línea que separa 2.5D de 3D: aquí sólo
cambia lo que se dibuja. Las colisiones, el salto y el alcance de los ataques
siguen siendo los mismos en dos ejes, así que ningún escenario entregado puede
volverse imposible por esto.

Por qué apagado por defecto
----------------------------
Misma decisión que AUD-141 con la estamina y AUD-260 con el tiempo bala, y por
la misma razón: los dieciséis escenarios entregados están calificados, y
encenderles una mecánica visual cambiaría cómo se ven sin que sus autores lo
hayan pedido.
"""
from __future__ import annotations


class EscalaPorProfundidad:
    """Cuánto se encoge lo que está al fondo.

    Se construye con lo que declara el mapa. Con los valores por defecto está
    **apagada**: `escala_en()` devuelve 1,0 para cualquier altura y quien la
    use no nota nada.
    """

    def __init__(self, mapa_alto: int = 0,
                 minimo: float = 1.0, maximo: float = 1.0,
                 curva: float = 1.0) -> None:
        self.mapa_alto = max(0, int(mapa_alto))
        self.minimo = float(minimo)
        self.maximo = float(maximo)
        # AUD-339 — la curva de la escala. 1.0 es la interpolación lineal de
        # AUD-277; con más de 1.0 las filas del fondo se encogen más rápido,
        # que es lo que hace un espacio con perspectiva de verdad: la fila
        # siguiente a tus pies casi no cambia y el horizonte se comprime.
        # Negativa o cero invertiría el degradado o lo congelaría, así que se
        # sujeta igual que `hardness` en la niebla.
        self.curva = max(0.01, float(curva))

    @property
    def activa(self) -> bool:
        """`False` cuando no hay nada que escalar.

        Declarar 1,0 y 1,0 es **apagarlo**, no un caso raro que haya que
        calcular igualmente: quien quiera el efecto declara valores distintos.
        """
        return self.mapa_alto > 0 and self.minimo != self.maximo

    def escala_en(self, y: float) -> float:
        """La escala de una entidad cuya base está a la altura `y` del mapa.

        Se recorta a los extremos. Sin recorte, un enemigo que cae a un pozo
        por debajo del mapa se agrandaría sin límite, y uno lanzado por encima
        del borde superior se haría diminuto: dos formas de que un fallo de
        física se convierta en un fallo visual espectacular.

        La curva se aplica sobre la altura normalizada, antes de interpolar:
        con `curva = 2.0` la mitad del mapa ya ha recorrido las tres cuartas
        partes de la escala, y con `curva = 1.0` la fórmula es exactamente la
        de AUD-277.
        """
        if not self.activa:
            return 1.0
        t = y / self.mapa_alto
        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
        return self.minimo + (self.maximo - self.minimo) * (t ** self.curva)
