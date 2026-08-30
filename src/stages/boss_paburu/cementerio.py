# Autor: Alejandro Josué Rodríguez Zamora
# Stage 4-2 «El Gran Shamán Paburu» — Legacy of InFest
"""
Module: cementerio
System: src.stages.boss_paburu
Academic Unit: II (vectores), IV (escenas), V (color e iluminación)

EL RECORRIDO DEL CEMENTERIO, Y LA TRAMPA

El stage 4-2 no es una sala: son 4160 px de camposanto que el jugador recorre
con la cámara siguiéndolo. Este módulo se encarga de las tres cosas que pasan
mientras camina, y que no son del jefe ni del mapa:

  1. LA BOCA        — dónde se entra a la catacumba: al final del camino.
  2. EL DESCENSO    — el jugador baja por el mecate a la CATACUMBA, la arena
                      excavada bajo el camposanto.
  3. EL POZO        — quién decide que el jugador está nadando.

POR QUÉ LA CATACUMBA Y NO EL SELLADO (decisión de Alejandro, 2026-08-14)
La primera versión sellaba el círculo pisado con dos muros y peleaba ahí.
Funcionaba, pero cargaba tres deudas: la pelea dependía de la vida con la que
llegaras (injusto entre partidas), morir devolvía a un checkpoint a media
pantalla de caminata (reintento caro), y los muros eran colisión invisible
apareciendo de la nada (un truco, no un lugar). La catacumba paga las tres:
Paburu CURA al portador al recibirlo —el juez quiere un juicio limpio—, el
checkpoint vive dentro de la cámara, y la arena es un sitio construido con
sus nichos, sus braseros y su encuadre exacto de una pantalla.

POR QUÉ SE QUITÓ EL SORTEO (D-01, 2026-08-16)
Durante meses uno de los cuatro círculos se sorteaba al cargar el nivel, y
pisarlo abría la tierra. La tesis era buena —«un disparador fijo se aprende en
la segunda partida»— pero el precio, medido, era ruinoso: el disparador de un
círculo mide 416 px de ancho y va pegado al suelo, o sea que es imposible
cruzarlo a pie. El sorteo no elegía dónde te atrapaban: elegía **dónde
terminaba el nivel**.

    Si salía el I   → veías hasta x=1360 (33 % del camposanto)
    Si salía el II  → 1936 (47 %)
    Si salía el III → 2736 (66 %)
    Si salía el IV  → 3536 (85 %)
                      media: 57 %

Y detrás del corte quedaba siempre lo mejor: la cripta, la tirolesa (x=3840) y
el resorte (x=3952), que en las cuatro partidas posibles eran **inalcanzables**.
El playtest lo dijo en una frase: «no se puede disfrutar el nivel porque lo
manda directamente a Paburu».

Había un segundo coste, más callado: el jugador no ELEGÍA bajar. Paburu se lo
llevaba. El momento se leía como un castigo por caminar, no como una llegada.

Lo que ocupa su sitio: Paburu no es un cazador, es un **juez**, y un juez
**cita**. La catacumba se entra por su boca, al final del camino, bajando por
el mecate de los sepultureros — y se baja cuando uno decide. El detalle
completo, con las alternativas descartadas, en `DISENO_ACCESO_CATACUMBA.md`.

Los cuatro círculos siguen ahí, con sus perfiles distintos y sus muebles: son
los sitios ceremoniales del camposanto y el soporte de las ofrendas. Lo que
perdieron es la trampa.

CÓMO SE CIERRA LA SALA SIN TOCAR EL MOTOR
`stage.collision_rects` es una lista que el jugador vuelve a leer **cada
fotograma**, así que añadirle un rectángulo en caliente basta: no hay que
recargar el mapa ni tocar `framework/`. Es lo mismo que hace el motor con las
puertas cerradas (AUD-140, «no hizo falta mutar collision_rects: se suman»).

QUIÉN AVISA DE QUE SE PISÓ UN CÍRCULO
El motor. Los cuatro círculos son `EventTrigger` del TMX: al entrar, el
`InteractableSystem` emite `INTERACT_TRIGGER_FIRED` con el nombre que declara
la propiedad `evento`. La primera versión de este archivo comparaba posiciones
a mano cada fotograma, lo cual funcionaba y estaba de más — el motor ya tenía
la pieza y la traía probada. Acá sólo se escucha y se decide si ese círculo
era el que salió sorteado.

EL POZO ES DEL MOTOR TAMBIÉN
`WaterZone` + `MecanicaDeAgua` ya meten al jugador en `SwimmingState`, le
cuentan el aire y lo ahogan si se queda. Lo único que este módulo aporta al
agua es dónde está, para que los ahogados sepan cuándo tirar.

Este archivo NO modifica engine/ ni framework/ — sólo los usa.
"""
from __future__ import annotations

import random
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pygame

# ── Luz ────────────────────────────────────────────────────────
#: Luz del recorrido.
#:
#: Estaba en 0.52 y era un error de bulto. `LightSystem` **multiplica** la
#: pantalla por este valor, así que 0.52 no oscurece "un poco": se come el
#: fondo pintado entero. La luna, las estrellas y las montañas de
#: `backgrounds/paburu/` seguían dibujándose y llegaban al ojo a la mitad de
#: su brillo, con lo que el cielo quedaba en un azul-morado sucio y el nivel
#: parecía tener el fondo roto. No lo estaba: estaba apagado.
#:
#: AUD-463 — de 0.82 a 0.50: ES DE NOCHE, y ahora se nota de verdad.
#:
#: 0.82 se eligió cuando la luz de este escenario no llegaba a aplicarse (la
#: sobrescribía el reloj del mundo cada fotograma, ver `AMBIENT_BY_PHASE` en
#: la escena), así que el número describía una intención y no una imagen. Con
#: la escena mandando sobre su luz y el mapa en `night` —tinte azul lunar en
#: vez del ocre de `dusk`— el camposanto por fin es un camposanto de noche:
#: el farol del jugador y los cuencos de fuego hacen los charcos de luz, y la
#: luna del parallax deja de competir con un cielo aclarado.
#:
#: 0.50 y no menos porque el camposanto se RECORRE: hay que ver dónde se pisa.
#: La penumbra de verdad es la de la sala (0.42 en la Forma 1) y el negro del
#: descenso (0.16); el contraste entre los tres es lo que hace el momento.
#: AUD-469 — 0.50 → 0.58 al apagar el farol del jugador. El disco de luz
#: que lo seguía se veía como un halo pegado al sprite («¿por qué se ve
#: como una luz en el personaje?»), y con la noche real el contraste lo
#: delataba. Sin él hacía falta un pelo más de luz base para leer el suelo;
#: los charcos los ponen ahora los catorce cuencos de fuego, que SE VEN y
#: por eso se entienden.
LUZ_CAMINO = 0.58

#: El instante negro, cuando se cierra el círculo. Dura lo que tarda la rampa.
LUZ_TRAMPA = 0.16

#: Prefijo del evento que emite cada círculo. Tiene que coincidir con
#: `EVENTO_CIRCULO` de `tools/gen_paburu_tmx.py`, que es quien lo escribe en
#: el TMX. Se comprueba al leer el mapa: si no coincidiera, ningún círculo
#: dispararía nunca y el jugador cruzaría el nivel entero sin jefe — un fallo
#: silencioso, del peor tipo, así que mejor que reviente al cargar.
EVENTO_CIRCULO = "PABURU_CIRCULO_"

#: LA BOCA DE LA CATACUMBA. Desde D-01 es la única entrada al juicio.
#:
#: Nació como red de seguridad —el jugador que cruzaba los cuatro círculos por
#: arriba llegaba al borde del mapa sin pelear— y al quitar el sorteo pasó a
#: ser la puerta principal, que es lo que su geometría venía siendo desde el
#: principio: un foso real al final del camino, no un muro con un evento.
#:
#: Conserva el nombre del evento (`..._PUERTA`) porque lo escribe el generador
#: del TMX y renombrarlo obligaría a regenerar el mapa por un motivo
#: cosmético. Lo que significa hoy: **aquí se baja**.
EVENTO_PUERTA = "PABURU_CIRCULO_PUERTA"

#: La losa del camposanto: `FLOOR_Y` del generador. Aquí se repite en vez de
#: importarse porque `tools/` no es un paquete instalado y el stage no puede
#: depender de él en runtime. Guardián: `test_cementerio_paburu`.
SUPERFICIE = 560

#: Alto de la bocanada sobre el foso. Dos cuerpos del jugador: lo justo para
#: que las brasas se vean desde lejos sin parecer una hoguera.
ALTO_BOCA = 96


@dataclass
class Circulo:
    """Uno de los cuatro sitios donde Paburu PUEDE emerger.

    Tiene DOS rectángulos y la diferencia importa:

      · `rect`  — el disparador. Está metido 80 px hacia adentro, para que
                  salte cuando el jugador ya entró de verdad.
      · `arena` — el círculo entero. Es donde van los muros y sobre lo que se
                  encuadra la cámara.

    Sellar sobre el disparador dejaría una arena 160 px más angosta de lo
    diseñado, con los muros por dentro de las plataformas del círculo. Es
    exactamente el fallo que tenía la primera versión, y sólo se vio midiendo
    dónde acababa el jugador después de sellar.
    """

    nombre: str
    evento: str
    rect: pygame.Rect
    arena: pygame.Rect
    boss_pos: pygame.Vector2


@dataclass
class Catacumba:
    """La arena excavada bajo el camposanto: donde ocurre la pelea.

    `interior` es la cámara jugable (800 px exactos de ancho: una pantalla).
    `arena` y `boss_pos` existen con esos nombres para que la escena la use
    donde antes usaba un `Circulo` —invocar al jefe, reubicar guardianes,
    lanzar la embestida del venado— sin duplicar código.
    """

    interior: pygame.Rect
    spawn: tuple[float, float]
    boss_pos: pygame.Vector2
    #: El foso de entrada física, para las pruebas y el depurador.
    foso: pygame.Rect

    @property
    def arena(self) -> pygame.Rect:
        return self.interior


@dataclass
class Cementerio:
    """El estado del recorrido: qué círculo tocó y si ya se descendió."""

    circulos: list[Circulo] = field(default_factory=list)
    agua: list[pygame.Rect] = field(default_factory=list)
    #: Conserva el nombre histórico de cuando había sorteo. Desde D-01
    #: **siempre es la boca**: el sitio donde este nivel baja al juicio.
    elegido: Circulo | None = None
    #: La boca del final. Desde D-01 es la entrada, no la red.
    puerta: Circulo | None = None
    #: La bocanada en la SUPERFICIE, sobre el foso: la columna de aire por
    #: la que se ve el agujero desde arriba. Es donde arde la señal de brasas
    #: (R2-8), que dejó de marcar «el círculo sorteado» para marcar el
    #: destino: en un camposanto de 4160 px oscuros, un faro al final.
    boca: pygame.Rect = field(default_factory=pygame.Rect)
    #: La cámara subterránea. Sin ella el mapa es de la versión vieja.
    catacumba: Catacumba | None = None
    #: `sellado` conserva su nombre histórico: significa «la pelea empezó y
    #: ningún otro disparador vale». Que hoy se baje en vez de amurallarse no
    #: cambia lo que la bandera decide.
    sellado: bool = False
    #: Encuadre de la cámara mientras dura la pelea. Se fija al descender.
    encuadre: pygame.Vector2 = field(default_factory=pygame.Vector2)

    # ── Lectura del mapa ────────────────────────────────────────
    @classmethod
    def leer(cls, tmx: Path, semilla: int | None = None) -> Cementerio:
        """Lee los marcadores del TMX y sortea el círculo de esta partida.

        Se parsea el TMX en vez de leerlo del `StageData` porque lo que hace
        falta —dónde emerge el jefe en cada círculo— viaja en propiedades que
        el cargador no interpreta: `Disparador` guarda el rect y el evento, y
        descarta `boss_x` / `boss_y`. Parsear el XML una vez al cargar cuesta
        unos milisegundos y evita tener que tocar el cargador del profesor
        para que conserve propiedades que sólo le sirven a este stage.

        `semilla` existe para las pruebas: con una semilla fija el sorteo es
        reproducible y se pueden comprobar los cuatro casos. En una partida
        normal va en None y el sorteo es de verdad.
        """
        raiz = ET.parse(tmx).getroot()
        circulos: list[Circulo] = []
        agua: list[pygame.Rect] = []

        # La catacumba viaja como propiedades de MAPA, no como objeto: el
        # validador del motor rechaza tipos de objeto desconocidos, y todos
        # los tipos conocidos hacen algo en runtime que acá sobraría.
        mapa = {
            p.get("name"): p.get("value")
            for p in raiz.findall("properties/property")
        }
        catacumba: Catacumba | None = None
        if "catacumba_x" in mapa:
            catacumba = Catacumba(
                interior=pygame.Rect(
                    int(mapa["catacumba_x"]), int(mapa["catacumba_y"]),
                    int(mapa["catacumba_w"]), int(mapa["catacumba_h"]),
                ),
                spawn=(float(mapa["catacumba_spawn_x"]),
                       float(mapa["catacumba_spawn_y"])),
                boss_pos=pygame.Vector2(
                    float(mapa["catacumba_boss_x"]),
                    float(mapa["catacumba_boss_y"]),
                ),
                foso=pygame.Rect(
                    int(mapa.get("catacumba_foso_x", 0)), 0,
                    int(mapa.get("catacumba_foso_w", 0)), 1,
                ),
            )

        for grupo in raiz.findall("objectgroup"):
            for obj in grupo.findall("object"):
                tipo = obj.get("type", "")
                x, y = float(obj.get("x", 0)), float(obj.get("y", 0))
                w, h = float(obj.get("width", 0)), float(obj.get("height", 0))
                props = {
                    p.get("name"): p.get("value")
                    for p in obj.findall("properties/property")
                }
                if tipo == "WaterZone":
                    agua.append(pygame.Rect(int(x), int(y), int(w), int(h)))
                elif tipo == "EventTrigger" and "boss_x" in props:
                    evento = str(props.get("evento", ""))
                    if not evento.startswith(EVENTO_CIRCULO):
                        raise ValueError(
                            f"{tmx}: el círculo {obj.get('name')!r} emite "
                            f"{evento!r}, que no empieza por {EVENTO_CIRCULO!r}. "
                            f"La escena no lo escucharía y el nivel se jugaría "
                            f"entero sin jefe."
                        )
                    circulos.append(Circulo(
                        nombre=obj.get("name", "?"),
                        evento=evento,
                        rect=pygame.Rect(int(x), int(y), int(w), int(h)),
                        arena=pygame.Rect(
                            int(props.get("arena_x", x)), int(y),
                            int(props.get("arena_w", w)), int(h),
                        ),
                        boss_pos=pygame.Vector2(
                            float(props.get("boss_x", x)),
                            float(props.get("boss_y", y)),
                        ),
                    ))

        puerta = next((c for c in circulos if c.evento == EVENTO_PUERTA), None)
        if puerta is not None:
            # La boca no es uno de los círculos: es la salida del camino.
            circulos = [c for c in circulos if c is not puerta]

        cem = cls(circulos=circulos, agua=agua, puerta=puerta,
                  catacumba=catacumba)
        # D-01 — ya no se sortea. La boca ES el destino, siempre. Si el mapa
        # fuera de la era del sorteo y no la trajera, se cae al comportamiento
        # viejo (un círculo al azar) en vez de dejar el nivel sin jefe: un
        # mapa antiguo tiene que seguir siendo jugable.
        if puerta is not None:
            cem.elegido = puerta
        elif circulos:
            rng = random.Random(semilla) if semilla is not None else random
            cem.elegido = rng.choice(circulos)

        # La bocanada de la superficie: la columna del foso hasta la losa.
        # Se deriva del foso declarado en el mapa —una sola fuente— para que
        # mover el agujero mueva también su faro.
        if catacumba is not None and catacumba.foso.width:
            cem.boca = pygame.Rect(catacumba.foso.x, SUPERFICIE - ALTO_BOCA,
                                   catacumba.foso.width, ALTO_BOCA)
        elif puerta is not None:
            cem.boca = puerta.rect.copy()
        return cem

    # ── El disparador ───────────────────────────────────────────
    def es_el_bueno(self, evento: str) -> bool:
        """¿Este disparador es el que baja al juicio?

        Desde D-01 la respuesta es **sólo la boca**. Los cuatro círculos
        siguen emitiendo al pisarlos —el motor no sabe nada de esto y no tiene
        por qué—, pero lo que hacen hoy es encenderse, no tragarse al jugador;
        de eso se encarga la escena escuchando el mismo evento.

        Se mantiene la comprobación de `sellado` porque sigue significando lo
        mismo que siempre: una pelea por partida. Bajar dos veces sería peor
        que no bajar.
        """
        if self.sellado:
            return False
        if evento == EVENTO_PUERTA:
            self.elegido = self.puerta or self.elegido
            return self.puerta is not None
        # Un mapa de la era del sorteo (sin boca) conserva su comportamiento:
        # el círculo elegido baja. Con boca, ningún círculo baja.
        return (self.puerta is None and self.elegido is not None
                and evento == self.elegido.evento)

    # ── El descenso ─────────────────────────────────────────────
    def descender(self, jugador: Any, mapa_ancho: int, mapa_alto: int,
                  ancho_vista: int, alto_vista: int) -> Catacumba:
        """Baja al jugador a la catacumba y devuelve la cámara.

        Lo que la versión de los muros hacía con `stage.collision_rects` acá
        no hace falta: la catacumba está cerrada por la roca del propio mapa
        —colisión declarada en el TMX, visible como piedra— y no por
        rectángulos invisibles añadidos en caliente. El teleport es la trampa
        entera: la tierra se abre y el camposanto se queda arriba.
        """
        cat = self.catacumba
        assert cat is not None, "descender() sin catacumba en el mapa"

        # D-01 — EL TELEPORT PASA A SER LA RED, NO EL CAMINO.
        #
        # Con el sorteo, el jugador estaba en la superficie a tres mil píxeles
        # de la arena y había que traerlo: el teleport ERA la trampa. Ahora
        # baja él, por el mecate, y arrastrarlo desde media cuerda hasta el
        # suelo sería quitarle de las manos justo el gesto que se le pidió.
        #
        # Así que sólo se le mueve si NO está donde tiene que estar. Sigue
        # cubriendo el caso de la red —cargar una partida rara, un respawn a
        # destiempo, un mapa viejo— sin pisar el descenso normal.
        if jugador is not None and not cat.interior.colliderect(jugador.rect):
            jugador.position.update(cat.spawn[0], cat.spawn[1] - 32)
            jugador.velocity.update(0, 0)
            jugador.rect.midbottom = (int(cat.spawn[0]), int(cat.spawn[1]))
            jugador.position.update(float(jugador.rect.x), float(jugador.rect.y))

        # El encuadre: la cámara mide exactamente una pantalla de ancho, así
        # que el encuadre es su esquina — centrar no tiene grados de libertad
        # y el borde de la vista coincide con la pared de roca.
        self.encuadre.update(
            max(0, min(cat.interior.left, mapa_ancho - ancho_vista)),
            max(0, min(cat.interior.bottom + 16 - alto_vista,
                       mapa_alto - alto_vista)),
        )
        self.sellado = True
        return cat

    # ── El pozo ─────────────────────────────────────────────────
    def en_agua(self, jugador: Any) -> pygame.Rect | None:
        """¿Está el jugador dentro del pozo? Devuelve el rect, o None."""
        if jugador is None:
            return None
        caja = jugador.hurtbox
        for rect in self.agua:
            if rect.colliderect(caja):
                return rect
        return None
