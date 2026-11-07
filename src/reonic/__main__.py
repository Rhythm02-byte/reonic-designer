"""CLI:  python -m reonic synth | eval | train"""
import argparse

from . import data, evaluate, synth
from .engine import Designer


def main() -> None:
    ap = argparse.ArgumentParser(prog="reonic")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("synth", help="write fake data in the canonical schema")
    s.add_argument("--n", type=int, default=3000)
    s.add_argument("--out", default="data/synthetic.csv")
    for name in ("eval", "train"):
        p = sub.add_parser(name)
        p.add_argument("--data", default="data/synthetic.csv")
        p.add_argument("--group-col", default=None, help="split column, e.g. installer_id (eval only)")
        p.add_argument("--out", default="models/designer.joblib")
    a = ap.parse_args()

    if a.cmd == "synth":
        synth.generate(a.n).to_csv(a.out, index=False)
        print(f"wrote {a.out}")
    elif a.cmd == "eval":
        evaluate.print_report(evaluate.run(data.load(a.data), group_col=a.group_col))
        print("details: reports/eval.json, reports/test_predictions.csv")
    elif a.cmd == "train":
        Designer.train(data.load(a.data)).save(a.out)
        print(f"saved {a.out}")


if __name__ == "__main__":
    main()
