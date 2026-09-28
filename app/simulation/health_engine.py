from app.simulation.context import SimulationContext, mutate_json


class HealthEngine:
    """Biological and life-state changes. Formulas are intentionally not locked."""

    def process_tick(self, ctx: SimulationContext) -> None:
        # No global per-tick drain. Character actions already mutate fatigue.
        # This hook exists so later health rules can run without changing orchestration.
        for person in ctx.people:
            health = (person.states or {}).get("health") or {}
            if health.get("condition") == "ill":
                mutate_json(
                    person,
                    "states",
                    lambda data: data.setdefault("health", {}).update({"note": "needs_rest"}),
                )
                ctx.note(f"{person.name} remains ill")
