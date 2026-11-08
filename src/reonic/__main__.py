"""CLI:  python -m reonic synth | build | eval | train"""
import argparse

from . import artifact, data, evaluate, synth
from .engine import Designer


def main() -> None:
    ap = argparse.ArgumentParser(prog="reonic")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("synth", help="write fake data in the canonical schema")
    s.add_argument("--n", type=int, default=1600)
    s.add_argument("--out", default="data/synthetic.csv")
    b = sub.add_parser("build", help="raw export -> one canonical row per project (for inspection)")
    b.add_argument("--data", default="data/raw")
    b.add_argument("--out", default="data/projects.csv")
    for name in ("eval", "train"):
        p = sub.add_parser(name)
        p.add_argument("--data", default=None, help="raw export folder (default data/raw if present) or canonical CSV")
        p.add_argument("--group-col", default=None, help="hold out whole groups, e.g. installer_id (eval only)")
        p.add_argument("--out", default="models/designer.joblib")
    a = ap.parse_args()
    if getattr(a, "data", "x") is None:
        a.data = data.default_data_path()

    if a.cmd == "synth":
        synth.generate(a.n).to_csv(a.out, index=False)
        print(f"wrote {a.out}")
    elif a.cmd == "eval":
        print(f"data: {a.data}")
        evaluate.print_report(evaluate.run(data.load(a.data), group_col=a.group_col))
        print("details: reports/eval.json, reports/test_predictions.csv")
    elif a.cmd == "build":
        df = data.load(a.data)
        df.to_csv(a.out, index=False)
        print(f"wrote {len(df)} projects to {a.out}")
        print("PV size source:", df["pv_source"].value_counts().to_dict() if "pv_source" in df else "n/a")
    elif a.cmd == "train":
        artifact.save(a.out, Designer.train(data.load(a.data)), artifact.signature(a.data))
        print(f"saved {a.out}")


if __name__ == "__main__":
    main()
