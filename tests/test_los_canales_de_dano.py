"""AUD-387 — el daño tenía un solo canal. Cierra GAP-043.

El hueco
========
`CollisionSystem._calculate_damage` devolvía un escalar y `EnemyBase.apply_hit`
lo restaba de la vida. No había forma de que un enemigo fuera **débil a una
cosa y resistente a otra**, que es la mecánica que separa un bestiario de una
lista de sacos de vida con distinta cantidad.

El diseño, decidido por el dueño
================================
Catálogo de canales en JSON y resistencias declaradas en Tiled, como todo lo
demás en este motor. Los canales salen del lore, que menciona **veneno** ocho
veces y **fuego** tres, y ninguna vez hielo o electricidad: se empieza con los
que tienen contenido detrás y el catálogo es JSON, así que añadir uno después
no cuesta nada.

Por qué es aditivo, y por qué eso no es negociable
==================================================
`apply_hit` tiene **32 llamantes y 26 están en `src/stages/`** — entregas de
estudiantes. El canal entra como parámetro con valor por defecto, y sin
resistencias declaradas la mitigación es 1,0. Un enemigo que nadie toque se
comporta **exactamente** igual que antes de este cambio, y eso lo comprueba
esta prueba antes que nada.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.combate import dano


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    yield


class TestElCatalogo:
    def test_trae_los_tres_canales_del_lore(self):
        assert set(dano.CANALES) == {"fisico", "veneno", "fuego"}

    def test_el_fisico_es_el_por_defecto(self):
        """El que reciben los 32 llamantes que no dicen nada."""
        assert dano.CANAL_POR_DEFECTO == "fisico"
        assert dano.CANAL_POR_DEFECTO in dano.CANALES

    def test_cada_canal_tiene_nombre_legible(self):
        """El catálogo lo lee un humano: es material de clase, no un enum."""
        for clave, ficha in dano.CANALES.items():
            assert ficha.get("nombre"), f"«{clave}» sin nombre"

    def test_un_canal_inventado_no_revienta(self):
        """La decisión de siempre en este cargador: el estudiante ve su nivel.

        Un canal mal escrito en Tiled se trata como físico y se avisa, en vez
        de tumbar la carga del mapa.
        """
        assert dano.canal_valido("veneno")
        assert not dano.canal_valido("plasma")
        assert dano.normalizar("plasma") == dano.CANAL_POR_DEFECTO


class TestLaMitigacion:
    def test_sin_resistencias_no_cambia_nada(self):
        assert dano.mitigar(10.0, "fuego", {}) == pytest.approx(10.0)

    def test_una_resistencia_reduce(self):
        assert dano.mitigar(10.0, "veneno", {"veneno": 0.25}) == pytest.approx(2.5)

    def test_una_debilidad_aumenta(self):
        """Mayor que 1 es debilidad: es lo que hace interesante un bestiario."""
        assert dano.mitigar(10.0, "fuego", {"fuego": 2.0}) == pytest.approx(20.0)

    def test_la_resistencia_de_otro_canal_no_aplica(self):
        assert dano.mitigar(10.0, "fuego", {"veneno": 0.0}) == pytest.approx(10.0)

    def test_la_inmunidad_deja_el_dano_en_cero(self):
        assert dano.mitigar(10.0, "veneno", {"veneno": 0.0}) == pytest.approx(0.0)

    def test_no_se_permite_curar_con_un_golpe(self):
        """Un factor negativo en Tiled no puede convertir un golpe en cura.

        Es el mismo criterio que `max(0.0, ...)` en el cargador: un dato
        hostil produce un valor raro pero jugable, no una mecánica invertida.
        """
        assert dano.mitigar(10.0, "fuego", {"fuego": -3.0}) == pytest.approx(0.0)


class TestElEnemigoLoUsa:
    """El corte vertical: que llegue desde el golpe hasta la vida."""

    def _enemigo(self, **kw):
        from src.framework.entities.enemy_walker import EnemyWalker

        e = EnemyWalker(pygame.Vector2(100, 100), **kw)
        e.current_health = 10.0
        return e

    def test_sin_resistencias_se_comporta_como_siempre(self):
        """La compatibilidad, comprobada antes que la característica.

        26 de los 32 llamantes de `apply_hit` están en entregas.
        """
        e = self._enemigo()
        e.apply_hit(3.0, (0.0, 0.0))
        assert e.current_health == pytest.approx(7.0)

    def test_resistente_al_veneno_recibe_menos(self):
        e = self._enemigo()
        e.resistencias = {"veneno": 0.5}
        e.apply_hit(4.0, (0.0, 0.0), canal="veneno")
        assert e.current_health == pytest.approx(8.0)

    def test_debil_al_fuego_recibe_mas(self):
        e = self._enemigo()
        e.resistencias = {"fuego": 2.0}
        e.apply_hit(3.0, (0.0, 0.0), canal="fuego")
        assert e.current_health == pytest.approx(4.0)

    def test_la_resistencia_no_afecta_a_otro_canal(self):
        e = self._enemigo()
        e.resistencias = {"veneno": 0.0}
        e.apply_hit(3.0, (0.0, 0.0))
        assert e.current_health == pytest.approx(7.0)


class TestLaPromesaRotaDelSpec:
    """`06_TMX_SPEC.md` prometía `damage_type` en `HazardZone` y no existía.

    AUD-310 la marcó «no está implementada» y dejó una prueba vigilando que
    siguiera sin estarlo. Llevaba ahí desde entonces porque **no había canales
    de daño**: prometer un tipo cuando el motor sólo sabe restar un número es
    prometer nada.

    Con el catálogo de AUD-387 la promesa se puede cumplir, y una zona de
    veneno deja de ser una zona de daño con otro nombre.
    """

    def test_la_zona_declara_su_canal(self):
        from src.framework.stage.stage_data import HazardZone

        z = HazardZone(rect=pygame.Rect(0, 0, 32, 32))
        assert z.damage_type == dano.CANAL_POR_DEFECTO

    def test_el_cargador_lee_la_propiedad(self):
        from src.framework.stage.stage_objetos import ObjetosDeTiled

        assert ObjetosDeTiled._canal_de({"damage_type": "veneno"}) == "veneno"

    def test_un_canal_inventado_cae_al_fisico(self):
        from src.framework.stage.stage_objetos import ObjetosDeTiled

        assert (ObjetosDeTiled._canal_de({"damage_type": "plasma"})
                == dano.CANAL_POR_DEFECTO)

    def test_sin_propiedad_es_fisico(self):
        from src.framework.stage.stage_objetos import ObjetosDeTiled

        assert ObjetosDeTiled._canal_de({}) == dano.CANAL_POR_DEFECTO


class TestSeDeclaraEnTiled:
    """Lo que lo hace usable: que un estudiante lo ponga sin escribir Python."""

    def test_el_cargador_entiende_la_propiedad(self):
        from src.framework.stage.stage_objetos import ObjetosDeTiled

        assert ObjetosDeTiled._resistencias_de("veneno:0.5, fuego:2") == {
            "veneno": 0.5, "fuego": 2.0,
        }

    def test_una_cadena_vacia_no_da_resistencias(self):
        from src.framework.stage.stage_objetos import ObjetosDeTiled

        assert ObjetosDeTiled._resistencias_de("") == {}
        assert ObjetosDeTiled._resistencias_de(None) == {}

    def test_lo_ilegible_se_ignora_y_el_resto_entra(self):
        """Un error de tecleo no puede costarle el nivel entero al estudiante."""
        from src.framework.stage.stage_objetos import ObjetosDeTiled

        assert ObjetosDeTiled._resistencias_de(
            "veneno:0.5, esto_no, fuego:x, plasma:2") == {"veneno": 0.5}
