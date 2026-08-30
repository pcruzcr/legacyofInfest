# Autor: Alejandro Josué Rodríguez Zamora
# Stage 4-2 «El Gran Shamán Paburu» — Legacy of InFest
"""
Module: moradores
System: src.stages.boss_paburu
Academic Unit: II (vectores), VI (interpolación)

LOS MORADORES DEL CAMPOSANTO

Las cuatro criaturas que viven en el cementerio de Paburu. No son "enemigos
de relleno": cada una existe para hacerle al jugador una pregunta distinta, y
si dos hicieran la misma sobraría una.

    Murcielago      · ¿estás mirando hacia arriba?
    MascaraTilawa   · ¿tenés espacio para esquivar?
    SukiaDeCeniza   · ¿te vas a quedar en el suelo?
    AhogadoDelPozo  · ¿de verdad querías meterte al agua?

SOBRE LA MÁSCARA TILAWA
En el juego son «tilawa» (cultura ficticia; regla dura del lore: jamás
nombrar culturas reales en el juego). La INVESTIGACION detrás — citada en
DISENO_NIVEL_Y_JEFE.md §referencias — es la danza real donde los
indígenas se enfrentan al toro español y ganan. Ponerlas acá como "monstruos"
sería justamente al revés de lo que significan, así que en este cementerio no
son monstruos: son **guardianes**. Están cuidando el camposanto de alguien que
entró sin permiso, y el que entró sin permiso es el jugador. Embisten porque
están echando a un intruso, no porque estén infectadas.

Es la misma lectura que el GDD le da a Paburu, que no es un villano sino un
shamán haciendo su trabajo. El jugador es el que llegó a molestar.

POR QUÉ SE REGISTRAN ACÁ Y NO EN EL BESTIARIO DEL MOTOR
`bestiary_registry.py` es del profesor y sus 21 especies cubren las zonas 1 a
3. La zona 4 es nuestra. Registrar desde este módulo —al importarlo, igual que
`BossPaburu`— deja el stage entero autocontenido: si mañana alguien borra la
carpeta `boss_paburu/`, no queda basura en el motor.

Se registra a nivel de MÓDULO y no dentro de un método, por AUD-151: el
validador, el calificador y el previsualizador abren el mapa sin construir la
escena, y si el tipo se registrara en `__init__` esas cuatro herramientas
verían «tipo desconocido» en un nivel que está bien.
"""
from __future__ import annotations

from typing import Any

import pygame

from src.framework.entities.enemy_charger import EnemyCharger
from src.framework.entities.enemy_flying import EnemyFlying
from src.framework.entities.enemy_shooter import EnemyShooter
from src.framework.stage.stage_loader import StageLoader

#: Zona 4. Lo leen el bestiario y la curva de dificultad del profesor.
ZONA = 4

# ── Qué tan pronto reaccionan ──────────────────────────────────
# El motor detecta al jugador en un rectángulo alrededor del enemigo
# (`detection_range_x/y`). Los valores por defecto son estrechos —48 px de
# alto en el `Charger`, 64 en el `Shooter`— y en un cementerio con
# plataformas a tres alturas eso significa que el jugador pasa por encima de
# medio nivel sin que nada se entere. Al jugarlo se notaba como enemigos
# decorativos: estaban ahí y no hacían nada.
#
# Se ensanchan sobre todo en VERTICAL, que es donde estaba el problema: el
# alto pasa de 48-96 a 128-160, así que un bicho del suelo levanta la cabeza
# cuando el jugador salta a la one-way de encima. En horizontal se sube menos
# —de 180-200 a 240-260—, lo justo para que reaccione antes de tenerlo encima
# y el aviso de la embestida sirva de algo.
#
# Ensancharlo más sería peor: con 400 px de alcance el nivel entero se
# despierta a la vez y el jugador pelea con seis cosas en cada tramo.



class AhogadoDelPozo(EnemyFlying):
    """Lo que vive en el fondo del pozo. No muerde: **tira**.

    El daño por contacto es bajísimo a propósito. El peligro no es que pegue,
    es que el jugador se quede abajo: mientras el ahogado lo tenga agarrado no
    sube, y bajo el agua el impulso de nado está limitado a uno por pulsación.
    Un enemigo que hace poco daño pero te impide salir da más miedo que uno
    que hace mucho y se puede esquivar.

    Se hereda de `EnemyFlying` porque volar y nadar son el mismo problema:
    moverse en dos ejes sin suelo. Lo único que agrega esta clase es el tirón.
    """

    #: Píxeles por segundo de arrastre hacia el ahogado, a quemarropa.
    FUERZA_DE_ARRASTRE = 45.0

    #: A partir de esta distancia ya no tira. Es corto: el pozo mide 384 px de
    #: ancho, así que dos ahogados no pueden cubrirlo entero y siempre hay una
    #: línea por donde pasar. Un tirón que alcanza todo el pozo no es un
    #: enemigo, es un impuesto.
    ALCANCE = 72.0

    def __init__(self, spawn_position: pygame.Vector2, **kwargs: Any) -> None:
        kwargs.setdefault("flight_mode", "sine")
        kwargs.setdefault("flight_speed", 34.0)     # lento: es agua
        # 22 → 14 (ronda 2: «el del agua se sale del agua»). Con el sprite
        # ×2 el cuerpo mide 20 px: amplitud 22 desde y=600 lo asomaba por
        # encima de la superficie (560). Con 14, el punto más alto del arte
        # queda ~576: siempre bajo el agua, que es donde vive un ahogado.
        kwargs.setdefault("sine_amplitude", 14.0)
        kwargs.setdefault("sine_frequency", 0.5)
        kwargs.setdefault("max_health", 2.0)
        kwargs.setdefault("damage_on_contact", 0.25)
        kwargs.setdefault("zone", ZONA)
        super().__init__(spawn_position, **kwargs)

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        """Hoja propia. Sin esto era idéntico al murciélago.

        `EnemyFlying` carga `enemy_fly_zone4.png` para toda la zona, y el
        ahogado hereda de él porque nadar y volar son el mismo problema de
        movimiento. El precio era visual: lo del fondo del pozo y lo que
        volaba por encima se dibujaban igual, y al jugar no había manera de
        saber cuál era cuál — «en el agua hay 2 pero ese es solo 1, y encima
        del agua hay uno, ¿ese qué es?».
        """
        super()._load_extra_sprites(zone, fw, fh)
        from src.engine.core import settings
        from src.engine.utils.asset_loader import AssetLoader
        ruta = (settings.ASSETS_DIR / "sprites" / "enemies" / "zone4"
                / "enemy_ahogado_zone4.png")
        try:
            marcos = AssetLoader.load_sprite_sheet(ruta, fw, fh)
            self._sprite_frames["fly"] = marcos
            self._sprite_frames["walk"] = marcos
        except (pygame.error, FileNotFoundError, PermissionError):
            pass

    def tirar_de(self, jugador: Any, dt: float) -> bool:
        """Arrastra al jugador hacia el fondo. La escena la llama por frame.

        Devuelve True si alcanzó a tirar, para que la escena pueda pintar el
        aviso: un tirón invisible se lee como un bug de física.

        El arrastre decae con la distancia en vez de ser todo-o-nada. Con un
        umbral duro, cruzar el borde del alcance se siente como pegar contra
        una pared invisible; con la caída suave el jugador nota que "algo lo
        está jalando" y puede pelearlo nadando en contra.
        """
        if not self.is_alive or jugador is None:
            return False
        delta = pygame.Vector2(self.rect.center) - pygame.Vector2(
            jugador.hurtbox.center)
        distancia = delta.length()
        if distancia < 1.0 or distancia > self.ALCANCE:
            return False
        # Interpolación lineal 1 → 0 sobre el alcance (Unidad VI).
        peso = 1.0 - distancia / self.ALCANCE
        tiron = delta.normalize() * self.FUERZA_DE_ARRASTRE * peso * dt
        jugador.velocity += tiron
        return True

    # ── AUD-468: un ahogado no sale del agua ────────────────────
    #: El rect del pozo, que le inyecta la escena. `None` = sin confinar
    #: (un arnés que lo instancie suelto se comporta como antes).
    pozo: pygame.Rect | None = None

    #: Cuánto queda SIEMPRE bajo la línea de flotación. El arte mide 20 px
    #: de alto tras el ×2, así que seis píxeles de cabeza dentro del agua
    #: es lo mínimo para que no se lea como que asoma.
    CALADO_MINIMO = 6

    def update(self, dt: float) -> None:
        """Se mueve como cualquier volador, y después vuelve a su pozo.

        AUD-468 — reportado dos veces: «el del agua se sale del agua» y «lo
        sigue fuera del agua, no puede seguirlo fuera del agua». La primera
        vez se corrigió la AMPLITUD del vaivén (22→14), que era la mitad del
        problema: el vaivén ya no lo asomaba **patrullando**. Pero en ALERTA
        `EnemyFlying` hace otra cosa —`_alert_behavior` lo lleva hacia el
        jugador y encima le sigue la Y con `_y_track_offset`—, así que en
        cuanto el jugador salía del pozo, el ahogado salía detrás. Un ahogado
        paseando por el camposanto no es un ahogado; y además rompe la
        promesa del pozo: el agua es la ruta lenta, pero salir de ella tiene
        que servir de algo.

        No se toca el motor ni se le quita la alerta: perseguir DENTRO del
        agua está bien y es lo que lo hace temible. Lo que se hace es lo que
        haría el agua — sujetarlo. Después de que el motor lo mueva, su caja
        vuelve dentro del pozo; si el jugador se fue, el ahogado se queda
        mirando desde abajo, que es la imagen correcta.
        """
        super().update(dt)
        self._confinar_al_pozo()

    def _confinar_al_pozo(self) -> None:
        agua = self.pozo
        if agua is None:
            return
        r = self.rect
        # Vertical primero: el techo del agua manda sobre todo lo demás.
        techo = agua.top + self.CALADO_MINIMO
        if r.top < techo:
            r.top = techo
        if r.bottom > agua.bottom:
            r.bottom = agua.bottom
        # Y los muros del pozo, para que no lo cruce por los lados.
        if r.left < agua.left:
            r.left = agua.left
        if r.right > agua.right:
            r.right = agua.right
        # `position` es la fuente de verdad del movimiento: corregir sólo el
        # rect dejaría que el fotograma siguiente lo sacara otra vez.
        self.position.update(float(r.x), float(r.y))
        # El vaivén senoidal parte de una base propia dentro de la estrategia
        # del motor: si quedó fuera del agua, se reancla al centro del pozo
        # para que el bamboleo no vuelva a empujarlo hacia la superficie.
        for nombre in ("_sine_origin_y", "_origen_y", "_base_y", "_origin_y"):
            base = getattr(self._strategy, nombre, None)
            if isinstance(base, (int, float)) and not (
                    agua.top <= base <= agua.bottom):
                setattr(self._strategy, nombre, float(agua.centery))


def _agrandar_frames(enemigo: Any, factor: int = 2) -> None:
    """Escala ×`factor` los frames YA recortados de un enemigo (playtest:
    «los murciélagos ni se ven» / «las mascaritas ni se ven»).

    Va aquí y no en las hojas PNG por una trampa del motor: cada clase
    recorta su hoja a un tamaño FIJO (`EnemyFlying` a 14×10, `EnemyCharger`
    a 14×12), así que escalar el PNG rompe el recorte en cuartos de frame.
    Escalar los frames recortados deja el recorte intacto y solo cambia lo
    que se dibuja. `scale` sin suavizado = cada texel se vuelve un bloque
    2×2, el estilo píxel se conserva.

    El hitbox NO crece (el rect ya quedó dimensionado antes): el cuerpo
    visible es ×2 y la caja sigue siendo la chica — más visible Y más
    justo para el jugador, nunca menos.
    """
    for clave, marcos in list(enemigo._sprite_frames.items()):
        if not marcos:
            continue
        enemigo._sprite_frames[clave] = [
            pygame.transform.scale(
                m, (m.get_width() * factor, m.get_height() * factor))
            for m in marcos
        ]
    # CRÍTICO (playtest ronda 2: «las máscaras están bajo tierra», «el del
    # agua se sale del agua»): `EnemyBase.draw` ancla los PIES con las
    # dimensiones GUARDADAS (`oy = rect.h - _sprite_fh`, `ox` centrado con
    # `_sprite_fw`). La primera versión escalaba los frames sin tocar esas
    # dos variables, así que el arte de 28×20 se dibujaba con el ancla de
    # 14×10: desbordaba 10 px HACIA ABAJO (enterrado) y 14 a la derecha.
    # Actualizándolas, el cuerpo crece hacia ARRIBA desde los pies, que es
    # como crecen los seres vivos.
    enemigo._sprite_fw *= factor
    enemigo._sprite_fh *= factor


class MurcielagoDelCamposanto(EnemyFlying):
    """El murciélago que SÍ recorre el camposanto (R2-5, AUD-476).

    El reporte fue «los murciélagos no bajan, se mueven pero no por el mapa», y
    describía exactamente lo que hacía `SineFlight`: avanza en horizontal, sí,
    pero **rebota a ±96 px de su origen** (está fijo en el motor). En un mapa de
    4160 px eso es un bicho colgado de un clavo bamboleándose: se mueve y no va
    a ninguna parte, que es justo lo que se veía.

    Se arregló sin tocar el motor y sin darle el picado que ya se probó y se
    rechazó (`alert_flight_mode="dive"`: en un pasillo es inesquivable, y el
    tramo se volvía un muro). Un murciélago de verdad hace otra cosa, y es
    mejor de jugar:

      · **RONDA LARGA** — cuando llega al tope de los 96 px del motor, en vez
        de rebotar se le corre el ANCLA: el vaivén sigue siendo el mismo, pero
        el centro viaja, así que el bicho recorre su tramo del camposanto de
        punta a punta. Sigue siendo predecible —va y viene por una franja— y
        ahora ocupa el espacio que le toca.
      · **BAJA A MIRAR** — al detectar al jugador, el ancla desciende despacio
        hacia su altura (30 px/s, con tope). No es una picada: es que el
        murciélago se acerca. La respuesta sigue siendo la misma —seguir
        andando o pegarle— pero por fin se nota que reaccionó, que era la
        mitad de la queja.
    """

    #: Media anchura de la ronda. 240 px es tramo y media pantalla: se cruza
    #: caminando y se ve venir desde lejos.
    RONDA = 240.0
    #: A qué velocidad baja el ancla al detectar. Lento a propósito: si bajara
    #: rápido sería un picado, y eso ya se descartó.
    DESCENSO = 30.0
    #: Cuánto puede bajar respecto de su altura de partida.
    CAIDA_MAXIMA = 96.0

    def __init__(self, spawn_position: pygame.Vector2, **kwargs: Any) -> None:
        super().__init__(spawn_position, **kwargs)
        self._casa = pygame.Vector2(spawn_position)
        self._deriva = 1.0

    def update(self, dt: float) -> None:
        super().update(dt)
        origen = getattr(self, "_origin", None)
        if origen is None:
            return
        # 1. La ronda: el ancla viaja con el bicho hasta el tope del tramo.
        #    `SineFlight` invierte `facing_direction` en cuanto se aleja 96 px
        #    del ancla, así que moviendo el ancla la vuelta se pospone.
        dx = origen.x - self._casa.x
        if abs(dx) < self.RONDA:
            origen.x += self._deriva * self.flight_speed * 0.45 * dt
        else:
            # En el tope se da la vuelta de verdad: una ronda, no una fuga.
            self._deriva *= -1.0
            origen.x += self._deriva * 4.0
        # 2. Bajar a mirar: sólo con el jugador detectado y por debajo.
        jugador = getattr(self, "_player_ref", None)
        if jugador is None:
            return
        # AUD-479b — y NUNCA por debajo del suelo. El playtest lo vio: «un
        # murciélago que aparte está súper abajo». Persiguiendo a un jugador
        # que camina,  cae casi al ras de la losa, y un
        # murciélago rozando el suelo deja de ser el enemigo que obliga a
        # mirar ARRIBA — que es su único trabajo. El tope son 40 px sobre la
        # cabeza del jugador de pie.
        objetivo = min(self._casa.y + self.CAIDA_MAXIMA,
                       float(jugador.centery) - 64.0)
        if objetivo > origen.y:
            origen.y = min(objetivo, origen.y + self.DESCENSO * dt)
        elif origen.y > self._casa.y:
            origen.y = max(self._casa.y, origen.y - self.DESCENSO * 0.6 * dt)


def _murcielago(spawn_position: pygame.Vector2, **kwargs: Any) -> EnemyFlying:
    """Murciélago del camposanto.

    Vuela en seno lento y ancho: cruza toda la franja donde el jugador salta,
    así que obliga a mirar arriba antes de saltar. Aguanta un golpe y muere,
    porque su trabajo es estorbar, no aguantar.

    Sobre el pozo cumple una segunda función que es la que lo justifica: el
    jugador puede **rebotar encima** con el golpe hacia abajo (el pogo), y ésa
    es la tercera forma de cruzar el agua sin tocarla.
    """
    kwargs.setdefault("flight_mode", "sine")
    kwargs.setdefault("flight_speed", 58.0)
    kwargs.setdefault("sine_amplitude", 34.0)
    kwargs.setdefault("sine_frequency", 0.9)
    kwargs.setdefault("max_health", 1.0)
    kwargs.setdefault("damage_on_contact", 0.5)
    kwargs.setdefault("detection_range_x", 200.0)
    kwargs.setdefault("detection_range_y", 120.0)
    # SIN picado.
    #
    # Se probó con `alert_flight_mode="dive"` para que se notara que
    # reaccionaban, y se pasó de frenada: un murciélago que pica es imposible
    # de esquivar en un pasillo, y con varios en pantalla el tramo se
    # convertía en un muro. «Los enemigos son muy intensos, hay uno arriba que
    # no deja pasar.»
    #
    # Que se note que reaccionó no vale el precio de que no se pueda pasar.
    # El vaivén en seno ya cruza la franja de salto, que es su trabajo; el
    # aviso lo da la aceleración, no un cambio de trayectoria.
    kwargs.setdefault("zone", ZONA)
    # AUD-476 — la clase propia: misma silueta y mismos números, pero con la
    # ronda larga y el descenso al detectar. Ver `MurcielagoDelCamposanto`.
    bicho = MurcielagoDelCamposanto(spawn_position, **kwargs)
    _agrandar_frames(bicho)
    return bicho


class MascaraTilawa(EnemyCharger):
    """El guardián enmascarado, con las tres animaciones que al motor le faltan.

    HALLAZGO — un `Charger` se dibuja como un cuadro rojo al embestir.

    `EnemyCharger._get_animation_key` devuelve `"wind_up"`, `"charge"` y
    `"stun"`, y **ninguna zona del juego trae esas hojas**: no existe un solo
    `enemy_charge_zoneN.png` en todo `assets/`, ni para la zona 1, ni la 2, ni
    la 3. `EnemyBase.draw` hace `self._sprite_frames.get(anim_key)`, no
    encuentra nada, y cae al marcador de posición — un rectángulo rojo liso de
    `PLACEHOLDER_COLORS["enemies"]`.

    El resultado es que la máscara se ve bien mientras patrulla y se convierte
    en un cuadro rojo **en los tres momentos en que el jugador necesita
    leerla**: cuando avisa, cuando embiste y cuando queda expuesta. Justo la
    información que hace que la pelea sea justa.

    No es un defecto de la zona 4 —le pasa a todos los `Charger` del juego—,
    así que vale la pena reportarlo. Aquí se tapa cargando las tres hojas.
    """

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        super()._load_extra_sprites(zone, fw, fh)
        from src.engine.core import settings
        from src.engine.utils.asset_loader import AssetLoader
        base = settings.ASSETS_DIR / "sprites" / "enemies" / "zone4"
        for clave in ("wind_up", "charge", "stun"):
            try:
                self._sprite_frames[clave] = AssetLoader.load_sprite_sheet(
                    base / f"enemy_{clave}_zone4.png", fw, fh)
            except (pygame.error, FileNotFoundError, PermissionError):
                # Antes que el cuadro rojo, cualquier cosa: se cae a la
                # animación de caminar, que al menos tiene forma de máscara.
                if "walk" in self._sprite_frames:
                    self._sprite_frames[clave] = self._sprite_frames["walk"]

    # ── R21 — el golpe no la muda de puesto ─────────────────────
    #: Playtest: «si le pego a los enemigos se mueven hacia donde los
    #: golpee y se quedan ahí como si fuera su nueva posición». La causa
    #: vive en el motor: el knockback desplaza `position`, pero el ancla
    #: de patrulla (`_patrol_origin`) queda fija — y la patrulla del
    #: `Charger` INVIERTE la dirección cada fotograma en cuanto está a más
    #: de 48 px del ancla, así que la máscara desplazada vibra en el sitio
    #: («se quedan ahí raros») en vez de caminar de vuelta. El guardián
    #: expulsado de su ronda ahora VUELVE andando a su puesto.
    RONDA_DE_GUARDIA = 48.0
    PASO_DE_VUELTA = 34.0        # px/s: vuelve caminando, no teletransportado

    def _patrol_behavior(self, dt: float) -> None:
        dx = self.position.x - self._patrol_origin.x
        if abs(dx) > self.RONDA_DE_GUARDIA + 6.0:
            self.facing_direction = -1 if dx > 0 else 1
            self.position.x += self.facing_direction * self.PASO_DE_VUELTA * dt
            return
        super()._patrol_behavior(dt)


def _mascara_tilawa(spawn_position: pygame.Vector2, **kwargs: Any) -> EnemyCharger:
    """Guardián enmascarado. Se planta, avisa, y embiste en línea recta.

    La embestida del motor tiene tres tiempos —telegrafiado, carrera,
    aturdimiento— y los tres importan: el aviso es la parte justa, la carrera
    es la amenaza, y el aturdimiento de después es la ventana donde el jugador
    cobra. Con 3 de vida hacen falta dos ventanas para matarla, así que hay que
    esquivar bien dos veces y no una.

    Va más lenta que el valor por defecto del motor (250 → 190). A 250 la
    embestida es más rápida que la reacción humana en un pasillo estrecho, y
    entonces no es un enemigo que se lee: es un enemigo que se memoriza.
    """
    kwargs.setdefault("max_health", 3.0)
    kwargs.setdefault("damage_on_contact", 1.0)
    kwargs.setdefault("charge_speed", 190.0)
    kwargs.setdefault("detection_range_x", 210.0)
    kwargs.setdefault("detection_range_y", 96.0)
    kwargs.setdefault("zone", ZONA)
    bicho = MascaraTilawa(spawn_position, **kwargs)
    _agrandar_frames(bicho)
    return bicho


class SukiaDeCeniza(EnemyShooter):
    """El sukia, con su propia hoja de sprites.

    `EnemyBase._load_zone_sprites` compone la ruta desde la zona
    (`enemy_zone4_walk.png`) y esa hoja la comparten TODAS las clases de la
    zona 4. Como el enemigo terrestre de la zona es la máscara tilawa, la hoja
    de la zona es la suya — y sin esta clase el sukia caminaba con cara de
    máscara. Se sobrescribe sólo la ruta de `walk`; el resto (herido, muerte,
    apuntar, disparar) se queda con lo de la zona, que le sirve.
    """

    def _load_zone_sprites(self, zone: int, fw: int, fh: int) -> None:
        super()._load_zone_sprites(zone, fw, fh)
        from src.engine.core import settings
        from src.engine.utils.asset_loader import AssetLoader
        ruta = (settings.ASSETS_DIR / "sprites" / "enemies" / "zone4"
                / "enemy_zone4_shooter_walk.png")
        try:
            self._sprite_frames["walk"] = AssetLoader.load_sprite_sheet(ruta, fw, fh)
        except (pygame.error, FileNotFoundError, PermissionError):
            pass       # se queda con la hoja de la zona; fea, pero visible

    # ── R21 — el rezo vuelve a su sitio ─────────────────────────
    #: El sukia no patrulla (`patrol_length=0`), así que el knockback lo
    #: dejaba plantado donde cayera, para siempre — el mismo hallazgo del
    #: playtest que la máscara, con otra cara. Desplazado, arrastra los
    #: pies de vuelta a su puesto de oración.
    PASO_DE_VUELTA = 26.0

    def _patrol_behavior(self, dt: float) -> None:
        dx = self.position.x - self._patrol_origin.x
        if abs(dx) > 6.0:
            self.facing_direction = -1 if dx > 0 else 1
            self.position.x += self.facing_direction * self.PASO_DE_VUELTA * dt
            return
        super()._patrol_behavior(dt)


def _sukia_de_ceniza(spawn_position: pygame.Vector2, **kwargs: Any) -> EnemyShooter:
    """El sukia: el que se quedó rezando y nunca paró.

    No se mueve (`patrol_length=0`) y escupe ceniza a ritmo lento. Es el único
    de los cuatro que castiga quedarse quieto en el suelo, y por eso está
    puesto donde hay plataformas: la respuesta correcta no es correr hacia él,
    es subirse a algo.
    """
    kwargs.setdefault("patrol_length", 0.0)
    kwargs.setdefault("fire_rate", 0.55)
    kwargs.setdefault("projectile_speed", 115.0)
    kwargs.setdefault("projectile_damage", 0.5)
    kwargs.setdefault("max_health", 2.5)
    kwargs.setdefault("damage_on_contact", 0.5)
    kwargs.setdefault("detection_range_x", 220.0)
    kwargs.setdefault("detection_range_y", 112.0)
    kwargs.setdefault("zone", ZONA)
    return SukiaDeCeniza(spawn_position, **kwargs)


def _ahogado(spawn_position: pygame.Vector2, **kwargs: Any) -> AhogadoDelPozo:
    bicho = AhogadoDelPozo(spawn_position, **kwargs)
    _agrandar_frames(bicho)
    return bicho


#: Nombre en el TMX → constructor. Los nombres son los que aparecen en Tiled.
MORADORES: dict[str, Any] = {
    "Murcielago": _murcielago,
    "MascaraTilawa": _mascara_tilawa,
    "SukiaDeCeniza": _sukia_de_ceniza,
    "AhogadoDelPozo": _ahogado,
}

#: Nombre bonito para el bestiario y el HUD de depuración.
NOMBRES: dict[str, str] = {
    "Murcielago": "Murciélago del camposanto",
    "MascaraTilawa": "Guardián de máscara tilawa",
    "SukiaDeCeniza": "Sukia de ceniza",
    "AhogadoDelPozo": "Ahogado del pozo",
}


def _con_id(fabrica: Any, nombre: str) -> Any:
    """Envuelve una fábrica pegándole `enemy_id` a cada instancia.

    `enemy_id` se pega por la misma razón que en AUD-154: las cuatro especies
    salen de tres clases base, así que sin esto el bestiario contaría un
    murciélago y un ahogado como el mismo bicho.
    """
    def _build(spawn_position: Any, **kwargs: Any) -> Any:
        bicho = fabrica(spawn_position, **kwargs)
        bicho.enemy_id = nombre
        return bicho

    # El loader y el bestiario muestran este nombre; sin él saldría
    # "_build" para las cuatro.
    _build.__name__ = nombre
    return _build


# Cuatro llamadas literales y no un bucle: `scripts/validate_tmx.py` descubre
# los tipos de un escenario leyendo el AST en busca de
# `register_entity("Nombre", ...)`, y un nombre en una variable es invisible
# para él — el mapa validaba en rojo con las especies perfectamente
# registradas en runtime. Es la misma convención de stage1_2 y boss_rey.
StageLoader.register_entity("Murcielago", _con_id(_murcielago, "Murcielago"))
StageLoader.register_entity("MascaraTilawa", _con_id(_mascara_tilawa, "MascaraTilawa"))
StageLoader.register_entity("SukiaDeCeniza", _con_id(_sukia_de_ceniza, "SukiaDeCeniza"))
StageLoader.register_entity("AhogadoDelPozo", _con_id(_ahogado, "AhogadoDelPozo"))
