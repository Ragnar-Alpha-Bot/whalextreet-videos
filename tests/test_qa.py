"""Revisión automática de calidad (caja/qa.py): separa lo grave de los avisos menores a partir de un informe de `hyperframes check` (datos sintéticos)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "caja"))
import qa  # noqa: E402

LIMPIO = {"layout": {"findings": []}, "contrast": {"findings": []}, "runtime": {"findings": []}, "craft": {"findings": [{"code": "line_unread", "severity": "warning"}] * 5},
          "lint": {"findings": [{"code": "nested_structure_needs_subcomposition", "severity": "warning"}]}}
g, a = qa.analizar(LIMPIO)
assert not g and a == {"line_unread": 5, "nested_structure_needs_subcomposition": 1}, (g, a)
assert qa.informe(g, a)[0].startswith("✔") and "Avisos menores" in qa.informe(g, a)[1]

MALO = {"layout": {"findings": [{"code": "text_overflow", "severity": "warning", "time": 3.2, "message": "Texto fuera del cuadro", "selector": "#s2_t"}]},
        "contrast": {"findings": [{"code": "contrast_aa_failure", "severity": "warning", "time": 51.7, "message": "Contraste 2,7:1", "text": "DIARIO", "selector": "#s5_kw"}]},
        "runtime": {"findings": [{"code": "console_error", "severity": "error", "message": "Fallo de JavaScript", "selector": ""}]},
        "craft": {"findings": [{"code": "first_frame_empty", "severity": "warning"}, {"code": "text_below_floor", "severity": "warning", "time": 16.0, "message": "Texto pequeño", "selector": "#x"}]},
        "lint": {"findings": []}}
g, a = qa.analizar(MALO)
cods = sorted(c for _, c, _ in g)
assert cods == ["console_error", "contrast_aa_failure", "text_below_floor", "text_overflow"], cods
assert a == {"first_frame_empty": 1}, "el primer fotograma vacío no es grave: la portada se hace aparte"
txt = " ".join(qa.informe(g, a))
assert "a los 3.2 s" in txt and "[DIARIO]" in txt and "✖" in txt
print("OK: revisión automática de calidad")
