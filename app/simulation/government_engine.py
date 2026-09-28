from app.simulation.context import SimulationContext


class GovernmentEngine:
    """Institutional boundary. V1 does not simulate government behavior."""

    def process_tick(self, ctx: SimulationContext) -> None:
        return None
