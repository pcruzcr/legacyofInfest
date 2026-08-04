"""
Module: stage4_1
System: src.stages.stage4_1
Academic Unit: V (color y transparencia) + VIII (visión por umbral)

NIVEL 4-1 — LA ENTRADA AL CEMENTERIO

La idea, en una frase: **el fondo avanza con el jugador**. Cada tramo que se
recorre enciende braseros, baja la luna, sube la tormenta y acerca las siluetas
— como el escenario de Magus, que se transforma por fases mientras la pelea
avanza. El 4-1 no es un pasillo con decoración: es un reloj de fondo.

Lo que este escenario NO tiene, y por qué
==========================================
**Cero enemigos.** Es la regla de oro de la ficha
(`docs/niveles/13_STAGE_4_1.md`): *«Si el nivel aburre, se arregla con más
marcas ocultas, no con serpientes.»* El lore lo dice desde el otro lado: en la
Entrada al Cementerio los ecos de los vencidos *«no atacan. Testifican.»*

Así que las siluetas del venado, la serpiente y el gavilán —y la Cegua— son
contornos dibujados en el fondo, sin colisión, sin IA y sin salud. Ver
`siluetas.py`.

Lo que sí tiene
================
* **Cinco actos** (`actos.py`), leídos de la `x` del jugador. Cada uno cambia
  clima, partículas, luna, siluetas y luz — nunca los controles.
* **Doce braseros** que se encienden por proximidad y **no se apagan**: el
  sendero queda marcado de luz por detrás, nunca por delante. Es la barra de
  progreso del nivel: si alguien pregunta cuánto falta, se cuentan los
  apagados.
* **Relámpagos** en la tormenta: un pico de luz que revela el tramo siguiente
  antes de que haya que jugarlo. La regla del diseño (§5) es que ningún peligro
  aparece sin que un rayo lo haya mostrado.
* **Visión espectral** (Unidad VIII): con el ataque largo, la pantalla se
  filtra por umbral y salen las huellas de pezuña que marcan el camino seguro.
* **Partículas verdes**: `spores` es el único efecto del motor que sale en
  verde —(150, 255, 130)— y es exactamente la «luz espectral verde» que el lore
  le pone al cementerio.

Sobre el reloj del mundo
-------------------------
El mapa arranca a las 19:00 con `day_length` 900, así que termina a las 23:00.
La luna **materializa** lo que ese reloj ya hace: no es un segundo sistema de
tiempo, es la misma hora dibujada de otra forma.
"""
from __future__ import annotations

import math
import random
from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.framework.scenes.stage_scene import StageScene
from src.framework.vfx.lighting import LightSource
from src.stages.stage4_1 import siluetas, trazado
from src.stages.stage4_1.actos import ACTOS, Acto, acto_en

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class Stage4_1(StageScene):
    """4-1 — La Entrada al Cementerio."""

    STAGE_ID: str = "stage4_1"
    STAGE_NAME: str = "4-1  LA ENTRADA AL CEMENTERIO"
    ZONE: int = 4
    # AUD-209: era `bgm_zone3`, la música del nivel anterior. El Asset Bible
    # (`docs/20_ASSET_BIBLE.md`) tiene una pista asignada a este nivel desde el
    # principio —«bgm_final_approach.wav | Stage 4-1 | Silence punctuated by
    # ritual drums»— y estaba en `assets/music/` sin que nada la reprodujera.
    BGM_TRACK: str = "bgm_final_approach"
    TMX_PATH = "assets/maps/stage4_1/stage4_1.tmx"

    # ── Braseros ──────────────────────────────────────────────
    #: A qué distancia se enciende un brasero al pasar. Generoso a propósito:
    #: el jugador no debe tener que rozarlo, sólo pasar cerca.
    DISTANCIA_DE_ENCENDIDO = 72.0
    #: Cuánto tarda en subir la llama. No es instantáneo porque el encendido es
    #: la única recompensa visual del nivel y merece medio segundo.
    SUBIDA_DE_LLAMA = 0.55

    # ── Relámpagos ────────────────────────────────────────────
    #: Cuánto dura el destello. 0,4 s es lo que pide el diseño (§5): suficiente
    #: para memorizar el tramo, corto para no volverse iluminación permanente.
    DURACION_DEL_RAYO = 0.4
    #: Cuánto sube la luz ambiente en el pico del destello.
    FUERZA_DEL_RAYO = 0.55

    # ── La oscuridad que susurra (AUD-211) ────────────────────
    #: Segundos quieto y a oscuras antes de que el cementerio conteste. Los ~4 s
    #: del §4 del diseño.
    ESPERA_DEL_SUSURRO = 4.0
    #: Cuánto brillan los ojos después. Lo justo para verlos si estás mirando.
    DURACION_DE_LOS_OJOS = 2.5
    #: A qué distancia deja de contar como oscuridad tener un brasero cerca.
    #: Es el radio grande de las luces del mapa: dentro de él, el sendero se ve.
    RADIO_DE_LA_LUZ = 150.0

    # ── Visión espectral ──────────────────────────────────────
    #: Segundos que dura la visión tras activarla. Los 3 s de la ficha.
    DURACION_DE_LA_VISION = 3.0
    #: Espera antes de poder volver a usarla. Sin esto, mantener el botón la
    #: dejaría encendida siempre y dejaría de ser una decisión.
    RECARGA_DE_LA_VISION = 1.2
    #: Umbral del filtro binario (Unidad VIII). 96 sobre 255 deja el suelo en
    #: negro y las marcas en blanco con la luz de este nivel.
    UMBRAL = 96

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path(self.TMX_PATH))
        #: Índice del acto actual, 0 a 4. Empieza fuera de rango para que el
        #: primer `update` **siempre** entre en el acto I y aplique su clima:
        #: con 0 aquí, el acto I nunca se aplicaría y el nivel arrancaría con
        #: lo que dijera el TMX. Es el fallo de «se inicializa a lo mismo que
        #: se compara» y aquí sería invisible.
        self._acto_actual: int = -1
        #: Braseros encendidos, por índice. Un conjunto y no una lista de
        #: booleanos porque la pregunta que se hace siempre es «¿está éste?».
        self._encendidos: set[int] = set()
        #: Brillo de cada llama, 0 a 1, para que suban en vez de aparecer.
        self._llama: dict[int, float] = {}
        #: Las luces del TMX, por índice de brasero. Se apagan al entrar y las
        #: enciende el jugador al pasar.
        self._luces: list[LightSource] = []
        self._rayo: float = 0.0
        self._proximo_rayo: float = 0.0
        self._vision: float = 0.0
        self._recarga: float = 0.0
        self._tiempo: float = 0.0
        #: Segundos que el jugador lleva quieto y a oscuras, y lo que queda de
        #: brillo en los ojos de la Cegua cuando el cementerio ya ha contestado.
        self._quieto: float = 0.0
        self._ojos: float = 0.0
        #: Las ocho superficies del degradado de las grietas. Se construyen la
        #: primera vez que se dibuja y no se vuelven a tocar.
        self._brillos: list[pygame.Surface] | None = None
        #: Lienzo de trabajo para componer una llama. Se reutiliza para las
        #: doce, así que no hay asignaciones por fotograma.
        self._lienzo_llama = pygame.Surface(self._LIENZO_LLAMA, pygame.SRCALPHA)
        #: Dónde estaba el jugador en el fotograma anterior. Es lo que decide si
        #: está quieto: preguntarle a la velocidad no vale, porque un jugador
        #: apoyado contra un muro tiene velocidad y no se mueve.
        self._donde_estaba: float = 0.0
        #: Marcas ocultas: las huellas de pezuña que deja la Cegua. Se colocan
        #: aquí y no en el TMX porque no son objetos del mundo —no colisionan,
        #: no se recogen— y meterlas en el mapa las convertiría en algo que el
        #: validador tendría que conocer.
        self._marcas: list[pygame.Rect] = []

    # ── Ciclo de vida ─────────────────────────────────────────

    def _setup_lighting(self) -> None:
        """Apaga los doce braseros. Los enciende el jugador al pasar.

        Se engancha aquí y **no** en `on_stage_start` — que es donde lo puse
        primero. Lo comprobé ejecutándolo: `on_stage_start()` corre en la línea
        476 de `on_enter` y `_setup_lighting()` en la 548, así que cuando el
        gancho del escenario se ejecuta la lista `_stage_lights` todavía está
        vacía y los braseros salían encendidos desde el primer fotograma. Es
        exactamente el fallo característico del proyecto —código correcto que
        corre en el momento equivocado— y sólo se ve corriéndolo.

        `_setup_lighting` es el método que **crea** esa lista, así que es el
        único sitio donde se la puede tocar con la garantía de que existe.
        """
        super()._setup_lighting()
        self._luces = list(self._stage_lights)
        self._intensidad_original = [luz.intensity for luz in self._luces]
        for luz in self._luces:
            luz.intensity = 0.0
        self._encendidos.clear()
        self._llama.clear()

    def on_stage_start(self) -> None:
        super().on_stage_start()
        self._colocar_marcas()

    def _colocar_marcas(self) -> None:
        """Huellas de pezuña sobre los tramos de salto.

        Van donde el diseño (§8) dice que sirven: marcando **dónde pisar** en
        los dos tramos de saltos. Con la visión espectral el tramo del acto IV
        se vuelve trivial, que es la recompensa de mirar.

        Las columnas salen de `trazado.py`, que es el mismo sitio del que las
        lee el generador del mapa. Escritas a mano aquí —como estaban— una
        grieta movida en el TMX dejaba la huella flotando sobre el vacío, y eso
        no rompe ninguna prueba: sólo miente al jugador (AUD-208).
        """
        self._marcas.clear()
        if self._stage_data is None:
            return
        ts = settings.TILE_SIZE
        for bx, by, ancho in trazado.marcas_de_pezuna():
            self._marcas.append(
                pygame.Rect(bx * ts, by * ts - 6, ancho * ts, 4),
            )

    # ── Actualización ─────────────────────────────────────────

    def update(self, dt: float) -> None:
        super().update(dt)
        if self._player is None or self._stage_data is None:
            return
        self._tiempo += dt
        self._actualizar_acto()
        self._actualizar_braseros(dt)
        self._actualizar_rayos(dt)
        self._actualizar_vision(dt)
        self._actualizar_oscuridad(dt)

    @property
    def acto(self) -> Acto:
        """El acto en el que está el jugador ahora mismo.

        Se mira la **fila**, no la columna: desde AUD-225 el nivel es un pozo y
        el avance es hacia abajo (ver `trazado.py`).
        """
        if self._player is None:
            return ACTOS[0]
        return acto_en(self._player.rect.centery / settings.TILE_SIZE)

    def _actualizar_acto(self) -> None:
        """Aplica el acto nuevo, si el jugador cambió de tramo.

        Sólo se aplica **al cambiar**: llamar a `set_climate` en cada fotograma
        vaciaría el emisor de la tormenta sesenta veces por segundo y no se
        vería llover.
        """
        acto = self.acto
        if acto.numero - 1 == self._acto_actual:
            return
        self._acto_actual = acto.numero - 1

        self._weather.set_climate(acto.clima)
        self._ambient_particles.set_effect(*acto.particulas)
        # El ambiente del acto pasa a ser la base sobre la que el ciclo
        # día/noche modula. Se escribe en `_ambiente_base` y no en el sistema
        # de luz: si se escribiera directo, `_aplicar_hora` lo pisaría en el
        # siguiente fotograma y el cambio de acto no se vería.
        self._ambiente_base = acto.ambiente
        self._aplicar_hora()
        self._proximo_rayo = self._espera_entre_rayos()
        if self._banner is not None and acto.numero > 1:
            self._banner.play(f"ACTO {acto.numero}", acto.nombre)

    def _actualizar_braseros(self, dt: float) -> None:
        """Enciende por proximidad y no apaga nunca."""
        if self._player is None:
            return
        centro = pygame.Vector2(self._player.rect.center)
        from src.framework.vfx.hit_effects import HitEffects

        for i, luz in enumerate(self._luces):
            if i not in self._encendidos:
                if centro.distance_to(luz.position) > self.DISTANCIA_DE_ENCENDIDO:
                    continue
                self._encendidos.add(i)
                self._llama[i] = 0.0
                # Ascuas al prender: es la única recompensa visual del nivel.
                self._particle_system.get_emitter("charge").emit(
                    luz.position.x, luz.position.y, HitEffects.CHARGE_GLOW,
                )
                # Y **no** se sale aquí: la llama empieza a subir en este mismo
                # fotograma. Con un `continue`, el brasero quedaba contado como
                # encendido y con intensidad cero durante un fotograma — el
                # contador decía «1» y la pantalla seguía a oscuras.
            avance = min(1.0, self._llama.get(i, 0.0) + dt / self.SUBIDA_DE_LLAMA)
            self._llama[i] = avance
            luz.intensity = self._intensidad_original[i] * avance

    @property
    def braseros_encendidos(self) -> int:
        """La barra de progreso del nivel, en braseros."""
        return len(self._encendidos)

    def _espera_entre_rayos(self) -> float:
        por_minuto = self.acto.rayos_por_minuto
        if por_minuto <= 0.0:
            return math.inf
        return random.uniform(0.5, 1.5) * (60.0 / por_minuto)

    def _actualizar_rayos(self, dt: float) -> None:
        """El relámpago: una linterna que enseña el tramo siguiente."""
        if self._rayo > 0.0:
            self._rayo = max(0.0, self._rayo - dt)
            # El pico se aplica encima del ambiente del acto, no lo sustituye.
            fuerza = (self._rayo / self.DURACION_DEL_RAYO) ** 2
            self._lighting.ambient_brightness = min(
                1.0, self.acto.ambiente + self.FUERZA_DEL_RAYO * fuerza)
            return
        if self.acto.rayos_por_minuto <= 0.0:
            return
        self._proximo_rayo -= dt
        if self._proximo_rayo <= 0.0:
            self._rayo = self.DURACION_DEL_RAYO
            self._proximo_rayo = self._espera_entre_rayos()
            # El trueno llega **después** del destello, como en la vida. El
            # retardo es el metrónomo de la tensión (§5 del diseño).
            self._play_sfx_named("sfx_environment_screen_shake", volume=0.5)

    # ── La oscuridad que susurra (Unidad V, y §4 del diseño) ──

    @property
    def a_oscuras(self) -> bool:
        """Si no hay ningún brasero encendido cerca del jugador.

        Se mide contra los braseros **encendidos**, no contra todos: el nivel
        entero está lleno de luces apagadas, y contarlas diría que hay luz donde
        no la hay.
        """
        if self._player is None:
            return False
        centro = pygame.Vector2(self._player.rect.center)
        return all(
            centro.distance_to(self._luces[i].position) > self.RADIO_DE_LA_LUZ
            for i in self._encendidos
        )

    def _actualizar_oscuridad(self, dt: float) -> None:
        """Quedarse quieto a oscuras: el cementerio contesta, y no hace daño.

        Es la «opción de tensión» del §4 del diseño, y su regla es explícita:
        *«No hay daño ni castigo: es recordatorio de seguir»*. Así que aquí no
        se toca la salud, ni la velocidad, ni los controles — sólo suena un
        susurro y brillan unos ojos en el fondo.

        El sonido es `sfx_environment_cemetery_silence`, que el Asset Bible ya
        tenía asignado a esta zona («Zone Final ambient») y que hasta ahora no
        reproducía nadie.
        """
        if self._player is None:
            return
        if self._ojos > 0.0:
            self._ojos = max(0.0, self._ojos - dt)

        ahora = float(self._player.rect.centerx)
        se_movio = abs(ahora - self._donde_estaba) > 1.0
        self._donde_estaba = ahora

        if se_movio or not self.a_oscuras:
            self._quieto = 0.0
            return

        self._quieto += dt
        if self._quieto < self.ESPERA_DEL_SUSURRO:
            return
        # Y se reinicia la cuenta: si se sigue quieto, el susurro vuelve, pero
        # espaciado. Sin esto sonaría sesenta veces por segundo.
        self._quieto = 0.0
        self._ojos = self.DURACION_DE_LOS_OJOS
        self._play_sfx_named("sfx_environment_cemetery_silence", volume=0.35)

    # ── Visión espectral (Unidad VIII) ────────────────────────

    def _actualizar_vision(self, dt: float) -> None:
        if self._vision > 0.0:
            self._vision = max(0.0, self._vision - dt)
            return
        if self._recarga > 0.0:
            self._recarga = max(0.0, self._recarga - dt)
            return
        im = self.input
        if im is not None and im.is_action_just_pressed(Action.LONG_ATTACK):
            self._vision = self.DURACION_DE_LA_VISION
            self._recarga = self.RECARGA_DE_LA_VISION

    @property
    def vision_activa(self) -> bool:
        return self._vision > 0.0

    # ── Dibujo ────────────────────────────────────────────────

    def dibujar_fondo(self, surface: pygame.Surface,
                      offset: pygame.Vector2) -> None:
        """La luna y las siluetas, detrás del mapa (AUD-162).

        Aquí y no en `draw()` porque el canon las pone **en el fondo**: pintadas
        después del mapa taparían al jugador y dejarían de ser recuerdos para
        pasar a ser primer plano.
        """
        acto = self.acto
        self._dibujar_luna(surface, acto)
        self._dibujar_espiritus(surface, acto, offset)
        self._dibujar_brujas(surface, acto, offset)
        self._dibujar_cegua(surface, acto, offset)
        self._dibujar_ojos(surface)
        # Las grietas van aquí, con el fondo, y no en `draw()` — que es donde
        # las puse primero. Dos motivos, los dos vistos en una captura:
        #
        # * `draw()` corre **después** de la interfaz, así que el brillo se
        #   pintaba encima del marcador y del minimapa.
        # * Aquí las apaga el sistema de luz igual que a todo lo demás. Sueltas
        #   por encima quedaban de neón: eran lo más brillante de la pantalla,
        #   por delante de los braseros, que son los que deben mandar.
        #
        # No se pierde nada por quedar detrás del mapa: la grieta ocupa la fila
        # de la repisa y las dos de aire que hay debajo, así que lo que se ve es
        # el resplandor saliendo por debajo del labio, que es lo que se buscaba.
        self._dibujar_grietas(surface)
        # Las antorchas, lo último del fondo. Siguen estando **detrás** del mapa
        # de baldosas —todo esto lo está—, y no importa: el cuenco y la llama
        # caen en el aire abierto que hay sobre cada repisa, así que no hay nada
        # que las tape. Ponerlas en `draw()` para tenerlas delante las pintaría
        # también encima del HUD, que es el error que ya costó una captura con
        # las grietas.
        self._dibujar_antorchas(surface, offset)
        self._dibujar_fantasmas(surface, offset)

    def _dibujar_luna(self, surface: pygame.Surface, acto: Acto) -> None:
        """El reloj del nivel: baja y crece con el avance.

        No hace falta que se mueva en cada píxel — el diseño (§2) pide que en
        los cinco puntos de acto esté donde la tabla dice. Se interpola dentro
        del tramo para que el cambio se vea y no se salte.
        """
        siguiente = ACTOS[min(acto.numero, len(ACTOS) - 1)]
        t = self._avance_dentro_del_acto(acto, siguiente)
        y = acto.luna_y + (siguiente.luna_y - acto.luna_y) * t
        radio = acto.luna_radio + (siguiente.luna_radio - acto.luna_radio) * t
        x = settings.INTERNAL_WIDTH * 0.78

        halo = pygame.Surface((int(radio * 4), int(radio * 4)), pygame.SRCALPHA)
        centro = (int(radio * 2), int(radio * 2))
        pygame.draw.circle(halo, (150, 190, 170, 26), centro, int(radio * 1.9))
        pygame.draw.circle(halo, (196, 228, 210, 60), centro, int(radio * 1.3))
        pygame.draw.circle(halo, (232, 244, 236, 220), centro, int(radio))
        surface.blit(halo, (int(x - radio * 2), int(y - radio * 2)))

    def _avance_dentro_del_acto(self, acto: Acto, siguiente: Acto) -> float:
        """0 al entrar en el acto, 1 al salir. Para interpolar la luna."""
        if self._player is None or siguiente is acto:
            return 0.0
        alto = max(1, siguiente.desde_fila - acto.desde_fila)
        recorrido = (self._player.rect.centery / settings.TILE_SIZE
                     - acto.desde_fila)
        return max(0.0, min(1.0, recorrido / alto))

    #: Dónde se planta cada espíritu, en fracción del ancho de pantalla. Están
    #: repartidos para que no se pisen y no se lean como una fila.
    _SITIOS_ESPIRITU: tuple[float, ...] = (0.16, 0.44, 0.66)

    def _dibujar_espiritus(self, surface: pygame.Surface, acto: Acto,
                           offset: pygame.Vector2) -> None:
        """Venado, serpiente y gavilán: los tres vencidos, testificando."""
        for i in range(min(acto.espiritus, len(siluetas.ESPIRITUS))):
            _nombre, forma = siluetas.ESPIRITUS[i]
            # Se mecen muy despacio: quietas del todo se leen como decorado
            # pintado, y el canon las llama ecos.
            vaiven = math.sin(self._tiempo * 0.35 + i * 2.1) * 6.0
            # Parallax lento: están lejos, así que se mueven poco con la cámara.
            x = int(settings.INTERNAL_WIDTH * self._SITIOS_ESPIRITU[i]
                    - offset.x * 0.12) % (settings.INTERNAL_WIDTH + 260) - 130
            alto = 96 + i * 12
            alfa = 42 + int(26 * self._visibilidad_de_fondo())
            siluetas.dibujar_contorno(
                surface, forma, x, int(210 + vaiven), int(alto * 0.9), alto,
                siluetas.VERDE_ESPECTRAL, alfa,
            )

    # ── Las brujas (AUD-210) ──────────────────────────────────
    #
    #: A qué altura de la pantalla vuela cada una. Están a alturas distintas a
    #: propósito: en fila se leerían como una bandada de pájaros.
    _ALTURAS_BRUJA: tuple[int, ...] = (96, 148, 62)
    #: Píxeles por segundo de cada una. Distintas también, y ninguna redonda:
    #: con la misma velocidad cruzan en formación y parecen un solo objeto.
    _VELOCIDADES_BRUJA: tuple[float, ...] = (54.0, 37.0, 71.0)

    def _dibujar_brujas(self, surface: pygame.Surface, acto: Acto,
                        offset: pygame.Vector2) -> None:
        """Las brujas cruzando el fondo del acto IV (§4 del diseño).

        Se ven, como la Cegua, sobre todo con el relámpago. La diferencia es que
        éstas **se mueven**: cruzan de un lado a otro y vuelven a entrar por el
        otro extremo. En el umbral se quedan posadas y quietas, que es lo que el
        diseño pide para el acto V.

        Igual que las siluetas, no son entidades: ni colisión, ni IA, ni salud.
        La regla de oro del nivel sigue siendo cero enemigos.
        """
        cuantas = min(acto.brujas, len(self._ALTURAS_BRUJA))
        if cuantas <= 0:
            return
        margen = 140
        recorrido = settings.INTERNAL_WIDTH + margen * 2
        for i in range(cuantas):
            if acto.brujas_quietas:
                # Posadas: repartidas por el ancho y sin avanzar. El parallax
                # sigue actuando —están en el mundo, no pegadas a la cámara—.
                x = int(settings.INTERNAL_WIDTH * (0.22 + 0.26 * i)
                        - offset.x * 0.1)
            else:
                avance = self._tiempo * self._VELOCIDADES_BRUJA[i]
                x = int((avance + i * 260 - offset.x * 0.1) % recorrido) - margen
            alto = 34 + i * 5
            # Sin relámpago son casi invisibles: el destello es lo que las
            # revela, igual que a la Cegua.
            alfa = 18 + int(120 * self._visibilidad_de_fondo())
            siluetas.dibujar_contorno(
                surface, siluetas._bruja, x, self._ALTURAS_BRUJA[i],
                int(alto * 1.9), alto, siluetas.BLANCO_CEGUA, alfa,
            )

    def _dibujar_cegua(self, surface: pygame.Surface, acto: Acto,
                       offset: pygame.Vector2) -> None:
        """La Cegua: presencia, nunca enemigo.

        Se acerca por acto y **se ve sobre todo con el relámpago**: el jugador
        elige mirar el rayo para verla, o no mirarlo para no verla. Esa
        elección es la tensión del nivel (§4 del diseño).
        """
        if acto.cegua <= 0.0:
            return
        cercania = acto.cegua
        alto = int(70 + 110 * cercania)
        x = int(settings.INTERNAL_WIDTH * (0.86 - 0.22 * cercania)
                - offset.x * 0.06)
        y = int(250 - 40 * cercania)
        base = 26 + int(40 * cercania)
        alfa = base + int(150 * self._visibilidad_de_fondo())
        siluetas.dibujar_contorno(
            surface, siluetas._cegua, x, y, int(alto * 0.8), alto,
            siluetas.BLANCO_CEGUA, min(255, alfa), grosor=2,
        )

    def _dibujar_ojos(self, surface: pygame.Surface) -> None:
        """Los ojos de la Cegua, cuando el cementerio contesta (AUD-211).

        Dos puntos verdes en el fondo, y nada más. La regla del §4 es que *«el
        miedo nunca cobra vida»*: no se acercan, no persiguen y no hacen daño —
        se encienden, se apagan, y el jugador decide si eso le da motivos para
        seguir andando.
        """
        if self._ojos <= 0.0:
            return
        # Se desvanecen por los dos extremos: aparecer y desaparecer de golpe
        # se lee como un fallo de dibujo, no como una presencia.
        t = self._ojos / self.DURACION_DE_LOS_OJOS
        alfa = int(210 * math.sin(t * math.pi) ** 0.6)
        if alfa <= 0:
            return
        x = int(settings.INTERNAL_WIDTH * 0.5)
        y = int(settings.INTERNAL_HEIGHT * 0.42)
        lienzo = pygame.Surface((40, 12), pygame.SRCALPHA)
        for dx in (7, 29):
            pygame.draw.circle(lienzo, (*siluetas.VERDE_ESPECTRAL, alfa),
                               (dx, 6), 3)
            pygame.draw.circle(lienzo, (*siluetas.VERDE_ESPECTRAL, alfa // 4),
                               (dx, 6), 7)
        surface.blit(lienzo, (x - 20, y - 6))

    def _visibilidad_de_fondo(self) -> float:
        """0 sin relámpago, 1 en el pico del destello."""
        if self._rayo <= 0.0:
            return 0.0
        return (self._rayo / self.DURACION_DEL_RAYO) ** 0.5

    # ── Las losas fantasma (AUD-247) ──────────────────────────
    #: Color de la losa cuando algo la revela. El mismo gris de la piedra, con
    #: el canto en verde espectral: se lee «esto es suelo» y «esto no es
    #: normal» a la vez.
    _COLOR_FANTASMA = (96, 96, 110)

    def _dibujar_fantasmas(self, surface: pygame.Surface,
                           offset: pygame.Vector2) -> None:
        """Las losas del acto IV: sólidas siempre, visibles casi nunca.

        Es el §5 del diseño llevado a su conclusión — *«el relámpago revela los
        peligros del tramo siguiente; el jugador memoriza el tramo con cada
        rayo»*—. Aquí lo que revela no es un peligro sino **el suelo**, y por eso
        funciona sin castigar a nadie: un pincho invisible es una trampa, un
        suelo invisible es una pregunta. ¿Te fías de lo que viste hace tres
        segundos?

        Se revelan con el rayo y con la visión espectral, las dos linternas que
        el nivel ya tenía. La visión las deja más nítidas que el rayo porque es
        la que cuesta usar: mirar tiene premio.
        """
        revelado = max(
            self._rayo / self.DURACION_DEL_RAYO if self._rayo > 0.0 else 0.0,
            1.0 if self.vision_activa else 0.0,
        )
        if revelado <= 0.0:
            return
        ts = settings.TILE_SIZE
        pantalla = surface.get_rect()
        alfa = int(230 * revelado)
        for indice in trazado.INDICES_FANTASMA:
            cx, fila = trazado.losa_extra(indice)
            r = pygame.Rect(cx * ts - int(offset.x), fila * ts - int(offset.y),
                            trazado.ANCHO_LOSA_EXTRA * ts, ts)
            if not pantalla.colliderect(r):
                continue
            losa = pygame.Surface(r.size, pygame.SRCALPHA)
            losa.fill((*self._COLOR_FANTASMA, alfa))
            pygame.draw.line(losa, (*siluetas.VERDE_ESPECTRAL, alfa),
                             (0, 0), (r.width - 1, 0))
            surface.blit(losa, r.topleft)

    # ── Las antorchas, que ahora se ven (AUD-246) ─────────────
    #
    #: Los doce braseros eran **sólo focos de luz**: `Light` en el TMX y nada
    #: dibujado. Se veía el charco de luz aparecer sobre la repisa sin nada que
    #: lo produjera, y el §3 del diseño se apoya entero en ellos —«si un jugador
    #: pregunta cuánto falta, la respuesta es cuenta los apagados»—. Un contador
    #: que no se ve no cuenta nada.
    #:
    #: Se dibujan aquí y no como sprite del TMX porque la llama tiene que
    #: **crecer** con `self._llama[i]`, que es el mismo número que sube la
    #: intensidad de la luz: así el fuego y su resplandor son la misma cosa y no
    #: pueden desincronizarse.
    _COLOR_CUENCO = (74, 70, 82)
    _COLOR_CUENCO_LUZ = (104, 100, 114)
    #: Tamaño del lienzo donde se compone cada llama. Da de sobra para la más
    #: alta (15 px) con su holgura.
    _LIENZO_LLAMA = (28, 34)
    #: De fuera hacia dentro. El verde espectral del canon, no naranja: en este
    #: cementerio arde otra cosa.
    _CAPAS_DE_LLAMA: tuple[tuple[tuple[int, int, int], float, float], ...] = (
        ((40, 130, 70), 1.00, 0.55),      # el halo exterior
        ((90, 210, 120), 0.66, 0.80),     # el cuerpo
        ((190, 255, 205), 0.30, 1.00),    # el corazón
    )

    def _dibujar_antorchas(self, surface: pygame.Surface,
                           offset: pygame.Vector2) -> None:
        """El cuenco siempre; la llama sólo si está encendida, y creciendo.

        Un brasero apagado se dibuja igual —piedra fría y vacía— porque ésa es
        la mitad del mensaje: el jugador tiene que **ver cuántos le faltan**.
        """
        ts = settings.TILE_SIZE
        pantalla = surface.get_rect()
        # Se dibuja sobre las coordenadas del **trazado**, no sobre las del foco.
        # El `Light` del TMX se centra en su rectángulo, así que su posición cae
        # dos filas por encima de la repisa: dibujar ahí dejaba la antorcha
        # flotando en el aire, y una llama sin nada debajo no se lee como una
        # antorcha. La correspondencia entre las dos listas la fija una prueba.
        for i, (bx, fila) in enumerate(trazado.braseros()):
            px = int(bx * ts + ts // 2 - offset.x)
            suelo = int(fila * ts - offset.y)          # el canto de la repisa
            if not pantalla.collidepoint(px, suelo):
                continue

            # El cuenco: piedra apoyada en la repisa, con el borde iluminado.
            cuenco = pygame.Rect(px - 8, suelo - 7, 16, 7)
            pygame.draw.rect(surface, self._COLOR_CUENCO, cuenco)
            pygame.draw.line(surface, self._COLOR_CUENCO_LUZ,
                             cuenco.topleft, cuenco.topright)
            pygame.draw.rect(surface, self._COLOR_CUENCO,
                             (px - 3, suelo - 10, 6, 3))   # el pie
            py = suelo - 9                                  # boca del cuenco

            avance = self._llama.get(i, 0.0)
            if avance <= 0.0:
                continue

            # El parpadeo: cada antorcha con su fase, o las doce respirarían a
            # la vez y se leerían como una sola luz encendida por un interruptor.
            latido = 0.86 + 0.14 * math.sin(self._tiempo * 7.3 + i * 1.9)
            alto = 22.0 * avance * latido
            ancho = 8.0 * avance

            # Las tres capas van a un lienzo pequeño y **reutilizado**, y de ahí
            # a la pantalla de un solo pegado. La primera versión creaba una
            # superficie del tamaño de la pantalla por capa y por antorcha: 24
            # asignaciones de 800×600 por fotograma, que es exactamente el
            # derroche que AUD-023 vino a quitar del motor.
            lienzo = self._lienzo_llama
            lienzo.fill((0, 0, 0, 0))
            cx, base = self._LIENZO_LLAMA[0] // 2, self._LIENZO_LLAMA[1] - 4
            for color, escala, opacidad in self._CAPAS_DE_LLAMA:
                a, h = ancho * escala, alto * escala
                if h < 1.0:
                    continue
                # Una gota: ancha abajo, en punta arriba.
                pygame.draw.polygon(lienzo, (*color, int(255 * opacidad)), [
                    (cx, base - h),
                    (cx + a, base - h * 0.42),
                    (cx + a * 0.72, base + 1),
                    (cx - a * 0.72, base + 1),
                    (cx - a, base - h * 0.42),
                ])
            surface.blit(lienzo, (px - cx, py + 2 - base))

    # ── Las grietas verdes (AUD-225) ──────────────────────────

    def _dibujar_grietas(self, surface: pygame.Surface) -> None:
        """Luz verde en el canto de cada repisa. **No hacen daño.**

        Esto es lo que sustituyó a las `HazardZone` del nivel viejo, y el porqué
        importa: el motor sólo pinta las zonas de daño que **suben** —la
        inundación de AUD-135—. Una zona fija espera a que el diseñador dibuje
        pinchos en las baldosas, y aquí no había ninguno pintado: el jugador
        recibía daño desde un rectángulo invisible. Se quitaron todas.

        Lo que queda es información, no amenaza: el borde por el que hay que
        dejarse caer, marcado con la luz del cementerio. Respira despacio para
        que se lea como algo vivo y no como una línea de la interfaz.
        """
        if self._stage_data is None:
            return
        ts = settings.TILE_SIZE
        offset = self._camera.offset
        pantalla = surface.get_rect()
        # El pulso es común a todas: si cada una llevara su fase, el pozo
        # parpadearía como un árbol de navidad en vez de respirar.
        pulso = 0.5 + 0.5 * math.sin(self._tiempo * 1.6)
        paso = self._brillos_de_grieta()[
            min(len(self._PASOS_DEL_PULSO) - 1, int(pulso * len(self._PASOS_DEL_PULSO)))
        ]
        for bx, fila, alto in trazado.grietas():
            r = pygame.Rect(bx * ts - int(offset.x), fila * ts - int(offset.y),
                            ts, alto * ts)
            if not pantalla.colliderect(r):
                continue
            surface.blit(paso, r.topleft, special_flags=pygame.BLEND_RGBA_ADD)

    #: Los escalones del pulso. Ocho bastan para que respire: el ojo no
    #: distingue más, y cada uno es una superficie que se construye una vez.
    _PASOS_DEL_PULSO: tuple[float, ...] = tuple(i / 7.0 for i in range(8))

    def _brillos_de_grieta(self) -> list[pygame.Surface]:
        """Las ocho superficies del degradado, construidas una sola vez.

        Medido antes de cachear: 0,56 ms por fotograma de los 5,9 que cuesta
        dibujar el nivel, sólo por rehacer 44 degradados que siempre son
        iguales. Es el mismo derroche que AUD-023 quitó del resto del motor —
        una asignación por fotograma para pintar un rectángulo con alfa— y aquí
        además compite con la visión espectral, que es la mecánica del nivel.
        """
        if self._brillos is not None:
            return self._brillos
        ts = settings.TILE_SIZE
        ancho, alto = ts, 3 * ts
        self._brillos = []
        for t in self._PASOS_DEL_PULSO:
            alfa = 70 + 90 * t
            brillo = pygame.Surface((ancho, alto), pygame.SRCALPHA)
            # Un degradado hacia abajo: la grieta nace en el canto y se apaga
            # con la profundidad, que es como se lee una fisura y no una barra.
            for i in range(alto):
                caida = 1.0 - i / max(1, alto - 1)
                pygame.draw.line(
                    brillo, (*siluetas.VERDE_ESPECTRAL, int(alfa * caida)),
                    (0, i), (ancho - 1, i),
                )
            self._brillos.append(brillo)
        return self._brillos

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        if self.vision_activa:
            self._dibujar_vision(surface)

    def _dibujar_vision(self, surface: pygame.Surface) -> None:
        """El filtro por umbral y las huellas que revela (Unidad VIII).

        El umbral se aplica a **una copia reducida** y se devuelve escalada.
        Medido en esta máquina, sobre el dibujo base de 5,65 ms:

            a 1/2 de resolución   +4,64 ms   → 10,3 ms, fuera de presupuesto
            a 1/3                 +2,05 ms
            a 1/4                 +1,60 ms   → 7,3 ms

        Se usa 1/4. No es sólo que quepa: un umbral grueso se lee **mejor** como
        visión fantasmal que uno fino, así que aquí lo barato y lo bonito
        coinciden. Y es procesamiento de imagen de verdad —Unidad VIII— no un
        tinte verde que lo imite.
        """
        from src.framework.processing.vision_tools import VisionTools

        ancho, alto = surface.get_size()
        reducida = pygame.transform.smoothscale(surface, (ancho // 4, alto // 4))
        try:
            binaria = VisionTools.threshold_binary(reducida, self.UMBRAL)
        except Exception:
            # Sin OpenCV no hay visión, pero el nivel se sigue jugando: es una
            # ayuda, no el camino.
            return
        espectral = pygame.transform.scale(binaria, (ancho, alto))
        # Se desvanece al final para que la vuelta a la vista normal no corte.
        restante = min(1.0, self._vision / 0.6)
        # El blanco del umbral se tiñe de verde y se **suma**: sumar deja el
        # negro en negro —no oscurece nada— y convierte lo revelado en luz.
        # Con `BLEND_RGB_MULT` sobre la pantalla, que fue lo primero que probé,
        # el resultado era más oscuro que sin visión: medido, el verde medio
        # bajaba de 26 a 11. Una «visión» que quita luz no es una visión.
        tinte = tuple(int(c * 0.55 * restante) for c in siluetas.VERDE_ESPECTRAL)
        espectral.fill(tinte, special_flags=pygame.BLEND_RGB_MULT)
        surface.blit(espectral, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        # Y ahora sí: las huellas, que sólo existen con la visión puesta.
        offset = self._camera.offset
        for marca in self._marcas:
            pygame.draw.rect(
                surface, siluetas.VERDE_ESPECTRAL,
                pygame.Rect(marca.x - int(offset.x), marca.y - int(offset.y),
                            marca.width, marca.height),
            )
