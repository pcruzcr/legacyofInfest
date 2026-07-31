"""
El enjambre de balas: miles de proyectiles en arreglos, no un objeto por bala.

F5.8 — por qué esto NO es un sistema ECS, y por qué eso está bien
=================================================================
El resto de la fase 5 empuja hacia componentes y sistemas. Aquí se hace lo
contrario a propósito, y la razón se mide.

Un *bullet hell* —Ikaruga, Enter the Gungeon, The Binding of Isaac, Just Shapes
& Beats: seis jefes del dossier— tiene entre **quinientos y tres mil**
proyectiles vivos a la vez. Con un objeto por bala, cada fotograma hace:

* tres mil búsquedas de atributo para leer la posición,
* tres mil más para la velocidad,
* tres mil sumas de `Vector2`, cada una con su asignación de objeto,
* y tres mil `colliderect`.

Medido en este mismo motor, contra `Projectile` —el objeto que ya usan los
enemigos y el arco del jugador— y contra este enjambre, actualizando y
comprobando impactos, milisegundos por fotograma:

    balas   objeto/bala    enjambre    factor
      500       3,96 ms    0,148 ms      27x
     1000       5,48 ms    0,092 ms      59x
     2000      12,94 ms    0,072 ms     180x
     3000      10,44 ms    0,073 ms     143x

    presupuesto a 60 fps: 16,667 ms

A dos mil balas, un objeto por bala se come **el 78 % del fotograma entero** sin
haber dibujado nada todavía; el enjambre gasta el 0,4 %. Y el enjambre apenas
sube al triplicar la cuenta, porque el coste ya no está en las balas sino en la
llamada a NumPy: es tiempo fijo, no por bala. Ahí está toda la diferencia.

(La fila de 3000 sale más barata que la de 2000 en el caso de objetos por el
recolector de basura, que dispara en distinto momento según cuánto se asignó.
Se deja el número medido tal cual en vez de repetir hasta que salga bonito: la
conclusión no depende de esa fila.)

No es una idea nueva en esta casa: `AmbientParticleSystem` ya lo hace para las
partículas de ambiente, por el mismo motivo. Tener las dos formas —componentes
para lo que es distinto entre sí, arreglos para lo que es idéntico y numeroso—
y saber cuándo toca cada una es mejor lección que aplicar una sola a todo.

La regla, dicha corta
---------------------
* Pocas entidades, cada una distinta  → componentes y sistemas.
* Muchas entidades, todas iguales     → arreglos paralelos.

Un jefe es lo primero. Sus balas son lo segundo.
"""
from __future__ import annotations

import numpy as np
import pygame

#: Tope de balas vivas. Al llegar, las nuevas se descartan.
#:
#: Un tope duro y no un crecimiento sin límite: sin él, un patrón mal calibrado
#: de un estudiante llena la memoria y el juego se muere sin decir por qué. Con
#: tope, el peor caso es que dejen de aparecer balas, que se ve y se entiende.
CAPACIDAD_POR_DEFECTO = 4096


class EnjambreDeBalas:
    """Proyectiles en arreglos paralelos, con hueco reutilizable.

    Cada atributo es un arreglo de `CAPACIDAD` elementos y la posición `i` de
    todos ellos describe la misma bala. `vivas[i]` dice si esa ranura está en
    uso. Es la estructura *structure of arrays*, y es lo que permite operar
    sobre todas a la vez.
    """

    __slots__ = ("_libres", "capacidad", "dano", "radio", "vidas", "vivas", "vx", "vy", "x", "y")

    def __init__(self, capacidad: int = CAPACIDAD_POR_DEFECTO) -> None:
        self.capacidad = capacidad
        # float32 y no float64: la mitad de memoria y de ancho de banda, y a
        # escala de píxeles la precisión sobra con creces.
        self.x = np.zeros(capacidad, dtype=np.float32)
        self.y = np.zeros(capacidad, dtype=np.float32)
        self.vx = np.zeros(capacidad, dtype=np.float32)
        self.vy = np.zeros(capacidad, dtype=np.float32)
        self.vidas = np.zeros(capacidad, dtype=np.float32)
        self.dano = np.zeros(capacidad, dtype=np.float32)
        self.radio = np.zeros(capacidad, dtype=np.float32)
        self.vivas = np.zeros(capacidad, dtype=bool)
        #: Pila de ranuras libres. Buscar un hueco recorriendo `vivas` costaría
        #: O(n) por disparo, y a treinta disparos por fotograma eso se nota.
        self._libres: list[int] = list(range(capacidad - 1, -1, -1))

    # -- alta y baja -----------------------------------------------
    def disparar(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        vida: float = 4.0,
        dano: float = 1.0,
        radio: float = 3.0,
    ) -> int:
        """Añade una bala. Devuelve su ranura, o -1 si el enjambre está lleno."""
        if not self._libres:
            return -1
        i = self._libres.pop()
        self.x[i] = x
        self.y[i] = y
        self.vx[i] = vx
        self.vy[i] = vy
        self.vidas[i] = vida
        self.dano[i] = dano
        self.radio[i] = radio
        self.vivas[i] = True
        return i

    def abanico(
        self,
        x: float,
        y: float,
        cuantas: int,
        velocidad: float,
        angulo_inicial: float = 0.0,
        apertura: float = 360.0,
        **kwargs: float,
    ) -> int:
        """Un abanico de balas de una vez. El patrón más común del género.

        Los ángulos se calculan con NumPy en vez de con un bucle: para 200
        balas son dos llamadas en vez de cuatrocientas operaciones en Python, y
        es exactamente la clase de detalle que decide si un patrón denso cabe en
        el fotograma.
        """
        if cuantas <= 0:
            return 0
        angulos = np.radians(
            angulo_inicial + np.linspace(0.0, apertura, cuantas, endpoint=apertura < 360.0),
        )
        vxs = np.cos(angulos) * velocidad
        vys = np.sin(angulos) * velocidad
        creadas = 0
        for k in range(cuantas):
            if self.disparar(x, y, float(vxs[k]), float(vys[k]), **kwargs) < 0:
                break
            creadas += 1
        return creadas

    def retirar(self, indices: np.ndarray) -> None:
        """Da de baja las ranuras indicadas."""
        if indices.size == 0:
            return
        self.vivas[indices] = False
        self._libres.extend(int(i) for i in indices)

    def limpiar(self) -> None:
        """Vacía el enjambre. Al cambiar de fase o de escenario."""
        self.vivas[:] = False
        self._libres = list(range(self.capacidad - 1, -1, -1))

    # -- ciclo -----------------------------------------------------
    def update(self, dt: float, limites: pygame.Rect | None = None) -> None:
        """Un fotograma para todas las balas a la vez."""
        vivas = self.vivas
        if not vivas.any():
            return

        # Se opera sobre el arreglo entero, no sobre las vivas. Filtrar primero
        # crea copias y a estos tamaños sale más caro que hacer aritmética de
        # más sobre ranuras muertas cuyo resultado se descarta.
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vidas -= dt

        caducadas = vivas & (self.vidas <= 0.0)
        if limites is not None:
            fuera = (
                (self.x < limites.left)
                | (self.x > limites.right)
                | (self.y < limites.top)
                | (self.y > limites.bottom)
            )
            caducadas |= vivas & fuera
        if caducadas.any():
            self.retirar(np.flatnonzero(caducadas))

    def impactos_contra(self, objetivo: pygame.Rect) -> np.ndarray:
        """Ranuras de las balas que tocan ese rectángulo, ahora mismo.

        Se aproxima la bala por su círculo inscrito frente al rectángulo
        expandido. Es la prueba círculo-rectángulo simplificada: exacta en los
        lados y ligeramente generosa en las cuatro esquinas.

        Generosa a favor del jugador cuando el rectángulo es un enemigo, y en
        contra cuando es él. Se documenta porque un estudiante que mida sus
        colisiones va a encontrar esa asimetría y merece saber que es
        deliberada, no un fallo.
        """
        if not self.vivas.any():
            return np.empty(0, dtype=np.intp)
        dentro = (
            (self.x >= objetivo.left - self.radio)
            & (self.x <= objetivo.right + self.radio)
            & (self.y >= objetivo.top - self.radio)
            & (self.y <= objetivo.bottom + self.radio)
        )
        return np.flatnonzero(self.vivas & dentro)

    def dano_total_contra(self, objetivo: pygame.Rect, consumir: bool = True) -> float:
        """Suma el daño de las balas que impactan y, por defecto, las retira."""
        golpes = self.impactos_contra(objetivo)
        if golpes.size == 0:
            return 0.0
        total = float(self.dano[golpes].sum())
        if consumir:
            self.retirar(golpes)
        return total

    # -- dibujado --------------------------------------------------
    def draw(
        self,
        surface: pygame.Surface,
        camera_offset: pygame.Vector2,
        color: tuple[int, int, int] = (255, 120, 200),
    ) -> None:
        """Dibuja las balas visibles.

        Se recortan a la pantalla **antes** de dibujar. Sin el recorte, tres mil
        `draw.circle` cuestan más que toda la simulación junta, y dos mil de
        ellos pintan fuera de la ventana.
        """
        vivas = np.flatnonzero(self.vivas)
        if vivas.size == 0:
            return
        ancho, alto = surface.get_size()
        px = self.x[vivas] - camera_offset.x
        py = self.y[vivas] - camera_offset.y
        r = self.radio[vivas]
        visibles = (px >= -r) & (px <= ancho + r) & (py >= -r) & (py <= alto + r)
        for k in np.flatnonzero(visibles):
            pygame.draw.circle(
                surface, color, (int(px[k]), int(py[k])), max(1, int(r[k])),
            )

    # -- diagnóstico -----------------------------------------------
    @property
    def contador(self) -> int:
        return int(self.vivas.sum())

    @property
    def lleno(self) -> bool:
        return not self._libres
