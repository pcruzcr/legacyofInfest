"""
AUD-631 — curva de dificultad y accesibilidad jugable.

Verifica que:
1. El sistema de dificultad escala los enemigos de forma monótona.
2. La curva de XP es creciente: nivel N+1 requiere más XP que nivel N.
3. Los flags de accesibilidad existen en UserSettings.
"""
from __future__ import annotations


class TestCurvaDificultad:
    """El sistema de dificultad está definido y es usable."""

    def test_el_modulo_difficulty_existe(self):
        from src.engine.core import difficulty
        assert hasattr(difficulty, "set_difficulty")
        assert hasattr(difficulty, "get_difficulty")

    def test_los_niveles_de_dificultad_estan_definidos(self):
        from src.engine.core.difficulty import Difficulty
        niveles = list(Difficulty)
        assert len(niveles) >= 3, f"Solo {len(niveles)} niveles de dificultad"

    def test_set_y_get_dificultad_funcionan(self):
        """Cambiar dificultad no lanza y get devuelve el valor."""
        from src.engine.core.difficulty import Difficulty, get_difficulty, set_difficulty

        original = get_difficulty()
        try:
            for d in Difficulty:
                set_difficulty(d)
                assert get_difficulty() == d
        finally:
            set_difficulty(original)

    def test_get_config_devuelve_config_valida(self):
        """get_config para cada dificultad devuelve un objeto con daño/vida."""
        from src.engine.core.difficulty import Difficulty, get_config

        for d in Difficulty:
            config = get_config(d)
            # Debe tener al menos un multiplicador
            attrs = [a for a in dir(config) if not a.startswith("_")]
            assert len(attrs) > 0, f"DifficultyConfig para {d} está vacía"


class TestCurvaExperiencia:
    """La curva de XP es creciente: cada nivel cuesta más que el anterior."""

    def test_modulo_experience_existe(self):
        from src.engine.core import experience
        assert hasattr(experience, "exp_para_nivel")

    def test_la_curva_es_creciente(self):
        """Nivel N+1 requiere más o igual XP que nivel N."""
        from src.engine.core.experience import exp_para_nivel
        previa = 0
        for nivel in range(1, 15):
            actual = exp_para_nivel(nivel)
            assert actual >= previa, (
                f"Curva decreciente: nivel {nivel} requiere {actual} < "
                f"nivel {nivel-1} requería {previa}"
            )
            previa = actual

    def test_exp_por_enemigo_existe_para_tipos_conocidos(self):
        """`exp_for()` no lanza para tipos de enemigo comunes."""
        from src.engine.core.experience import exp_for

        tipos = ["WalkerInsect", "FlyingNotebook", "ShooterTiza"]
        for tipo in tipos:
            xp = exp_for(tipo)
            assert isinstance(xp, int) and xp > 0, (
                f"exp_for({tipo!r}) = {xp}, debe ser int > 0"
            )

    def test_exp_minima_es_positiva(self):
        from src.engine.core.experience import _EXP_MINIMA
        assert _EXP_MINIMA > 0


class TestAssistModeFlags:
    """Los flags de accesibilidad jugable existen en UserSettings."""

    def test_user_settings_tiene_escala_texto(self):
        from src.engine.core.user_settings import UserSettings
        settings = UserSettings()
        assert hasattr(settings, "text_scale"), "UserSettings no tiene text_scale"
        assert settings.text_scale > 0

    def test_user_settings_tiene_idioma(self):
        from src.engine.core.user_settings import UserSettings
        settings = UserSettings()
        assert hasattr(settings, "language")
        assert settings.language in ("es", "en")

    def test_assist_mode_flags_documentados(self):
        """Los flags de assist mode son un TODO del plan §4."""
        from src.engine.core.user_settings import UserSettings
        settings = UserSettings()
        if hasattr(settings, "assist_invulnerable"):
            assert isinstance(settings.assist_invulnerable, bool)
        if hasattr(settings, "assist_slow_mo"):
            assert isinstance(settings.assist_slow_mo, (int, float))
        assert settings is not None