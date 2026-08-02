"""
El arco del jugador: disparo a distancia con munición y recarga.

F4.2 — de dónde sale esto
=========================
Petición de los estudiantes tras jugar la fase 1: *«si el player puede tener
más ataques ya sea con un arco o un arma hacer disparos»*.

El jugador tenía tres ataques —corto, largo y el ultimate— y **todos cuerpo a
cuerpo**. Contra un enemigo volador o al otro lado de un foso no había nada
que hacer salvo esperar a que bajase.

Por qué munición y no enfriamiento
-----------------------------------
Un enfriamiento sin más convierte el arco en el ataque por defecto: es seguro,
llega lejos y no cuesta nada. La munición limitada, que se recupera al golpear
cuerpo a cuerpo, mantiene el arco como **recurso** y empuja a alternar, que es
lo que hace interesante el combate de este género.

Se recarga golpeando, no con el tiempo, por la misma razón: recompensa
acercarse en vez de premiar la paciencia.

Por qué reutiliza `Projectile` del enemigo
-------------------------------------------
Ya existía, hace exactamente esto y está probado. Escribir una segunda clase
de proyectil habría dado dos implementaciones del mismo concepto —el defecto
que AUD-099 acaba de retirar del motor— y el estudiante tendría que aprender
dos.
"""
from __future__ import annotations

import pygame

from src.framework.entities.enemy_shooter import Projectile

#: Flechas que caben en el carcaj.
MUNICION_MAXIMA: int = 5
#: Segundos entre disparos. Sin esto, mantener pulsado vacía el carcaj en un
#: fotograma y el recurso deja de significar nada.
CADENCIA: float = 0.35
#: Velocidad de la flecha, px/s.
VELOCIDAD: float = 420.0
#: Daño de una flecha. Menos que un golpe corto a propósito: la distancia ya
#: es la ventaja, y si además pegara más fuerte no habría motivo para acercarse.
DANO: float = 0.5
#: Segundos que vive una flecha antes de desaparecer.
VIDA: float = 1.6
#: Flechas que devuelve un golpe cuerpo a cuerpo conectado.
RECARGA_POR_GOLPE: int = 1


#: Caída de la flecha, px/s².
#:
#: AUD-193. Calibrado midiendo la caída de un tiro horizontal a las distancias
#: a las que de verdad se combate, no elegido a ojo:
#:
#: caída de un tiro horizontal, integrada con el mismo paso que usa el juego:
#:
#:     gravedad   a 10 baldosas   a 20 baldosas
#:          110          10 px           34 px
#:     ->   180          16 px           55 px
#:          340          29 px          104 px
#:
#: Se toma 180. A diez baldosas la flecha cae 16 px —la mitad de la altura del
#: jugador—, así que el combate cercano se sigue resolviendo apuntando de
#: frente y nadie tiene que reaprender a disparar. A veinte cae 55 px y ahí
#: acertar pasa a ser una habilidad. Esa progresión es justamente lo que hace
#: que valga la pena dibujar la trayectoria.
#:
#: Con 340 —el primer valor que puse, y a ojo— la flecha caía 104 px en veinte
#: baldosas, más que la altura del salto del jugador: el arco quedaba
#: inservible a media distancia y los enemigos ya colocados en los mapas
#: calibrados pasaban a ser inalcanzables.
GRAVEDAD_FLECHA: float = 180.0

#: Cuántos puntos se calculan al dibujar la trayectoria y cada cuánto.
#:
#: 28 pasos de 1/30 s son casi un segundo de vuelo, más que suficiente para
#: cualquier tiro útil. El paso es más grueso que el del juego a propósito: la
#: línea se dibuja punteada y muestrear más sólo gasta CPU en puntos que caen
#: uno encima de otro.
PASOS_TRAYECTORIA: int = 28
PASO_TRAYECTORIA: float = 1.0 / 30.0


def velocidad_inicial(direccion: int | pygame.Vector2) -> pygame.Vector2:
    """El vector de salida de la flecha, venga de una tecla o de un apuntado.

    Un `int` (-1 o +1) es el disparo horizontal de siempre. Un `Vector2` es la
    dirección apuntada, que se normaliza aquí: quien apunta entrega hacia
    dónde, no a qué velocidad, y dejar que el módulo del vector llegue hasta la
    flecha haría que apuntar lejos con el ratón disparara más fuerte.
    """
    if isinstance(direccion, pygame.Vector2):
        if direccion.length_squared() > 0.0:
            return direccion.normalize() * VELOCIDAD
        # Un stick en reposo o el cursor justo encima del jugador: se dispara
        # a la derecha en vez de no disparar, porque gastar la flecha sin que
        # salga nada es peor que gastarla en una dirección discutible.
        return pygame.Vector2(VELOCIDAD, 0.0)
    signo = -1 if direccion < 0 else 1
    return pygame.Vector2(VELOCIDAD * signo, 0.0)


def trayectoria(
    origen: pygame.Vector2,
    direccion: int | pygame.Vector2,
    pasos: int = PASOS_TRAYECTORIA,
) -> list[pygame.Vector2]:
    """Los puntos por los que pasará la flecha, para dibujarlos antes de tirar.

    Integra **el mismo paso que usa `Projectile.update`**, y en el mismo orden
    —primero la gravedad sobre la velocidad, luego la posición—. Calcular la
    curva con una fórmula cerrada distinta sería más elegante y estaría mal: la
    línea dibujada y la flecha que vuela se separarían, y el jugador nota
    enseguida que la previsualización le miente.
    """
    velocidad = velocidad_inicial(direccion)
    posicion = pygame.Vector2(origen)
    puntos = [pygame.Vector2(posicion)]
    for _ in range(pasos):
        velocidad.y += GRAVEDAD_FLECHA * PASO_TRAYECTORIA
        posicion.x += velocidad.x * PASO_TRAYECTORIA
        posicion.y += velocidad.y * PASO_TRAYECTORIA
        puntos.append(pygame.Vector2(posicion))
    return puntos


class ArcoDelJugador:
    """Munición, cadencia y creación de flechas.

    No conoce al jugador: recibe posición y dirección. Así se puede probar
    sin construir un `Player` entero, y un estudiante puede dárselo a un
    aliado o a un jefe sin heredar nada.
    """

    def __init__(
        self,
        municion_maxima: int = MUNICION_MAXIMA,
        cadencia: float = CADENCIA,
        dano: float = DANO,
    ) -> None:
        self.municion_maxima = municion_maxima
        self.municion = municion_maxima
        self.cadencia = cadencia
        self.dano = dano
        self._espera = 0.0
        self.flechas: list[Projectile] = []

    # -- estado ----------------------------------------------------
    @property
    def listo(self) -> bool:
        """¿Se puede disparar ahora mismo?"""
        return self.municion > 0 and self._espera <= 0.0

    @property
    def vacio(self) -> bool:
        return self.municion <= 0

    # -- ciclo -----------------------------------------------------
    def update(self, dt: float) -> None:
        if self._espera > 0.0:
            self._espera -= dt
        for flecha in self.flechas:
            flecha.update(dt)
        # Una flecha caducada se queda con `is_active = False`; si no se
        # retiran, la lista crece durante toda la partida.
        self.flechas = [f for f in self.flechas if f.is_active]

    def disparar(
        self,
        origen: pygame.Vector2,
        direccion: int | pygame.Vector2,
    ) -> Projectile | None:
        """Lanza una flecha. Devuelve `None` si no se puede.

        AUD-193 — por qué ahora sí se apunta en diagonal
        ------------------------------------------------
        Esto admitía sólo -1 o +1, y el motivo escrito era:

            «No se admite disparar en diagonal: el juego es de plataformas con
            movimiento horizontal, y apuntar en ocho direcciones exigiría un
            control que no existe.»

        El argumento no era que apuntar libre estuviera mal: era que **no
        había con qué**. Con el ratón o el stick derecho ese control existe, así
        que la razón deja de sostenerse — y sólo por eso se cambia.

        Se admiten las dos formas a propósito. Un `int` dispara horizontal
        exactamente como antes, que es lo que hacen los 17 mapas ya calibrados
        y las entregas de estudiantes; un `Vector2` apunta libre. Nadie tiene
        que migrar nada.
        """
        if not self.listo:
            return None

        self.municion -= 1
        self._espera = self.cadencia
        flecha = Projectile(
            spawn_position=pygame.Vector2(origen),
            velocity=velocidad_inicial(direccion),
            damage=self.dano,
            lifetime=VIDA,
            gravity=GRAVEDAD_FLECHA,
        )
        self.flechas.append(flecha)
        return flecha

    def recargar(self, cantidad: int = RECARGA_POR_GOLPE) -> int:
        """Devuelve flechas al carcaj. Retorna cuántas entraron de verdad."""
        antes = self.municion
        self.municion = min(self.municion_maxima, self.municion + max(0, cantidad))
        return self.municion - antes

    def llenar(self) -> None:
        """Carcaj lleno. Se usa al reaparecer en un punto de control."""
        self.municion = self.municion_maxima

    def limpiar(self) -> None:
        """Retira las flechas en vuelo. Al cambiar de escenario o morir."""
        self.flechas.clear()

    # -- combate ---------------------------------------------------
    @staticmethod
    def _barrido(flecha: Projectile, dt: float) -> pygame.Rect:
        """El área que la flecha recorre en un fotograma, no dónde acaba.

        La flecha mide **4 px** y viaja a 420 px/s: a 60 fotogramas por
        segundo avanza **7 px por fotograma**. Comprobar sólo su posición
        final se salta cualquier objetivo más estrecho que 3 px, y —peor— la
        deja atravesar a un enemigo si el fotograma cae justo delante y justo
        detrás de él.

        Es el fallo clásico del proyectil rápido, y se ve poquísimo: pasa una
        vez de cada muchas y parece «mala suerte». Comprobar el segmento
        recorrido lo elimina por completo y cuesta un `union`.
        """
        recorrido = flecha.rect.move(
            int(flecha.velocity.x * dt), int(flecha.velocity.y * dt),
        )
        return flecha.rect.union(recorrido)

    def impactos_contra(
        self, objetivos: list, dt: float = 1.0 / 60.0,
    ) -> list[tuple[Projectile, object]]:
        """Pares (flecha, objetivo) que se tocan este fotograma.

        No aplica el daño: sólo informa. Quién puede dañar a quién es una
        decisión de la escena, no del arma, y mezclarlo aquí obligaría a este
        módulo a conocer enemigos, jefes y aliados.
        """
        golpes: list[tuple[Projectile, object]] = []
        for flecha in self.flechas:
            if not flecha.is_active:
                continue
            area = self._barrido(flecha, dt)
            for objetivo in objetivos:
                rect = getattr(objetivo, "rect", None)
                if rect is None or not getattr(objetivo, "is_alive", True):
                    continue
                if area.colliderect(rect):
                    golpes.append((flecha, objetivo))
                    flecha.is_active = False
                    break
        return golpes

    def choca_con_muros(self, muros: list[pygame.Rect], dt: float = 1.0 / 60.0) -> None:
        """Una flecha que da en la pared se para. Si no, atraviesa el nivel.

        Usa el mismo barrido que `impactos_contra`: una pared de un tile es
        más ancha que el avance por fotograma, pero un borde fino no, y una
        flecha que atraviesa la geometría se ve enseguida.
        """
        for flecha in self.flechas:
            if flecha.is_active and self._barrido(flecha, dt).collidelist(muros) != -1:
                flecha.is_active = False
