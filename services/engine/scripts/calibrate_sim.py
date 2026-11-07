"""Calibration table vs HTW literature (H0 4,500 kWh; no feed-in cap). Run from services/engine."""
from engine.sim import simulate

HOME = {"demandKwh": 4500}
print("kWp  battery  selfCons  autarky  cycles")
for kwp in (4.5, 10):
    for bat in (0, 4.5, 5, 10):
        r = simulate(HOME, {"pv": {"kwp": kwp}, "battery": {"kwh": bat}}, {"feedInCap": False})
        print(f"{kwp:>4} {bat:>7}  {r['selfConsumption']*100:7.1f}%  {r['autarky']*100:6.1f}%  {r['fullCyclesPerYear']:6.0f}")
