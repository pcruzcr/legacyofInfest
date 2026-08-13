---
document_id: "LOI-AUDIO-049"
title: "Legacy of InFest — Especificación de audio ambiental"
aliases: ["Especificación de audio ambiental", "Ambient Audio"]
tags: ["ambiente", "audio", "sonido"]
description: "Sistema de audio ambiental"
source: "docs/49_AMBIENT_AUDIO.md"
date_processed: "2026-08-12"
---

# Legacy of InFest — Especificación de audio ambiental

**ID del documento:** LOI-AUDIO-049
**Versión:** 1.1.0
**Estado:** Oficial
**Audiencia:** Profesor, ayudantes, estudiantes, asistentes de código

> **AUD-455.** Traduce el documento y lo pone al día: decía que
> `audio_manager.py` tenía 231 líneas y era "toda la funcionalidad de audio
> en una sola clase"; hoy tiene 436 líneas, con un sistema de **4 buses**
> (música, efectos, voz, ambiente), **ducking** (el diálogo baja la música)
> y **voces sintetizadas** que este documento no mencionaba en absoluto.

---

## 1. Visión general

El audio ambiental lo gestiona `AudioManager` (`src/engine/audio/audio_manager.py`), que da soporte de sonido en capas: música de fondo, cruce dinámico de música, efectos de sonido y capas de audio ambiental (viento, lluvia, maquinaria, etc.). El sistema degrada con elegancia si falta un recurso — registra un aviso y sigue en silencio.

---

## 2. Capas de audio

### 2.1 Música de fondo
- `play_music(path, loops=-1, fundido_ms=0)` — reproduce una pista (bucle infinito por defecto; `fundido_ms` funde la entrada)
- `stop_music()`, `pause_music()`, `resume_music()` — ciclo de vida
- `posicion_musica()` — posición actual de reproducción, la usa `RelojMusical` (`music_clock.py`) para sincronizar bloques rítmicos con la pista
- Volumen: `set_music_volume(0.0–1.0)`

### 2.2 Música dinámica (cruce)

La música dinámica es un sistema del framework (`src/framework/audio/dynamic_music.py`), no un método de `AudioManager`:
- `DynamicMusicSystem(audio_manager)` — lo construye `StageScene`
- `set_zone(zone, bgm_track)` — nombra la pista base de la zona actual
- `set_intensity(level)` — cambia a `INTENSITY_CALM` (0), `INTENSITY_COMBAT` (1) o `INTENSITY_BOSS` (2), cruzando entre `{bgm}_traverse.wav` / `{bgm}_combat.wav` / `{bgm}_boss.wav` cuando existen
- `detect_intensity_from_state(has_boss, has_alive_enemies)` — detección automática que usa `StageScene` cada fotograma

### 2.3 Efectos de sonido (SFX)
- `play_sfx(name, volume)` — de un solo disparo, desde `SoundBank`
- `play_stinger(name, volume)` — acento musical corto superpuesto
- `play_sfx_at(name, world_x, screen_center_x, volume)` — paneo estéreo según la posición X en el mundo
- `play_sfx_critico(name, volume, ...)` — variante para sonidos que no se deben silenciar aunque el bus de efectos esté bajo (AUD-el sonido crítico no se calla)

### 2.4 Voces
- `play_voz(name, volume, ...)` — reproduce una línea de voz sintetizada y **baja la música al 35%** mientras suena (mismo generador de audio que el resto del proyecto, no grabaciones)

### 2.5 Capa ambiental
- `play_ambient(path, volume)` — sonido ambiental en bucle
- `crossfade_ambient(path, duration, volume)` — transición suave entre ambientes
- `stop_ambient()`, `set_ambient_volume(vol)` — ciclo de vida

### 2.6 Los 4 buses y el ducking (AUD-144)

El volumen real de cualquier sonido es `master × bus × petición`. Los cuatro buses son `musica`, `efectos`, `voz`, `ambiente`:
- `volumen_de_bus(bus)` / `ajustar_bus(bus, volumen)` — leer y fijar el volumen de un bus
- `agachar_musica(segundos=0.0)` / `soltar_musica()` — el **ducking**: baja la música 0.15s y la sube de vuelta 0.5s; lo dispara un diálogo activo, no el jugador directamente
- La mezcla del ducking y de los buses la implementa `mixer_buses.py` (`Mezclador`)

---

## 3. `SoundBank`

`src/engine/audio/sound_bank.py` — carga y gestiona los recursos de efectos de sonido, con carga perezosa y caché. `AudioManager` lo consulta para toda reproducción de SFX.

---

## 4. Silencio / control de volumen

- `toggle_mute()` — silencio global
- `is_muted` (propiedad) — estado actual
- Controles de volumen individuales para música, efectos y capas ambientales (`music_volume`, `sfx_volume`, propiedades con getter/setter)
- El estado silenciado anula todos los niveles de volumen a 0
- `current_music` (propiedad) — nombre de la pista que suena actualmente

---

## 5. Estado de implementación

**Fichero:** `src/engine/audio/audio_manager.py` (436 líneas)
**Estado:** ✅ Completo — música, cruce dinámico, SFX con paneo, capas ambientales, silencio, control de volumen, 4 buses con ducking, voces sintetizadas
**Nota:** `ambient_particles.py` es un sistema de VFX visual aparte; ver `docs/20_ASSET_BIBLE.md` para las convenciones de recursos de audio.

---
## 🔗 Documentos relacionados

- [[40_DIALOGUE_SYSTEM.md|Sistema de diálogo]]
- [[42_CUTSCENE_SYSTEM.md|Sistema de escenas cinemáticas]]
