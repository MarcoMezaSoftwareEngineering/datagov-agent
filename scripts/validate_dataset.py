"""CLI: valida las detecciones de DataGov Agent contra el ground truth del dataset.

Uso:
    python scripts/validate_dataset.py

Carga datagov_agent_dataset/, ejecuta perfilado + calidad, compara con
known_issues_expected.json e imprime una tabla. Sale con código 1 si falla algún
chequeo "duro" (las métricas deterministas). Las métricas duplicate_* se reportan
como informativas (convención de conteo distinta).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.dataset_validation import (  # noqa: E402
    hard_failures,
    load_expected,
    load_tables,
    run_validation,
)


def main() -> int:
    tables = load_tables()
    if not tables:
        print("[ERROR] No se encontraron CSV del dataset. Revisa RAW_DIR en la config.")
        return 1

    expected = load_expected()
    checks = run_validation(tables, expected)

    print("=" * 78)
    print("VALIDACION DataGov Agent vs known_issues_expected.json")
    print("=" * 78)

    current_table = None
    for c in checks:
        if c.table != current_table:
            current_table = c.table
            print(f"\n[{c.table}]")
        status = "OK " if c.ok else ("!! " if c.hard else "~  ")
        tag = "" if c.hard else "  (informativo)"
        print(
            f"  {status} {c.metric:38s} esperado={str(c.expected):<32} "
            f"detectado={c.detected}{tag}"
        )

    fails = hard_failures(checks)
    total_hard = sum(1 for c in checks if c.hard)
    passed_hard = total_hard - len(fails)
    print("\n" + "-" * 78)
    print(f"Chequeos duros: {passed_hard}/{total_hard} OK")
    if fails:
        print("FALLOS DUROS:")
        for c in fails:
            print(f"  - {c.table}.{c.metric}: esperado {c.expected}, detectado {c.detected}")
        return 1
    print("Todos los chequeos duros pasaron. [OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
