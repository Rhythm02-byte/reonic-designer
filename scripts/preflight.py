"""Preflight before submitting: one command, pass or fail per check.

    python scripts/preflight.py              # everything
    python scripts/preflight.py --skip-tests # skip the slow unit tests

Checks
  1. unit tests pass
  2. no Reonic data is tracked in git or anywhere in its history
  3. the README results table matches the saved reports
  4. the deck (slides and charts) matches the saved reports and the business-case model
  5. the numbers quoted in docs/demo-script.md match what the app shows on the real data

Checks 3-5 need the reports from `python -m reonic eval`, scripts/repeated_splits.py and scripts/unseen_installer.py.
Check 5 needs the real export in data/raw; without it, it is skipped (not failed). Exit code is 1 if anything fails.
"""
import argparse
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
results: list[tuple[str, str, str]] = []  # (status, name, detail)


def record(status: str, name: str, detail: str = "") -> None:
    results.append((status, name, detail))
    print(f"[{status:4}] {name}" + (f": {detail}" if detail else ""))


def missing(text: str, expected: list[str]) -> list[str]:
    return [e for e in expected if e not in text]


def pct(x: float, digits: int = 1) -> str:
    return f"{x * 100:.{digits}f}%"


def signed(x: float) -> str:
    return f"{x * 100:+.1f}"


def load(name: str):
    path = ROOT / "reports" / name
    return json.loads(path.read_text()) if path.exists() else None


# -- 1 ------------------------------------------------------------------------------------------------
def check_tests() -> None:
    p = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, capture_output=True, text=True)
    last = (p.stdout.strip().splitlines() or ["no output"])[-1]
    record("PASS" if p.returncode == 0 else "FAIL", "unit tests", last)


# -- 2 ------------------------------------------------------------------------------------------------
def check_no_data_in_git() -> None:
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
    bad = [f for f in tracked if re.match(r"^(data/(raw|projects|synthetic)|reports/[^.])", f) or f.endswith((".joblib", ".csv"))]
    history = subprocess.run(["git", "log", "--all", "--name-only", "--pretty=format:"], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
    bad_hist = sorted({f for f in history if re.match(r"^(data/raw|data/projects)", f) or f.endswith((".joblib", ".csv"))})
    ok = not bad and not bad_hist
    record("PASS" if ok else "FAIL", "no data in git or its history", "clean" if ok else f"tracked={bad[:3]} history={bad_hist[:3]}")


# -- 3 ------------------------------------------------------------------------------------------------
def check_readme() -> None:
    rs, un = load("repeated_splits.json"), load("unseen_installer.json")
    if not rs or not un:
        return record("SKIP", "README numbers match reports", "run scripts/repeated_splits.py and scripts/unseen_installer.py first")
    b = rs["B_bootstrap_out_of_fold"]
    expected = []
    for name in ("pv", "battery", "whole"):
        expected += [pct(b[f"{name}_model"]["point"]), pct(b[f"{name}_typical"]["point"]), pct(b[f"{name}_rule"]["point"])]
        g = b[f"{name}_model_minus_typical"]
        expected += [f"{signed(g['point'])} points", f"({signed(g['ci_low'])} to {signed(g['ci_high'])})"]
    for key in ("train_on_2a8ba8e2__test_on_23c108b7", "train_on_23c108b7__test_on_2a8ba8e2"):
        expected.append(f"{pct(un[key]['whole_design'])} vs {pct(un[key]['typical_whole_design'])}")
    text = (ROOT / "README.md").read_text().replace("−", "-")
    miss = missing(text, expected)
    record("PASS" if not miss else "FAIL", "README numbers match reports", f"{len(expected)} numbers checked" if not miss else f"missing {miss}")


# -- 4 ------------------------------------------------------------------------------------------------
def deck_text() -> str:
    path = ROOT / "docs" / "pitch" / "home-energy-designer.pptx"
    out = []
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if re.match(r"ppt/(slides/slide|charts/chart)\d+\.xml$", n):
                out += re.findall(r"<(?:a:t|c:v)>([^<]*)</(?:a:t|c:v)>", z.read(n).decode("utf8"))
    return "\n".join(out).replace("−", "-")


def check_deck() -> None:
    rs, un = load("repeated_splits.json"), load("unseen_installer.json")
    if not rs or not un:
        return record("SKIP", "deck numbers match reports", "reports missing")
    sys.path.insert(0, str(ROOT / "src"))
    from reonic.business import SCENARIOS, evaluate

    a, b = rs["A_thirty_splits"], rs["B_bootstrap_out_of_fold"]
    expected = []
    for who in ("model", "typical", "rule"):
        for metric in ("whole", "pv", "battery"):
            expected.append(f"{a[f'{who}_{metric}']['mean'] * 100:.1f}")
    for name in ("pv", "battery", "whole"):
        g = b[f"{name}_model_minus_typical"]
        expected += [signed(g["point"]), f"{signed(g['ci_low'])} to {signed(g['ci_high'])}"]
    for key in ("train_on_2a8ba8e2__test_on_23c108b7", "train_on_23c108b7__test_on_2a8ba8e2"):
        expected.append(f"{pct(un[key]['whole_design'])} vs {pct(un[key]['typical_whole_design'])}")
    vals = {s.name: evaluate(s)["value_per_planner_eur"] for s in SCENARIOS}
    expected += [f"{vals['Conservative']:.0f}", f"{vals['Base']:.0f}",
                 f"€{round(vals['Conservative'], -3):,.0f} to €{round(vals['Base'], -3):,.0f}"]
    miss = missing(deck_text(), expected)
    record("PASS" if not miss else "FAIL", "deck numbers match reports", f"{len(expected)} numbers checked" if not miss else f"missing {miss}")


# -- 5 ------------------------------------------------------------------------------------------------
def check_demo_script() -> None:
    if not (ROOT / "data" / "raw").is_dir():
        return record("SKIP", "demo script matches the app", "data/raw not found")
    ev = load("eval.json")
    if not ev:
        return record("SKIP", "demo script matches the app", "run python -m reonic eval first")
    sys.path.insert(0, str(ROOT / "src"))
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=300).run()
    options = at.selectbox(key="example").options
    live: dict[str, dict] = {}
    for opt in options[1:]:
        at.selectbox(key="example").select(opt).run()
        ours = {m.label: m.value for m in at.metric if m.label != "Whole design within tolerance"}
        table = at.dataframe[0].value
        live[opt] = {"ours": ours, "expert": dict(zip(table["Component"], table["Expert"])),
                     "inputs": {k: at.session_state[k] for k in ("consumption", "pv_existing")}}
    g = lambda v: v.split()[0] if v != "none" else "0"
    typ, pvx, hp = live[options[1]], live[options[3]], live[options[2]]
    expected = [
        f"PV {g(typ['ours']['PV'])} kWp, battery {g(typ['ours']['Battery'])} kWh",
        f"expert PV {typ['expert']['PV (kWp)']} vs ours {g(typ['ours']['PV'])}, battery {typ['expert']['Battery (kWh)']} vs {g(typ['ours']['Battery'])}",
        f"expert PV {hp['expert']['PV (kWp)']} vs ours {g(hp['ours']['PV'])}, battery {hp['expert']['Battery (kWh)']} vs {g(hp['ours']['Battery'])}, wallbox {hp['expert']['Wallbox (kW)']} vs {g(hp['ours']['Wallbox'])}",
        f"({pvx['inputs']['pv_existing']:.1f} kWp already)",
        f"added only a {pvx['expert']['Battery (kWh)']} kWh battery",
        f"{g(pvx['ours']['PV'])} kWp of new PV",
        pct(ev["model"]["pv_kwp"]["within_tolerance"]), pct(ev["typical"]["pv_kwp"]["within_tolerance"]),
        pct(ev["model"]["battery_kwh"]["within_tolerance"]), pct(ev["typical"]["battery_kwh"]["within_tolerance"]),
        pct(ev["model"]["whole_design_within_tolerance"]), pct(ev["typical"]["whole_design_within_tolerance"]),
    ]
    # refine step: add an EV with 12,000 km to the typical home
    at.selectbox(key="example").select(options[1]).run()
    at.checkbox(key="has_ev").check().run()
    at.number_input(key="ev_km").set_value(12000.0).run()
    after = {m.label: m.value for m in at.metric if m.label != "Whole design within tolerance"}
    expected.append(f"PV goes to {g(after['PV'])} kWp, battery {g(after['Battery'])} kWh, and a wallbox of {g(after['Wallbox'])} kW")
    text = (ROOT / "docs" / "demo-script.md").read_text().replace("**", "")
    miss = missing(text, expected)
    record("PASS" if not miss else "FAIL", "demo script matches the app", f"{len(expected)} phrases checked" if not miss else f"missing {miss}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-tests", action="store_true")
    args = ap.parse_args()
    if not args.skip_tests:
        check_tests()
    check_no_data_in_git()
    check_readme()
    check_deck()
    check_demo_script()
    failed = [r for r in results if r[0] == "FAIL"]
    print(f"\n{len([r for r in results if r[0] == 'PASS'])} passed, {len(failed)} failed, {len([r for r in results if r[0] == 'SKIP'])} skipped")
    sys.exit(1 if failed else 0)
