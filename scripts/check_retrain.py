"""Bramka jakości Continuous Training: porównaj świeży model z referencyjnym championem.

Czyta ``data/08_reporting/optimized_metrics.json`` (świeży retrening) oraz
``champion_reference.json`` (aktualny champion). Raportuje wynik do
GITHUB_STEP_SUMMARY i kończy się błędem tylko, gdy jakość spadła poniżej twardego
progu (regresja). Uruchamiany z katalogu ``training/``.
"""

import json
import os
import sys
from pathlib import Path

MIN_R2 = 0.85
REPORT = Path("data/08_reporting/optimized_metrics.json")
REFERENCE = Path("champion_reference.json")


def main() -> int:
    new = json.loads(REPORT.read_text())
    ref = json.loads(REFERENCE.read_text()) if REFERENCE.exists() else {"r2": MIN_R2}
    beats = new["r2"] >= ref["r2"]

    verdict = (
        "✅ NOWY MODEL BIJE CHAMPIONA — kwalifikuje się do (re)rejestracji"
        if beats
        else "ℹ️ Nowy model nie bije championa — bez re-rejestracji"
    )
    report = "\n".join(
        [
            "## Continuous Training — wynik retreningu",
            "",
            f"- Nowy: **R²={new['r2']:.4f}**, RMSE={new['rmse']:,.0f} PLN, MAPE={new['mape_pct']:.2f}%",
            f"- Champion referencyjny: R²={ref['r2']:.4f}",
            f"- {verdict}",
        ]
    )
    print(report)

    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        Path(summary_path).write_text(report + "\n")

    if new["r2"] < MIN_R2:
        print(f"::error::R²={new['r2']:.4f} poniżej progu {MIN_R2} — regresja jakości!")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
