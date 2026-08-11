"""
Module: audio_manager
System: engine.audio
Academic Unit: N/A
Description: High-level audio manager for music playback and sound effects.
Never crashes on missing files — logs warning and continues silently.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pygame

from src.engine.audio.mixer_buses import (
    BUS_AMBIENTE,
    BUS_EFECTOS,
    BUS_MUSICA,
    BUS_VOZ,
    DUCK_EFECTO_SEGUNDOS,
    DUCK_NIVEL_EFECTO,
    Mezclador,
)
from src.engine.audio.sound_bank import SoundBank
from src.engine.core import settings

logger = logging.getLogger(__name__)

#: Distancia (píxeles de mundo) a la que un efecto espacial deja de oírse
#: (AUD-348). Dos pantallas y media: lo que está dentro de la cámara se oye
#: entero y lo que está a la vuelta de la esquina se va apagando, lineal.
RADIO_AUDIBLE_EFECTOS: float = 2_000.0

#: Volumen mínimo de un efecto **crítico**, por lejos que ocurra (AUD-369).
#:
#: `play_sfx_critico` agacha la música un 30 % para hacerle sitio al sonido.
#: Con el desvanecimiento de AUD-348 aplicado sin suelo, un cambio de fase de
#: jefe más allá de `RADIO_AUDIBLE_EFECTOS` dejaba la música hundida un segundo
#: **y ningún sonido que lo justificara**: el jugador no oye «algo lejos», oye
#: que la música se cae sin motivo. Peor que no haber hecho nada, porque el
#: ducking anuncia un sonido que no llega.
#:
#: Es un suelo y no una exención a propósito: el crítico se sigue alejando como
#: cualquier otro efecto —la distancia se nota— pero nunca por debajo de esto.
#: 0,35 es «se oye que pasó algo»; por debajo de 0,2 lo tapa la propia música
#: agachada al 70 %, y por encima de 0,5 deja de leerse como lejano.
SUELO_CRITICO: float = 0.35

class AudioManager:
    """Manages music and SFX playback. Graceful fallback on missing assets."""

    def __init__(self) -> None:
        if pygame.mixer.get_init() is not None:
            pygame.mixer.set_num_channels(16)
        self.sound_bank: SoundBank = SoundBank()
        self.sound_bank.load_all()
        self._current_music: str | None = None
        self._music_volume: float = 0.7
        self._sfx_volume: float = 1.0
        self._muted: bool = False
        # AUD-144 — buses de mezcla. `_music_volume` y `_sfx_volume` siguen
        # existiendo porque los leen las opciones y varias entregas; lo que
        # cambia es que ahora son la cara visible de dos buses, y que hay dos
        # buses más —voz y ambiente— que antes colgaban de «efectos».
        self.mezcla: Mezclador = Mezclador()

        # Dynamic music layers
        self._calm_channel: pygame.mixer.Channel | None = None
        self._combat_channel: pygame.mixer.Channel | None = None
        self._calm_sound: pygame.mixer.Sound | None = None
        self._combat_sound: pygame.mixer.Sound | None = None
        self._intensity: float = 0.0
        self._target_intensity: float = 0.0
        self._crossfade_speed: float = 1.0
        self._calm_volume: float = 1.0
        self._combat_volume: float = 0.0
        self._dynamic_music_active: bool = False

        # Ambient audio layers
        self._ambient_sound: pygame.mixer.Sound | None = None
        self._ambient_channel: pygame.mixer.Channel | None = None
        self._ambient_volume: float = 0.5
        self._ambient_active: bool = False
        self._ambient_sounds: dict[str, pygame.mixer.Sound] = {}

    # NOTE (AUD-022): play_dynamic_music / stop_dynamic_music /
    # set_music_intensity / update_dynamic_music used to live here. They were a
    # second, complete implementation of layered dynamic music that nothing ever
    # called — framework.audio.DynamicMusicSystem implements the same feature and
    # *is* wired into StageScene. Two rival implementations of one feature, one
    # of them dead, is worse than one: it doubles the surface that can rot and
    # makes it unclear which is authoritative. The dead copy has been removed.

    def play_music(self, path: str | Path, loops: int = -1, fundido_ms: int = 0) -> None:
        """Play background music. -1 loops = infinite. Falls back silently.

        `fundido_ms` funde la entrada de la pista (AUD-313): SDL_mixer no
        permite dos pistas de música a la vez, así que el crossfade completo no
        existe aquí; el fundido de entrada es lo que hace audible el cambio de
        intensidad en vez de un corte seco.
        """
        path_str = str(path)
        try:
            pygame.mixer.music.load(path_str)
            pygame.mixer.music.set_volume(0.0 if self._muted else self._music_volume)
            pygame.mixer.music.play(loops=loops, fade_ms=fundido_ms)
            self._current_music = path_str
        except (pygame.error, FileNotFoundError, OSError) as e:  # BUG-074 FIX: pygame.error no atrapa FileNotFoundError
            logger.warning("AudioManager: no se pudo cargar música %s: %s", path_str, e)

    def posicion_musica(self) -> float | None:
        """Segundos reproducidos de la pista actual, o `None` si no se sabe.

        AUD-137 (F6) — la fuente de verdad del reloj musical.

        `pygame.mixer.music.get_pos()` cuenta desde el último `play()` en
        milisegundos y devuelve -1 cuando no hay nada sonando. Devolver `None`
        en ese caso y no 0.0 es la diferencia entre «la música va por el
        principio» y «no hay música», y quien pregunta necesita distinguirlas:
        con `None` el reloj sigue con su propio tiempo en vez de quedarse
        clavado en el pulso cero para siempre.
        """
        if not self._mixer_listo() or self._current_music is None:
            return None
        try:
            ms = pygame.mixer.music.get_pos()
        except pygame.error:  # pragma: no cover - mezclador caído a mitad
            return None
        if ms is None or ms < 0:
            return None
        return ms / 1000.0

    @staticmethod
    def _mixer_listo() -> bool:
        """¿Hay un mezclador con el que hablar?

        AUD-089 — un aula sin tarjeta de sonido tumbaba el juego
        --------------------------------------------------------
        `play_music` ya envolvía sus llamadas en `try/except pygame.error`,
        pero `stop_music`, `pause_music` y `resume_music` no. Si
        `pygame.mixer.init()` falla —máquina sin dispositivo de audio, sesión
        remota, contenedor, laboratorio con el sonido deshabilitado— cualquier
        transición de escena que pare la música lanza
        ``pygame.error: mixer not initialized`` y el juego se cae.

        Es un fallo de disponibilidad, no de sonido: el jugador pierde la
        partida entera por no tener altavoces. Salió al añadir `on_exit` a una
        prueba de la pantalla de inicio.
        """
        return pygame.mixer.get_init() is not None

    def stop_music(self) -> None:
        """Stop current music playback."""
        if self._mixer_listo():
            pygame.mixer.music.stop()
        self._current_music = None
        self._stop_layered_channels()

    def _stop_layered_channels(self) -> None:
        """Silence the calm/combat crossfade channels if they are running.

        Retained from the removed dynamic-music layer (see the note above
        ``play_music``) because the channels are still allocated in ``__init__``
        and must be stopped when music stops.
        """
        self._dynamic_music_active = False
        if self._calm_channel:
            self._calm_channel.stop()
        if self._combat_channel:
            self._combat_channel.stop()
        self._calm_sound = None
        self._combat_sound = None

    def pause_music(self) -> None:
        """Pause current music."""
        if self._mixer_listo():
            pygame.mixer.music.pause()

    def resume_music(self) -> None:
        """Resume paused music."""
        if self._mixer_listo():
            pygame.mixer.music.unpause()

    def play_sfx(self, name: str, volume: float = 1.0) -> None:
        """Play a sound effect from the sound bank at the current SFX volume."""
        if self._muted:
            return
        self.sound_bank.play(name, volume=self.mezcla.ganancia(BUS_EFECTOS, volume))

    def play_stinger(self, name: str, volume: float = 0.8) -> None:
        """Play a music stinger (short SFX overlay) without interrupting music."""
        if self._muted:
            return
        # AUD-311 — por el bus como el resto: antes multiplicaba `_sfx_volume`
        # a mano y se saltaba `Mezclador.ganancia`, con lo que el stinger
        # ignoraba el volumen del bus de efectos (y el silencio del maestro).
        self.sound_bank.play(name, volume=self.mezcla.ganancia(BUS_EFECTOS, volume))

    def play_ambient(self, path: str | Path, volume: float = 0.5, loops: int = -1) -> None:
        """Play ambient audio layer (wind, rain, machinery) with crossfade."""
        try:
            if self._ambient_active:
                self.stop_ambient()
            path_str = str(path)
            if path_str in self._ambient_sounds:
                self._ambient_sound = self._ambient_sounds[path_str]
            else:
                self._ambient_sound = pygame.mixer.Sound(path_str)
                self._ambient_sounds[path_str] = self._ambient_sound
            self._ambient_channel = pygame.mixer.find_channel()
            if self._ambient_channel:
                self._ambient_channel.play(self._ambient_sound, loops=loops)
                self._ambient_volume = max(0.0, min(1.0, volume))
                self._ambient_active = True
                if not self._muted:
                    self._ambient_channel.set_volume(self._ambient_volume * self._sfx_volume)
        except (pygame.error, FileNotFoundError, OSError) as e:
            logger.warning("AudioManager: no se pudo cargar audio ambiental: %s", e)
            self._ambient_active = False

    def stop_ambient(self) -> None:
        """Stop ambient audio layer."""
        self._ambient_active = False
        if self._ambient_channel:
            self._ambient_channel.stop()
        self._ambient_sound = None
        self._ambient_channel = None

    def set_ambient_volume(self, volume: float) -> None:
        """Volumen del ambiente, de 0 a 1.

        AUD-149: lo llama `ajustar_bus(BUS_AMBIENTE)`. Llevaba meses escrito y
        sin usar, con el ambiente colgando del volumen de efectos.
        """
        self._ambient_volume = max(0.0, min(1.0, volume))
        if self._ambient_channel and self._ambient_active and not self._muted:
            self._ambient_channel.set_volume(self._ambient_volume * self._sfx_volume)

    def crossfade_ambient(self, path: str | Path, duration: float = 2.0, volume: float = 0.5) -> None:
        """Crossfade from current ambient to new ambient sound."""
        if self._muted:
            return
        old_channel = self._ambient_channel
        path_str = str(path)
        try:
            if path_str in self._ambient_sounds:
                new_sound = self._ambient_sounds[path_str]
            else:
                new_sound = pygame.mixer.Sound(path_str)
                self._ambient_sounds[path_str] = new_sound
            # Fade out old channel regardless of whether new channel is available
            if old_channel is not None:
                old_channel.fadeout(int(duration * 1000))
            new_channel = pygame.mixer.find_channel()
            if new_channel is not None:
                new_channel.play(new_sound, loops=-1)
                new_channel.set_volume(volume * self._sfx_volume)
                self._ambient_sound = new_sound
                self._ambient_channel = new_channel
                self._ambient_volume = volume
                self._ambient_active = True
        # AUD-411 — la misma red que `play_ambient` (línea ~217): `Sound` con
        # un `.wav` que se borró o se volvió ilegible lanza
        # `FileNotFoundError`/`OSError`, no `pygame.error`. La gemela lo
        # capturaba y degradaba con un aviso; ésta dejaba escapar el fallo a
        # la transición de escena.
        except (pygame.error, FileNotFoundError, OSError) as e:
            logger.warning("AudioManager: no se pudo crossfade audio ambiental: %s", e)
            self._ambient_active = False

    def play_sfx_at(self, name: str, world_x: float, screen_center_x: float | None = None,
                    volume: float = 1.0, suelo: float = 0.0) -> None:
        """Play SFX with stereo pan based on X position relative to screen center.

        AUD-348 — el sonido se **desvanece con la distancia**, no sólo se
        desplaza. Antes, un enemigo dos pantallas a la izquierda sonaba a la
        misma potencia que uno a tu lado: el pan lo movía, la mezcla no lo
        callaba, y un combate con varios emisores fuera de cámara se oía como
        una pared de ruido que estorbaba a lo que de verdad estaba pasando.
        El desvanecimiento es lineal hasta el radio audible y cero después;
        lo que está en pantalla se oye entero, lo que no está, se acerca.
        """
        if self._muted:
            return
        if screen_center_x is None or screen_center_x <= 0:
            screen_center_x = settings.INTERNAL_WIDTH / 2.0
        pan = max(-1.0, min(1.0, (world_x - screen_center_x) / screen_center_x))
        left = 1.0 - max(0.0, pan)
        right = 1.0 + min(0.0, pan)
        distancia = abs(world_x - screen_center_x)
        # AUD-369 — `suelo` lo pone quien reproduce, no esta función: sólo la
        # llamada sabe si el sonido es prescindible. Por defecto 0, o sea el
        # desvanecimiento completo de AUD-348 para todo lo demás.
        atenuacion = max(suelo, 1.0 - distancia / RADIO_AUDIBLE_EFECTOS)
        self.sound_bank.play(
            name, volume=self.mezcla.ganancia(BUS_EFECTOS, volume * atenuacion),
            pan=(left, right))

    # ── AUD-144: buses y ducking ──────────────────────────────────
    def play_voz(self, name: str, volume: float = 1.0,
                 duracion_duck: float = 0.0) -> None:
        """Reproduce una línea de voz y **aparta la música**.

        Es el único método que agacha la música por su cuenta, y por eso
        existe: si el ducking hubiera que pedirlo aparte, alguien se olvidaría
        en la mitad de las líneas y la mezcla sería distinta según la escena.
        """
        self.mezcla.agachar_musica(duracion_duck)
        self._aplicar_volumen_de_musica()
        if self.sound_bank is not None:
            self.sound_bank.play(name, volume=self.mezcla.ganancia(BUS_VOZ, volume))

    def play_sfx_critico(self, name: str, volume: float = 1.0,
                         world_x: float | None = None,
                         screen_center_x: float | None = None) -> None:
        """Un efecto que **se lleva por delante a la música** — AUD-284.

        La muerte de un jefe, un logro, el final de un escenario. Hasta ahora el
        ducking sólo lo disparaba `play_voz`: el mecanismo estaba entero y
        ningún efecto lo usaba, así que el momento más ruidoso de la partida era
        justo donde peor se oía lo importante.

        Baja la música un 30 % durante un segundo —no al 35 % como una voz—
        porque bajo un jefe que cae la música es parte del momento: se le hace
        hueco, no se la apaga.
        """
        self.mezcla.agachar_musica(DUCK_EFECTO_SEGUNDOS, nivel=DUCK_NIVEL_EFECTO)
        self._aplicar_volumen_de_musica()
        if world_x is not None:
            # AUD-369 — con suelo: este efecto acaba de agachar la música y
            # tiene que llegar.
            self.play_sfx_at(name, world_x, screen_center_x, volume=volume,
                             suelo=SUELO_CRITICO)
        else:
            self.play_sfx(name, volume=volume)

    def agachar_musica(self, segundos: float = 0.0) -> None:
        self.mezcla.agachar_musica(segundos)
        self._aplicar_volumen_de_musica()

    def soltar_musica(self) -> None:
        self.mezcla.soltar_musica()

    def volumen_de_bus(self, bus: str) -> float:
        return self.mezcla.volumen_de(bus)

    def ajustar_bus(self, bus: str, volumen: float) -> None:
        self.mezcla.ajustar(bus, volumen)
        if bus == BUS_MUSICA:
            self._music_volume = self.mezcla.volumen_de(BUS_MUSICA)
            self._aplicar_volumen_de_musica()
        elif bus == BUS_EFECTOS:
            self._sfx_volume = self.mezcla.volumen_de(BUS_EFECTOS)
        elif bus == BUS_AMBIENTE:
            # AUD-149: por `set_ambient_volume` y no tocando el canal a mano.
            # Ese método existía desde hacía meses sin que nadie lo llamara, y
            # además sabe cosas que aquí habría que repetir: si hay ambiente
            # sonando y si el juego está silenciado.
            self.set_ambient_volume(self.mezcla.volumen_de(BUS_AMBIENTE))

    def _aplicar_volumen_de_musica(self) -> None:
        """Lleva el volumen calculado al mezclador de SDL."""
        if not self._mixer_listo():
            return
        try:
            pygame.mixer.music.set_volume(self.mezcla.ganancia(BUS_MUSICA))
        except pygame.error:  # pragma: no cover - mezclador caído a mitad
            pass

    def update(self, dt: float) -> None:
        """Mueve el *ducking*. **Con `dt` real**, nunca escalado.

        El tiempo bala ralentiza el mundo; la mezcla no. Si esto se alimentara
        con el `dt` del juego, una ralentización dejaría la música agachada el
        triple de tiempo.
        """
        antes = self.mezcla.factor_de_duck
        self.mezcla.update(dt)
        if self.mezcla.factor_de_duck != antes:
            self._aplicar_volumen_de_musica()

    def set_music_volume(self, volume: float) -> None:
        """Set music volume (0.0 to 1.0).

        AUD-144: escribe en el bus, no en un campo suelto. Si los dos vivieran
        por separado, mover el deslizador de opciones dejaría el bus a lo suyo
        y el *ducking* calcularía sobre el volumen equivocado.

        AUD-245: delega en `ajustar_bus` en vez de repetir sus tres pasos. Eran
        el mismo procedimiento escrito dos veces —ajustar la mezcla, releer el
        bus, aplicar— y `ajustar_bus` no lo llamaba nadie: la mitad genérica del
        sistema de buses estaba muerta mientras dos casos particulares la
        reimplementaban al lado. Dos copias de una regla es una que se queda
        atrás.
        """
        self.ajustar_bus(BUS_MUSICA, max(0.0, min(1.0, volume)))

    def set_sfx_volume(self, volume: float) -> None:
        """Set SFX volume (0.0 to 1.0). AUD-245: ídem, por `ajustar_bus`."""
        self.ajustar_bus(BUS_EFECTOS, max(0.0, min(1.0, volume)))

    def toggle_mute(self) -> None:
        """Toggle mute on/off."""
        self._muted = not self._muted
        self.mezcla.silencio = self._muted
        # AUD-311 — por la composición del bus, no a mano: `ganancia(BUS_MUSICA)`
        # ya devuelve 0 con el silencio puesto, y además respeta el *ducking*
        # vivo. Antes, desmutear con un diálogo abierto devolvía la música a
        # pleno volumen a pesar de que estuviera agachada.
        self._aplicar_volumen_de_musica()
        if self._ambient_channel:
            self._ambient_channel.set_volume(0.0 if self._muted else self._ambient_volume * self._sfx_volume)

    @property
    def music_volume(self) -> float:
        return self._music_volume

    @music_volume.setter
    def music_volume(self, value: float) -> None:
        self.set_music_volume(value)

    @property
    def sfx_volume(self) -> float:
        return self._sfx_volume

    @sfx_volume.setter
    def sfx_volume(self, value: float) -> None:
        self.set_sfx_volume(value)

    @property
    def is_muted(self) -> bool:
        return self._muted

    @property
    def current_music(self) -> str | None:
        return self._current_music
