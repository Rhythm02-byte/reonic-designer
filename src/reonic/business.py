"""Business case: what faster first designs are worth to an installer, with every assumption visible.

Nothing here is a Reonic figure. Every input is an ASSUMPTION, shown as a conservative / base / optimistic range.
The biggest unknown is how long a design takes today (open question 7 for Reonic). Replace the inputs when
Reonic answers; the formulas stay the same.

The tool produces a first design that a planner reviews and adjusts. It does not replace the planner: our whole
design agrees with the installer's for only about 14% of homes (see reonic-evaluate), so review time is real.
"""
from dataclasses import dataclass

WEEKS_PER_YEAR = 46          # ASSUMPTION: working weeks after holidays
HOURS_PER_WEEK = 40          # ASSUMPTION
MAX_DESIGN_SHARE = 0.80      # sanity limit: a planner cannot spend more than this share of the year designing


@dataclass(frozen=True)
class Scenario:
    name: str
    designs_per_week: float      # per planner. Reonic's brief: planners create "several offers per day"; the number is an assumption
    hours_per_design_today: float  # Reonic's brief says "hours"; the number is an assumption
    minutes_per_design_with_tool: float  # review and adjust a first design. Conservative because most designs need edits
    planner_cost_eur_per_hour: float     # ASSUMPTION: loaded cost of a planner in Germany
    planners: int                        # ASSUMPTION: "mid-sized installation company"


SCENARIOS = (
    Scenario("Conservative", designs_per_week=8, hours_per_design_today=1.0, minutes_per_design_with_tool=45,
             planner_cost_eur_per_hour=45, planners=2),
    Scenario("Base", designs_per_week=12, hours_per_design_today=1.5, minutes_per_design_with_tool=30,
             planner_cost_eur_per_hour=50, planners=3),
    Scenario("Optimistic", designs_per_week=15, hours_per_design_today=2.0, minutes_per_design_with_tool=20,
             planner_cost_eur_per_hour=55, planners=4),
)


def evaluate(s: Scenario) -> dict:
    designs_per_year = s.designs_per_week * WEEKS_PER_YEAR
    hours_today = designs_per_year * s.hours_per_design_today
    hours_with_tool = designs_per_year * s.minutes_per_design_with_tool / 60
    saved = hours_today - hours_with_tool
    available = WEEKS_PER_YEAR * HOURS_PER_WEEK
    return {
        "designs_per_planner_per_year": designs_per_year,
        "hours_designing_today": hours_today,
        "share_of_year_designing_today": hours_today / available,
        "plausible": hours_today <= MAX_DESIGN_SHARE * available,
        "hours_saved_per_planner": saved,
        "share_of_design_time_saved": saved / hours_today,
        "value_per_planner_eur": saved * s.planner_cost_eur_per_hour,
        "hours_saved_per_installer": saved * s.planners,
        "value_per_installer_eur": saved * s.planners * s.planner_cost_eur_per_hour,
        "extra_site_days_per_installer": saved * s.planners / 8,  # if freed hours go to work on site (8 h days)
    }


def sensitivity(base: Scenario = SCENARIOS[1]) -> list[tuple[str, float, float]]:
    """Value per planner when one input moves from the base case to a conservative and an optimistic value."""
    def value(**changes) -> float:
        return evaluate(Scenario(**{**base.__dict__, **changes}))["value_per_planner_eur"]

    return [
        ("hours per design today (1.0 / 1.5 / 2.0)", value(hours_per_design_today=1.0), value(hours_per_design_today=2.0)),
        ("minutes with the tool (45 / 30 / 20)", value(minutes_per_design_with_tool=45), value(minutes_per_design_with_tool=20)),
        ("designs per planner per week (8 / 12 / 15)", value(designs_per_week=8), value(designs_per_week=15)),
        ("planner cost per hour (45 / 50 / 55)", value(planner_cost_eur_per_hour=45), value(planner_cost_eur_per_hour=55)),
    ]


def markdown() -> str:
    rows = {s.name: evaluate(s) for s in SCENARIOS}
    fmt = lambda f, v: f(v)
    lines = ["| | " + " | ".join(rows) + " |", "|---|" + "---|" * len(rows)]
    spec = [
        ("Designs per planner per week", lambda s: f"{s.designs_per_week:g}", True),
        ("Hours per design today", lambda s: f"{s.hours_per_design_today:g}", True),
        ("Minutes per design with the tool", lambda s: f"{s.minutes_per_design_with_tool:g}", True),
        ("Planner cost (€/hour)", lambda s: f"{s.planner_cost_eur_per_hour:g}", True),
        ("Planners per installer", lambda s: f"{s.planners}", True),
    ]
    for label, f, _ in spec:
        lines.append(f"| {label} (assumption) | " + " | ".join(f(s) for s in SCENARIOS) + " |")
    calc = [
        ("Designs per planner per year", "designs_per_planner_per_year", lambda v: f"{v:,.0f}"),
        ("Share of the year spent designing today", "share_of_year_designing_today", lambda v: f"{v:.0%}"),
        ("Hours saved per planner per year", "hours_saved_per_planner", lambda v: f"{v:,.0f}"),
        ("Share of design time saved", "share_of_design_time_saved", lambda v: f"{v:.0%}"),
        ("**Value per planner per year (€)**", "value_per_planner_eur", lambda v: f"**{v:,.0f}**"),
        ("Value per installer per year (€)", "value_per_installer_eur", lambda v: f"{v:,.0f}"),
        ("Site days freed per installer per year", "extra_site_days_per_installer", lambda v: f"{v:,.0f}"),
    ]
    for label, key, f in calc:
        lines.append(f"| {label} | " + " | ".join(f(r[key]) for r in rows.values()) + " |")
    return "\n".join(lines)


if __name__ == "__main__":
    print(markdown())
    print("\nSensitivity of value per planner per year (€), base case with one input moved:")
    for label, lo, hi in sensitivity():
        print(f"  {label:<46} {lo:>8,.0f}  to  {hi:>8,.0f}")
    bad = [s.name for s in SCENARIOS if not evaluate(s)["plausible"]]
    print("\nplausibility check:", "all scenarios fit within working hours" if not bad else f"IMPLAUSIBLE: {bad}")
