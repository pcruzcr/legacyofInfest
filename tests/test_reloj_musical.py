"""
El reloj musical — AUD-137 (F6).

Por qué el juego no podía tener niveles rítmicos
================================================
Se puede hacer un bloque que aparezca cada segundo. Lo que no se podía hacer
es que ese bloque apareciera **con la música**, y ésa es toda la diferencia
entre *Mega Man 2* y *Super Mario Bros. Wonder*.

El motivo es aritmético y se llama deriva. Un objeto que suma `dt` cuenta su
propio tiempo; la música cuenta el suyo, marcado por el reloj de la tarjeta de
sonido. Los dos relojes no van igual, así que al minuto llevan cien
milisegundos de diferencia —más de lo que el oído tolera— y a los cinco
minutos, medio compás.

La solución no es afinar el `dt`: es dejar de contar y preguntar.

Lo que estas pruebas defienden
-------------------------------
1. **La fuente es el audio**, con caída a tiempo real cuando no hay mezclador
   —si no, esto no se podría probar ni correr en un aula sin tarjeta—.
2. **El tiempo es real, nunca escalado.** El tiempo bala ralentiza el mundo y
   la música sigue igual.
3. **Los pulsos se cuentan, no se marcan.** Un fotograma largo puede cruzar
   dos pulsos, y un booleano se comería el segundo (AUD-116 otra vez).
"""
from __future__ import annotations

import pytest

from src.engine.audio.music_clock import RelojMusical


class _FuenteFalsa:
    """Un mezclador de mentira que va por donde le digamos."""

    def __init__(self, posicion: float | None = 0.0) -> None:
        self.posicion = posicion

    def posicion_musica(self) -> float | None:
        return self.posicion


class TestPulsosYCompases:
    def test_a_120_bpm_un_pulso_dura_medio_segundo(self) -> None:
        assert RelojMusical(bpm=120).segundos_por_pulso == pytest.approx(0.5)

    def test_un_compas_de_cuatro_a_120_dura_dos_segundos(self) -> None:
        assert RelojMusical(bpm=120, compas=4).segundos_por_compas == pytest.approx(2.0)

    def test_el_pulso_avanza_con_el_tiempo(self) -> None:
        reloj = RelojMusical(bpm=120)
        reloj.update(0.5)
        assert reloj.pulso_actual == 1

    def test_el_compas_avanza_cada_cuatro_pulsos(self) -> None:
        reloj = RelojMusical(bpm=120, compas=4)
        reloj.update(2.0)
        assert reloj.compas_actual == 1
        assert reloj.pulso_en_compas == 0

    def test_el_pulso_dentro_del_compas_da_la_vuelta(self) -> None:
        reloj = RelojMusical(bpm=120, compas=4)
        reloj.update(1.5)          # pulso 3
        assert reloj.pulso_en_compas == 3
        reloj.update(0.5)          # pulso 4 = primero del siguiente compás
        assert reloj.pulso_en_compas == 0

    def test_un_compas_de_tres_es_un_vals(self) -> None:
        reloj = RelojMusical(bpm=120, compas=3)
        reloj.update(1.5)
        assert reloj.compas_actual == 1

    def test_la_fraccion_dice_por_donde_va_el_pulso(self) -> None:
        reloj = RelojMusical(bpm=120)
        reloj.update(0.25)
        assert reloj.fraccion == pytest.approx(0.5)

    def test_un_bpm_de_cero_no_divide_entre_cero(self) -> None:
        """Dato hostil: `bpm = 0` en Tiled. Sin el recorte, esto es una
        división por cero en el primer fotograma."""
        reloj = RelojMusical(bpm=0)
        reloj.update(0.1)          # no debe lanzar
        assert reloj.segundos_por_pulso > 0


class TestLosPulsosSeCuentan:
    """AUD-116, otra vez: un booleano por fotograma miente cuando el
    fotograma es largo."""

    def test_el_primer_update_cruza_el_pulso_cero(self) -> None:
        """Si el pulso 0 no contara, el primer tiempo del nivel se perdería
        y nadie sabría por qué el compás entra tarde."""
        reloj = RelojMusical(bpm=120)
        reloj.update(1 / 60)
        assert reloj.pulsos_cruzados == 1

    def test_un_fotograma_normal_no_cruza_nada(self) -> None:
        reloj = RelojMusical(bpm=120)
        reloj.update(1 / 60)       # cruza el 0
        reloj.update(1 / 60)
        assert reloj.pulsos_cruzados == 0

    def test_un_fotograma_larguisimo_cruza_varios(self) -> None:
        reloj = RelojMusical(bpm=120)
        reloj.update(1 / 60)
        reloj.update(2.0)          # cuatro pulsos de golpe
        assert reloj.pulsos_cruzados == 4, (
            "con un booleano, tres de los cuatro pulsos se habrían perdido"
        )

    def test_en_un_minuto_a_120_bpm_hay_120_pulsos(self) -> None:
        """La cuenta que importa: ni uno de más ni uno de menos."""
        reloj = RelojMusical(bpm=120)
        total = 0
        for _ in range(60 * 60):
            reloj.update(1 / 60)
            total += reloj.pulsos_cruzados
        assert total == 120

    def test_el_primer_tiempo_del_compas_se_avisa(self) -> None:
        reloj = RelojMusical(bpm=120, compas=4)
        avisos = 0
        for _ in range(8 * 60):
            reloj.update(1 / 60)
            if reloj.acaba_de_empezar_compas:
                avisos += 1
        assert avisos == 4, f"8 s a 120 bpm son 4 compases, contó {avisos}"


class TestLaFuenteEsElAudio:
    """Contar fotogramas deriva; preguntar al mezclador no."""

    def test_si_el_audio_contesta_manda_el_audio(self) -> None:
        fuente = _FuenteFalsa(10.0)
        reloj = RelojMusical(bpm=120, fuente=fuente)
        reloj.update(1 / 60)
        assert reloj.posicion == pytest.approx(10.0)
        assert reloj.pulso_actual == 20

    def test_si_el_audio_calla_se_cuenta_el_tiempo(self) -> None:
        """Un aula sin tarjeta de sonido tiene que poder jugar el nivel."""
        reloj = RelojMusical(bpm=120, fuente=_FuenteFalsa(None))
        reloj.update(0.5)
        assert reloj.pulso_actual == 1

    def test_una_posicion_negativa_se_trata_como_sin_musica(self) -> None:
        """`pygame.mixer.music.get_pos()` devuelve -1 cuando no suena nada.
        Tratarlo como 0.0 dejaría el reloj clavado en el pulso cero."""
        reloj = RelojMusical(bpm=120, fuente=_FuenteFalsa(-1.0))
        reloj.update(0.5)
        assert reloj.pulso_actual == 1

    def test_una_fuente_que_revienta_no_para_el_juego(self) -> None:
        class _Rota:
            def posicion_musica(self):
                raise RuntimeError("el mezclador se cayó")

        reloj = RelojMusical(bpm=120, fuente=_Rota())
        reloj.update(0.5)
        assert reloj.pulso_actual == 1

    def test_el_reloj_no_deriva_contra_la_musica(self) -> None:
        """La prueba que da sentido a todo esto.

        Se simula una máquina cuyo fotograma dura un 2 % más de lo que cree
        —algo normalísimo—: contando `dt`, al minuto el nivel va más de un
        segundo por delante de la canción; preguntando al audio, no.
        """
        fuente = _FuenteFalsa(0.0)
        reloj = RelojMusical(bpm=120, fuente=fuente)
        for i in range(60 * 60):
            fuente.posicion = (i + 1) / 60          # el audio, exacto
            reloj.update(1 / 60 * 1.02)             # el juego, un 2 % largo
        assert reloj.posicion == pytest.approx(60.0, abs=0.05), (
            "el reloj se fue con el fotograma en vez de con la música"
        )

    def test_la_vuelta_de_la_pista_no_cuenta_pulsos_hacia_atras(self) -> None:
        fuente = _FuenteFalsa(30.0)
        reloj = RelojMusical(bpm=120, fuente=fuente)
        reloj.update(1 / 60)
        fuente.posicion = 0.0                       # la canción vuelve a empezar
        reloj.update(1 / 60)
        assert reloj.pulsos_cruzados == 0
        assert reloj.pulso_actual == 0


class TestLaLatencia:
    """Entre que el motor manda un sonido y el jugador lo oye pasan decenas
    de milisegundos, y cambian con los cascos y el sistema. Sin desfase
    ajustable, «a compás» significa cosas distintas en cada ordenador."""

    def test_el_desfase_retrasa_la_posicion(self) -> None:
        reloj = RelojMusical(bpm=120, desfase=0.1, fuente=_FuenteFalsa(1.0))
        reloj.update(1 / 60)
        assert reloj.posicion == pytest.approx(0.9)

    def test_el_desfase_no_manda_la_posicion_a_negativo(self) -> None:
        reloj = RelojMusical(bpm=120, desfase=5.0, fuente=_FuenteFalsa(1.0))
        reloj.update(1 / 60)
        assert reloj.posicion == 0.0

    def test_sin_desfase_no_cambia_nada(self) -> None:
        reloj = RelojMusical(bpm=120, fuente=_FuenteFalsa(1.0))
        reloj.update(1 / 60)
        assert reloj.posicion == pytest.approx(1.0)


class TestLaVentanaDeAcierto:
    def test_justo_en_el_pulso_esta_dentro(self) -> None:
        reloj = RelojMusical(bpm=120, fuente=_FuenteFalsa(1.0))
        reloj.update(1 / 60)
        assert reloj.en_ventana() is True

    def test_a_mitad_de_pulso_esta_fuera(self) -> None:
        reloj = RelojMusical(bpm=120, fuente=_FuenteFalsa(1.25))
        reloj.update(1 / 60)
        assert reloj.en_ventana() is False

    def test_llegar_pronto_vale_igual_que_llegar_tarde(self) -> None:
        """Un juego que sólo perdonara una dirección castigaría a quien se
        anticipa a la música, que es lo que hace todo el mundo."""
        tarde = RelojMusical(bpm=120, fuente=_FuenteFalsa(1.05))
        tarde.update(1 / 60)
        pronto = RelojMusical(bpm=120, fuente=_FuenteFalsa(1.45))
        pronto.update(1 / 60)
        assert tarde.en_ventana() and pronto.en_ventana()

    def test_la_ventana_se_puede_apretar(self) -> None:
        reloj = RelojMusical(bpm=120, fuente=_FuenteFalsa(1.08))
        reloj.update(1 / 60)
        assert reloj.en_ventana(0.09) is True
        assert reloj.en_ventana(0.02) is False

    def test_cuanto_falta_para_el_proximo(self) -> None:
        reloj = RelojMusical(bpm=120, fuente=_FuenteFalsa(1.25))
        reloj.update(1 / 60)
        assert reloj.tiempo_hasta_el_proximo_pulso() == pytest.approx(0.25)

    def test_cuantizar_lleva_al_pulso_mas_cercano(self) -> None:
        """Sirve para programar: «que la puerta se abra en el próximo pulso»
        en vez de «dentro de 0,3 s», que es lo que suena mal."""
        reloj = RelojMusical(bpm=120)
        assert reloj.cuantizar(0.6) == pytest.approx(0.5)
        assert reloj.cuantizar(0.9) == pytest.approx(1.0)


class TestElPatronDeCompas:
    """`"x.x."` es sí, no, sí, no. Se lee de un vistazo, que es más de lo que
    puede decirse de dos números en segundos."""

    @pytest.mark.parametrize(
        ("pulso", "esperado"),
        [(0, True), (1, False), (2, True), (3, False), (4, True)],
    )
    def test_el_patron_se_repite(self, pulso, esperado) -> None:
        reloj = RelojMusical(bpm=120, fuente=_FuenteFalsa(pulso * 0.5))
        reloj.update(1 / 60)
        assert reloj.presente_en_patron("x.x.") is esperado

    def test_un_patron_vacio_significa_siempre(self) -> None:
        """Compatibilidad: un bloque sin patrón no puede desaparecer de golpe
        en los mapas que ya existen."""
        assert RelojMusical().presente_en_patron("") is True

    def test_un_patron_de_basura_no_rompe_el_nivel(self) -> None:
        assert RelojMusical().presente_en_patron("¿qué?") is True

    def test_un_patron_largo_da_un_ritmo_de_dos_compases(self) -> None:
        reloj = RelojMusical(bpm=120, fuente=_FuenteFalsa(3.0))   # pulso 6
        reloj.update(1 / 60)
        assert reloj.presente_en_patron("x..x..x.") is True


class TestElBloqueSigueALaMusica:
    """La cadena entera: componente, sistema y mundo.

    Que el reloj funcione aislado no significa que un bloque lo use — es el
    fallo que este proyecto ha cometido nueve veces este mes.
    """

    def _mundo_con_bloque(self, patron: str):
        from src.framework.ecs.components import BloqueRitmico, Solido, Transform
        from src.framework.ecs.world import World

        mundo = World()
        entidad = mundo.crear(BloqueRitmico(patron=patron), Solido())
        return mundo, entidad, Solido, Transform

    def test_con_patron_el_bloque_pregunta_a_la_musica(self) -> None:
        from src.framework.ecs.systems import sistema_bloques_ritmicos

        mundo, entidad, Solido, _T = self._mundo_con_bloque("x.")
        reloj = RelojMusical(bpm=120, fuente=_FuenteFalsa(0.5))   # pulso 1: «.»
        reloj.update(1 / 60)
        mundo.poner_recurso("reloj_musical", reloj)

        sistema_bloques_ritmicos(mundo, 1 / 60)
        assert not mundo.tiene(entidad, Solido), (
            "el bloque sigue sólido en un pulso en el que el patrón dice que "
            "no está: no está mirando la música"
        )

    def test_y_vuelve_en_el_pulso_siguiente(self) -> None:
        from src.framework.ecs.systems import sistema_bloques_ritmicos

        mundo, entidad, Solido, _T = self._mundo_con_bloque("x.")
        fuente = _FuenteFalsa(0.5)
        reloj = RelojMusical(bpm=120, fuente=fuente)
        mundo.poner_recurso("reloj_musical", reloj)

        reloj.update(1 / 60)
        sistema_bloques_ritmicos(mundo, 1 / 60)
        fuente.posicion = 1.0                       # pulso 2: «x»
        reloj.update(1 / 60)
        sistema_bloques_ritmicos(mundo, 1 / 60)
        assert mundo.tiene(entidad, Solido)

    def test_sin_reloj_el_bloque_sigue_contando_segundos(self) -> None:
        """Compatibilidad: los mapas entregados no declaran `bpm` y sus
        bloques tienen que comportarse exactamente igual que antes."""
        from src.framework.ecs.components import BloqueRitmico, Solido
        from src.framework.ecs.systems import sistema_bloques_ritmicos
        from src.framework.ecs.world import World

        mundo = World()
        entidad = mundo.crear(
            BloqueRitmico(visible_seg=1.0, oculto_seg=1.0), Solido())
        sistema_bloques_ritmicos(mundo, 0.1)
        assert mundo.tiene(entidad, Solido)
        sistema_bloques_ritmicos(mundo, 1.2)
        assert not mundo.tiene(entidad, Solido)

    def test_el_patron_llega_desde_el_tmx(self) -> None:
        from src.framework.ecs.components import BloqueRitmico
        from src.framework.stage.stage_loader import StageData, StageLoader

        stage = StageData(map_layer=None)  # type: ignore[arg-type]
        obj = type("Obj", (), {"x": 0, "y": 0, "width": 32, "height": 16})()
        StageLoader._handle_componente(
            stage, obj, {"patron": "x..x"}, "RhythmBlock")
        bloques = [c for grupo in stage.componentes for c in grupo
                   if isinstance(c, BloqueRitmico)]
        assert bloques and bloques[0].patron == "x..x"

    def test_el_laboratorio_de_mecanicas_declara_su_compas(self) -> None:
        """El camino completo, desde el TMX de verdad.

        No basta con que el cargador sepa leer `bpm`: si ningún mapa lo
        declara, la función existe y nadie la ve. El escenario de referencia
        de las mecánicas es donde se enseña, así que es donde tiene que
        estar.
        """
        import pygame

        from src.engine.core import settings
        from src.framework.stage.stage_loader import StageLoader

        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((320, 240))
        ruta = settings.ASSETS_DIR / "maps/stage_mecanicas/stage_mecanicas.tmx"
        if not ruta.exists():
            pytest.skip("el laboratorio de mecánicas no está en este árbol")
        stage = StageLoader.load(ruta)
        assert stage.bpm == pytest.approx(120.0)
        assert stage.compas == 4

    def test_ese_mapa_tiene_bloques_que_siguen_la_musica(self) -> None:
        import pygame

        from src.engine.core import settings
        from src.framework.ecs.components import BloqueRitmico
        from src.framework.stage.stage_loader import StageLoader

        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((320, 240))
        ruta = settings.ASSETS_DIR / "maps/stage_mecanicas/stage_mecanicas.tmx"
        if not ruta.exists():
            pytest.skip("el laboratorio de mecánicas no está en este árbol")
        stage = StageLoader.load(ruta)
        bloques = [c for grupo in stage.componentes for c in grupo
                   if isinstance(c, BloqueRitmico)]
        con_musica = [b for b in bloques if b.sigue_la_musica]
        sin_musica = [b for b in bloques if not b.sigue_la_musica]
        assert con_musica, "ningún bloque sigue la música: nadie verá la función"
        assert sin_musica, (
            "todos siguen la música: el mapa dejó de enseñar el modo de "
            "siempre, que es el que usan los 15 escenarios entregados"
        )
