"""
Dashboard Web App — Professor dashboard for tracking student progress.

Usage:
    pip install flask
    python web/app.py

    Then open http://localhost:5000 in your browser.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# Path to grading results
RESULTS_DIR = Path(os.environ.get("RESULTS_DIR", "results"))
RESULTS_DIR.mkdir(exist_ok=True)

# Static demo data for when no CI results exist yet
DEMO_STUDENTS = [
    {"name": "student1", "stages": {"stage0": 91, "stage1": 85, "stage2": 0}, "boss": None, "speedrun": 120.5, "achievements": 3},
    {"name": "student2", "stages": {"stage0": 100, "stage1": 92, "stage2": 78}, "boss": 88, "speedrun": 95.2, "achievements": 5},
    {"name": "student3", "stages": {"stage0": 45, "stage1": 0, "stage2": 0}, "boss": None, "speedrun": None, "achievements": 1},
    {"name": "student4", "stages": {"stage0": 88, "stage1": 76, "stage2": 82}, "boss": 92, "speedrun": 105.0, "achievements": 4},
    {"name": "student5", "stages": {"stage0": 95, "stage1": 90, "stage2": 88}, "boss": 95, "speedrun": 88.7, "achievements": 6},
]


def load_results() -> list[dict]:
    """Load grading results from results/ directory."""
    results = []
    if RESULTS_DIR.exists():
        for f in sorted(RESULTS_DIR.glob("*.json")):
            try:
                with open(f) as fh:
                    results.append(json.load(fh))
            except (json.JSONDecodeError, OSError):
                pass
    return results if results else DEMO_STUDENTS


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Professor Dashboard</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #0a0a1a; color: #ccc; padding: 20px; }
  h1 { color: #ffdc50; font-size: 24px; margin-bottom: 20px; }
  h2 { color: #64b5f6; font-size: 18px; margin: 20px 0 10px; }
  table { width: 100%; border-collapse: collapse; background: #12122a; border-radius: 8px; overflow: hidden; }
  th { background: #1a1a3a; color: #ffdc50; padding: 10px 12px; text-align: left; font-size: 13px; }
  td { padding: 10px 12px; border-bottom: 1px solid #222; font-size: 13px; }
  tr:hover { background: #1a1a3a; }
  .score-good { color: #50c850; }
  .score-ok { color: #ffdc50; }
  .score-bad { color: #ff5050; }
  .score-none { color: #555; }
  .summary { display: flex; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
  .card { background: #12122a; border-radius: 8px; padding: 16px; flex: 1; min-width: 140px; }
  .card h3 { color: #888; font-size: 11px; text-transform: uppercase; }
  .card .value { color: #ffdc50; font-size: 28px; font-weight: bold; }
  button { background: #ffdc50; color: #000; border: none; padding: 8px 16px;
           border-radius: 4px; cursor: pointer; font-weight: bold; margin: 4px; }
  button:hover { background: #ffe070; }
  .controls { margin-bottom: 16px; }
</style></head>
<body>
  <h1> Professor Dashboard — Legacy of InFest</h1>

  <div class="summary">
    <div class="card"><h3>Students</h3><div class="value">{{ students|length }}</div></div>
    <div class="card"><h3>Avg Stage</h3><div class="value">{{ avg_stage|round(1) }}%</div></div>
    <div class="card"><h3>Avg Boss</h3><div class="value">{{ avg_boss|round(1) }}%</div></div>
    <div class="card"><h3>Avg Achievements</h3><div class="value">{{ avg_achievements|round(1) }}</div></div>
  </div>

  <div class="controls">
    <button onclick="window.location.reload()">Refresh</button>
  </div>

  <h2>Student Progress</h2>
  <table>
    <tr><th>Student</th><th>Stage 0</th><th>Stage 1</th><th>Stage 2</th><th>Boss</th><th>Speedrun</th><th>Achievements</th></tr>
    {% for s in students %}
    <tr>
      <td>{{ s.name }}</td>
      <td class="{{ s.stage0_class }}">{{ s.stage0 }}</td>
      <td class="{{ s.stage1_class }}">{{ s.stage1 }}</td>
      <td class="{{ s.stage2_class }}">{{ s.stage2 }}</td>
      <td class="{{ s.boss_class }}">{{ s.boss_str }}</td>
      <td class="{{ s.speedrun_class }}">{{ s.speedrun_str }}</td>
      <td>{{ s.achievements }}</td>
    </tr>
    {% endfor %}
  </table>

  <h2>Estimated Grades</h2>
  <table>
    <tr><th>Student</th><th>Stages (50%)</th><th>Boss (25%)</th><th>Speedrun (15%)</th><th>Achievements (10%)</th><th>Total</th></tr>
    {% for s in students %}
    <tr>
      <td>{{ s.name }}</td>
      <td>{{ s.stage_grade }}/50</td>
      <td>{{ s.boss_grade }}/25</td>
      <td>{{ s.speedrun_grade }}/15</td>
      <td>{{ s.achievements_grade }}/10</td>
      <td class="{{ s.total_class }}">{{ s.total }}/100</td>
    </tr>
    {% endfor %}
  </table>

  <p style="margin-top:30px;color:#555;font-size:11px;">
    Dashboard v1.0 — Data from results/ directory. Run auto-graders to populate real data.
  </p>
</body></html>
"""


def _score_class(score: float | None) -> str:
    if score is None:
        return "score-none"
    if score >= 80:
        return "score-good"
    if score >= 60:
        return "score-ok"
    return "score-bad"


def _score_str(score: float | None) -> str:
    if score is None:
        return "-"
    return f"{score:.0f}"


@app.route("/")
def dashboard():
    raw = load_results()

    students = []
    for s in raw:
        stages = s.get("stages", {})
        stage0 = stages.get("stage0") or 0
        stage1 = stages.get("stage1") or 0
        stage2 = stages.get("stage2") or 0

        boss = s.get("boss")
        speedrun = s.get("speedrun")
        achievements = s.get("achievements", 0)

        # Estimated grade: stages 50%, boss 25%, speedrun 15%, achievements 10%
        stage_avg = (stage0 + stage1 + stage2) / 3 if any([stage0, stage1, stage2]) else 0
        stage_grade = stage_avg * 0.5
        boss_grade = (boss or 0) * 0.25
        speedrun_pct = max(0, min(100, 100 - ((speedrun or 999) - 60) * 2)) if speedrun else 0
        speedrun_grade = speedrun_pct * 0.15
        achievements_grade = min(10, achievements * 2)

        total = stage_grade + boss_grade + speedrun_grade + achievements_grade

        students.append({
            "name": s.get("name", "unknown"),
            "stage0": _score_str(stage0),
            "stage0_class": _score_class(stage0),
            "stage1": _score_str(stage1),
            "stage1_class": _score_class(stage1),
            "stage2": _score_str(stage2),
            "stage2_class": _score_class(stage2),
            "boss_str": _score_str(boss),
            "boss_class": _score_class(boss),
            "speedrun_str": f"{speedrun:.1f}s" if speedrun else "-",
            "speedrun_class": _score_class(speedrun_pct) if speedrun else "score-none",
            "achievements": achievements,
            "stage_grade": f"{stage_grade:.1f}",
            "boss_grade": f"{boss_grade:.1f}",
            "speedrun_grade": f"{speedrun_grade:.1f}",
            "achievements_grade": f"{achievements_grade:.1f}",
            "total": f"{total:.1f}",
            "total_class": _score_class(total),
        })

    avg_stage = sum(
        (s.get("stages", {}).get("stage0", 0) +
         s.get("stages", {}).get("stage1", 0) +
         s.get("stages", {}).get("stage2", 0)) / 3
        for s in raw if s.get("stages")
    ) / len(raw) if raw else 0

    avg_boss = sum(s.get("boss", 0) or 0 for s in raw) / len(raw) if raw else 0
    avg_achievements = sum(s.get("achievements", 0) for s in raw) / len(raw) if raw else 0

    return render_template_string(
        HTML_TEMPLATE,
        students=students,
        avg_stage=avg_stage,
        avg_boss=avg_boss,
        avg_achievements=avg_achievements,
    )


@app.route("/api/students")
def api_students():
    return jsonify(load_results())


if __name__ == "__main__":
    print("Dashboard running at http://localhost:5000")
    # AUD-539 — `debug=True` expone el debugger de Werkzeug (ejecución remota
    # de código) si el dashboard se sirve desde otra máquina; es una
    # herramienta local del profesor, no necesita debugger.
    app.run(debug=False, port=5000)
