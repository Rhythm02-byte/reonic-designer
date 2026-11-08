// ours: additions to Faris's lib/copy.ts without editing it (so his file can be re-copied verbatim).
// Runs once on import (components/AskNext.tsx imports it, which his Planner mounts).
import { CHOICE_LABEL, FIELD_COPY, FIELD_GROUPS, type FieldCopy } from "./copy";

// Our engine's heating enum has one more value than his labels.
CHOICE_LABEL.other_renewable ??= "Other renewable";

// The roof size is the engine's top Ask-next question; show it with the home so an answer can be seen and edited.
const roof: FieldCopy = { label: "Roof fits about", unit: "modules", step: 1 };
const home = FIELD_GROUPS.find((g) => g.title === "Home & household");
if (home && !("roof_max_modules" in home.fields)) home.fields.roof_max_modules = roof;
FIELD_COPY.roof_max_modules ??= roof;
