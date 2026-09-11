"""AUD-814 — Trazado nuevo del Stage 4.1 «La Entrada al Cementerio Sagrado».

Pasillo horizontal de seis secciones de 160 columnas (960x40 baldosas,
15360x640 px), suelo firme en la fila 32 y cero fosos: la única altura la
dan el repiso del Venado y las dos lomas de la Serpiente, que suben, no
perforan. Todo lo que la escena y el generador del TMX necesitan (fases,
fricción, lomas, grietas, llaves de la puerta final) vive aquí para que el
mapa, el código y la documentación no puedan desincronizarse.
"""
from __future__ import annotations

#: Lado de la baldosa en píxeles.
TS = 16

#: Ancho de cada sección en baldosas. Seis secciones de 160: el nivel se
#: atraviesa de izquierda a derecha y cada fase es un espacio real.
ANCHO_SECCION = 160

#: Dimensiones del mapa en baldosas.
MW = ANCHO_SECCION * 6
MH = 40

#: Fila del suelo llano (y = 512 px).
FILA_SUELO = 30 + 2

#: Grosor de los muros de los extremos, en columnas.
MURO_ANCHO = 2

#: Primera columna de cada fase (0, 160, ..., 800).
INICIO_DE_FASE = tuple(i * ANCHO_SECCION for i in range(6))

# ── Elevaciones (formato: inicio_subida, ancho_subida, ancho_cima,
#    ancho_bajada, fila_cima). Triángulos puros (cima 0): la subida y la
#    bajada comparten el vértice y no hay hueco entre ellas. Sin bloque
#    bajo las rampas salvo la base de seguridad (ver generador): una
#    unión dura entre pendiente y bloque clava al jugador.
#    Repiso del Venado: subida corta que aterriza en el musgo (se aprende
#    a frenar antes de entrar). Lomas de la Serpiente: dos desniveles, el
#    segundo más alto (el «cuello» de la serpiente).
REPISO_VENADO: tuple[int, int, int, int, int] = (288, 8, 0, 8, 28)
LOMA_BAJA: tuple[int, int, int, int, int] = (350, 26, 0, 14, 27)
LOMA_ALTA: tuple[int, int, int, int, int] = (408, 24, 0, 18, 24)
LOMAS_FASE3 = (LOMA_BAJA, LOMA_ALTA)
ELEVACIONES = (REPISO_VENADO, LOMA_BAJA, LOMA_ALTA)


def altura_del_suelo(columna: int) -> int:
    """Fila del suelo en esa columna (FILA_SUELO salvo en elevaciones)."""
    for inicio, sub, cima, baj, fila_cima in ELEVACIONES:
        fin_sub = inicio + sub
        fin_cima = fin_sub + cima
        fin_baj = fin_cima + baj
        if inicio <= columna < fin_sub:
            avance = (columna - inicio) / sub
            return round(FILA_SUELO - avance * (FILA_SUELO - fila_cima))
        if fin_sub <= columna < fin_cima:
            return fila_cima
        if fin_cima <= columna < fin_baj:
            avance = (columna - fin_cima) / baj
            return round(fila_cima + avance * (FILA_SUELO - fila_cima))
    return FILA_SUELO


def perfil_del_suelo() -> tuple[int, ...]:
    """Fila del suelo columna a columna para todo el mapa."""
    return tuple(altura_del_suelo(c) for c in range(MW))


def fase_de_la_columna(columna: float) -> int:
    """Número de fase (1-6) para una columna del mapa."""
    return max(1, min(6, int(columna) // ANCHO_SECCION + 1))


# ── Superficies de fricción (columnas, tipo) ──────────────────────────
#: (inicio, fin, material). El musgo resbala (inercia alta), el lodo frena
#: (multiplicador bajo), el sendero y el polvo son suelo normal.
SEGMENTOS_FRICCION: tuple[tuple[int, int, str], ...] = (
    (8, 148, "sendero"),     # F1: suelo normal (referencia de la demo)
    (190, 229, "musgo"),     # F2: resbala
    (240, 279, "lodo"),      # F2: frena
    (285, 309, "musgo"),     # F2: recoge el aterrizaje del repiso
    (650, 790, "polvo"),     # F5: suelo normal nocturno
)
#: Parámetros físicos por material (los consume la escena).
INERCIA_DEL_MUSGO = 0.15
FRENO_DEL_LODO = 0.88

# ── Puntos de interés (columnas) ──────────────────────────────────────
COLUMNA_SPAWN = 8
COLUMNAS_CHECKPOINT = (12, 172, 332, 492, 652, 812, 932)
#: El bot de P0 demostró que todo se camina salvo los vértices: el primero
#: avisa con tutorial para que ningún jugador lo lea como bug.
COLUMNA_AVISO_CIMA = 280
COLUMNA_LAPIDA_CAMPANERO = 44   # easter egg: M. Tilarán, el campanero
COLUMNA_LAPIDA_MAESTRA = 50     # easter egg: R. Arenal, la maestra
COLUMNA_DIALOGO_VENADO = 215
COLUMNA_ALTAR_VENADO = 235      # llano entre musgo (190-229) y lodo (240-279)
COLUMNA_DIALOGO_SERPIENTE = 340
COLUMNA_ALTAR_SERPIENTE = 466   # llano tras la loma alta (462-479)
COLUMNA_SILENCIO_HALCON = 560   # avance 0.5 de la F4
COLUMNA_DIALOGO_HALCON = 578
COLUMNA_ALTAR_HALCON = 598
COLUMNA_CANTO_PLANICIE = 700
COLUMNA_MIRADOR_FINAL = 905     # cutscene del despertar
COLUMNA_PORTAL_PABURU = 945     # WarpZone a boss_paburu (con llave)
GRIETA_INICIO, GRIETA_FIN, GRIETA_PASO = 820, 940, 10

#: Piras del incendio de la F4 (columnas; el rayo las enciende en orden).
PIRAS_FASE4: tuple[int, ...] = (500, 522, 544)
#: Antorchas del camino (columnas; se encienden en orden al avanzar).
ANTORCHAS_FASE6: tuple[int, ...] = (830, 860, 890, 920)
#: Columnas con luz/grieta de la Fase 6.
COLUMNAS_DE_LUZ = tuple(range(GRIETA_INICIO, GRIETA_FIN + 1, GRIETA_PASO))

# ── Llaves y banderas (la puerta final es causal, no un NextTrigger) ──
LLAVE_VENADO = "espiritu_venado"
LLAVE_SERPIENTE = "espiritu_serpiente"
LLAVE_HALCON = "espiritu_halcon"
LLAVE_PABURU = "paburu_despertado"
BANDERA_VENADO = "stage4_1.spirit_venado_released"
BANDERA_SERPIENTE = "stage4_1.spirit_serpiente_released"
BANDERA_HALCON = "stage4_1.spirit_halcon_released"
BANDERA_PABURU = "stage4_1.paburu_awakened"

#: Texto de las lápidas del easter egg (también en el TMX y el diseño).
TEXTO_CAMPANERO = "M. Tilarán — el campanero. «Aquí sigo, dando las horas a los que ya no las cuentan.»"
TEXTO_MAESTRA = "R. Arenal — la maestra. «Enseñó a leer a medio pueblo; el pueblo la trajo de vuelta.»"
