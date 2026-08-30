# Autor: Alejandro Josué Rodríguez Zamora
# Stage 4-2 «El Gran Shamán Paburu» — Legacy of InFest
"""
Module: intro
System: stages.boss_paburu
Academic Unit: VI (interpolación y easing), V (color e iluminación)
Description: Secuencia de entrada de El Gran Shaman Paburu — Stage 4-2.

POR QUÉ EXISTE
El combate arrancaba en seco: se cargaba la escena y la cabeza ya estaba
ahí, encendida, atacando. El GDD §4 describe otra cosa — Paburu aparece
DORMIDO, con los ojos cerrados, y despierta cuando John y Jin entran al
cementerio. Ese despertar es su presentación y no estaba en ningún lado.

CÓMO ESTÁ HECHO
Sobre el `CutsceneSystem` del motor (`framework/stage/cutscene_system.py`),
que ya define el contrato `CutsceneAction`: `start()`, `update(dt) -> bool`
—devuelve True al terminar— y `draw(surface)`. `CutsceneScript` las corre
en orden. No se modifica nada del framework: solo se heredan acciones
nuevas, que es justamente el punto de extensión que el sistema ofrece.

Es el mismo patrón que usa `stages/stage0/stage0.py` para su intro, así
que un lector del proyecto ya lo conoce.

LA SECUENCIA
    1. El silencio     — la Sala del Juicio casi a oscuras, solo rescoldos.
    2. El despertar    — los cuatro braseros se encienden uno a uno.
    3. Los ojos        — la piedra abre los ojos y nace el aura.
    4. El nombre       — la placa con el título.

Se salta entera con ESC.

AUDITORÍA POST-CATACUMBA (tarea #43)
La secuencia se escribió cuando la pelea era en el círculo de la
superficie y la mudanza a la catacumba obligó a revisarla entera — la
lección de PAB-07 aplicada a tiempo. El movimiento salió ileso: todas
las alturas son RELATIVAS al ancla del jefe (`Aparicion` sube 150 px
desde donde esté, `Transformacion` vuelve a `_anchor`), así que la
coreografía funciona a cualquier coordenada del mundo. Lo que sí estaba
roto era el GUION: dos líneas señalaban cosas del círculo de arriba
—«las marcas bajo sus pies», «el del centro es Kavë»— que en la Sala no
existen; ahora señalan el columbario, que es lo que el jugador tiene
delante. Ver la nota sobre LINEAS.

NOTA SOBRE `CutsceneScript.draw`
El motor dibuja la acción actual **y todas las que vienen después**
(`for i in range(self._index, len(...))`). Por eso cada acción de acá lleva
su bandera `_activa` y no pinta nada hasta que le toca: sin eso, la placa
del título aparecería desde el primer frame.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.framework.stage.cutscene_system import CutsceneAction
from src.stages.boss_paburu.boss_paburu import FORM_SPIRIT, FORM_STONE

if TYPE_CHECKING:
    from src.stages.boss_paburu.boss_paburu import BossPaburu
    from src.stages.boss_paburu.boss_paburu_scene import BossPaburuScene


def suave(t: float) -> float:
    """Smoothstep 3t² − 2t³ (Unidad VI).

    Las rampas lineales delatan que hay un temporizador detrás: el brillo
    sube a velocidad constante y arranca y frena de golpe. Smoothstep tiene
    derivada nula en los dos extremos, así que cada tramo entra y sale sin
    quiebre. Es la misma función que usa el ruido de los tilesets.
    """
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


class AccionBase(CutsceneAction):
    """Acción con duración y bandera de actividad."""

    def __init__(self, duracion: float) -> None:
        self._duracion = max(1e-6, duracion)
        self._t = 0.0
        self._activa = False

    def start(self) -> None:
        self._t = 0.0
        self._activa = True

    def update(self, dt: float) -> bool:
        self._t += dt
        self._aplicar(min(1.0, self._t / self._duracion))
        if self._t >= self._duracion:
            self._activa = False
            return True
        return False

    def _aplicar(self, u: float) -> None:
        """`u` va de 0 a 1 a lo largo de la acción."""


class Penumbra(AccionBase):
    """Lleva la luz ambiente de un valor a otro."""

    def __init__(self, escena: BossPaburuScene, desde: float, hasta: float,
                 duracion: float) -> None:
        super().__init__(duracion)
        self._escena = escena
        self._desde, self._hasta = desde, hasta

    def _aplicar(self, u: float) -> None:
        k = suave(u)
        self._escena._lighting.ambient_brightness = (
            self._desde + (self._hasta - self._desde) * k
        )


class EncenderCuenco(AccionBase):
    """Prende un cuenco de fuego y sube un poco la luz de la sala.

    Cada cuenco que prende aporta su parte: la arena se va revelando por
    partes en vez de aparecer iluminada de una vez.
    """

    def __init__(self, escena: BossPaburuScene, indice: int,
                 ambiente_final: float, duracion: float = 0.45) -> None:
        super().__init__(duracion)
        self._escena = escena
        self._i = indice
        self._ambiente_final = ambiente_final
        self._ambiente_inicial = 0.0

    def start(self) -> None:
        super().start()
        self._ambiente_inicial = self._escena._lighting.ambient_brightness

    def _aplicar(self, u: float) -> None:
        k = suave(u)
        if self._i < len(self._escena._braziers):
            self._escena._braziers[self._i].intensity = 0.95 * k
        self._escena._lighting.ambient_brightness = (
            self._ambiente_inicial
            + (self._ambiente_final - self._ambiente_inicial) * k
        )


class AbrirOjos(AccionBase):
    """La piedra abre los ojos: `intro_eyes` de 0 a 1."""

    def __init__(self, boss: BossPaburu, duracion: float = 1.1) -> None:
        super().__init__(duracion)
        self._boss = boss

    def start(self) -> None:
        super().start()
        self._boss.intro_eyes = 0.0

    def _aplicar(self, u: float) -> None:
        self._boss.intro_eyes = suave(u)


class Placa(AccionBase):
    """La placa con el nombre del jefe: entra, se sostiene y sale.

    Se dibuja acá y no con el `ScreenBanner` del motor porque el banner
    tiene su propio tiempo y su propia animación, y no se puede sincronizar
    con el resto de la secuencia.
    """

    COL_TITULO = (232, 226, 210)
    COL_SUB = (0, 200, 100)
    COL_LINEA = (232, 177, 44)

    def __init__(self, titulo: str, subtitulo: str, duracion: float = 2.4,
                 ancho: int = 800, alto: int = 600) -> None:
        super().__init__(duracion)
        self._titulo, self._sub = titulo, subtitulo
        self._w, self._h = ancho, alto
        self._alpha = 0.0
        self._f_titulo: pygame.font.Font | None = None
        self._f_sub: pygame.font.Font | None = None

    def _fuentes(self) -> None:
        if self._f_titulo is None:
            self._f_titulo = pygame.font.Font(None, 46)
            self._f_sub = pygame.font.Font(None, 20)

    def _aplicar(self, u: float) -> None:
        # Entra en el primer 25 %, se sostiene, y sale en el último 30 %.
        if u < 0.25:
            self._alpha = suave(u / 0.25)
        elif u > 0.70:
            self._alpha = 1.0 - suave((u - 0.70) / 0.30)
        else:
            self._alpha = 1.0

    def draw(self, surface: pygame.Surface) -> None:
        if not self._activa or self._alpha <= 0.01:
            return
        self._fuentes()
        assert self._f_titulo is not None and self._f_sub is not None

        titulo = self._f_titulo.render(self._titulo, True, self.COL_TITULO)
        sub = self._f_sub.render(self._sub, True, self.COL_SUB)
        cx = self._w // 2
        cy = int(self._h * 0.38)

        capa = pygame.Surface((self._w, 120), pygame.SRCALPHA)
        # Banda oscura detrás: sin ella el texto claro se pierde contra la
        # luna y contra la piedra clara de las cornisas.
        pygame.draw.rect(capa, (10, 6, 16, 205), (0, 18, self._w, 84))
        pygame.draw.line(capa, (*self.COL_LINEA, 220), (0, 18), (self._w, 18))
        pygame.draw.line(capa, (*self.COL_LINEA, 220), (0, 101), (self._w, 101))
        capa.blit(titulo, (cx - titulo.get_width() // 2, 34))
        capa.blit(sub, (cx - sub.get_width() // 2, 76))
        capa.set_alpha(int(255 * self._alpha))
        surface.blit(capa, (0, cy - 60))


class Aparicion(AccionBase):
    """Paburu se materializa en su forma real antes de la pelea.

    GDD §2.1: las cuatro formas son intentos de juzgar sin repetir el error
    que cometió con Kavë. La Forma 1 juzga **sin mirar**, con los ojos
    cerrados, "como juzgó a Kavë". Que el jugador vea primero el rostro y
    después la piedra convierte esa piedra en lo que el lore dice que es:
    no un monstruo, sino un hombre escondiéndose de su propio juicio.

    Se reutiliza la hoja de sprites de la Forma 4 cambiando `current_phase`;
    no hace falta arte nuevo.
    """

    # Cuánto se eleva sobre su posición de combate mientras habla. La caja
    # de diálogo ocupa la franja de abajo: si se queda en el suelo, el
    # jugador escucha a Paburu sin verle la cara, que es justo lo único que
    # esta escena existe para mostrar.
    ALTURA = 150.0

    def __init__(self, boss: BossPaburu, duracion: float = 1.4) -> None:
        super().__init__(duracion)
        self._boss = boss
        self._suelo = 0.0

    def start(self) -> None:
        super().start()
        self._suelo = self._boss.position.y
        self._boss.current_phase = FORM_SPIRIT
        self._boss.intro_eyes = 0.0

    def _aplicar(self, u: float) -> None:
        k = suave(u)
        # El aura crece con la aparición: se materializa desde la luz...
        self._boss.intro_eyes = k
        # ...y a la vez asciende.
        self._boss.position.y = self._suelo - self.ALTURA * k
        self._boss.rect.y = int(self._boss.position.y)


class Dialogo(AccionBase):
    """Una línea de Paburu, escrita a máquina.

    No se usa el `DialogueAction` del motor: está pensado para conversación
    con NPC —caja chica abajo, fuente de 14 px y un `[ENTER]` esperando— y
    acá hace falta texto centrado, con tiempo propio, que corra sincronizado
    con la aparición y la transformación. Sí se hereda de `CutsceneAction`,
    que es el punto de extensión previsto.

    El efecto de máquina de escribir no es adorno: obliga a leer al ritmo
    que marca el personaje. Paburu está aterrado, no apurado.
    """

    COL_NOMBRE = (0, 200, 100)
    COL_TEXTO = (236, 230, 214)

    def __init__(self, texto: str, duracion: float = 3.2,
                 ancho: int = 800, alto: int = 600) -> None:
        super().__init__(duracion)
        self._texto = texto
        self._w, self._h = ancho, alto
        self._visibles = 0
        self._alpha = 1.0
        self._f_txt: pygame.font.Font | None = None
        self._f_nom: pygame.font.Font | None = None

    def update(self, dt: float) -> bool:
        """ENTER adelanta: primero completa la línea, después pasa a la
        siguiente. Sin esto la escena dura veinte segundos fijos y en una
        demostración de tres minutos eso es un tercio del tiempo."""
        pulsadas = pygame.key.get_pressed()
        if pulsadas[pygame.K_RETURN] or pulsadas[pygame.K_SPACE]:
            if self._visibles < len(self._texto):
                self._t = self._duracion * 0.55      # completa el texto
            else:
                self._t = self._duracion             # pasa de línea
        return super().update(dt)

    def _aplicar(self, u: float) -> None:
        # Escribe durante el primer 55 % y se desvanece en el último 15 %.
        self._visibles = int(len(self._texto) * min(1.0, u / 0.55))
        self._alpha = 1.0 if u < 0.85 else 1.0 - suave((u - 0.85) / 0.15)

    def draw(self, surface: pygame.Surface) -> None:
        if not self._activa or self._alpha <= 0.01:
            return
        if self._f_txt is None:
            self._f_txt = pygame.font.Font(None, 26)
            self._f_nom = pygame.font.Font(None, 18)
        assert self._f_nom is not None

        texto = self._f_txt.render(self._texto[:self._visibles], True, self.COL_TEXTO)
        nombre = self._f_nom.render("PABURU", True, self.COL_NOMBRE)

        alto_caja = 76
        capa = pygame.Surface((self._w, alto_caja), pygame.SRCALPHA)
        capa.fill((8, 5, 14, 215))
        pygame.draw.line(capa, (0, 200, 100, 150), (0, 0), (self._w, 0))
        capa.blit(nombre, (40, 12))
        capa.blit(texto, (40, 36))
        capa.set_alpha(int(255 * self._alpha))
        surface.blit(capa, (0, self._h - alto_caja - 24))


class Transformacion(AccionBase):
    """El espíritu se apaga y queda la cabeza de piedra.

    Es el gesto que resume al personaje: puede mirar de frente, y elige no
    hacerlo. La piedra no es su forma verdadera, es donde se esconde.
    """

    def __init__(self, escena: BossPaburuScene, boss: BossPaburu,
                 duracion: float = 1.6) -> None:
        super().__init__(duracion)
        self._escena = escena
        self._boss = boss
        self._cambiado = False
        self._alto = 0.0
        self._suelo = 0.0

    def start(self) -> None:
        super().start()
        self._alto = self._boss.position.y
        self._suelo = float(self._boss._anchor.y)

    def _aplicar(self, u: float) -> None:
        # Desciende hasta su posición de combate mientras se apaga.
        k = suave(min(1.0, u / 0.45))
        self._boss.position.y = self._alto + (self._suelo - self._alto) * k
        self._boss.rect.y = int(self._boss.position.y)
        if u < 0.45:
            # Se apaga: el aura y los ojos se van a cero.
            self._boss.intro_eyes = 1.0 - suave(u / 0.45)
        else:
            if not self._cambiado:
                self._cambiado = True
                self._boss.current_phase = FORM_STONE
                self._escena._set_phase_light(0)
            # La piedra despierta: los ojos vuelven, ahora ciegos.
            self._boss.intro_eyes = suave((u - 0.45) / 0.55)

    def draw(self, surface: pygame.Surface) -> None:
        if not self._activa:
            return
        # Destello blanco en el instante del cambio, para tapar el corte
        # entre las dos hojas de sprites.
        d = abs(self._t / self._duracion - 0.45)
        if d < 0.12:
            flash = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            flash.fill((236, 255, 244, int(150 * (1.0 - d / 0.12))))
            surface.blit(flash, (0, 0))


# ── El texto ──────────────────────────────────────────────────────
# Sale del lore del GDD §2.1, §2.2 y §2.3. Paburu **no está furioso**:
# está aterrado de volver a equivocarse. El orden es: la espera, los
# guardianes, los nombres de los nichos, Kavë, y la decisión de cerrar los
# ojos —que es exactamente lo que el jugador va a pelear en la Forma 1—.
#
# La línea de los guardianes ANUNCIA, no describe. Antes decía "los tres
# que miran desde arriba", porque estaban ahí en el cielo desde el primer
# frame; ahora no aparecen hasta la Forma 2, así que señalarlos sería
# señalar un techo vacío. Decir "aún no me atrevo a llamarlos" hace dos
# cosas: explica por qué no están, y convierte su aparición en la Máscara
# en el cumplimiento de algo que el jugador ya escuchó.
#
# REESCRITURA POST-CATACUMBA (#43): las líneas 3 y 4 señalaban el círculo
# de la superficie — «las marcas bajo sus pies» eran las marcas del
# círculo sorteado, y «el del centro» su marca central. En la Sala del
# Juicio no hay ninguna de las dos; lo que hay es el COLUMBARIO: los
# nichos en filas tallados en el muro, a la vista durante toda la charla.
# Ahora las líneas señalan eso. El giro de Kavë mejora con la mudanza:
# su nombre NO está en los nichos porque ella no murió esperando — fue
# juzgada. Es la diferencia exacta que atormenta a Paburu, y antes la
# línea no la decía.
LINEAS = (
    "Cuatro siglos esperé a alguien digno... y cuatro siglos temí que llegara.",
    "Tuve tres guardianes. Llevan siglos esperándome, y aún no me atrevo a llamarlos.",
    "Estos nichos guardan nombres. Portadores que murieron esperando su prueba.",
    "Hay un nombre que no está en los muros: Kavë. A ella sí la juzgué. Y me equivoqué.",
    "No confío en mis ojos. Los cerraré, como los cerré con ella.",
    "Si sobreviven a mi error... les mostraré mi rostro.",
)


def construir(escena: BossPaburuScene, boss: BossPaburu,
              ambiente_final: float) -> list[CutsceneAction]:
    """Arma la lista de acciones de la entrada.

    `ambiente_final` es la luz de la Forma 1: la secuencia termina
    exactamente en el valor con el que sigue el combate, así que no hay
    salto al devolver el control.
    """
    paso = ambiente_final / 4.0
    acciones: list[CutsceneAction] = [
        # 1. El silencio. La Sala queda casi negra y se sostiene un
        #    instante: sin esta pausa el resto no se lee como un despertar.
        Penumbra(escena, escena._lighting.ambient_brightness, 0.18, 0.7),
        # 2. El despertar, un cuenco por vez.
        EncenderCuenco(escena, 0, 0.18 + paso),
        EncenderCuenco(escena, 1, 0.18 + paso * 2),
        EncenderCuenco(escena, 2, 0.18 + paso * 3),
        EncenderCuenco(escena, 3, ambiente_final),
        # 3. Se muestra como fue en vida.
        Aparicion(boss),
        # 4. Habla. Es lo único que dice en toda la pelea.
        *[Dialogo(t) for t in LINEAS],
        # 5. Se esconde en la piedra.
        Transformacion(escena, boss),
        # 6. El nombre.
        Placa("EL GRAN SHAMAN PABURU", "STAGE 4-2   ·   LA CABEZA DE PIEDRA"),
    ]
    return acciones
