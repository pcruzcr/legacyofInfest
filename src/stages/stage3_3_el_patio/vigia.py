"""
Module: vigia
System: stage (student assignment)
Academic Unit: Unidad VII (filtros) + VIII (segmentacion) + IX (reconocimiento).

El Vigia de la Fuente. La fuente del patio no solo cura: vigila. Cada cierto
tiempo MIRA la pantalla —el fotograma ya dibujado, no la lista de enemigos— y
de ahi saca dos cosas distintas:

  1) SEGMENTACION (Unidad VIII): umbral de Otsu sobre el recorte, apertura
     morfologica para quitar el ruido de un pixel, y componentes conectados
     para contar y medir las siluetas que hay alrededor. El numero de siluetas
     es el "nivel de amenaza".

  2) RECONOCIMIENTO (Unidad IX): la silueta mas grande se recorta DE LA
     MASCARA que acaba de producir la segmentacion, se le sacan
     caracteristicas HOG y un bosque aleatorio entrenado
     (`models/vigia.pkl`) decide si lo que se acerca es AEREO o TERRESTRE.
     El clasificador se alimenta de la salida de la Unidad VIII, no de la
     imagen cruda: es la tuberia que pide la rubrica, y ademas es la unica
     que funciona (ver `generar_dataset.py` para el intento que fallo).

Por que mira la pantalla y no la lista de enemigos
===================================================
Preguntarle al motor "que enemigos hay cerca" seria trivial y no demostraria
nada de vision por computadora: la respuesta ya esta en memoria. El ejercicio
de la Unidad VIII/IX es justamente el contrario — partir de una imagen, que es
lo unico que tendria una camara de verdad, y recuperar de ahi la informacion.
Por eso el Vigia trabaja sobre pixeles aunque el dato "facil" exista.

El modelo se carga una sola vez en `__init__` y la inferencia va a 0,8 Hz
sobre UNA region, no una por enemigo y fotograma: el propio motor avisa en
`ai_predictor.py` de que la inferencia individual cuesta 1,89 ms y que a una
llamada por entidad se come el presupuesto de 60 fps.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pygame

from src.framework.processing.filter_tools import FilterTools
from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools
from src.framework.processing.vision_tools import VisionTools


def _invertir(mascara: pygame.Surface) -> pygame.Surface:
    """Devuelve el negativo de la mascara.

    Otsu marca en blanco lo MAS CLARO, y cual de los dos lados contiene a las
    criaturas depende del fondo: con el patio de dia el cielo era claro y los
    pajaros oscuros —habia que invertir—, y con el patio de noche es al reves,
    porque lo brillante son las ventanas encendidas. Por eso `segmentar()` ya
    no invierte siempre: prueba las dos polaridades. Ver su docstring.
    """
    return pygame.surfarray.make_surface(255 - pygame.surfarray.array3d(mascara))

logger = logging.getLogger(__name__)

RUTA_MODELO = Path(__file__).resolve().parent / "models" / "vigia.pkl"

INTERVALO = 1.25      # s entre analisis (0,8 Hz)
# 128 y no mas: el coste de la tuberia crece con el area, y a 160 px el
# analisis completo tardaba tanto que se notaba el tiron cada vez que corria.
LADO_ANALISIS = 128   # lado del recorte de pantalla que se examina
AREA_MINIMA = 40      # px^2: por debajo es ruido, no una silueta
AREA_MAXIMA = 1500    # por encima es fondo (un muro, el cielo), no una criatura
# Los enemigos de la zona 3 miden entre 12x10 y 20x16 px. Estos limites de
# caja descartan lo que la segmentacion encuentra pero no puede ser un bicho:
# un tronco sale como 10x40 y una rama como 46x6, y los dos caian dentro del
# rango de area aceptable.
CAJA_MIN = (8, 5)
CAJA_MAX = (40, 30)
KERNEL_APERTURA = 3
LADO_PARCHE = 32      # lado del parche que se clasifica (igual que el dataset)
AMENAZA_ALTA = 3      # siluetas simultaneas para considerar el patio "en alerta"
# Cuanto vale un veredicto antes de caducar. Sin esto el ultimo resultado se
# quedaba pegado para siempre: el jugador se alejaba del halcon y la Onda
# seguia con la bonificacion "aereo" media partida despues, sin nada aereo
# cerca. Ocho segundos es algo mas que el intervalo de analisis, asi que un
# hueco suelto sin deteccion no apaga el veredicto de golpe.
VIGENCIA = 8.0


def _parece_criatura(region) -> bool:
    """Filtra lo que la segmentacion encuentra pero no puede ser un enemigo."""
    if not (AREA_MINIMA <= region.area <= AREA_MAXIMA):
        return False
    caja = region.bounding_rect
    return (CAJA_MIN[0] <= caja.width <= CAJA_MAX[0]
            and CAJA_MIN[1] <= caja.height <= CAJA_MAX[1])


class Vigia:
    """Analiza el fotograma y publica `modo`, `amenaza` y `regiones`."""

    def __init__(self) -> None:
        self._reloj = 0.0
        self.modo: str | None = None          # "aereo" | "terrestre" | None
        self.confianza: float = 0.0
        self.edad: float = 0.0                # segundos desde el ultimo acierto
        self.amenaza: int = 0
        self.regiones: list = []
        self._recuadros: list[pygame.Rect] = []
        self._fuente = pygame.font.Font(None, 18)
        self._modelo = None
        try:
            self._modelo = PatternRecognitionTools.load_model(RUTA_MODELO)
            logger.info("Vigia: modelo %s cargado (%s, %.1f%% entrenamiento)",
                        RUTA_MODELO.name, self._modelo.model_type,
                        self._modelo.training_accuracy * 100)
        except Exception as exc:
            # Sin modelo el nivel sigue siendo jugable: el Vigia se queda en
            # modo pasivo en vez de tumbar la escena. Un .pkl que falta es un
            # problema de entrega, no una razon para que no arranque el juego.
            logger.warning("Vigia: no pude cargar %s (%s); sigo sin clasificar",
                           RUTA_MODELO, exc)

    # -- analisis ----------------------------------------------
    def _recorte(self, pantalla: pygame.Surface, jugador, offset: pygame.Vector2):
        """Region cuadrada de pantalla centrada en el jugador, recortada al borde."""
        if jugador is None:
            return None
        cx = int(jugador.position.x - offset.x)
        cy = int(jugador.position.y - offset.y)
        mitad = LADO_ANALISIS // 2
        zona = pygame.Rect(cx - mitad, cy - mitad, LADO_ANALISIS, LADO_ANALISIS)
        zona = zona.clip(pantalla.get_rect())
        if zona.width < 32 or zona.height < 32:
            return None
        return pantalla.subsurface(zona).copy()

    # -- tuberia de vision (la comparte `generar_dataset.py`) --
    def segmentar(self, recorte: pygame.Surface):
        """Recorte de pantalla -> (mascara binaria, regiones de criatura).

        Es el bloque entero de la Unidad VIII y esta aislado a proposito:
        `generar_dataset.py` llama a este mismo metodo para fabricar las
        muestras, asi que entrenamiento e inferencia no pueden separarse.
        """
        # Unidad VII: un desenfoque suave antes de umbralizar. Sin el, el
        # adoquinado del suelo genera decenas de componentes de 1-2 px y el
        # conteo de siluetas no significa nada.
        suave = FilterTools.gaussian_blur(recorte, sigma=1.0)

        # Unidad VII (2/2): el patio de noche es oscuro —luminancia media en
        # torno a 64 de 255— y todo el detalle se apelmaza en la parte baja
        # del histograma. Se mide y, si esta oscuro, se realza ANTES de
        # umbralizar; si no, Otsu corta sobre un rango aplastado y las
        # siluetas no se separan del cielo.
        hist = FilterTools.compute_histogram(suave)
        total = int(hist["total_pixels"]) or 1
        # media = suma(i * pixeles_con_luminancia_i) / total, igual que en
        # `fountain.py`: `compute_histogram` devuelve arrays de 256 por canal.
        media = sum(i * int(c) for i, c in enumerate(hist["luminance"])) / total
        if media < 110:
            # `adjust_brightness` solo acepta factores hasta 4,0, y un recorte
            # casi negro (media de 26) pedia 4,1. Se acota.
            factor = min(4.0, 110.0 / max(media, 1.0))
            suave = FilterTools.adjust_brightness(suave, factor)

        # Unidad VIII (1/3): umbral de Otsu — elige el corte solo, sin numero
        # magico, que es lo que hace falta aqui porque el patio cambia mucho
        # de luminosidad entre el cielo y las ventanas encendidas.
        mascara, _umbral = VisionTools.threshold_otsu(suave)

        # Unidad VIII (2/3) y polaridad: apertura sobre las DOS versiones de
        # la mascara. Cual sirve depende del fondo —de dia las criaturas eran
        # lo oscuro y habia que invertir; de noche son lo claro y no— y
        # fijarlo a mano dejo al Vigia ciego (0 de 8 detecciones) en cuanto se
        # cambio el fondo a nocturno. Se queda la polaridad que encuentre mas
        # siluetas con forma de bicho, asi que se adapta sola.
        mejor_mascara, mejor_regiones = None, []
        for candidata in (mascara, _invertir(mascara)):
            abierta = VisionTools.morphological_open(candidata, KERNEL_APERTURA)
            # Unidad VIII (3/3): componentes conectados, ya medidos por region.
            regs = [r for r in VisionTools.analyze_regions(abierta)
                    if _parece_criatura(r)]
            if mejor_mascara is None or len(regs) > len(mejor_regiones):
                mejor_mascara, mejor_regiones = abierta, regs
        return mejor_mascara, mejor_regiones

    def parche_de(self, recorte: pygame.Surface, cerca_de=None):
        """Segmenta y devuelve el parche de una region. Lo usa el generador.

        `cerca_de` elige la region mas proxima a ese punto (el generador sabe
        donde puso el sprite); sin el manda la de mayor area, que es lo unico
        que se puede saber en ejecucion.
        """
        mascara, regiones = self.segmentar(recorte)
        if not regiones:
            return None
        if cerca_de is None:
            region = regiones[0]
        else:
            region = min(regiones, key=lambda r: (r.centroid[0] - cerca_de[0]) ** 2
                         + (r.centroid[1] - cerca_de[1]) ** 2)
        return self.encuadrar(mascara, region)

    def encuadrar(self, mascara: pygame.Surface, region):
        """Recorta de `mascara` el parche que se le pasa al clasificador.

        Separado de `parche_de` porque `analizar` ya tiene la mascara y las
        regiones: llamar a `parche_de` alli repetia la segmentacion entera y
        duplicaba el coste del analisis (100 ms en vez de 50).
        """
        caja = region.bounding_rect
        # El parche tiene que estar encuadrado COMO LAS MUESTRAS: cuadrado,
        # de lado >= 32 y con la silueta centrada. Recortar la caja ajustada
        # daba un encuadre que el modelo no habia visto nunca y clasificaba
        # casi al azar (un halcon salia "terrestre" al 65%).
        cx, cy = region.centroid
        lado = max(LADO_PARCHE, int(max(caja.width, caja.height) * 1.6))
        cuadro = pygame.Rect(0, 0, lado, lado)
        cuadro.center = (int(cx), int(cy))
        cuadro = cuadro.clip(mascara.get_rect())
        if cuadro.width < 12 or cuadro.height < 12:
            return None
        return mascara.subsurface(cuadro).copy()

    def analizar(self, pantalla: pygame.Surface, jugador, offset: pygame.Vector2) -> None:
        recorte = self._recorte(pantalla, jugador, offset)
        if recorte is None:
            return
        mascara, regiones = self.segmentar(recorte)
        self.regiones = regiones
        self.amenaza = len(regiones)
        self._recuadros = [r.bounding_rect.copy() for r in regiones[:6]]

        # Unidad IX: manda la silueta MAS CERCANA AL JUGADOR, no la mas
        # grande. El patio nocturno tiene ventanas encendidas que el umbral
        # tambien marca, y varias son mayores que un pajaro: con "la mas
        # grande" el Vigia acababa clasificando una ventana. El jugador esta
        # siempre en el centro del recorte, y lo que le amenaza es lo que se
        # le acerca. Se clasifica el parche de la MASCARA, que es la salida de
        # la Unidad VIII alimentando a la IX.
        if not regiones or self._modelo is None:
            return
        centro = (recorte.get_width() / 2, recorte.get_height() / 2)
        cerca = min(regiones, key=lambda r: (r.centroid[0] - centro[0]) ** 2
                    + (r.centroid[1] - centro[1]) ** 2)
        parche = self.encuadrar(mascara, cerca)
        if parche is None:
            return
        try:
            rasgos = VisionTools.extract_features(parche, method="hog")
            probabilidades = PatternRecognitionTools.classify_proba(rasgos, self._modelo)
            self.modo = max(probabilidades, key=lambda k: probabilidades[k])
            self.confianza = float(probabilidades[self.modo])
            self.edad = 0.0
        except Exception as exc:
            logger.debug("Vigia: no pude clasificar la region (%s)", exc)

    # -- ciclo de vida -----------------------------------------
    def update(self, dt: float, pantalla: pygame.Surface, jugador,
               offset: pygame.Vector2) -> None:
        if self.modo is not None:
            self.edad += dt
            if self.edad > VIGENCIA:
                # Caducado: se olvida el veredicto y con el la bonificacion.
                self.modo = None
                self.confianza = 0.0
        self._reloj += dt
        if self._reloj < INTERVALO:
            return
        self._reloj = 0.0
        self.analizar(pantalla, jugador, offset)

    # -- comportamiento que dispara la clasificacion -----------
    @property
    def multiplicador_radio(self) -> float:
        """AEREO -> la Onda se abre mas: los voladores estan lejos y arriba."""
        return 1.6 if self.modo == "aereo" else 1.0

    @property
    def dano_extra(self) -> float:
        """TERRESTRE -> la Onda pega mas fuerte: vienen de cerca y aguantan."""
        return 1.5 if self.modo == "terrestre" else 0.0

    @property
    def en_alerta(self) -> bool:
        return self.amenaza >= AMENAZA_ALTA

    def draw(self, surface: pygame.Surface) -> None:
        """Panel del Vigia arriba a la IZQUIERDA, con lo que ha medido.

        Estaba a la derecha y se solapaba con el minimapa del motor, que el
        HUD coloca en Rect(675, 15, 110, 110). Al traerlo a la izquierda se
        puso en y=92 y entonces pisaba la barra de estamina, que ocupa
        Rect(15, 94, 60, 12). Ahora va debajo del radar, que es el ultimo
        hueco libre de la columna izquierda.
        """
        x = 10
        y = 272
        panel = pygame.Surface((124, 52), pygame.SRCALPHA)
        panel.fill((10, 20, 35, 165))
        surface.blit(panel, (x, y))
        pygame.draw.rect(surface, (90, 170, 220), (x, y, 124, 52), 1)

        titulo = "VIGIA  [!]" if self.en_alerta else "VIGIA"
        color_t = (255, 170, 120) if self.en_alerta else (150, 210, 240)
        surface.blit(self._fuente.render(titulo, True, color_t), (x + 6, y + 4))
        surface.blit(self._fuente.render("siluetas: %d" % self.amenaza, True,
                                         (215, 235, 250)), (x + 6, y + 19))
        if self._modelo is None:
            surface.blit(self._fuente.render("sin modelo", True, (200, 140, 140)),
                         (x + 6, y + 34))
            return
        if self.modo is None:
            # "sin contacto" y no "analizando...": el Vigia SIEMPRE esta
            # analizando, asi que ese texto no informaba de nada y con el
            # nivel a 5 enemigos se quedaba fijo tramos enteros — parecia
            # que la pieza estaba colgada. Esto dice lo que de verdad pasa:
            # se ha mirado y no hay nada que clasificar.
            surface.blit(self._fuente.render("sin contacto", True, (150, 165, 180)),
                         (x + 6, y + 34))
            return
        color_m = (255, 200, 120) if self.modo == "aereo" else (150, 230, 160)
        etiqueta = "%s %.0f%%" % (self.modo, self.confianza * 100)
        surface.blit(self._fuente.render(etiqueta, True, color_m), (x + 6, y + 34))
        # Antiguedad del veredicto: distingue "lo esta viendo ahora" de "lo
        # vio hace rato", que es justo lo que cambia el comportamiento.
        if self.edad >= 1.0:
            viejo = self._fuente.render("hace %ds" % int(self.edad), True,
                                        (130, 145, 160))
            surface.blit(viejo, (x + 118 - viejo.get_width(), y + 34))

    def draw_regiones(self, surface: pygame.Surface, jugador,
                      offset: pygame.Vector2) -> None:
        """Recuadros de las siluetas detectadas, en coordenadas de pantalla."""
        if not self._recuadros or jugador is None:
            return
        mitad = LADO_ANALISIS // 2
        ox = int(jugador.position.x - offset.x) - mitad
        oy = int(jugador.position.y - offset.y) - mitad
        ox = max(0, min(ox, surface.get_width() - LADO_ANALISIS))
        oy = max(0, min(oy, surface.get_height() - LADO_ANALISIS))
        for caja in self._recuadros:
            pygame.draw.rect(surface, (120, 200, 245),
                             (ox + caja.x, oy + caja.y, caja.width, caja.height), 1)
