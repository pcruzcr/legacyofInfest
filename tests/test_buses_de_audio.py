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

from src.engine.audio.mixer_buses import (
    BUS_AMBIENTE,
    BUS_EFECTOS,
    BUS_MUSICA,
    BUS_VOZ,
    DUCK_NIVEL,
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

    def test_la_escena_funde_entre_ambientes(self) -> None:
        import inspect

        from src.framework.scenes import stage_scene

        fuente = inspect.getsource(stage_scene)
        assert "crossfade_ambient" in fuente, (
            "al volver de una sala de jefe el ambiente cortaría en seco, que "
            "se oye como un fallo"
        )

    def test_la_primera_vez_no_funde_nada(self) -> None:
        """No hay ambiente anterior con el que fundir: arrancar normal."""
        import inspect

        from src.framework.scenes import stage_scene

        fuente = inspect.getsource(stage_scene)
        assert "_ambient_active" in fuente
        assert "play_ambient(ambient_path, volume=0.3)" in fuente
