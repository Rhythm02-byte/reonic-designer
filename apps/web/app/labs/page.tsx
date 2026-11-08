// ours: /labs is only an alias; redirect to the canonical /lab (re-exporting the page broke the production build:
// the dynamic history read needs /lab's own loading boundary).
import { redirect } from "next/navigation";

export default function LabsAlias() {
  redirect("/lab");
}
