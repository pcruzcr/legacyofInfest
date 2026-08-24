"""
Module: test_dynamic_music
System: tests
Description: AUD-485 — la resolución de pista de música debe preferir `.ogg`
sobre `.wav` cuando los dos existen, para que la conversión de AUD-484 sirva
para algo. El orden contrario sólo se justificaba mientras existían `.ogg`
mal etiquetados (AUD-159); esa entrada de `KNOWN_GAPS`/`test_auditoria_157_160`
documenta que los tres restantes eran del contenido de música y ya no están
en `assets/music/` — verificado aquí mismo por `test_auditoria_157_160` antes
de tocar nada.
"""
from __future__ import annotations

from src.engine.core import settings
from src.framework.audio.dynamic_music import DynamicMusicSystem, resolver_pista_de_musica


def test_resolver_pista_prefiere_ogg_cuando_los_dos_existen() -> None:
    """Un nombre con `.wav` y `.ogg` reales debe devolver el `.ogg`."""
    base = settings.ASSETS_DIR / "music"
    candidatos = [
        p.stem for p in base.glob("*.wav")
        if p.with_suffix(".ogg").exists()
    ]
    assert candidatos, "no hay ningún par .wav/.ogg real para probar contra"
    nombre = candidatos[0]
    ruta = resolver_pista_de_musica(nombre)
    assert ruta is not None
    assert ruta.suffix == ".ogg", (
        f"con .wav y .ogg disponibles para '{nombre}' debería preferir .ogg, "
        f"devolvió {ruta}"
    )


def test_resolver_pista_cae_a_wav_si_no_hay_ogg(tmp_path, monkeypatch) -> None:
    """Sin `.ogg`, sigue sirviendo el `.wav` — ningún mapa se queda mudo."""
    musica = tmp_path / "music"
    musica.mkdir()
    (musica / "solo_wav.wav").write_bytes(b"RIFF" + b"\0" * 40)
    monkeypatch.setattr(settings, "ASSETS_DIR", tmp_path)
    ruta = resolver_pista_de_musica("solo_wav")
    assert ruta is not None and ruta.suffix == ".wav"


def test_resolver_pista_none_si_no_existe_ninguna(tmp_path, monkeypatch) -> None:
    musica = tmp_path / "music"
    musica.mkdir()
    monkeypatch.setattr(settings, "ASSETS_DIR", tmp_path)
    assert resolver_pista_de_musica("no_existe_esto") is None


def test_get_track_for_intensity_prefiere_ogg(monkeypatch, tmp_path) -> None:
    """AUD-485: `_get_track_for_intensity` usaba `.wav` a mano — debe pasar
    por el mismo resolutor que prefiere `.ogg`."""
    musica = tmp_path / "music"
    musica.mkdir()
    (musica / "zona1_boss.wav").write_bytes(b"RIFF" + b"\0" * 40)
    (musica / "zona1_boss.ogg").write_bytes(b"OggS" + b"\0" * 40)
    monkeypatch.setattr(settings, "ASSETS_DIR", tmp_path)

    sistema = DynamicMusicSystem(audio_manager=None)
    sistema.set_zone(0, "zona1")
    pista = sistema._get_track_for_intensity(DynamicMusicSystem.INTENSITY_BOSS)
    assert pista is not None and pista.suffix == ".ogg"
