"""
Buses de mezcla y *ducking* — AUD-144.

Hasta ahora había dos volúmenes, música y efectos, y todo lo demás colgaba de
uno de los dos. Con eso no se puede resolver el problema básico de la mezcla
de un juego: **que la voz se oiga**. Subirla la deja gritando en las escenas
tranquilas; bajar la música la deja inaudible en las de acción.

El *ducking* —agachar la música mientras alguien habla— es el truco más viejo
de la radio y el que más se nota: sin él, el jugador sube el volumen para
seguir el diálogo y se lleva un susto con el siguiente golpe.

Lo que estas pruebas defienden
-------------------------------
1. **Un solo sitio multiplica los volúmenes.** Maestro × bus × el que pida
   quien reproduce. Si hubiera dos, el silencio o el *duck* se olvidarían en
   la mitad de las llamadas.
2. **Bajar rápido y subir despacio.** Bajar lento se come la primera palabra;
   subir de golpe suena a fallo técnico.
3. **El deslizador de opciones y el bus son lo mismo.** Si vivieran por
   separado, mover el volumen de música dejaría el *duck* calculando sobre el
   valor equivocado.
"""
from __future__ import annotations

import pytest

from src.engine.audio import mixer_buses
from src.engine.audio.mixer_buses import (
    BUS_AMBIENTE,
    BUS_EFECTOS,
    BUS_MUSICA,
    BUS_VOZ,
    DUCK_ATAQUE,
    DUCK_NIVEL,
    DUCK_RECUPERACION,
    Mezclador,
)


class TestLosCuatroBuses:
    def test_estan_los_cuatro(self) -> None:
        m = Mezclador()
        for bus in (BUS_MUSICA, BUS_EFECTOS, BUS_VOZ, BUS_AMBIENTE):
            assert 0.0 <= m.volumen_de(bus) <= 1.0

    def test_la_musica_arranca_por_debajo_de_los_efectos(self) -> None:
        """Un golpe tiene que oírse por encima de la canción, o el combate
        se vuelve sordo."""
        m = Mezclador()
        assert m.volumen_de(BUS_MUSICA) < m.volumen_de(BUS_EFECTOS)

    def test_la_ganancia_es_el_producto_de_los_tres(self) -> None:
        m = Mezclador()
        m.maestro = 0.5
        m.ajustar(BUS_EFECTOS, 0.8)
        assert m.ganancia(BUS_EFECTOS, 0.5) == pytest.approx(0.5 * 0.8 * 0.5)

    def test_nunca_se_pasa_de_uno(self) -> None:
        m = Mezclador()
        m.ajustar(BUS_EFECTOS, 1.0)
        assert m.ganancia(BUS_EFECTOS, 10.0) == 1.0

    def test_nunca_baja_de_cero(self) -> None:
        m = Mezclador()
        assert m.ganancia(BUS_EFECTOS, -5.0) == 0.0

    def test_el_silencio_lo_apaga_todo(self) -> None:
        m = Mezclador()
        m.silencio = True
        assert all(m.ganancia(b) == 0.0 for b in
                   (BUS_MUSICA, BUS_EFECTOS, BUS_VOZ, BUS_AMBIENTE))

    def test_un_bus_que_no_existe_no_rompe_nada(self) -> None:
        m = Mezclador()
        m.ajustar("bus_inventado", 0.5)          # avisa y sigue
        assert m.ganancia("bus_inventado") <= 1.0


class TestElDucking:
    def _agachada(self, m: Mezclador, segundos: float) -> None:
        pasos = int(segundos * 60)
        for _ in range(pasos):
            m.update(1 / 60)

    def test_al_pedirlo_la_musica_baja(self) -> None:
        m = Mezclador()
        antes = m.ganancia(BUS_MUSICA)
        m.agachar_musica()
        self._agachada(m, 0.5)
        assert m.ganancia(BUS_MUSICA) < antes * 0.5

    def test_baja_hasta_el_nivel_declarado_y_no_mas(self) -> None:
        m = Mezclador()
        m.agachar_musica()
        self._agachada(m, 2.0)
        assert m.factor_de_duck == pytest.approx(DUCK_NIVEL, abs=0.01)

    def test_al_soltarla_vuelve(self) -> None:
        m = Mezclador()
        m.agachar_musica()
        self._agachada(m, 1.0)
        m.soltar_musica()
        self._agachada(m, 2.0)
        assert m.factor_de_duck == pytest.approx(1.0, abs=0.01)

    def test_baja_mas_rapido_de_lo_que_sube(self) -> None:
        """Bajar lento se come la primera palabra; subir de golpe suena a
        fallo técnico. Las dos velocidades son distintas a propósito."""
        bajando = Mezclador()
        bajando.agachar_musica()
        t_baja = 0.0
        while bajando.factor_de_duck > DUCK_NIVEL + 0.01 and t_baja < 3:
            bajando.update(1 / 60)
            t_baja += 1 / 60

        subiendo = Mezclador()
        subiendo.agachar_musica()
        for _ in range(180):
            subiendo.update(1 / 60)
        subiendo.soltar_musica()
        t_sube = 0.0
        while subiendo.factor_de_duck < 0.99 and t_sube < 3:
            subiendo.update(1 / 60)
            t_sube += 1 / 60

        assert t_baja < t_sube, (
            f"baja en {t_baja:.2f} s y sube en {t_sube:.2f} s: con la misma "
            f"velocidad en los dos sentidos se oye el bombeo"
        )

    def test_con_duracion_se_suelta_sola(self) -> None:
        """Una línea de diálogo sabe lo que dura; una conversación entera, no.
        Por eso hay las dos formas."""
        m = Mezclador()
        m.agachar_musica(0.3)
        self._agachada(m, 2.0)
        assert m.factor_de_duck == pytest.approx(1.0, abs=0.01)

    def test_solo_afecta_a_la_musica(self) -> None:
        m = Mezclador()
        antes = m.ganancia(BUS_EFECTOS)
        m.agachar_musica()
        self._agachada(m, 1.0)
        assert m.ganancia(BUS_EFECTOS) == antes, (
            "el duck se comió también los efectos: los golpes se apagarían "
            "mientras alguien habla"
        )

    def test_un_dt_de_cero_no_mueve_nada(self) -> None:
        m = Mezclador()
        m.agachar_musica()
        m.update(0.0)
        assert m.factor_de_duck == 1.0


class TestLoQueLaMutacionDestapo:
    """AUD-181 / GAP-023 — ocho cambios que la suite no detectaba.

    `scripts/mutation_check.py` puntuó este módulo con un 56 %. El agujero más
    llamativo: se podía poner a **cero** el volumen de partida del bus de
    ambiente y el nivel del *duck*, y ninguna prueba fallaba. Las que había
    comprobaban que los volúmenes estuvieran *entre* 0 y 1, que es cierto
    también cuando valen 0 — es decir, cuando no se oye nada.

    La lección es la de siempre en este repositorio: un rango no comprueba un
    valor. `0.0 <= x <= 1.0` pasa con el altavoz apagado.

    Los tres que siguen vivos, y por qué no se persiguen
    -----------------------------------------------------
    Quedan 3 de 25 (88 %). Los tres son **equivalentes**: cambian el código
    sin cambiar lo que hace. Escribirles una prueba exigiría afirmar algo
    falso, así que se dejan documentados en vez de tapados.

    * **línea 144, `segundos > 0.0` → `>= 0.0`.** La rama sólo se ejecuta de
      más cuando `segundos` vale 0, y entonces hace
      `max(_duck_restante, 0.0)`. Eso sólo cambia algo si el contador es
      negativo, y un contador negativo ya está inerte: el descuento del
      `update` corre bajo `if _duck_restante > 0.0`, que es falso tanto para
      -0,4 como para 0,0. Comprobado sobre 20.000 secuencias aleatorias de
      llamadas: **0 diferencias** en la interfaz pública.
    * **línea 164, `dt <= 0.0` → `dt < 0.0`.** Con `dt == 0.0` el cuerpo se
      ejecuta pero cada paso es una operación nula: no se descuenta nada y el
      paso del *duck* vale `(1 - DUCK_NIVEL) * 0 / duracion` = 0. Comprobado
      sobre 4.000 secuencias comparando incluso el estado interno:
      **0 diferencias**.
    * **línea 177, `objetivo < self._duck` → `<=`.** Las dos formas sólo
      difieren cuando son iguales, y tres líneas antes hay un
      `if self._duck == objetivo: return` que ya se llevó ese caso. La rama
      se instrumentó: la igualdad se da **0 veces**.
    """

    def _avanzar(self, m: Mezclador, segundos: float) -> None:
        for _ in range(int(segundos * 60)):
            m.update(1 / 60)

    # ── constantes que nadie miraba ───────────────────────────────
    @pytest.mark.parametrize(
        "bus", [BUS_MUSICA, BUS_EFECTOS, BUS_VOZ, BUS_AMBIENTE],
    )
    def test_ningun_bus_arranca_mudo(self, bus: str) -> None:
        """Un bus que arranca en 0 no se distingue de uno roto: el jugador
        oye silencio y no tiene forma de saber que hay un deslizador que
        subir."""
        assert Mezclador().ganancia(bus) > 0.0

    def test_la_musica_agachada_baja_pero_no_se_calla(self) -> None:
        """Con `DUCK_NIVEL` en 0 la música desaparece mientras alguien habla.
        Eso no es *ducking*: es un corte, y se nota tanto como el problema que
        el *ducking* venía a resolver."""
        m = Mezclador()
        entera = m.ganancia(BUS_MUSICA)

        m.agachar_musica()
        self._avanzar(m, 1.0)
        agachada = m.ganancia(BUS_MUSICA)

        assert 0.0 < agachada < entera, (
            f"la música pasó de {entera:.3f} a {agachada:.3f}: por debajo de "
            f"cero no hay duck que valga, hay un corte"
        )

    def test_bajar_tarda_lo_que_dice_el_ataque(self) -> None:
        """No basta con «baja más rápido de lo que sube»: eso lo cumple
        cualquier par de números. El ataque son 0,15 s porque menos se oye
        como un corte y más se come la primera palabra."""
        m = Mezclador()
        m.agachar_musica()

        transcurrido = 0.0
        while m.factor_de_duck > DUCK_NIVEL + 0.001 and transcurrido < 2.0:
            m.update(1 / 240)
            transcurrido += 1 / 240

        # Los límites son absolutos y no `approx(DUCK_ATAQUE)` a propósito: si
        # la referencia se lee de la propia constante, cambiarla mueve también
        # la prueba y el mutante sobrevive. Por debajo de 0,05 s el corte se
        # oye; por encima de 0,3 s la música se come la primera palabra.
        assert 0.05 <= transcurrido <= 0.30, (
            f"tardó {transcurrido:.3f} s en agacharse: fuera de la ventana en "
            f"la que el duck no se nota"
        )
        assert transcurrido == pytest.approx(DUCK_ATAQUE, abs=0.02), (
            f"tardó {transcurrido:.3f} s y la constante declara {DUCK_ATAQUE} s"
        )

    def test_volver_tarda_lo_que_dice_la_recuperacion(self) -> None:
        m = Mezclador()
        m.agachar_musica()
        self._avanzar(m, 1.0)
        m.soltar_musica()

        transcurrido = 0.0
        while m.factor_de_duck < 0.999 and transcurrido < 3.0:
            m.update(1 / 240)
            transcurrido += 1 / 240

        assert 0.25 <= transcurrido <= 1.50, (
            f"tardó {transcurrido:.3f} s en volver: subir de golpe suena a "
            f"fallo técnico y tardar demasiado deja la música apagada"
        )
        assert transcurrido == pytest.approx(DUCK_RECUPERACION, abs=0.05), (
            f"tardó {transcurrido:.3f} s y la constante declara "
            f"{DUCK_RECUPERACION} s"
        )

    # ── el estado de partida ──────────────────────────────────────
    def test_un_mezclador_recien_creado_no_agacha_la_musica_solo(self) -> None:
        """Con `_duck_pedido` arrancando en `True`, la música empieza
        agachándose sin que nadie hable — y como nadie llamó a
        `agachar_musica`, tampoco hay quien la suelte."""
        m = Mezclador()
        entera = m.ganancia(BUS_MUSICA)

        self._avanzar(m, 1.0)

        assert not m.musica_agachada
        assert m.factor_de_duck == 1.0
        assert m.ganancia(BUS_MUSICA) == entera

    # ── las fronteras ─────────────────────────────────────────────
    def test_una_milesima_por_debajo_de_uno_no_cuenta_como_agachada(
        self,
    ) -> None:
        """`musica_agachada` usa un umbral de 0,999 porque el *duck* se mueve
        en coma flotante y nunca vuelve a valer 1.0 exacto. La frontera se
        toca aquí a mano: no hay forma de aterrizar en 0,999 justo desde la
        integración, y sin fijarla el umbral se puede invertir sin que nada
        falle.
        """
        m = Mezclador()
        m._duck = 0.999

        assert not m.musica_agachada, (
            "0,999 es indistinguible de 1,0 para el oído; contarlo como "
            "agachada dejaría el indicador encendido para siempre"
        )

        m._duck = 0.998
        assert m.musica_agachada

    def test_al_agotarse_el_tiempo_justo_la_musica_se_suelta(self) -> None:
        """El caso de borde exacto: se pide 0,5 s y pasan 0,5 s clavados. Si
        la comprobación fuera `< 0` en vez de `<= 0`, el contador se quedaría
        en cero sin llegar a soltar nunca, y la música no volvería jamás."""
        m = Mezclador()
        m.agachar_musica(0.5)

        # De una sola vez, no en 50 pasos de 0,01: sumar 0,01 cincuenta veces
        # en coma flotante no aterriza en el cero exacto —cae un pelo por
        # encima o por debajo— y es justo el cero exacto lo que distingue
        # `<= 0` de `< 0`. Con `< 0`, el contador se queda clavado en 0.0 y,
        # como el descuento sólo corre mientras es `> 0`, no vuelve a moverse:
        # la música se queda agachada para el resto de la partida.
        m.update(0.5)

        self._avanzar(m, 2.0)
        assert m.factor_de_duck == pytest.approx(1.0, abs=0.01), (
            "la música se quedó agachada tras agotarse su tiempo"
        )

    def test_un_ataque_de_cero_no_divide_por_cero(self, monkeypatch) -> None:
        """El `max(0.01, duracion)` del paso es una guarda, no un adorno: sin
        ella, poner cualquiera de las dos constantes a 0 —algo que un
        estudiante ajustando la mezcla hará— revienta con ZeroDivisionError en
        mitad del bucle de juego."""
        monkeypatch.setattr(mixer_buses, "DUCK_ATAQUE", 0.0)
        monkeypatch.setattr(mixer_buses, "DUCK_RECUPERACION", 0.0)

        m = Mezclador()
        m.agachar_musica()
        m.update(1 / 60)            # no debe lanzar

        assert m.factor_de_duck == pytest.approx(DUCK_NIVEL, abs=0.001)


class TestElGestorDeAudioLosUsa:
    """Que el mezclador funcione aislado no significa que nadie lo use."""

    def _audio(self):
        from src.engine.audio.audio_manager import AudioManager

        return AudioManager()

    def test_el_gestor_tiene_mezclador(self) -> None:
        assert self._audio().mezcla is not None

    def test_el_deslizador_de_musica_mueve_el_bus(self) -> None:
        """Si vivieran por separado, mover el volumen en opciones dejaría el
        *duck* calculando sobre el valor equivocado."""
        audio = self._audio()
        audio.set_music_volume(0.3)
        assert audio.mezcla.volumen_de(BUS_MUSICA) == pytest.approx(0.3)

    def test_el_deslizador_de_efectos_mueve_el_bus(self) -> None:
        audio = self._audio()
        audio.set_sfx_volume(0.25)
        assert audio.mezcla.volumen_de(BUS_EFECTOS) == pytest.approx(0.25)

    def test_silenciar_pasa_por_el_mezclador(self) -> None:
        audio = self._audio()
        estado = audio.mezcla.silencio
        audio.toggle_mute()
        assert audio.mezcla.silencio != estado

    def test_desmutear_respeta_el_duck_vivo(self, monkeypatch) -> None:
        """AUD-311 — desmutear escribía el volumen crudo a mano: con un
        diálogo abierto, la música volvía a pleno volumen a pesar de que
        estuviera agachada."""
        import pygame

        from src.engine.audio.audio_manager import AudioManager

        if pygame.mixer.get_init() is None:
            try:
                pygame.mixer.init()
            except pygame.error as exc:  # sin dispositivo de audio: se salta
                pytest.skip(f"sin mezclador disponible: {exc}")

        capturados: list[float] = []
        monkeypatch.setattr(pygame.mixer.music, "set_volume", capturados.append)
        audio = AudioManager()
        audio.play_voz("sfx_ui_menu_confirm")  # agacha la música
        for _ in range(120):
            audio.update(1 / 60)
        assert audio.mezcla.musica_agachada

        audio.toggle_mute()  # silencio
        audio.toggle_mute()  # desmutear: debe componer con el duck
        assert capturados, "la música nunca se aplicó al mezclador de SDL"
        assert capturados[-1] == pytest.approx(
            audio.mezcla.ganancia(BUS_MUSICA), abs=0.001
        )
        assert capturados[-1] < 0.999, (
            "desmutear levantó la música por encima del duck en curso"
        )

    def test_el_stinger_pasa_por_el_bus_de_efectos(self, monkeypatch) -> None:
        """AUD-311 — el stinger multiplicaba `_sfx_volume` a mano y se
        saltaba `Mezclador.ganancia`: ignoraba el volumen del bus y el del
        maestro."""
        from src.engine.audio.audio_manager import AudioManager

        audio = AudioManager()
        audio.mezcla.ajustar(BUS_EFECTOS, 0.5)
        audio.mezcla.maestro = 0.5
        llamadas: list[float] = []
        monkeypatch.setattr(
            audio.sound_bank, "play", lambda name, volume: llamadas.append(volume)
        )
        audio.play_stinger("cualquiera")
        assert llamadas
        assert llamadas[0] == pytest.approx(0.5 * 0.5 * 0.8, abs=0.001)

    def test_un_ambiente_que_falta_no_tumba_el_crossfade(self, monkeypatch) -> None:
        """AUD-411 — `crossfade_ambient` capturaba menos que `play_ambient`.

        Las dos cargan un `.wav` del disco con `pygame.mixer.Sound`; la
        primera captura `pygame.error, FileNotFoundError, OSError` y degrada
        con un aviso, la segunda sólo `pygame.error`. Un fichero que se borra
        o se vuelve ilegible entre el `exists()` del llamador y la carga
        —ventana TOCTOU, o una instalación en medio de solo lectura— lanzaba
        fuera del método y la transición de escena terminaba en la pantalla
        de error. Degradar o lanzar es una decisión, pero no puede ser
        distinta en dos métodos hermanos que hacen lo mismo.
        """
        import pygame

        from src.engine.audio.audio_manager import AudioManager

        if pygame.mixer.get_init() is None:
            try:
                pygame.mixer.init()
            except pygame.error as exc:  # sin dispositivo de audio: se salta
                pytest.skip(f"sin mezclador disponible: {exc}")

        audio = AudioManager()

        def _rota(*args, **kwargs):
            raise FileNotFoundError("el ambiente desapareció del disco")

        monkeypatch.setattr(pygame.mixer, "Sound", _rota)

        audio.crossfade_ambient("assets/audio/ambiente/inexistente.wav")

        assert not audio._ambient_active, (
            "el ambiente roto quedó marcado como activo: el audio miente"
        )

    def test_hablar_agacha_la_musica(self) -> None:
        audio = self._audio()
        audio.play_voz("sfx_ui_menu_confirm")
        for _ in range(60):
            audio.update(1 / 60)
        assert audio.mezcla.musica_agachada

    def test_el_bucle_del_juego_actualiza_la_mezcla(self) -> None:
        """El *ducking* se mueve en `App.run`, con tiempo real y fuera de las
        escenas: tiene que seguir subiendo en el menú de pausa."""
        import inspect

        from src.engine.core import app

        fuente = inspect.getsource(app)
        assert "audio_manager.update(" in fuente, (
            "nadie actualiza la mezcla: la música se agacharía y no volvería"
        )
        assert "unscaled_dt" in fuente


class TestElDialogoLoPide:
    """La cadena entera: abrir un diálogo tiene que apartar la música."""

    def test_abrir_un_dialogo_agacha(self) -> None:
        import inspect

        from src.framework.ui import dialogue_system

        fuente = inspect.getsource(dialogue_system)
        assert "agachar_musica" in fuente
        assert "soltar_musica" in fuente, (
            "se agacha y no se suelta: la música se quedaría baja el resto de "
            "la partida"
        )


class TestLoQueNoSePuedeHacer:
    """La reverberación por zona, dicha sin adornos.

    El mezclador de SDL no tiene efectos: reproduce muestras y las suma. Una
    reverberación exige convolucionar cada sonido con la respuesta al impulso
    de la sala, y eso o se hace sobre la muestra al cargarla —dos copias de
    cada sonido— o con una biblioteca de DSP externa.

    Prometerla encima de esto sería la clase de afirmación que este mes ha
    habido que corregir dos veces (AUD-133, AUD-142).
    """

    def test_el_modulo_dice_que_no_hay_reverberacion(self) -> None:
        from src.engine.audio import mixer_buses

        assert "Reverberación por zona no" in (mixer_buses.__doc__ or ""), (
            "el módulo no advierte de lo que NO hace, y alguien construirá "
            "encima suponiendo que sí"
        )

    def test_y_no_hay_una_api_que_finja_tenerla(self) -> None:
        from src.engine.audio.mixer_buses import Mezclador

        assert not hasattr(Mezclador, "reverberacion")


class TestLasDosApisDeAmbienteQueNadieLlamaba:
    """AUD-149 — `set_ambient_volume` y `crossfade_ambient`.

    Las dos llevaban meses escritas, completas y sin una sola llamada. El
    registro las tenía en la fila «API de audio escrita y nunca llamada».
    """

    def _audio(self):
        from src.engine.audio.audio_manager import AudioManager

        return AudioManager()

    def test_el_bus_de_ambiente_pasa_por_set_ambient_volume(self) -> None:
        import inspect

        from src.engine.audio.audio_manager import AudioManager

        fuente = inspect.getsource(AudioManager.ajustar_bus)
        assert "set_ambient_volume" in fuente, (
            "el bus toca el canal a mano y `set_ambient_volume` vuelve a ser "
            "un huérfano"
        )

    def test_ajustar_el_bus_mueve_el_volumen_del_ambiente(self) -> None:
        audio = self._audio()
        audio.ajustar_bus(BUS_AMBIENTE, 0.2)
        assert audio._ambient_volume == pytest.approx(0.2)

    # AUD-500 — estas dos miraban el texto de `stage_scene.py`, y el cableado
    # del ambiente se mudó a `stage_parts/simulacion.py`, junto a
    # `_cambiar_clima`, que es quien lo llama. Ahora se mira **el método**:
    # así siguen protegiendo lo mismo y dejan de romperse cada vez que el
    # código se coloca donde le corresponde.

    def _fuente_del_ambiente(self) -> str:
        import inspect

        from src.framework.scenes.stage_scene import StageScene

        return inspect.getsource(StageScene._aplicar_ambiente_del_clima)

    def test_la_escena_funde_entre_ambientes(self) -> None:
        assert "crossfade_ambient" in self._fuente_del_ambiente(), (
            "al volver de una sala de jefe el ambiente cortaría en seco, que "
            "se oye como un fallo"
        )

    def test_la_primera_vez_no_funde_nada(self) -> None:
        """No hay ambiente anterior con el que fundir: arrancar normal."""
        fuente = self._fuente_del_ambiente()
        assert "_ambient_active" in fuente
        assert "play_ambient(" in fuente

    def test_un_clima_sin_ambiente_para_el_anterior(self) -> None:
        """AUD-500 — la mitad que faltaba, y el defecto reportado jugando:
        `AMBIENTES["clear"]` es `None`, y sin esto la lluvia seguía sonando
        sobre un cielo despejado."""
        assert "stop_ambient" in self._fuente_del_ambiente(), (
            "el ambiente sólo sabe arrancar: un clima sin sonido deja "
            "sonando el anterior"
        )
