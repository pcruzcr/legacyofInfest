# Autor: Alejandro Josué Rodríguez Zamora
# Stage 4-2 «El Gran Shamán Paburu» — Legacy of InFest
"""
Module: ataques_guardianes
System: stages.boss_paburu
Academic Unit: II (vectores), VI (interpolación y movimiento paramétrico)
Description: Los ecos de combate de los tres guardianes — venado, serpiente
             y gavilán (DISENO_NIVEL_Y_JEFE.md §3.4).

POR QUÉ EXISTE
Los guardianes aparecían con la Forma 2 y se quedaban mirando. El lore dice
que custodiaron el camposanto junto a Paburu en vida (GDD §41): un custodio
que mira no custodia nada. Cada uno ataca con el eco de la firma del jefe
que fue — la pelea final cita el viaje entero del jugador.

Tres ataques, tres respuestas distintas, igual que en la Forma 2:

    · La embestida del venado va recta a media altura: se SALTA.
    · El orbe de la serpiente serpentea lento: se PARA (y devuelto, tumba
      a su dueña).
    · La picada del gavilán marca su sombra en el suelo: se ESQUIVA a un
      lado.

La regla de presión es explícita en el diseño: moderado, no imposible.
Cadencias largas (≥6 s por guardián), un solo eco en vuelo a la vez, y
telegrafiado siempre — los tres avisan más tiempo del que pegan.

Mismo contrato que `form2_attacks`: `alive`, `is_telegraphing`, `rect`
(None mientras telegrafía), `update(dt)`, `draw(surface, offset)`; el orbe
además `devolver()` para el parry, como los ecos de Paburu.
"""
from __future__ import annotations

import math

import pygame

# Paleta espectral de los guardianes: más fría que el verde de Paburu
# (ESPECTRO en form2_attacks es (0, 200, 100)); los ecos se tienen que
# distinguir del jefe de un vistazo, sobre todo cuando conviven en pantalla.
ECO_FRIO = (110, 190, 235)
ECO_CLARO = (185, 230, 255)
ECO_OSC = (55, 105, 150)
AVISO = (255, 210, 90)          # el mismo amarillo de aviso de todo el stage


def suave(t: float) -> float:
    """Smoothstep 3t² − 2t³ (Unidad VI): arranque y frenado sin escalón."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


# ── AUD-471: los ecos dejan de ser figuras geométricas ────────────────────
#
# «Los ataques de los guardianes se ven muy toscos», y era exacto: los tres se
# dibujaban con primitivas opacas —una elipse, un círculo, un rombo— pegadas
# sobre el fondo. Una elipse azul no es un venado espectral; es una elipse
# azul. Y se juzga justo ahora porque hasta AUD-461 estos ecos **no se
# dibujaban en absoluto** en la máquina del jugador: la primera vez que se
# vieron fue la primera vez que se pudieron mirar.
#
# Cambia la técnica, no el diseño: mismas trayectorias, mismas ventanas,
# mismas respuestas (saltar / parar / esquivar). Se dibujan sobre una
# superficie con alfa y se componen sumando luz (`BLEND_RGBA_ADD`), que es lo
# que hace que una silueta se lea como aparición y no como pintura — la misma
# técnica de las ánimas del epílogo y de las brasas del círculo. Tres capas
# siempre: halo, cuerpo, núcleo claro. El halo es el borde difuso que un
# espíritu tiene y una primitiva no.


def _lienzo(w: int, h: int) -> pygame.Surface:
    return pygame.Surface((max(1, w), max(1, h)), pygame.SRCALPHA)


def _fundir(surface: pygame.Surface, capa: pygame.Surface,
            pos: tuple[int, int]) -> None:
    """Compone un eco sobre la escena, sumando luz."""
    surface.blit(capa, pos, special_flags=pygame.BLEND_RGBA_ADD)


def _halo(capa: pygame.Surface, centro: tuple[float, float], radio: float,
          color: tuple[int, int, int], fuerza: float = 1.0) -> None:
    """Resplandor de caída suave. Cuatro anillos bastan y son baratos."""
    cx, cy = int(centro[0]), int(centro[1])
    for i in range(4, 0, -1):
        r = int(radio * i / 4)
        if r <= 0:
            continue
        alfa = int(44 * fuerza * (1.0 - (i - 1) / 4.0)) + 6
        pygame.draw.circle(capa, (*color, max(0, min(255, alfa))), (cx, cy), r)


class EmbestidaDelVenado:
    """Una silueta de venado cruza la arena en línea recta, a media altura.

    Eco del CHARGE del venado (su firma en el bosque). Va a la altura del
    pecho del jugador de pie —ni rasante ni aérea— para que la respuesta sea
    saltar en el momento justo, no agacharse: agachado el pulso de la máscara
    ya castiga quedarse quieto, y dos ataques con la misma respuesta se
    pisarían.

    No se para con parry: es un cuerpo, no un proyectil. La respuesta es de
    tiempo, no de reflejos de botón.
    """

    TELEGRAFIADO = 0.8
    VELOCIDAD = 250.0
    ANCHO = 52
    ALTO = 26
    DANIO = 1.0

    def __init__(self, origen: pygame.Vector2, arena: pygame.Rect,
                 hacia_derecha: bool, altura_y: float | None = None,
                 retraso: float = 0.0) -> None:
        # Nace fuera del borde del que viene, a la altura del pecho — o a la
        # que pida la procesión de ANCIENT_CALL (tres pasadas a alturas
        # distintas, escalonadas con `retraso`: pasillos de esquive, no muro).
        #
        # AUD-483 — LA EMBESTIDA PASABA POR ENCIMA DEL JUGADOR SIEMPRE.
        #
        # Medido con un maniquí de pie en el suelo de la sala: 0 impactos en 9
        # embestidas. `arena.bottom - 58` con `ALTO`=26 pone la banda de daño
        # en [bottom-71, bottom-45], y el hurtbox del jugador de pie ocupa
        # [bottom-28, bottom]: quedaban 17 px de aire entre las dos. El
        # docstring decía «a la altura del pecho» y la aritmética la ponía por
        # encima de la cabeza — se escribió tomando `arena.bottom` por el
        # centro del jugador cuando es la línea de sus pies.
        #
        # Peor que no hacer daño: el ataque enseñaba lo contrario de lo que
        # telegrafía. Como sólo alcanzaba a quien estaba en el aire, la
        # respuesta óptima era NO saltar.
        #
        # `bottom - 20` deja la banda en [bottom-33, bottom-7]: 21 px de
        # solape con el hurtbox de pie —no se esquiva quedándose quieto— y su
        # techo a 33 px del suelo, muy por debajo de los ~160 px que alcanza
        # el salto, así que saltar sigue siendo la salida.
        self.y = float(arena.bottom - 20 if altura_y is None else altura_y)
        self.x = float(arena.left - self.ANCHO if hacia_derecha
                       else arena.right + self.ANCHO)
        self.dir = 1.0 if hacia_derecha else -1.0
        self._arena = arena
        self._t = -self.TELEGRAFIADO - retraso
        self.alive = True
        self.ya_golpeo = False

    @property
    def is_telegraphing(self) -> bool:
        return self._t < 0.0

    def update(self, dt: float) -> None:
        self._t += dt
        if self.is_telegraphing:
            return
        self.x += self.VELOCIDAD * self.dir * dt
        if (self.x < self._arena.left - self.ANCHO * 2
                or self.x > self._arena.right + self.ANCHO * 2):
            self.alive = False

    @property
    def rect(self) -> pygame.Rect | None:
        if self.is_telegraphing or not self.alive:
            return None
        return pygame.Rect(int(self.x), int(self.y - self.ALTO // 2),
                           self.ANCHO, self.ALTO)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        if not self.alive:
            return
        if self.is_telegraphing:
            # El aviso: el carril de la carrera se enciende desde el borde de
            # salida, con la marca creciendo hacia donde va a pasar el venado.
            # Es una línea de tierra levantada, no una fila de palotes: el
            # jugador tiene que leer LA ALTURA, que es lo que decide el salto.
            p = suave(1.0 + self._t / self.TELEGRAFIADO)
            bx = self._arena.left if self.dir > 0 else self._arena.right
            sx = int(bx - offset.x)
            sy = int(self.y - offset.y)
            largo = int(150 * p)
            capa = _lienzo(largo + 24, 40)
            base_y = 20
            for i in range(largo):
                q = i / max(1, largo)
                alfa = int(150 * (1.0 - q) * p)
                x = int(12 + self.dir * i) if self.dir > 0 else int(largo + 12 - i)
                pygame.draw.line(capa, (*AVISO, alfa),
                                 (x, base_y - 3), (x, base_y + 3), 1)
            # La cabeza del aviso: donde arranca el cuerpo.
            _halo(capa, (12 if self.dir > 0 else largo + 12, base_y),
                  9 * p, AVISO, 1.4)
            _fundir(surface, capa, (sx - 12, sy - base_y))
            return
        r = self.rect
        if r is None:
            return
        sx, sy = int(r.x - offset.x), int(r.y - offset.y)
        # Lienzo con margen para el halo y para la estela de atrás.
        MARGEN, ESTELA = 16, 40
        capa = _lienzo(r.w + MARGEN * 2 + ESTELA, r.h + MARGEN * 2)
        # El origen del cuerpo dentro del lienzo: la estela va detrás, así que
        # con dir>0 (va a la derecha) el cuerpo se corre a la derecha.
        ox = MARGEN + (ESTELA if self.dir > 0 else 0)
        oy = MARGEN
        cx, cy = ox + r.w / 2, oy + r.h / 2

        # 1. La estela: jirones que se deshacen detrás del sentido de marcha.
        for i in range(1, 6):
            q = i / 6.0
            jx = cx - self.dir * (r.w * 0.35 + i * 7)
            jy = cy + math.sin(self._t * 9.0 + i) * 3.0
            _halo(capa, (jx, jy), (1.0 - q) * 9 + 2, ECO_FRIO, 0.8 * (1.0 - q))

        # 2. EL GALOPE (AUD-474): el cuerpo sube y baja con la zancada, y se
        #    estira y encoge — un animal corriendo no es un óvalo rígido que
        #    se traslada. Cuatro zancadas por segundo, que es el trote de algo
        #    grande; sincronizado con el vaivén de la estela de arriba.
        zancada = math.sin(self._t * 25.0)
        cy += zancada * 2.0
        estirado = int(r.w * 0.06 * math.cos(self._t * 25.0))
        _halo(capa, (cx, cy), r.h * 0.95, ECO_FRIO, 1.0)
        cuerpo = pygame.Rect(ox - estirado, oy + 2 + int(zancada * 2.0),
                             r.w + estirado * 2, r.h - 4)
        pygame.draw.ellipse(capa, (*ECO_OSC, 200), cuerpo)
        pygame.draw.ellipse(capa, (*ECO_FRIO, 220), cuerpo.inflate(-8, -7))
        # 3. El pecho, lo más brillante: hacia donde embiste.
        pecho = pygame.Rect(0, 0, int(r.w * 0.34), max(4, r.h - 11))
        pecho.center = (int(cx + self.dir * r.w * 0.26), int(cy))
        pygame.draw.ellipse(capa, (*ECO_CLARO, 235), pecho)

        # 4. La cornamenta: tres puntas curvadas hacia atrás, que es lo que
        #    hace reconocible al venado de un vistazo (y lo que lo distingue
        #    del orbe de la serpiente cuando los dos cruzan la sala).
        base_x = cx + self.dir * r.w * 0.30
        base_y = cy - r.h * 0.34
        for k, (largo_p, alto_p) in enumerate(((16, 15), (13, 11), (9, 7))):
            x0 = base_x - self.dir * k * 5
            pygame.draw.lines(
                capa, (*ECO_CLARO, 210), False,
                [(x0, base_y),
                 (x0 - self.dir * largo_p * 0.45, base_y - alto_p * 0.7),
                 (x0 - self.dir * largo_p, base_y - alto_p)], 2)
        # 5. El ojo: un punto de luz que da dirección a la silueta.
        _halo(capa, (cx + self.dir * r.w * 0.30, cy - 3), 4, ECO_CLARO, 1.6)
        _fundir(surface, capa, (sx - ox, sy - oy))


class OrbeDeLaSerpiente:
    """Un orbe que serpentea hacia donde estaba el jugador al lanzarse.

    Eco del Rey Terciopelo. Lento a propósito (la ventana de parry es 0,2 s
    y contra algo rápido sería memoria, no lectura) y sinuoso porque una
    serpiente no viaja recta: el vaivén perpendicular es un seno sobre la
    dirección de avance (Unidad VI), y además hace que esquivarlo sin parar
    exija mirarlo hasta el final.

    Devuelto con parry vuela hacia su dueña y la TUMBA: la única manera de
    sacar a un guardián de la ronda un rato. La escena hace el retarget cada
    fotograma porque la guardiana deriva.
    """

    TELEGRAFIADO = 0.55
    VELOCIDAD = 95.0
    VELOCIDAD_DEVUELTO = 240.0
    RADIO = 8
    DANIO = 0.75
    VIDA = 8.0
    AMPLITUD = 22.0
    FRECUENCIA = 3.4

    def __init__(self, origen: pygame.Vector2, objetivo: pygame.Vector2,
                 guardian_idx: int) -> None:
        self.pos = pygame.Vector2(origen)
        d = pygame.Vector2(objetivo) - self.pos
        self.rumbo = d.normalize() if d.length() > 1 else pygame.Vector2(1, 0)
        self.guardian_idx = guardian_idx
        self._t = -self.TELEGRAFIADO
        self._fase = 0.0
        self.alive = True
        self.devuelta = False
        self._objetivo_devuelto = pygame.Vector2(origen)

    @property
    def is_telegraphing(self) -> bool:
        return self._t < 0.0

    def devolver(self, hacia: pygame.Vector2) -> None:
        if self.devuelta:
            return
        self.devuelta = True
        self._objetivo_devuelto = pygame.Vector2(hacia)

    def retarget(self, hacia: pygame.Vector2) -> None:
        """La dueña deriva; el orbe devuelto la sigue."""
        self._objetivo_devuelto = pygame.Vector2(hacia)

    def update(self, dt: float) -> None:
        self._t += dt
        if self.is_telegraphing:
            return
        # AUD-494 — EL ORBE DEVUELTO NO CADUCABA NUNCA.
        #
        # El mismo defecto que la gota de la Perla: el chequeo de `VIDA`
        # estaba después del `return` de la rama `devuelta`, así que un orbe
        # parado con parry que no alcanzase a su dueña (guardiana ya caída,
        # forma cambiada, `d.length() <= 1`) quedaba vivo indefinidamente —
        # medido: vivo a los 120 s con `VIDA` = 8. Y un orbe vivo conserva su
        # `rect`, o sea que la escena lo sigue recorriendo y puede tumbar a
        # una guardiana un minuto después de la parada que lo devolvió.
        if self._t > self.VIDA:
            self.alive = False
            return
        if self.devuelta:
            d = self._objetivo_devuelto - self.pos
            if d.length() > 1:
                self.pos += d.normalize() * self.VELOCIDAD_DEVUELTO * dt
            return
        self._fase += dt * self.FRECUENCIA
        perpendicular = pygame.Vector2(-self.rumbo.y, self.rumbo.x)
        self.pos += (self.rumbo * self.VELOCIDAD
                     + perpendicular * math.sin(self._fase) * self.AMPLITUD) * dt

    @property
    def rect(self) -> pygame.Rect | None:
        if self.is_telegraphing or not self.alive:
            return None
        r = self.RADIO
        return pygame.Rect(int(self.pos.x - r), int(self.pos.y - r), r * 2, r * 2)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        if not self.alive:
            return
        sx, sy = int(self.pos.x - offset.x), int(self.pos.y - offset.y)
        R = self.RADIO
        if self.is_telegraphing:
            # AUD-471 — el aviso del orbe es el que más importa de los tres:
            # es el ÚNICO parable, y el jugador tiene 0,2 s de ventana. Antes
            # era un círculo de 1 px que se encogía. Ahora: anillo que colapsa
            # + destello creciente en el centro, para que el ojo sepa DÓNDE
            # va a nacer sin tener que buscarlo.
            p = suave(1.0 + self._t / self.TELEGRAFIADO)
            radio = R + 10 * (1 - p)
            capa = _lienzo(int(radio * 4), int(radio * 4))
            c = (radio * 2, radio * 2)
            pygame.draw.circle(capa, (*AVISO, int(70 + 120 * p)), c,
                               int(radio), 2)
            _halo(capa, c, R * p * 1.3, AVISO, 1.2 * p)
            _fundir(surface, capa, (sx - int(radio * 2), sy - int(radio * 2)))
            return

        color = ECO_CLARO if self.devuelta else ECO_FRIO
        # La estela sinuosa: seis segmentos que se estrechan y se apagan, con
        # la ondulación de la propia trayectoria — una serpiente, no una fila
        # de círculos iguales. Devuelta, la estela desaparece: ya no serpentea,
        # va derecha a su dueña, y esa diferencia se lee.
        MARGEN = R * 3
        LARGO = 0 if self.devuelta else 58
        capa = _lienzo(int(MARGEN * 2 + LARGO), int(MARGEN * 2))
        atras = -self.rumbo if not self.devuelta else pygame.Vector2()
        perp = pygame.Vector2(-self.rumbo.y, self.rumbo.x)
        cx, cy = MARGEN + (LARGO if atras.x < 0 else 0), MARGEN
        for i in range(6, 0, -1):
            q = i / 6.0
            desfase = math.sin(self._fase - i * 0.7) * self.AMPLITUD * 0.06
            d = atras * (i * 8) + perp * desfase
            _halo(capa, (cx + d.x, cy + d.y), (1.0 - q) * 7 + 3,
                  color, 0.75 * (1.0 - q * 0.7))
        # El cuerpo: halo, disco y núcleo. Los rombos de la Terciopelo se
        # insinúan con dos marcas claras sobre el disco.
        _halo(capa, (cx, cy), R * 2.4, color, 1.25)
        pygame.draw.circle(capa, (*ECO_OSC, 215), (int(cx), int(cy)), R + 2)
        pygame.draw.circle(capa, (*color, 235), (int(cx), int(cy)), R)
        # AUD-474 — los rombos GIRAN alrededor del núcleo y el núcleo LATE.
        # El orbe es el único eco parable, así que tiene que pedir atención
        # de otra manera que los otros dos: no por su trayectoria, por su
        # pulso. El latido va al doble de la ondulación del cuerpo, que es lo
        # que lo hace ver «cargado» en vez de simplemente moverse.
        giro = self._t * 3.4
        for k in range(3):
            a = giro + k * 2.094                      # 120° entre rombos
            ex, ey = math.cos(a) * R * 0.5, math.sin(a) * R * 0.5
            rombo = [(cx + ex, cy + ey - R * 0.34),
                     (cx + ex + R * 0.3, cy + ey),
                     (cx + ex, cy + ey + R * 0.34),
                     (cx + ex - R * 0.3, cy + ey)]
            pygame.draw.polygon(capa, (*ECO_CLARO, 150), rombo)
        late = 1.0 + 0.35 * math.sin(self._t * 12.0)
        pygame.draw.circle(capa, (255, 255, 255, 205), (int(cx), int(cy)),
                           max(1, int(R / 3 * late)))
        _fundir(surface, capa, (sx - int(cx), sy - int(cy)))


class PicadaDelGavilan:
    """La sombra crece en el suelo; después cae la picada en diagonal.

    Eco del DIVE del gavilán. El aviso está en el SUELO y no en el aire —la
    sombra del ave que ya viene— porque es donde el jugador está mirando
    cuando esquiva. Marca la posición del jugador al iniciarse y NO corrige:
    moverse un paso a un lado basta, que es exactamente la respuesta que se
    quiere enseñar. Un ataque teledirigido aquí sería injusto: ya hay dos
    ecos más en la ronda.
    """

    TELEGRAFIADO = 0.8
    VELOCIDAD = 330.0
    RADIO = 11
    DANIO = 1.0

    def __init__(self, origen: pygame.Vector2, marca: pygame.Vector2) -> None:
        self.pos = pygame.Vector2(origen)
        self.marca = pygame.Vector2(marca)
        d = self.marca - self.pos
        self.rumbo = d.normalize() if d.length() > 1 else pygame.Vector2(0, 1)
        self._t = -self.TELEGRAFIADO
        self._recorrido = d.length()
        self._avance = 0.0
        self.alive = True
        self.ya_golpeo = False

    @property
    def is_telegraphing(self) -> bool:
        return self._t < 0.0

    def update(self, dt: float) -> None:
        self._t += dt
        if self.is_telegraphing:
            return
        paso = self.VELOCIDAD * dt
        self.pos += self.rumbo * paso
        self._avance += paso
        # Pasa la marca y sigue un poco más — el ave remonta y se disuelve.
        if self._avance > self._recorrido + 70:
            self.alive = False

    @property
    def rect(self) -> pygame.Rect | None:
        if self.is_telegraphing or not self.alive:
            return None
        r = self.RADIO
        return pygame.Rect(int(self.pos.x - r), int(self.pos.y - r), r * 2, r * 2)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        if not self.alive:
            return
        if self.is_telegraphing:
            # AUD-471 — la sombra que crece en el suelo, con el pulso del ave
            # acercándose. Sigue siendo una elipse porque una sombra ES una
            # elipse; lo que cambia es que ahora se lee como sombra: oscura,
            # de borde blando, con el aro de aviso latiendo encima.
            p = suave(1.0 + self._t / self.TELEGRAFIADO)
            w = int(12 + 30 * p)
            sx = int(self.marca.x - offset.x)
            sy = int(self.marca.y - offset.y)
            # La sombra oscurece: va con `BLEND_RGBA_SUB`, no sumando luz.
            oscura = _lienzo(w + 12, 22)
            for i in range(3, 0, -1):
                rr = pygame.Rect(0, 0, int(w * i / 3), int(9 * i / 3) + 3)
                rr.center = (oscura.get_width() // 2, 11)
                pygame.draw.ellipse(oscura, (26, 30, 40, int(70 * p)), rr)
            surface.blit(oscura, (sx - oscura.get_width() // 2, sy - 11),
                         special_flags=pygame.BLEND_RGBA_SUB)
            # Y encima, el aro de aviso que late con el compás del ataque.
            aro = _lienzo(w + 16, 26)
            marco = pygame.Rect(0, 0, w, 9)
            marco.center = (aro.get_width() // 2, 13)
            pygame.draw.ellipse(aro, (*AVISO, int(60 + 150 * p)), marco, 2)
            _halo(aro, marco.center, 5 * p, AVISO, 1.1 * p)
            _fundir(surface, aro, (sx - aro.get_width() // 2, sy - 13))
            return

        sx, sy = int(self.pos.x - offset.x), int(self.pos.y - offset.y)
        # El ave plegada, ahora con alas de verdad: cinco plumas por ala
        # abiertas hacia atrás del rumbo — la misma firma que el espíritu del
        # gavilán del cielo, para que se lea como «el mismo bicho que está
        # ahí arriba», no como un proyectil suelto.
        LADO = 78
        capa = _lienzo(LADO, LADO)
        c = pygame.Vector2(LADO / 2, LADO / 2)
        atras = -self.rumbo
        perp = pygame.Vector2(-self.rumbo.y, self.rumbo.x)
        # 1. La estela de la caída.
        for i in range(1, 5):
            q = i / 5.0
            _halo(capa, c + atras * (i * 8), (1 - q) * 8 + 2, ECO_FRIO,
                  0.7 * (1 - q))
        # 2. EL ALETEO (AUD-474): las alas se pliegan y se abren mientras cae.
        #    Un ave en picada no lleva las alas fijas — las ajusta, y ese
        #    movimiento es lo que la hace estar VIVA y no ser un proyectil.
        bate = 0.62 + 0.38 * abs(math.sin(self._t * 11.0))
        for lado in (-1, 1):
            for k in range(5):
                largo = (22 - k * 3) * bate
                raiz = c + atras * (4 + k * 2.4)
                punta = raiz + perp * lado * largo * 0.72 + atras * largo * 0.5
                pygame.draw.line(capa, (*ECO_FRIO, 190 - k * 18),
                                 (raiz.x, raiz.y), (punta.x, punta.y), 2)
        # 3. El cuerpo y la cabeza, que van por delante de todo.
        cuerpo = [c + self.rumbo * 13,
                  c + perp * 5 + atras * 9,
                  c + atras * 15,
                  c - perp * 5 + atras * 9]
        pygame.draw.polygon(capa, (*ECO_OSC, 215), [(p.x, p.y) for p in cuerpo])
        pygame.draw.polygon(capa, (*ECO_CLARO, 205),
                            [(p.x, p.y) for p in cuerpo], 2)
        # 4. La máscara ceremonial: lo más luminoso del gavilán, como en el
        #    espíritu del cielo (§3.4 — esa máscara es la que busca a Paburu).
        _halo(capa, c + self.rumbo * 8, 7, ECO_CLARO, 1.7)
        _fundir(surface, capa, (sx - LADO // 2, sy - LADO // 2))
