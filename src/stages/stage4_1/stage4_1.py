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
from src.stages.stage4_1 import siluetas
from src.stages.stage4_1.actos import ACTOS, Acto, acto_en

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class Stage4_1(StageScene):
    """4-1 — La Entrada al Cementerio."""

    STAGE_ID: str = "stage4_1"
    STAGE_NAME: str = "4-1  LA ENTRADA AL CEMENTERIO"
    ZONE: int = 4
    BGM_TRACK: str = "bgm_zone3"
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
        """
        self._marcas.clear()
        if self._stage_data is None:
            return
        ts = settings.TILE_SIZE
        suelo = 30 * ts
        # Acto III: el borde seguro antes de cada grieta.
        for bx in (43, 49, 55):
            self._marcas.append(pygame.Rect(bx * ts, suelo - 6, ts, 4))
        # Acto IV: encima de cada losa que cede.
        for bx in (64, 69, 74, 79):
            self._marcas.append(pygame.Rect(bx * ts + 8, suelo - 2 * ts - 8,
                                            2 * ts, 4))

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

    @property
    def acto(self) -> Acto:
        """El acto en el que está el jugador ahora mismo."""
        if self._player is None:
            return ACTOS[0]
        return acto_en(self._player.rect.centerx / settings.TILE_SIZE)

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
        self._dibujar_cegua(surface, acto, offset)

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
        ancho = max(1, siguiente.desde_baldosa - acto.desde_baldosa)
        recorrido = (self._player.rect.centerx / settings.TILE_SIZE
                     - acto.desde_baldosa)
        return max(0.0, min(1.0, recorrido / ancho))

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

    def _visibilidad_de_fondo(self) -> float:
        """0 sin relámpago, 1 en el pico del destello."""
        if self._rayo <= 0.0:
            return 0.0
        return (self._rayo / self.DURACION_DEL_RAYO) ** 0.5

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
