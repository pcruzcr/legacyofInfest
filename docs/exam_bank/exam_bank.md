# Exam Bank — Practice Exam Generator

**Course:** Legacy of InFest
**Source:** Compiled from `docs/quizzes/` quizzes (Units II, IV, VI, IX)

## Usage

Run `python scripts/generate_exam.py` to generate a random practice exam:

```bash
python scripts/generate_exam.py                    # 10 random questions
python scripts/generate_exam.py --unit II           # Unit II only
python scripts/generate_exam.py --num-questions 5   # 5 questions
```

## Question Bank

| Source | Unit | Topic | Questions |
|--------|------|-------|-----------|
| `quiz_unit02.md` | II | Vectors & 2D Transformations | 7 |
| `quiz_unit04.md` | IV | Interpolation & Animation | 6 |
| `quiz_unit06.md` | VI | Collision Detection & Resolution | 6 |
| `quiz_unit09.md` | IX | Pattern Recognition | 7 |

**Total bank:** 26 questions across 4 units.

## Question Format

Each question targets one of four skill levels:

| Level | Weight | Description |
|-------|--------|-------------|
| Conceptual accuracy | 40% | Theoretical understanding |
| Applied reasoning | 30% | Real-world application |
| Mathematical correctness | 20% | Formula/algorithm computation |
| Clarity of expression | 10% | Written communication |

## Exam Generation Logic

1. Select unit(s) based on `--unit` (or all if omitted)
2. Shuffle questions within each unit
3. Pick `--num-questions` (default: 10) distributing evenly across units
4. Output randomized exam with answer key


--- Traducción al Español ---

## Banco de Exámenes — Generador de Exámenes de Práctica

**Fuente:** Compilado de los quizzes (Unidades II, IV, VI, IX)

### Uso
```
python scripts/generate_exam.py                    # 10 preguntas aleatorias
python scripts/generate_exam.py --unit II           # Solo Unidad II
python scripts/generate_exam.py --num-questions 5   # 5 preguntas
```

### Banco de Preguntas
- Unidad II (Vectores): 7 preguntas
- Unidad IV (Interpolación): 6 preguntas
- Unidad VI (Colisiones): 6 preguntas
- Unidad IX (Patrones): 7 preguntas
**Total:** 26 preguntas en 4 unidades.

### Formato de Preguntas
Cada pregunta apunta a uno de cuatro niveles: Precisión conceptual (40%), Razonamiento aplicado (30%), Corrección matemática (20%), Claridad de expresión (10%).
