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

    def disparar(self, origen: pygame.Vector2, direccion: int) -> Projectile | None:
        """Lanza una flecha. Devuelve `None` si no se puede.

        `direccion` es -1 o +1. No se admite disparar en diagonal: el juego es
        de plataformas con movimiento horizontal, y apuntar en ocho
        direcciones exigiría un control que no existe.
        """
        if not self.listo:
            return None

        self.municion -= 1
        self._espera = self.cadencia
        signo = -1 if direccion < 0 else 1
        flecha = Projectile(
            spawn_position=pygame.Vector2(origen),
            velocity=pygame.Vector2(VELOCIDAD * signo, 0.0),
            damage=self.dano,
            lifetime=VIDA,
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
