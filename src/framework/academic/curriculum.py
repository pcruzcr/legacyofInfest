"""
El plan de estudios: qué unidad va antes de cuál, y qué se enseña en cada una.

AUD-095 — por qué existe este módulo
====================================
Antes, `DemoMenuScene` tenía una lista de diecisiete tuplas planas. De ellas
salía todo: el orden de aparición, el nombre de la unidad y la clave de la
escena. No había noción de *unidad académica*, así que:

- Las diez demos estaban disponibles desde el primer minuto. Un estudiante
  podía abrir reconocimiento de patrones (Unidad IX) sin haber visto un
  vector, y no entendía nada de lo que veía.
- No había ninguna explicación de las matemáticas. La escena dibujaba una
  Bézier; de dónde sale el polinomio de Bernstein, en ninguna parte.
- No había forma de saber si el estudiante había entendido algo. El
  cuestionario existía pero no bloqueaba ni registraba nada: se abría con Q,
  se contestaba, y se olvidaba al cerrar la escena.

Este módulo es la fuente única de esas tres cosas: **orden**, **teoría** y
**preguntas**. Es datos, no lógica; la lógica de progreso está en
`progress.py` y el dibujado en las escenas.

Sobre el contenido de la teoría
-------------------------------
Cada unidad trae bloques con una fórmula y su explicación, y una referencia
al fichero del motor donde esa fórmula está implementada. Eso último es
deliberado: el valor de este proyecto como material docente es que la
distancia entre la fórmula de la pizarra y el código que la ejecuta sea de un
clic, no de una búsqueda.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType


@dataclass(frozen=True)
class BloqueTeorico:
    """Una idea: su enunciado, su fórmula y dónde vive en el código."""

    titulo: str
    formula: str
    explicacion: str
    #: Ruta, relativa a la raíz del repositorio, del fichero que la implementa.
    codigo: str


@dataclass(frozen=True)
class Pregunta:
    """Una pregunta de opción múltiple. `correcta` indexa `opciones`."""

    enunciado: str
    opciones: tuple[str, ...]
    correcta: int
    #: Por qué la respuesta correcta lo es. Se muestra tras contestar, acierte
    #: o falle: una pregunta que sólo dice «mal» no enseña nada.
    porque: str

    def __post_init__(self) -> None:
        if not 0 <= self.correcta < len(self.opciones):
            msg = (
                f"la respuesta correcta ({self.correcta}) cae fuera de las "
                f"{len(self.opciones)} opciones de: {self.enunciado!r}"
            )
            raise ValueError(msg)


@dataclass(frozen=True)
class Unidad:
    """Una unidad del temario, con su demo, su teoría y su examen."""

    #: Identificador estable. Se guarda en el progreso del estudiante, así que
    #: renombrarlo invalida las notas guardadas.
    id: str
    #: Numeración académica tal y como aparece en el programa de la asignatura.
    numero: str
    titulo: str
    resumen: str
    #: Clave con la que `scene_registry` construye la demo.
    escena: str
    teoria: tuple[BloqueTeorico, ...] = field(default_factory=tuple)
    preguntas: tuple[Pregunta, ...] = field(default_factory=tuple)


def _p(enunciado: str, opciones: tuple[str, ...], correcta: int, porque: str) -> Pregunta:
    return Pregunta(enunciado=enunciado, opciones=opciones, correcta=correcta, porque=porque)


def _b(titulo: str, formula: str, explicacion: str, codigo: str) -> BloqueTeorico:
    return BloqueTeorico(titulo=titulo, formula=formula, explicacion=explicacion, codigo=codigo)


# ── El plan ────────────────────────────────────────────────────────
#
# El orden es el del programa de la asignatura y **es también la cadena de
# desbloqueo**: para abrir una unidad hay que haber aprobado la anterior. No
# hay grafo de prerrequisitos porque el temario es lineal; si algún día deja
# de serlo, este orden se sustituye por una lista de dependencias y
# `progress.esta_desbloqueada` es el único sitio que hay que tocar.

PLAN: tuple[Unidad, ...] = (
    Unidad(
        id="vectores",
        numero="II",
        titulo="Vectores",
        resumen="Suma, resta, longitud, normalización y producto escalar.",
        escena="vector",
        teoria=(
            _b(
                "Longitud de un vector",
                "|v| = √(vx² + vy²)",
                "El teorema de Pitágoras aplicado a las componentes. Es la "
                "distancia del origen a la punta del vector. En el juego es "
                "lo que responde a «¿a qué distancia está el jugador?».",
                "src/engine/utils/math_utils.py",
            ),
            _b(
                "Normalización",
                "v̂ = v / |v|,  con |v| ≠ 0",
                "Dividir un vector por su longitud da otro que apunta en la "
                "misma dirección y mide exactamente 1. Sirve para separar "
                "«hacia dónde» de «cuánto»: el enemigo persigue con v̂ y "
                "decide su velocidad aparte. Por eso hay que comprobar que "
                "|v| ≠ 0 antes de dividir.",
                "src/engine/utils/math_utils.py",
            ),
            _b(
                "Producto escalar",
                "a · b = ax·bx + ay·by = |a|·|b|·cos θ",
                "Mide cuánto se parecen dos direcciones. Vale 0 si son "
                "perpendiculares, positivo si apuntan al mismo lado y "
                "negativo si se oponen. Con vectores normalizados el "
                "resultado *es* el coseno del ángulo, que es como se "
                "resuelve «¿el enemigo me ve?» sin calcular ángulos.",
                "src/engine/utils/math_utils.py",
            ),
        ),
        preguntas=(
            _p("¿Qué devuelve normalizar un vector?",
               ("El vector cero", "Un vector de longitud 1 con la misma dirección",
                "El vector multiplicado por 2", "El ángulo del vector"), 1,
               "Normalizar conserva la dirección y fija la longitud en 1."),
            _p("¿Cuánto vale el producto escalar de dos vectores perpendiculares?",
               ("1", "0", "Su producto", "No está definido"), 1,
               "a·b = |a||b|cos θ, y cos 90° = 0."),
            _p("¿Qué hay que comprobar antes de normalizar?",
               ("Que las componentes sean enteras", "Que el vector sea horizontal",
                "Que su longitud no sea cero", "Nada"), 2,
               "Normalizar divide por la longitud: con longitud 0 sería una división por cero."),
            _p("Si a·b < 0 con a y b normalizados, ¿qué se sabe?",
               ("Forman un ángulo mayor de 90°", "Son paralelos",
                "b es más largo que a", "Uno de los dos es cero"), 0,
               "El coseno es negativo justo por encima de los 90°."),
            _p("¿Qué mide |b − a| entre dos posiciones a y b?",
               ("La distancia en línea recta", "La diferencia en X",
                "La suma de coordenadas", "El ángulo entre ellas"), 0,
               "Restar da el vector que va de a a b; su longitud es la distancia."),
        ),
    ),
    Unidad(
        id="transformaciones",
        numero="II/III",
        titulo="Transformaciones 2D",
        resumen="Traslación, rotación, escala, cizalla y composición.",
        escena="transform",
        teoria=(
            _b(
                "Rotación alrededor del origen",
                "x' = x·cos θ − y·sen θ\ny' = x·sen θ + y·cos θ",
                "Cada punto gira sobre el origen. Nótese que rota alrededor "
                "del **origen**, no del centro de la figura: para girar una "
                "figura sobre sí misma hay que trasladarla al origen, rotar y "
                "devolverla. Ese es el error clásico de esta unidad.",
                "src/engine/scenes/transform_lab_scene.py",
            ),
            _b(
                "Coordenadas homogéneas",
                "[x' y' 1]ᵀ = M · [x y 1]ᵀ",
                "La traslación no se puede escribir como matriz 2x2, porque "
                "no es lineal: no deja quieto el origen. Añadiendo una "
                "tercera coordenada que siempre vale 1 se convierte en una "
                "matriz 3x3, y entonces traslación, rotación y escala se "
                "componen multiplicando matrices.",
                "src/engine/scenes/transform_lab_scene.py",
            ),
            _b(
                "La composición no es conmutativa",
                "T·R ≠ R·T",
                "Rotar y luego trasladar no da lo mismo que trasladar y luego "
                "rotar. En la demo se ve con el modo COMPOSITE: es la razón "
                "por la que el orden de las operaciones en el código de "
                "dibujado importa tanto.",
                "src/engine/scenes/transform_lab_scene.py",
            ),
        ),
        preguntas=(
            _p("¿Alrededor de qué punto rota la fórmula x' = x·cos θ − y·sen θ?",
               ("Del centro de la figura", "Del origen de coordenadas",
                "De la esquina de la pantalla", "Del centro de la pantalla"), 1,
               "Es una transformación lineal: deja el origen quieto."),
            _p("¿Por qué se usan coordenadas homogéneas?",
               ("Para ahorrar memoria", "Para poder escribir la traslación como matriz",
                "Para trabajar con enteros", "Para acelerar el dibujado"), 1,
               "La traslación no es lineal en 2D; con la tercera coordenada sí es matricial."),
            _p("T·R y R·T con la misma T y la misma R…",
               ("dan siempre lo mismo", "dan lo mismo sólo si θ = 0",
                "dan resultados distintos en general", "no se pueden multiplicar"), 2,
               "La multiplicación de matrices no es conmutativa."),
            _p("¿Qué hace una matriz de cizalla (shear)?",
               ("Gira la figura", "Desplaza cada punto en proporción a la otra coordenada",
                "La escala por igual", "La refleja"), 1,
               "x' = x + shx·y: el desplazamiento en X depende de la Y."),
            _p("Para rotar una figura sobre su propio centro c hay que…",
               ("rotar y ya está", "trasladar por −c, rotar y trasladar por +c",
                "escalar antes", "usar coordenadas polares"), 1,
               "Se lleva el centro al origen, se rota allí y se devuelve."),
        ),
    ),
    Unidad(
        id="curvas",
        numero="III",
        titulo="Curvas y splines",
        resumen="Bézier por de Casteljau, Catmull-Rom y B-spline.",
        escena="curve",
        teoria=(
            _b(
                "Bézier cúbica",
                "B(t) = (1−t)³P₀ + 3(1−t)²t·P₁ + 3(1−t)t²·P₂ + t³P₃,  t ∈ [0,1]",
                "Los coeficientes son los polinomios de Bernstein de grado 3. "
                "Suman 1 para cualquier t, lo que garantiza que la curva "
                "queda dentro de la envolvente convexa de los puntos de "
                "control.",
                "src/framework/processing/curve_tools.py",
            ),
            _b(
                "Algoritmo de de Casteljau",
                "Pᵢ^(k) = (1−t)·Pᵢ^(k−1) + t·Pᵢ₊₁^(k−1)",
                "Interpolación lineal repetida: se interpolan los puntos de "
                "control de dos en dos, luego los resultados de dos en dos, "
                "hasta quedar uno. Es más lento que evaluar el polinomio pero "
                "numéricamente más estable, y se puede dibujar paso a paso, "
                "que es lo que hace el modo DE_CASTELJAU.",
                "src/framework/processing/curve_tools.py",
            ),
            _b(
                "Interpolar frente a aproximar",
                "Catmull-Rom pasa por sus puntos; Bézier y B-spline, no",
                "Una Bézier sólo toca el primero y el último punto de "
                "control; los intermedios tiran de ella. Catmull-Rom pasa por "
                "todos, y por eso es la que se usa para caminos de patrulla: "
                "el punto que se coloca en Tiled es un punto por el que el "
                "enemigo pasa de verdad.",
                "src/framework/processing/curve_tools.py",
            ),
        ),
        preguntas=(
            _p("¿Por cuántos de sus 4 puntos de control pasa una Bézier cúbica?",
               ("Por los 4", "Por 2: el primero y el último", "Por ninguno", "Por 3"), 1,
               "Los intermedios sólo influyen en la forma."),
            _p("¿Qué operación repite el algoritmo de de Casteljau?",
               ("La raíz cuadrada", "La interpolación lineal",
                "El producto escalar", "La derivada"), 1,
               "Son lerps encadenados por niveles."),
            _p("¿Cuánto suman los polinomios de Bernstein para un t dado?",
               ("0", "1", "t", "Depende del grado"), 1,
               "Por eso la curva queda dentro de la envolvente convexa."),
            _p("¿Qué curva conviene para un camino que debe pasar por puntos marcados?",
               ("Bézier cúbica", "B-spline uniforme", "Catmull-Rom", "Ninguna"), 2,
               "Catmull-Rom es interpolante: pasa por sus puntos de control."),
            _p("En B(t), ¿qué recorre t?",
               ("Los grados de 0 a 360", "El intervalo [0, 1]",
                "Los píxeles de la curva", "Los puntos de control"), 1,
               "t es el parámetro normalizado de la curva."),
        ),
    ),
    Unidad(
        id="interpolacion",
        numero="III/IV",
        titulo="Interpolación y suavizado",
        resumen="lerp, curvas de easing y animación por fotogramas clave.",
        escena="interpolate",
        teoria=(
            _b(
                "Interpolación lineal",
                "lerp(a, b, t) = a + (b − a)·t",
                "Con t = 0 da a, con t = 1 da b, y en medio recorre el "
                "segmento a velocidad constante. Es la operación más usada "
                "del motor: cámara, colores, barras de vida, transiciones.",
                "src/engine/utils/math_utils.py",
            ),
            _b(
                "Curvas de suavizado",
                "posición = lerp(a, b, f(t)),  con f(0)=0 y f(1)=1",
                "El truco del easing es que no se toca el lerp: se deforma el "
                "**tiempo** antes de pasárselo. `ease_in_out` arranca y frena "
                "despacio; `ease_out` frena al final. Por eso todas las f "
                "valen 0 en 0 y 1 en 1: si no, el movimiento no llegaría a su "
                "destino.",
                "src/engine/utils/math_utils.py",
            ),
            _b(
                "Independencia del fotograma",
                "t ← t + dt / duración",
                "Avanzar t con dt y no con «un poco cada fotograma» hace que "
                "la animación dure lo mismo a 30 que a 144 fotogramas por "
                "segundo. Es el mismo motivo por el que la física del motor "
                "multiplica siempre por dt.",
                "src/framework/entities/player.py",
            ),
        ),
        preguntas=(
            _p("¿Cuánto vale lerp(a, b, 0)?",
               ("b", "a", "(a+b)/2", "0"), 1,
               "a + (b−a)·0 = a."),
            _p("¿Qué se cambia para conseguir un movimiento suavizado?",
               ("La fórmula del lerp", "El valor de t antes de pasarlo al lerp",
                "Los extremos a y b", "La resolución de pantalla"), 1,
               "El easing deforma el tiempo; el lerp se queda igual."),
            _p("¿Qué debe cumplir una curva de easing f?",
               ("f(0)=0 y f(1)=1", "Ser lineal", "Ser periódica", "Estar acotada por 2"), 0,
               "Si no, la animación no sale del origen o no llega al destino."),
            _p("¿Por qué se avanza t con dt?",
               ("Para gastar menos CPU", "Para que la animación dure lo mismo a cualquier tasa de fotogramas",
                "Para poder usar enteros", "No hace falta"), 1,
               "Sin dt la duración depende de la velocidad de la máquina."),
            _p("En animación por fotogramas clave, ¿qué se interpola?",
               ("Los propios fotogramas clave", "El tramo entre dos fotogramas clave consecutivos",
                "Toda la animación de una vez", "La paleta de color"), 1,
               "Se localiza el tramo y se interpola dentro de él con la t local."),
        ),
    ),
    Unidad(
        id="color",
        numero="V",
        titulo="Espacios de color",
        resumen="RGB, HSV, HSL, CMYK y mezcla alfa.",
        escena="color",
        teoria=(
            _b(
                "Mezcla alfa",
                "out = src·α + dst·(1 − α)",
                "Una media ponderada entre el color que se pinta y el que ya "
                "hay. Con α = 1 el origen tapa; con α = 0 no se ve. Los pesos "
                "suman 1, que es lo que impide que la imagen se aclare u "
                "oscurezca sola al superponer capas.",
                "src/framework/processing/color_tools.py",
            ),
            _b(
                "De RGB a HSV",
                "V = máx(R,G,B)\nS = (máx − mín) / máx\nH = sector donde cae el máximo",
                "RGB dice cuánta luz de cada primario hay; HSV separa el "
                "**tono** de la **saturación** y del **brillo**. Por eso para "
                "«hacer este color más oscuro sin cambiarlo de color» se pasa "
                "a HSV, se baja V y se vuelve: en RGB habría que tocar los "
                "tres canales a la vez y es fácil desviar el tono.",
                "src/framework/processing/color_tools.py",
            ),
            _b(
                "Luminancia",
                "Y = 0,299·R + 0,587·G + 0,114·B",
                "El ojo no es igual de sensible a los tres primarios: el verde "
                "pesa casi seis veces más que el azul. Convertir a gris "
                "haciendo la media de los tres canales da un resultado plano y "
                "equivocado; esta fórmula ponderada es la que usa el motor.",
                "src/framework/processing/filter_tools.py",
            ),
        ),
        preguntas=(
            _p("En out = src·α + dst·(1−α), ¿qué pasa con α = 0?",
               ("Se ve sólo el origen", "Se ve sólo el destino",
                "Se ven mezclados a partes iguales", "Sale negro"), 1,
               "El peso del origen es 0 y el del destino 1."),
            _p("¿Para qué sirve pasar a HSV?",
               ("Para comprimir la imagen", "Para separar tono, saturación y brillo",
                "Para invertir los colores", "Para detectar bordes"), 1,
               "Es la razón de ser del espacio: aísla el tono del brillo."),
            _p("Al convertir a gris, ¿por qué no se hace la media de R, G y B?",
               ("Sería más lento", "Porque el ojo no responde igual a los tres primarios",
                "Porque daría números decimales", "Sí se hace así"), 1,
               "El verde aporta mucho más a la luminancia percibida que el azul."),
            _p("En HSV, ¿qué canal se toca para oscurecer sin cambiar el tono?",
               ("H", "S", "V", "Los tres"), 2,
               "V es el valor o brillo."),
            _p("¿Cuánto suman los pesos de la mezcla alfa?",
               ("α", "1", "2", "Depende del color"), 1,
               "α + (1−α) = 1, y por eso la mezcla no cambia el nivel general."),
        ),
    ),
    Unidad(
        id="ruido",
        numero="V/VIII",
        titulo="Ruido y generación procedural",
        resumen="Ruido de valor, Perlin, octavas y persistencia.",
        escena="noise",
        teoria=(
            _b(
                "Ruido de valor",
                "n(x,y) = interpolación bilineal de valores aleatorios en una rejilla",
                "Se sortea un número por vértice de una rejilla y se "
                "interpola entre ellos. El resultado es continuo, a "
                "diferencia del ruido blanco, y por eso sirve para terreno: "
                "puntos cercanos dan valores parecidos.",
                "src/engine/scenes/noise_lab_scene.py",
            ),
            _b(
                "Ruido de Perlin",
                "n = Σ (gradiente del vértice · vector al punto), interpolado",
                "En vez de un valor por vértice se sortea un **gradiente**, y "
                "se hace el producto escalar con el vector que va del vértice "
                "al punto. Da un ruido sin la retícula visible del ruido de "
                "valor, que es su defecto característico.",
                "src/engine/scenes/noise_lab_scene.py",
            ),
            _b(
                "Ruido fractal",
                "N(x) = Σᵢ pⁱ · n(lⁱ·x),  p = persistencia, l = lacunaridad",
                "Sumar varias capas del mismo ruido, cada una con el doble de "
                "frecuencia y la mitad de amplitud. Las primeras octavas dan "
                "las montañas y las últimas la rugosidad. La persistencia "
                "controla cuánto sobrevive el detalle.",
                "src/engine/scenes/noise_lab_scene.py",
            ),
        ),
        preguntas=(
            _p("¿En qué se diferencia el ruido de valor del ruido blanco?",
               ("En nada", "En que es continuo: puntos cercanos dan valores parecidos",
                "En que usa enteros", "En que es más rápido"), 1,
               "La interpolación entre vértices es lo que lo hace utilizable para terreno."),
            _p("¿Qué se sortea por vértice en el ruido de Perlin?",
               ("Un valor escalar", "Un vector gradiente", "Un color", "Una frecuencia"), 1,
               "Y luego se hace el producto escalar con el vector al punto."),
            _p("¿Qué controla la persistencia en el ruido fractal?",
               ("Cuántas octavas hay", "Cuánta amplitud conserva cada octava siguiente",
                "El tamaño del mapa", "La semilla"), 1,
               "Con persistencia baja el detalle fino casi desaparece."),
            _p("¿Qué hace la lacunaridad?",
               ("Multiplica la frecuencia de cada octava", "Cambia la semilla",
                "Recorta el resultado", "Suaviza los bordes"), 0,
               "Frecuencia por lacunaridad en cada capa; amplitud por persistencia."),
            _p("¿Por qué el mismo mapa se repite con la misma semilla?",
               ("Por casualidad", "Porque el generador pseudoaleatorio es determinista",
                "Porque se guarda en disco", "No se repite"), 1,
               "Misma semilla, misma secuencia: es lo que hace reproducible un mundo procedural."),
        ),
    ),
    Unidad(
        id="colisiones",
        numero="VI",
        titulo="Colisiones AABB",
        resumen="Solapamiento de cajas y resolución por ejes separados.",
        escena="collision",
        teoria=(
            _b(
                "Solapamiento de dos AABB",
                "hay choque ⟺ a.izq < b.der ∧ a.der > b.izq ∧ a.arr < b.aba ∧ a.aba > b.arr",
                "Cuatro comparaciones. Basta con que **una** falle para que no "
                "haya contacto, y por eso conviene escribirlas en ese orden: "
                "la mayoría de los pares se descartan en la primera.",
                "src/framework/stage/collision_system.py",
            ),
            _b(
                "Resolución por ejes separados",
                "resolver X, luego resolver Y (nunca los dos a la vez)",
                "Si se mueve en las dos direcciones y luego se corrige, no hay "
                "forma de saber por cuál se entró. Moviendo y corrigiendo un "
                "eje cada vez, la respuesta es inequívoca. El modo Y-FIRST de "
                "la demo enseña el fallo contrario: tratar cualquier caja "
                "solapada como suelo hace que el jugador trepe por las "
                "paredes.",
                "src/framework/stage/collision_system.py",
            ),
            _b(
                "Aterrizaje con la posición anterior",
                "aterriza ⟺ borde_inferior_anterior ≤ borde_superior_de_la_baldosa",
                "Comparar contra dónde estaba el jugador *antes* de moverse "
                "distingue caer sobre una plataforma de atravesarla desde "
                "abajo. Es también lo que hace posibles las plataformas de un "
                "solo sentido.",
                "src/framework/stage/collision_system.py",
            ),
        ),
        preguntas=(
            _p("¿Cuántas comparaciones bastan para descartar un choque entre dos AABB?",
               ("Las cuatro", "Una que falle", "Dos", "Ninguna, hay que calcular el área"), 1,
               "Los ejes son independientes: si se separan en uno, no hay contacto."),
            _p("¿Por qué se resuelven los ejes por separado?",
               ("Por rendimiento", "Para saber por qué eje se produjo la penetración",
                "Porque pygame lo exige", "Para usar menos memoria"), 1,
               "Resolviendo los dos a la vez la dirección de la corrección es ambigua."),
            _p("¿Qué fallo enseña el modo Y-FIRST de la demo?",
               ("El jugador atraviesa el suelo", "El jugador trepa por las paredes",
                "El jugador no salta", "Los enemigos no se mueven"), 1,
               "Trata la pared como si fuera suelo y sube baldosa a baldosa."),
            _p("¿Para qué sirve guardar el borde inferior anterior?",
               ("Para dibujar la sombra", "Para distinguir aterrizar de atravesar desde abajo",
                "Para calcular la velocidad", "Para el sonido"), 1,
               "Es la condición que hace posibles las plataformas de un sentido."),
            _p("Una plataforma de un solo sentido debe frenar al jugador…",
               ("siempre", "sólo cuando cae sobre ella", "sólo al saltar", "nunca"), 1,
               "Si sube desde abajo tiene que poder pasar."),
        ),
    ),
    Unidad(
        id="imagen",
        numero="VII",
        titulo="Procesamiento digital de imagen",
        resumen="Convolución, filtros, histograma y umbralización.",
        escena="filter",
        teoria=(
            _b(
                "Convolución 2D",
                "g(x,y) = Σᵢ Σⱼ f(x−i, y−j)·h(i,j)",
                "Se desliza una máscara pequeña sobre la imagen y en cada "
                "posición se suman los productos. Cambiando la máscara se "
                "obtiene desenfoque, realce o detección de bordes: es la "
                "misma operación con distintos números.",
                "src/framework/processing/filter_tools.py",
            ),
            _b(
                "Operador de Sobel",
                "Gx = [[−1,0,1],[−2,0,2],[−1,0,1]],  |G| = √(Gx² + Gy²)",
                "Dos convoluciones que aproximan las derivadas parciales. La "
                "fila central pesa el doble porque hace de suavizado a la vez "
                "que de derivada, lo que la vuelve menos sensible al ruido "
                "que una diferencia simple.",
                "src/framework/processing/edge_detection.py",
            ),
            _b(
                "Canny",
                "suavizar → gradiente → supresión no máxima → histéresis",
                "Cuatro pasos. La supresión no máxima adelgaza los bordes a un "
                "píxel de ancho, y la histéresis usa **dos** umbrales: lo que "
                "supera el alto es borde, y lo que supera sólo el bajo lo es "
                "si toca a uno que ya lo era. Ese doble umbral es lo que "
                "evita bordes rotos.",
                "src/framework/processing/edge_detection.py",
            ),
        ),
        preguntas=(
            _p("¿Qué cambia entre un desenfoque y una detección de bordes por convolución?",
               ("El tamaño de la imagen", "Los valores de la máscara",
                "El espacio de color", "El orden de los píxeles"), 1,
               "La operación es la misma; lo que cambia es el núcleo."),
            _p("¿Por qué la fila central de Sobel pesa 2 y no 1?",
               ("Por convención", "Porque suaviza a la vez que deriva",
                "Para que sume 0", "Para acelerar el cálculo"), 1,
               "Ese peso extra es lo que lo hace robusto frente al ruido."),
            _p("¿Cuántos umbrales usa la histéresis de Canny?",
               ("Uno", "Dos", "Tres", "Ninguno"), 1,
               "Uno alto para bordes seguros y uno bajo para los conectados a ellos."),
            _p("¿Qué hace la supresión no máxima?",
               ("Elimina el ruido de fondo", "Adelgaza los bordes a un píxel",
                "Aumenta el contraste", "Rellena huecos"), 1,
               "Conserva sólo el máximo local en la dirección del gradiente."),
            _p("¿Qué representa un histograma de una imagen en gris?",
               ("El brillo medio", "Cuántos píxeles hay de cada nivel de gris",
                "Los bordes detectados", "El tamaño del fichero"), 1,
               "Es la distribución de intensidades, y de ahí sale el umbral de Otsu."),
        ),
    ),
    Unidad(
        id="vision",
        numero="VIII",
        titulo="Segmentación y análisis",
        resumen="Umbral de Otsu, morfología y componentes conexas.",
        escena="vision",
        teoria=(
            _b(
                "Umbral de Otsu",
                "maximizar σ²ₑ(t) = ω₀(t)·ω₁(t)·[μ₀(t) − μ₁(t)]²",
                "Se prueba cada umbral posible y se elige el que más separa "
                "las dos clases de píxeles. No hay que decidir el número a "
                "mano: sale del histograma de la propia imagen.",
                "src/framework/processing/vision_tools.py",
            ),
            _b(
                "Erosión y dilatación",
                "erosión: mínimo en el vecindario · dilatación: máximo",
                "La erosión encoge las regiones claras y se come el ruido "
                "suelto; la dilatación las engorda y cierra agujeros. "
                "Encadenadas dan la apertura (erosión + dilatación) y el "
                "cierre (dilatación + erosión), que limpian sin cambiar el "
                "tamaño de lo que queda.",
                "src/framework/processing/vision_tools.py",
            ),
            _b(
                "Componentes conexas",
                "etiquetar píxeles vecinos con la misma etiqueta (4 u 8 vecinos)",
                "Recorrer la imagen binaria agrupando los píxeles que se "
                "tocan. De cada grupo salen el área, el centroide y la caja "
                "envolvente, que es como se cuenta «cuántos objetos hay» sin "
                "saber qué son.",
                "src/framework/processing/vision_tools.py",
            ),
        ),
        preguntas=(
            _p("¿Qué maximiza el umbral de Otsu?",
               ("El contraste global", "La varianza entre las dos clases",
                "El número de bordes", "La entropía"), 1,
               "Elige el corte que mejor separa fondo de objeto."),
            _p("¿Qué le hace la erosión a una región clara?",
               ("La engorda", "La encoge", "La desplaza", "La invierte"), 1,
               "Toma el mínimo del vecindario, así que los bordes se retiran."),
            _p("¿Qué combinación cierra los agujeros de una región?",
               ("Apertura", "Cierre (dilatación y luego erosión)",
                "Dos erosiones", "Un umbral más alto"), 1,
               "La dilatación tapa el hueco y la erosión devuelve el tamaño."),
            _p("¿Qué sale de etiquetar componentes conexas?",
               ("Los bordes", "Una lista de regiones con su área y su centroide",
                "El histograma", "El umbral óptimo"), 1,
               "Es el paso que convierte píxeles en objetos contables."),
            _p("La conectividad de 8 vecinos, frente a la de 4, une además…",
               ("los píxeles en diagonal", "los píxeles del borde",
                "los de distinto color", "nada"), 0,
               "Con 4 vecinos dos píxeles que sólo se tocan por la esquina quedan separados."),
        ),
    ),
    Unidad(
        id="patrones",
        numero="IX",
        titulo="Reconocimiento de patrones",
        resumen="Descriptores HOG, k-NN y evaluación con matriz de confusión.",
        escena="pattern",
        teoria=(
            _b(
                "Descriptor HOG",
                "histograma de orientaciones del gradiente por celda, normalizado por bloque",
                "En vez de comparar píxeles, se describe la imagen por cómo se "
                "reparten las direcciones de sus bordes. Eso la vuelve "
                "insensible a los cambios de iluminación, que es justo lo que "
                "arruina la comparación píxel a píxel.",
                "src/framework/processing/reference_model.py",
            ),
            _b(
                "Clasificador k-NN",
                "clase(x) = la más votada entre los k vecinos más cercanos",
                "No hay entrenamiento propiamente dicho: se guardan los "
                "ejemplos y se clasifica por proximidad. Es lento al predecir "
                "y sensible a la escala de las variables, pero se explica en "
                "una frase y por eso es el primer clasificador del temario.",
                "src/framework/processing/reference_model.py",
            ),
            _b(
                "Matriz de confusión",
                "precisión = VP / (VP + FP) · exhaustividad = VP / (VP + FN)",
                "Una tasa de acierto global esconde el desequilibrio de "
                "clases: con un 95 % de ejemplos de una clase, decir siempre "
                "esa clase acierta el 95 % y no ha aprendido nada. La matriz "
                "enseña **en qué** se equivoca.",
                "src/framework/processing/reference_model.py",
            ),
        ),
        preguntas=(
            _p("¿Qué describe HOG?",
               ("El color medio", "El reparto de las orientaciones del gradiente",
                "El tamaño del objeto", "La textura por Fourier"), 1,
               "Por eso aguanta los cambios de iluminación."),
            _p("¿Cuándo entrena un k-NN?",
               ("Antes de predecir, con descenso de gradiente", "No entrena: guarda los ejemplos",
                "En cada predicción", "Sólo con datos etiquetados a mano"), 1,
               "Es un método perezoso; todo el coste está en la predicción."),
            _p("¿Por qué no basta con la tasa de acierto global?",
               ("Porque es difícil de calcular", "Porque con clases desequilibradas puede ser alta sin haber aprendido",
                "Porque depende del lenguaje", "Sí basta"), 1,
               "El clasificador trivial de la clase mayoritaria ya la consigue."),
            _p("La exhaustividad (recall) VP/(VP+FN) responde a…",
               ("¿cuántos de los que dije que sí, lo eran?", "¿cuántos de los que eran, encontré?",
                "¿cuántos hay en total?", "¿cuánto tardo?"), 1,
               "Precisión y exhaustividad responden a preguntas distintas y suelen oponerse."),
            _p("¿Qué le pasa a k-NN si una variable tiene un rango mucho mayor que las demás?",
               ("Nada", "Domina la distancia y las demás dejan de contar",
                "Se ignora", "Acelera el cálculo"), 1,
               "Por eso hay que normalizar los descriptores antes de medir distancias."),
        ),
    ),
)

#: Índice por identificador. Inmutable: el plan es dato, no estado.
_POR_ID: MappingProxyType[str, Unidad] = MappingProxyType({u.id: u for u in PLAN})
_POR_ESCENA: MappingProxyType[str, Unidad] = MappingProxyType({u.escena: u for u in PLAN})


def ids_de_unidades() -> tuple[str, ...]:
    """Los identificadores, en el orden del temario."""
    return tuple(u.id for u in PLAN)


def unidad(id_unidad: str) -> Unidad | None:
    """La unidad con ese identificador, o `None` si no existe."""
    return _POR_ID.get(id_unidad)


def unidad_de_escena(clave_escena: str) -> Unidad | None:
    """La unidad a la que pertenece una demo, por su clave de registro.

    Las escenas que no son de una unidad —el cajón de arena, el constructor
    de tuberías, las tablas de récords— devuelven `None`, y por eso están
    siempre disponibles: no forman parte del temario evaluable.
    """
    return _POR_ESCENA.get(clave_escena)


def siguiente_unidad(id_unidad: str) -> Unidad | None:
    """La unidad que viene después, o `None` si es la última."""
    ids = ids_de_unidades()
    if id_unidad not in ids:
        return None
    i = ids.index(id_unidad) + 1
    return PLAN[i] if i < len(PLAN) else None
