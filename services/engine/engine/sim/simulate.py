"""Public simulation API: hourly energy balance + 20-year economics for one home and system.

``home`` / ``system`` / ``opts`` are plain dicts following PLAN section 7 (camelCase keys). Every
key is optional. See :func:`simulate` for the keys read.
"""
from __future__ import annotations

import numpy as np

from . import economics as eco
from . import heatpump as hpm
from .battery import DEFAULT as BAT, flows
from .ev import ev_load
from .profiles import calendar, load_profile, pv_profile, pv_unit_profile, temperature

DEFAULT_SIZES = (0, 2.5, 5, 7.5, 10, 12.5, 15, 20)
DEFAULT_HEAT_DEMAND_KWH = 18000.0  # UNVERIFIED typical single-family house, used if heating data is missing
EV_SOCKET_KW = 3.7


# ------------------------------------------------------------------ helpers
def _d(x) -> dict:
    return x if isinstance(x, dict) else {}


def _num(x, default=0.0) -> float:
    try:
        return float(x) if x is not None else default
    except (TypeError, ValueError):
        return default


def _ctx(home: dict, system: dict, opts: dict) -> dict:
    """Resolve inputs and build everything that does not depend on kWp / battery size."""
    m = eco.load_market()
    tar, tech = m["tariffs"], m["technical"]
    notes: list[str] = []
    flags: list[dict] = []
    demand = _num(home.get("demandKwh"), 4500.0)
    base = load_profile(demand, home.get("loadProfile") or "H0", noise=_num(opts.get("loadNoise")), seed=int(_num(opts.get("seed"))))
    temp = temperature()
    heating = _d(home.get("heating"))
    htype = str(heating.get("type") or "Unknown")
    sys_hp = system.get("heatPump")
    cost_fuel = 0.0
    hp_new = np.zeros_like(base)
    hp_exist = np.zeros_like(base)
    heat_demand = None
    if htype == "Heatpump":
        elec = _num(heating.get("hpElecKwh"))
        if elec > 0:
            hp_exist = hpm.hp_electric(temp, elec * 3.4)["elec"]
            notes.append("Existing heat pump included in baseline load.")
    else:
        if heating.get("heatDemandKwh"):
            heat_demand = _num(heating["heatDemandKwh"])
        elif heating.get("fuelKwh") or heating.get("fuelLitres"):
            heat_demand = hpm.heat_demand_kwh("oil" if htype == "Oil" else "gas", heating.get("fuelKwh"),
                                              heating.get("fuelLitres"), bool(heating.get("oldBoiler")))
        fuel_price = tar["oil_eur_kwh"] if htype == "Oil" else tar["gas_eur_kwh"]
        if heating.get("costEurYear"):
            cost_fuel = _num(heating["costEurYear"])
        elif heat_demand:
            eff = hpm.EFFICIENCY["oil" if htype == "Oil" else "gas"]
            cost_fuel = heat_demand / eff * fuel_price
        if sys_hp:
            if not heat_demand:
                heat_demand = DEFAULT_HEAT_DEMAND_KWH
                cost_fuel = cost_fuel or heat_demand / hpm.EFFICIENCY["gas"] * tar["gas_eur_kwh"]
                flags.append({"severity": "info", "code": "heat_demand_default",
                              "message": f"No heating data: assumed {DEFAULT_HEAT_DEMAND_KWH:.0f} kWh heat/yr."})
            hp_kw = _num(_d(sys_hp).get("kw"), 0.0) or None
            hp_new = hpm.hp_electric(temp, heat_demand, hp_thermal_kw=hp_kw)["elec"]
            notes.append("§14a EnWG: controllable HP/wallbox (>4.2 kW) can get reduced grid fees in exchange for "
                         "curtailment; not priced here (tariff specific).")
    ev = _d(home.get("ev"))
    ex_wb = _d(home.get("existingWallbox"))
    sys_wb = system.get("wallbox")
    has_ev = bool(ev.get("has"))
    if sys_wb and not has_ev:
        notes.append("Wallbox without EV in the home inputs: no EV load modelled.")
    ex_pv = _d(home.get("existingPv"))
    ex_kwp = _num(ex_pv.get("kwp"))
    pv_cfg = _d(system.get("pv"))
    orient = pv_cfg.get("orientation") or _d(home.get("building")).get("orientation") or "S"
    roof_flat = str(_d(home.get("building")).get("roofType") or "").lower().startswith("flat")
    tilt = _num(pv_cfg.get("tiltDeg"), 10.0 if roof_flat else 35.0)
    az = pv_cfg.get("azimuthDeg")
    unit_new = pv_unit_profile(orient, tilt, None if az is None else float(az))
    pv_exist = pv_profile(ex_kwp, "S", _num(ex_pv.get("tiltDeg"), 35.0), ex_pv.get("azimuthDeg")) if ex_kwp > 0 else np.zeros_like(base)
    ex_bat = _num(_d(home.get("existingStorage")).get("kwh"))
    cal = calendar()
    night = pv_unit_profile("S", 35.0) < 0.01
    year0 = int(m["as_of"][:4])
    fit_new = _num(opts.get("feedInEurKwh"), tar["feed_in_eur_kwh_le10kwp_partial"])
    fit_ex = _num(ex_pv.get("feedInEurKwh"), fit_new)
    years = int(_num(opts.get("years"), tech["horizon_years"]))
    fit_ex_t = np.full(years, fit_ex)
    if ex_pv.get("builtYear"):
        end = int(ex_pv["builtYear"]) + 20
        fit_ex_t = np.array([fit_ex if year0 + t < end else tar["post_eeg_market_value_eur_kwh"] for t in range(years)])
    return {
        "m": m, "demand": demand, "base": base, "hp_new": hp_new, "hp_exist": hp_exist, "has_ev": has_ev,
        "ev": ev, "ex_wb_kw": _num(ex_wb.get("kw")), "sys_wb": sys_wb, "unit_new": unit_new,
        "pv_exist": pv_exist, "ex_kwp": ex_kwp, "ex_bat": ex_bat, "night": night, "fit_new": fit_new,
        "fit_ex_t": fit_ex_t, "years": years, "fuel_year1": cost_fuel, "heat_demand": heat_demand,
        "has_new_hp": bool(sys_hp), "price": _num(home.get("priceEurKwh"), tar["retail_eur_kwh"]),
        "esc": _num(home.get("priceEscalation"), tar["price_escalation_per_year"]) if home.get("priceEscalation") is not None else tar["price_escalation_per_year"],
        "notes": notes, "flags": flags, "inv_kw": _num(pv_cfg.get("inverterKw")) or None,
        "level": opts.get("priceLevel", "mid"), "opts": opts, "hod": cal["hod"], "month": cal["month"],
    }


def _ev_for(c: dict, pv_total, other, new: bool):
    """EV hourly load for baseline (new=False) or new system."""
    if not c["has_ev"]:
        return 0.0
    ev = c["ev"]
    km = _num(ev.get("kmPerYear"), 15000.0)
    wb_kw = _num(_d(c["sys_wb"]).get("kw"), 0.0) if (new and c["sys_wb"]) else 0.0
    wb_kw = wb_kw or c["ex_wb_kw"] or (11.0 if (new and c["sys_wb"]) else 0.0)
    has_wb = wb_kw > 0
    smart = bool(ev.get("smartCharging"))
    if new:
        mode = c["opts"].get("evMode") or ("solar" if smart and has_wb else "evening")
    else:
        mode = "solar" if (smart and c["ex_wb_kw"] > 0) else "evening"
    if not has_wb:
        mode, wb_kw = "evening", EV_SOCKET_KW
    return ev_load(km, mode, pv_total, other, wb_kw)


def _run(c: dict, kwp_list, bat_list, hourly: bool = False) -> dict:
    """Simulate (kwp_new, battery_new) pairs for year 1 and the last year, plus the baseline."""
    opts = c["opts"]
    tech = c["m"]["technical"]
    years = c["years"]
    deg = (1 - tech["pv_degradation_per_year"]) ** (years - 1)
    fade = max(1 - tech["battery_fade_per_year"] * (years - 1), 0.0)
    n = len(kwp_list)
    cap_on = bool(opts.get("feedInCap", True))
    cap_share = c["m"]["tariffs"]["feed_in_cap_share_of_kwp_without_smart_meter"]
    other = c["base"] + c["hp_new"] + c["hp_exist"]
    # baseline (existing assets, same loads as the new system incl. HP)
    pv0 = c["pv_exist"]
    L0 = other + _ev_for(c, pv0, other, False)
    base = flows(pv0, L0, c["ex_bat"])
    ev_cache: dict = {}
    res = []
    for phase in (0, 1):  # year 1 (full year), last year (every 3rd day, scaled: it is only a snapshot)
        pv_cols, L_cols, nom, cap = [], [], [], []
        for k, b in zip(kwp_list, bat_list):
            new = c["unit_new"] * k
            if c["inv_kw"]:
                new = np.minimum(new, c["inv_kw"])
            key = float(k)
            if key not in ev_cache:
                ev_cache[key] = _ev_for(c, c["pv_exist"] + new, other, True)
            pv_cols.append(c["pv_exist"] + new * (deg if phase else 1.0))
            L_cols.append(other + ev_cache[key])
            nom.append(c["ex_bat"] + b * (fade if phase else 1.0))
            cap.append(cap_share * (c["ex_kwp"] + k) if (cap_on and k > 0) else np.inf)
        nom_a, cap_a = np.array(nom), np.array(cap)
        capv = None if np.all(np.isinf(cap_a)) else cap_a
        if len({float(k) for k in kwp_list}) == 1:  # only the battery varies: shared net, fast 1-D path
            pv_in, L_in = pv_cols[0], L_cols[0]
        else:
            pv_in, L_in = np.stack(pv_cols, 1), np.stack(L_cols, 1)
        scale = 1.0
        if phase:
            hrs = (np.arange(0, 365, 3)[:, None] * 24 + np.arange(24)).ravel()
            pv_in, L_in, scale = pv_in[hrs], L_in[hrs], 365.0 / len(hrs) * 24
        f = flows(pv_in, L_in, nom_a, capv, hourly=(hourly and phase == 0))
        if scale != 1.0:
            for key in ("pv", "load", "import_kwh", "grid_to_load", "export", "curtailed", "self_consumed",
                        "charge_ac", "discharge_ac", "standby_kwh", "cycles"):
                f[key] = f[key] * scale
        res.append(f)
        if phase == 0:
            L_new, pv_y1 = L_cols[0], pv_cols[0]
    new = {k: (np.concatenate([res[0][k], res[1][k]]) if k != "hourly" else res[0][k]) for k in res[0]}
    return {"base": base, "new": new, "n": n, "L_new": L_new, "L0": L0, "pv_y1": pv_y1}


def _economics(c: dict, r: dict, kwp_list, bat_list, opts: dict) -> dict:
    m = c["m"]
    tech, tar = m["technical"], m["tariffs"]
    n = r["n"]
    kwp = np.asarray(kwp_list, float)
    bat = np.asarray(bat_list, float)
    lvl = c["level"]
    pv_p = np.asarray(eco.pv_price_eur(kwp, lvl, m))
    bat_p = np.asarray(eco.battery_price_eur(bat, lvl, m))
    hp_p = eco.hp_price_eur(lvl, m) if c["has_new_hp"] else 0.0
    sub = eco.kfw_subsidy_eur(hp_p, m) if (c["has_new_hp"] and opts.get("kfw", True)) else 0.0
    wb_p = eco.wallbox_price_eur(lvl, m) if c["sys_wb"] else 0.0
    gross = pv_p + bat_p + hp_p + wb_p
    if opts.get("priceEur") is not None and n == 1:
        gross = np.array([float(opts["priceEur"])])
    invest = gross - sub
    om = tech["om_pct_of_pv_battery_capex_per_year"] * (pv_p + bat_p)
    inv_repl = m["inverter_replacement_eur_per_kwp"][lvl] * kwp
    nw, bs = r["new"], r["base"]
    years = c["years"]
    # blended feed-in: existing PV keeps its own rate (EEG end -> market value), new PV the current rate
    wt_ex = c["ex_kwp"] / np.maximum(c["ex_kwp"] + kwp, 1e-9)
    fit1 = wt_ex[None, :] * c["fit_ex_t"][:, None] + (1 - wt_ex[None, :]) * c["fit_new"]
    fuel1 = 0.0 if c["has_new_hp"] else c["fuel_year1"]
    out = eco.project(
        imp0=bs["import_kwh"][0], exp0=bs["export"][0], imp1_first=nw["import_kwh"][:n], exp1_first=nw["export"][:n],
        imp1_last=nw["import_kwh"][n:], exp1_last=nw["export"][n:], price=c["price"], escalation=c["esc"],
        fit0=c["fit_ex_t"], fit1=fit1, fuel0_year1=c["fuel_year1"], fuel1_year1=fuel1,
        fuel_escalation=tar["fuel_escalation_per_year"], invest=invest, om_year=om, inverter_repl=inv_repl,
        years=years, discount=_num(opts.get("discount"), tech["discount_rate"]),
        inverter_year=int(tech["inverter_replacement_year"]))
    out.update(price=gross, subsidy=np.full(n, sub), invest=invest, om=om)
    return out


def _row(c, r, eco_out, kwp_list, bat_list, i: int) -> dict:
    nw, bs = r["new"], r["base"]
    pv = float(nw["pv"][i])
    kt = c["ex_kwp"] + float(kwp_list[i])
    pay = eco_out["payback"][i]
    return {
        "batteryKwh": float(bat_list[i]), "pvKwp": float(kwp_list[i]),
        "pvYieldKwh": pv, "selfConsumption": float(nw["self_consumption"][i]), "autarky": float(nw["autarky"][i]),
        "gridImportKwh": float(nw["import_kwh"][i]), "feedInKwh": float(nw["export"][i]),
        "curtailedKwh": float(nw["curtailed"][i]), "fullCyclesPerYear": float(nw["cycles"][i]),
        "batteryKwhPerKwp": float((c["ex_bat"] + bat_list[i]) / kt) if kt > 0 else 0.0,
        "batteryEmptyShare06": float(nw["empty_share_06"][i]),
        "savingsEurYear": float(eco_out["savings_year1"][i]), "paybackYears": None if np.isnan(pay) else float(pay),
        "npv20": float(eco_out["npv"][i]), "priceEur": float(eco_out["price"][i]),
        "subsidyEur": float(eco_out["subsidy"][i]),
    }


def _typical_days(c, r) -> dict:
    nw = r["new"]
    h = nw["hourly"]
    pv = r["pv_y1"]
    L = r["L_new"]
    out = {}
    for name, months in (("summer", (6, 7, 8)), ("winter", (12, 1, 2))):
        mask = np.isin(c["month"], months)
        def byhod(x):
            x = np.asarray(x)
            return [round(float(x[mask & (c["hod"] == k)].mean()), 3) for k in range(24)]
        out[name] = {
            "pvKwh": byhod(pv), "loadKwh": byhod(L),
            "batteryKwh": byhod(h["charge"][:, 0] - h["discharge"][:, 0]),  # + charging, - discharging (AC)
            "gridKwh": byhod(h["import"][:, 0] - h["export"][:, 0]),  # + import, - export
            "socKwh": byhod(h["soc"][:, 0]),
        }
    return out


def _flags(c, row, kwp_total, bat_total) -> list:
    f = list(c["flags"])
    if bat_total > 0:
        if row["fullCyclesPerYear"] < 150:
            f.append({"severity": "warn", "code": "battery_oversized", "message": f"Only {row['fullCyclesPerYear']:.0f} full cycles/yr (<150): battery likely oversized."})
        if bat_total * BAT.usable > 1.5 * max(kwp_total, 1e-9):
            f.append({"severity": "warn", "code": "battery_vs_kwp", "message": "Usable battery kWh exceeds 1.5 x kWp."})
        night = float(c["base"][c["night"]].sum() / 365.0)
        if bat_total * BAT.usable > night * 1.2:
            f.append({"severity": "info", "code": "battery_vs_night_load", "message": f"Usable capacity exceeds the average nightly load ({night:.1f} kWh)."})
    if row["curtailedKwh"] > 0.02 * max(row["pvYieldKwh"], 1):
        f.append({"severity": "info", "code": "curtailment", "message": f"{row['curtailedKwh']:.0f} kWh/yr curtailed by the 60% feed-in cap."})
    return f


def _pairs(system, kwp_list=None, bat_list=None):
    kwp = _num(_d(system.get("pv")).get("kwp"))
    bat = _num(_d(system.get("battery")).get("kwh"))
    return kwp, bat


# ------------------------------------------------------------------ public API
def simulate(home: dict, system: dict, opts: dict | None = None) -> dict:
    """Hourly (8,760 h) energy balance and 20-year economics of ``system`` in ``home``.

    home keys: demandKwh (4500), loadProfile ("H0"|"FamilyOfFour"|"HomeOffice*"|"Senior*"|"Working*"),
      priceEurKwh, priceEscalation, ev {has, kmPerYear (15000), smartCharging}, existingPv {kwp, tiltDeg,
      azimuthDeg (0=S), builtYear, feedInEurKwh}, existingStorage {kwh}, existingWallbox {kw},
      heating {type, fuelKwh | fuelLitres | heatDemandKwh, costEurYear, oldBoiler, hpElecKwh},
      building {orientation, roofType}.
    system keys: pv {kwp, orientation "S"|"E"|"W"|"EW"|mix, tiltDeg, azimuthDeg, inverterKw},
      battery {kwh}, wallbox {kw}, heatPump {kw}.
    opts keys: feedInCap (True), evMode ("evening"|"solar"|"homeoffice"), loadNoise (0), years (20),
      discount (0.03), priceLevel ("low"|"mid"|"high"), kfw (True), priceEur (override), feedInEurKwh.
    All savings/payback/NPV are *incremental* to the baseline (existing PV/storage, same loads, existing
    heating); ``baseline`` holds the baseline metrics. Fractions (selfConsumption, autarky) are 0..1.
    """
    home, system, opts = _d(home), _d(system), _d(opts)
    c = _ctx(home, system, opts)
    kwp, bat = _pairs(system)
    r = _run(c, [kwp], [bat], hourly=True)
    e = _economics(c, r, [kwp], [bat], opts)
    row = _row(c, r, e, [kwp], [bat], 0)
    nw, bs = r["new"], r["base"]
    night = float(r["L_new"][c["night"]].sum() / 365.0)
    kwp_total = c["ex_kwp"] + kwp
    out = dict(row)
    out.pop("pvKwp"), out.pop("batteryKwh")
    out.update({
        "nightLoadKwh": night, "loadKwh": float(nw["load"][0]),
        "evKwh": float((r["L_new"] - c["base"] - c["hp_new"] - c["hp_exist"]).sum()),
        "hpElecKwh": float(c["hp_new"].sum()), "fuelCostAvoidedEurYear": c["fuel_year1"] if c["has_new_hp"] else 0.0,
        "priceAfterSubsidyEur": float(e["invest"][0]), "omEurYear": float(e["om"][0]),
        "hourlyTypicalDays": _typical_days(c, r),
        "baseline": {"pvYieldKwh": float(bs["pv"][0]), "selfConsumption": float(bs["self_consumption"][0]),
                     "autarky": float(bs["autarky"][0]), "gridImportKwh": float(bs["import_kwh"][0]),
                     "feedInKwh": float(bs["export"][0]), "loadKwh": float(bs["load"][0])},
        "incremental": {"autarkyPts": float(nw["autarky"][0] - bs["autarky"][0]) * 100.0,
                        "pvYieldKwh": float(nw["pv"][0] - bs["pv"][0]),
                        "gridImportKwh": float(nw["import_kwh"][0] - bs["import_kwh"][0])},
        "flags": _flags(c, row, kwp_total, c["ex_bat"] + bat),
        "notes": c["notes"] + ["Reference site Kassel (PVGIS representative year); smooth H0 overstates self-consumption.",
                               f"Prices as of {c['m']['as_of']} (config/market.json); project price overrides."],
        "audit": {"charge_ac": float(nw["charge_ac"][0]), "discharge_ac": float(nw["discharge_ac"][0]),
                  "standby_kwh": float(nw["standby_kwh"][0]), "curtailed": float(nw["curtailed"][0]),
                  "pv": float(nw["pv"][0]), "load": float(nw["load"][0]), "import": float(nw["import_kwh"][0]),
                  "export": float(nw["export"][0]), "delta_soc": float(nw["delta_soc"][0]),
                  "soc_max_usable": float(BAT.usable * (c["ex_bat"] + bat)),
                  "soc_hourly_max": float(nw["hourly"]["soc"][:, 0].max()), "soc_hourly_min": float(nw["hourly"]["soc"][:, 0].min())},
    })
    return out


def sweep_battery(home: dict, system: dict, sizes=DEFAULT_SIZES, opts: dict | None = None) -> list[dict]:
    """Metrics per new battery size (kWh), PV fixed at ``system['pv']``, one pass over 8,760 h.

    Returns a list of dicts (one per size) with batteryKwh, selfConsumption, autarky, gridImportKwh,
    feedInKwh, curtailedKwh, fullCyclesPerYear, batteryEmptyShare06, savingsEurYear, paybackYears,
    npv20, priceEur - the data for the "why this size" chart.
    """
    home, system, opts = _d(home), _d(system), _d(opts)
    c = _ctx(home, system, opts)
    kwp, _ = _pairs(system)
    sizes = [float(s) for s in sizes]
    r = _run(c, [kwp] * len(sizes), sizes)
    e = _economics(c, r, [kwp] * len(sizes), sizes, opts)
    return [_row(c, r, e, [kwp] * len(sizes), sizes, i) for i in range(len(sizes))]


def sweep_pv(home: dict, system: dict, kwp_list, opts: dict | None = None) -> list[dict]:
    """Metrics per new PV size (kWp) with the battery fixed at ``system['battery']``.

    Same row format as :func:`sweep_battery` (rows carry ``pvKwp``).
    """
    home, system, opts = _d(home), _d(system), _d(opts)
    c = _ctx(home, system, opts)
    _, bat = _pairs(system)
    ks = [float(k) for k in kwp_list]
    r = _run(c, ks, [bat] * len(ks))
    e = _economics(c, r, ks, [bat] * len(ks), opts)
    return [_row(c, r, e, ks, [bat] * len(ks), i) for i in range(len(ks))]


def recommend_battery(home: dict, system: dict, sizes=DEFAULT_SIZES, opts: dict | None = None) -> dict:
    """PLAN 6.3 battery sizing: economic optimum capped by night load and the 150-350 cycle band.

    Candidates must have usable kWh <= nightly (no-sun hours) load, usable <= 1.5 x kWp and
    150 <= full cycles/yr <= 350 (if none qualify the band is relaxed to >= 150, then to all sizes).
    ``economic`` = max NPV among candidates (battery 0 if no battery has NPV above no battery);
    ``maxAutarky`` = smallest size reaching 99% of the best autarky within the 1.5 x kWp guard (shown
    as a separate, uneconomic variant). Returns dict(economic, maxAutarky, nightLoadKwh, rows).
    """
    home, system, opts = _d(home), _d(system), _d(opts)
    c = _ctx(home, system, opts)
    kwp, _ = _pairs(system)
    ss = sorted({float(s) for s in sizes} | {0.0})
    r = _run(c, [kwp] * len(ss), ss)
    e = _economics(c, r, [kwp] * len(ss), ss, opts)
    rows = [_row(c, r, e, [kwp] * len(ss), ss, i) for i in range(len(ss))]
    night = float(r["L_new"][c["night"]].sum() / 365.0)
    kt = max(c["ex_kwp"] + kwp, 1e-9)
    guard = [x for x in rows if x["batteryKwh"] > 0 and BAT.usable * x["batteryKwh"] <= night and BAT.usable * x["batteryKwh"] <= 1.5 * kt]
    cand = [x for x in guard if 150 <= x["fullCyclesPerYear"] <= 350] or [x for x in guard if x["fullCyclesPerYear"] >= 150] or guard
    zero = rows[0]
    best = max(cand, key=lambda x: x["npv20"]) if cand else zero
    if best["npv20"] <= zero["npv20"]:
        best = zero
    g2 = [x for x in rows if BAT.usable * x["batteryKwh"] <= 1.5 * kt] or rows
    amax = max(x["autarky"] for x in g2)
    near = [x for x in g2 if x["autarky"] >= amax - 0.01 * abs(amax)]  # 99% of the best; never empty (the best row qualifies)
    alt = min(near or g2, key=lambda x: x["batteryKwh"])
    return {"economic": best, "maxAutarky": alt, "nightLoadKwh": night, "rows": rows}
