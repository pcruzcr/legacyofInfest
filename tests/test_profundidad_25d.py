"""AUD-277 — el 2.5D: escala por profundidad, declarada desde el mapa.

Qué es y qué no
===============
No es 3D. `docs/62` C2 lo dejó decidido: la tubería GL de 479 líneas no es un
scene graph, y portar a Godot sería el camino si hiciera falta 3D de verdad.
**2.5D sí es viable**, y es esto: una entidad se dibuja más pequeña cuanto más
«al fondo» esté, con una escala que sale de su posición vertical en el mapa.

Con eso, un pasillo con tres filas de plataformas deja de leerse como un plano
y pasa a leerse como un espacio con profundidad — **sin tocar la física**, que
sigue siendo la misma en dos ejes. Ésa es la línea que separa 2.5D de 3D: aquí
sólo cambia lo que se dibuja.

Cómo se declara
---------------
Dos propiedades del mapa, y **apagado por defecto** — la misma decisión que
AUD-141 tomó con la estamina y AUD-260 con el tiempo bala, por la misma razón:
los dieciséis escenarios entregados están calificados, y encenderles una
mecánica visual cambiaría cómo se ven sin que sus autores lo pidan.

    profundidad_min = 0.75    # escala arriba del todo (lo más lejano)
    profundidad_max = 1.0     # escala abajo del todo (lo más cercano)

Sin declararlas, la escala es 1,0 para todo y el dibujado no cambia una coma.
"""
from __future__ import annotations

import pytest

from src.framework.stage.profundidad import EscalaPorProfundidad


class TestApagadoPorDefecto:
    def test_sin_declarar_nada_no_escala(self) -> None:
        e = EscalaPorProfundidad()

        assert e.activa is False
        assert e.escala_en(0) == pytest.approx(1.0)
        assert e.escala_en(5000) == pytest.approx(1.0)

    def test_min_igual_a_max_tampoco_escala(self) -> None:
        """Declarar 1.0 y 1.0 es apagarlo, no un caso raro."""
        e = EscalaPorProfundidad(mapa_alto=1000, minimo=1.0, maximo=1.0)

        assert e.activa is False


class TestLoQueHaceEncendido:
    @pytest.fixture
    def escala(self) -> EscalaPorProfundidad:
        return EscalaPorProfundidad(mapa_alto=1000, minimo=0.75, maximo=1.0)

    def test_arriba_del_todo_es_lo_mas_pequeno(self, escala) -> None:
        assert escala.escala_en(0) == pytest.approx(0.75)

    def test_abajo_del_todo_es_lo_mas_grande(self, escala) -> None:
        assert escala.escala_en(1000) == pytest.approx(1.0)

    def test_a_mitad_de_camino_va_a_mitad(self, escala) -> None:
        assert escala.escala_en(500) == pytest.approx(0.875)

    def test_crece_monotonamente_hacia_abajo(self, escala) -> None:
        valores = [escala.escala_en(y) for y in range(0, 1001, 100)]

        assert valores == sorted(valores), "la escala no crece al bajar"

    def test_fuera_del_mapa_se_recorta(self, escala) -> None:
        """Una entidad por encima del borde o por debajo del suelo no puede
        salirse del rango: sin recorte, un enemigo que cae a un pozo se
        agrandaría sin límite."""
        assert escala.escala_en(-500) == pytest.approx(0.75)
        assert escala.escala_en(9999) == pytest.approx(1.0)


class TestComoLaLeeElMapa:
    def test_stage_data_publica_las_dos_propiedades(self) -> None:
        import dataclasses

        from src.framework.stage.stage_loader import StageData

        campos = {f.name for f in dataclasses.fields(StageData)}
        assert {"profundidad_min", "profundidad_max"} <= campos

    def test_por_defecto_valen_uno(self) -> None:
        """El valor por defecto es lo que decide si el cambio es aditivo."""
        import dataclasses

        from src.framework.stage.stage_loader import StageData

        por_nombre = {f.name: f.default for f in dataclasses.fields(StageData)}
        assert por_nombre["profundidad_min"] == pytest.approx(1.0)
        assert por_nombre["profundidad_max"] == pytest.approx(1.0)

    #: AUD-383 — el laboratorio de la vista cenital sí las declara, y ése es su
    #: trabajo: era una de las cuatro propiedades que ningún mapa demostraba
    #: (GAP-052), y una característica que ningún mapa declara no la descubre
    #: ningún estudiante. Se exceptúa por nombre y no relajando la prueba,
    #: porque lo que ésta vigila sigue importando: que **el contenido que ya
    #: existía** no cambie de aspecto por haber añadido la propiedad.
    #: Modernización 2.5D — stage0 y stage_mecanicas activan profundidad 0.85/1.0
    #: curva 1.5 + orden_por_y (mantiene estilo pixel, 256, 32 colores, liquidos y
    #: normal maps).
    LABORATORIOS_QUE_LAS_DEMUESTRAN: frozenset[str] = frozenset({
        "stage_cenital.tmx",
        "stage0.tmx",
        "stage_mecanicas.tmx",
    })

    def test_ningun_mapa_entregado_las_declara(self) -> None:
        from pathlib import Path

        raiz = Path(__file__).resolve().parents[1]
        con_prop = [
            p.name for p in (raiz / "assets" / "maps").rglob("*.tmx")
            if 'name="profundidad_min"' in p.read_text(encoding="utf-8",
                                                       errors="replace")
        ]
        inesperados = sorted(set(con_prop) - self.LABORATORIOS_QUE_LAS_DEMUESTRAN)
        assert not inesperados, f"ya la usaban: {inesperados}"

    def test_el_laboratorio_cenital_las_declara(self) -> None:
        """El otro sentido: la excepción no puede quedarse vacía en silencio.

        Si alguien borra la propiedad del laboratorio, la prueba de arriba
        seguiría en verde —no habría mapas inesperados— y la característica
        volvería a no estar demostrada en ninguna parte, que es el estado del
        que AUD-383 la sacó.
        """
        from pathlib import Path

        raiz = Path(__file__).resolve().parents[1]
        cenital = raiz / "assets" / "maps" / "stage_cenital" / "stage_cenital.tmx"
        assert 'name="profundidad_min"' in cenital.read_text(
            encoding="utf-8", errors="replace"), (
            "el laboratorio cenital dejó de declarar `profundidad_min`: "
            "ningún mapa la demuestra otra vez"
        )


class TestElDibujadoLaUsa:
    def test_el_sistema_de_dibujo_la_conoce(self) -> None:
        from src.framework.stage.drawing_system import DrawingSystem

        assert hasattr(DrawingSystem, "_escala_de_profundidad")
