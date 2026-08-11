"""AUD-397 — memoria de textura y detección de fugas. Cierra GAP-049.

Qué quedaba del hueco
=====================
`GAP-049` pedía tres cifras de recurso: llamadas de dibujo, memoria de textura
viva, y detección de que una superficie no se libera. La primera se cerró en
AUD-377. Estas son las otras dos.

Por qué el registro vive fuera de `gl_pipeline.py`
==================================================
Para que estas pruebas puedan existir. `gl_pipeline` necesita un contexto
ModernGL para casi todo y en CI no hay ninguno: una medición escrita dentro de
esa clase sería código que no se ejecuta hasta que alguien abra el juego en una
máquina con tarjeta. Instrumentación que sólo corre donde nadie mira es
justamente lo que este hueco existe para evitar.

`MemoriaDeTexturas` no toca OpenGL: registra objetos que declaran `size` y
`components`, y eso lo cumple una textura de ModernGL igual que el doble de
tres líneas de aquí abajo.
"""
from __future__ import annotations

import pytest

from src.engine.render.memoria_de_textura import MemoriaDeTexturas, bytes_de


class _Textura:
    """Lo que `MemoriaDeTexturas` necesita saber de una textura."""

    def __init__(self, ancho: int, alto: int, components: int = 4) -> None:
        self.size = (ancho, alto)
        self.components = components


@pytest.fixture
def memoria() -> MemoriaDeTexturas:
    return MemoriaDeTexturas()


class TestLaCuenta:
    def test_una_textura_pesa_ancho_por_alto_por_canales(self) -> None:
        assert bytes_de(_Textura(800, 600)) == 800 * 600 * 4

    def test_media_resolucion_pesa_la_cuarta_parte(self) -> None:
        """El objetivo de *bloom* va a la mitad de lado, no a la mitad de área."""
        assert bytes_de(_Textura(400, 300)) == bytes_de(_Textura(800, 600)) // 4

    def test_registrar_suma_y_soltar_resta(self, memoria: MemoriaDeTexturas) -> None:
        t = _Textura(100, 100)
        memoria.registrar(t)
        assert memoria.bytes_vivos == 100 * 100 * 4
        memoria.soltar(t)
        assert memoria.bytes_vivos == 0

    def test_soltar_dos_veces_no_estalla(self, memoria: MemoriaDeTexturas) -> None:
        """En una tubería real, un `release()` defensivo pasa dos veces."""
        t = _Textura(10, 10)
        memoria.registrar(t)
        memoria.soltar(t)
        memoria.soltar(t)
        assert memoria.bytes_vivos == 0

    def test_cuenta_las_texturas_vivas(self, memoria: MemoriaDeTexturas) -> None:
        for _ in range(5):
            memoria.registrar(_Textura(10, 10))
        assert memoria.texturas_vivas == 5

    def test_el_pico_no_baja_al_soltar(self, memoria: MemoriaDeTexturas) -> None:
        """El pico es la cifra que decide si algo cabe en una tarjeta modesta;
        la instantánea de ahora mismo no dice nada."""
        t = _Textura(800, 600)
        memoria.registrar(t)
        pico = memoria.pico_de_bytes
        memoria.soltar(t)
        assert memoria.bytes_vivos == 0
        assert memoria.pico_de_bytes == pico

    def test_olvidar_todo_deja_el_registro_a_cero(
        self, memoria: MemoriaDeTexturas
    ) -> None:
        memoria.registrar(_Textura(10, 10))
        memoria.olvidar_todo()
        assert memoria.bytes_vivos == 0
        assert memoria.texturas_vivas == 0


class TestLaDeteccionDeFugas:
    def _correr(self, memoria: MemoriaDeTexturas, fotogramas: int,
                fuga: bool) -> None:
        """Simula fotogramas. Con `fuga`, cada uno reserva y no suelta."""
        reutilizable = _Textura(64, 64)
        memoria.registrar(reutilizable)
        for _ in range(fotogramas):
            if fuga:
                memoria.registrar(_Textura(64, 64))
            memoria.anotar_fotograma()

    def test_una_tuberia_sana_no_parece_fuga(
        self, memoria: MemoriaDeTexturas
    ) -> None:
        """Lo normal: se reutiliza la textura entre fotogramas."""
        self._correr(memoria, 300, fuga=False)
        assert not memoria.parece_fuga()

    def test_reservar_sin_soltar_si_lo_parece(
        self, memoria: MemoriaDeTexturas
    ) -> None:
        """El defecto que el hueco quería poder ver."""
        self._correr(memoria, 300, fuga=True)
        assert memoria.parece_fuga(), (
            "trescientos fotogramas reservando sin soltar y el detector no "
            "dice nada: la fuga clásica seguiría sin verse"
        )

    def test_los_primeros_fotogramas_no_cuentan(
        self, memoria: MemoriaDeTexturas
    ) -> None:
        """Cargar un nivel **siempre** sube. Llamar fuga a eso sería un aviso
        que se aprende a ignorar, que es peor que no avisar."""
        self._correr(memoria, 20, fuga=True)
        assert not memoria.parece_fuga()

    def test_los_dientes_de_sierra_no_son_fuga(
        self, memoria: MemoriaDeTexturas
    ) -> None:
        """Una tubería sana suelta y vuelve a reservar al cambiar de tamaño,
        así que algún escalón hacia abajo aparece siempre.

        El primer intento de esta prueba soltaba **una de cada cincuenta**
        texturas nuevas y esperaba que eso no fuera fuga. Se equivocaba la
        prueba, no el código: quedarse 49 de cada 50 es exactamente una fuga,
        y el detector hacía bien en decirlo. Aquí la memoria sube y se devuelve
        entera, que es lo que se quería expresar.
        """
        vivas: list[_Textura] = []
        for i in range(300):
            t = _Textura(64, 64)
            memoria.registrar(t)
            vivas.append(t)
            if i % 50 == 49:
                for vieja in vivas:
                    memoria.soltar(vieja)
                vivas.clear()
            memoria.anotar_fotograma()
        assert not memoria.parece_fuga()

    def test_el_historial_esta_acotado(self, memoria: MemoriaDeTexturas) -> None:
        """Un detector de fugas que se fuga sería un buen chiste y un mal
        detector: el historial no puede crecer sin techo."""
        for _ in range(MemoriaDeTexturas.VENTANA * 3):
            memoria.anotar_fotograma()
        assert len(memoria._historial) == MemoriaDeTexturas.VENTANA


def test_el_resumen_se_lee_de_un_vistazo() -> None:
    """Es una línea del panel de F11, así que tiene que caber y entenderse."""
    memoria = MemoriaDeTexturas()
    memoria.registrar(_Textura(800, 600))
    resumen = memoria.resumen()
    assert "MiB" in resumen
    assert "1 texturas" in resumen
    assert len(resumen) < 60, f"no cabe en el panel: {resumen!r}"


class TestElCableado:
    """Que la tubería dé de alta y de baja, que es donde esto puede mentir."""

    def test_el_renderer_publica_el_registro(self) -> None:
        from src.engine.render.gl_pipeline import GLRenderer

        renderer = GLRenderer()
        assert isinstance(renderer.memoria_de_textura, MemoriaDeTexturas)
        assert renderer.memoria_de_textura.bytes_vivos == 0

    def test_subir_y_crear_fbos_dan_de_alta(self) -> None:
        """Por AST: los dos sitios donde nacen texturas registran.

        Se comprueba así y no ejecutando la tubería porque eso exige GPU. Es
        una comprobación estructural y se sabe: mira que exista una llamada a
        `memoria_de_textura.registrar` dentro de cada función, no que el número
        salga bien — de eso se encargan las pruebas de arriba, que sí ejercitan
        el registro.
        """
        import ast
        import inspect

        from src.engine.render import gl_pipeline

        arbol = ast.parse(inspect.getsource(gl_pipeline))
        for nombre in ("_subir", "_create_fbos"):
            funcion = next(
                (n for n in ast.walk(arbol)
                 if isinstance(n, ast.FunctionDef) and n.name == nombre),
                None,
            )
            assert funcion is not None, f"no existe {nombre}"
            registra = [
                n for n in ast.walk(funcion)
                if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr == "registrar"
            ]
            assert registra, (
                f"{nombre} crea texturas y no las da de alta: el contador de "
                "memoria diría 0 con la tarjeta llena"
            )
