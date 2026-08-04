"""
Los logros siguen a quien juega, no a la máquina (AUD-200).

Por qué existe esta prueba
--------------------------
Los logros vivían en un único `achievements.json` por máquina. En un aula con
una PC y veinte estudiantes, el segundo jugador veía los logros del primero.
Ahora cada estudiante identificado tiene su propio fichero (nombrado por
correo) y el anónimo conserva la ruta histórica.
"""
from __future__ import annotations

import orjson


def _identificar(correo: str, monkeypatch) -> None:
    import src.framework.academic.sesion as sesion

    class _SesionFalsa:
        pass

    _SesionFalsa.correo = correo

    monkeypatch.setattr(sesion.SesionAcademica, "instancia", lambda: _SesionFalsa())


class TestLaRutaDelFichero:
    def test_sin_identificar_usa_la_ruta_historica(self, monkeypatch, tmp_path) -> None:
        import src.engine.core.achievements as ach

        base = tmp_path / "achievements.json"
        monkeypatch.setattr(ach, "ACHIEVEMENTS_PATH", base)
        # Anónimo explícito: el resolver inyectado (`sesion.py`) decide la ruta
        # por la sesión activa, así que la prueba fija cuál es.
        _identificar("", monkeypatch)
        assert ach._ruta_de_logros() == base

    def test_identificado_tiene_un_fichero_propio_y_legible(
        self, monkeypatch, tmp_path,
    ) -> None:
        import src.engine.core.achievements as ach

        base = tmp_path / "achievements.json"
        monkeypatch.setattr(ach, "ACHIEVEMENTS_PATH", base)

        _identificar("Ana María <ana.maria@universidad.edu>", monkeypatch)
        ruta = ach._ruta_de_logros()
        assert ruta != base
        assert ruta.parent == base.parent
        assert "ana" in ruta.name


class TestElGuardadoPorEstudiante:
    def test_cada_estudiante_lee_su_propio_fichero(self, monkeypatch, tmp_path) -> None:
        import src.engine.core.achievements as ach

        base = tmp_path / "achievements.json"
        monkeypatch.setattr(ach, "ACHIEVEMENTS_PATH", base)

        _identificar("ana@universidad.edu", monkeypatch)
        ana = ach.AchievementSystem()
        ana.mark_explorer("stage0")
        ana.mark_explorer("stage1_1")
        ana.save()
        ruta_ana = ach._ruta_de_logros()
        assert ruta_ana.exists(), f"no se escribió el fichero de Ana: {ruta_ana}"

        # Ana, leyendo otra vez su fichero, recupera su progreso.
        ana_de_nuevo = ach.AchievementSystem()
        ana_de_nuevo.load()
        assert ana_de_nuevo._explored_stages == ["stage0", "stage1_1"]

        # Beto, con su propio fichero, no ve el progreso de Ana.
        _identificar("beto@universidad.edu", monkeypatch)
        beto = ach.AchievementSystem()
        beto.load()
        assert beto._explored_stages == []

    def test_el_anonimo_no_escribe_por_otro_estudiante(self, monkeypatch, tmp_path) -> None:
        import src.engine.core.achievements as ach

        base = tmp_path / "achievements.json"
        monkeypatch.setattr(ach, "ACHIEVEMENTS_PATH", base)

        _identificar("ana@universidad.edu", monkeypatch)
        ana = ach.AchievementSystem()
        ana.mark_explorer("stage0")
        ana.save()
        contenedor = tmp_path / "achievements.json"
        assert not contenedor.exists(), (
            "identificarse guardó en el fichero global: dos estudiantes "
            "siguen compartiendo progreso"
        )

    def test_el_formato_por_estudiante_es_el_mismo_que_antes(self, monkeypatch, tmp_path) -> None:
        """El formato en disco no cambia con el perfil; cambia solo la ruta."""
        import src.engine.core.achievements as ach

        base = tmp_path / "achievements.json"
        monkeypatch.setattr(ach, "ACHIEVEMENTS_PATH", base)

        _identificar("ana@universidad.edu", monkeypatch)
        ana = ach.AchievementSystem()
        ana.mark_explorer("stage0")
        ana.save()
        datos = orjson.loads(ach._ruta_de_logros().read_bytes())
        assert "progress" in datos and "stats" in datos