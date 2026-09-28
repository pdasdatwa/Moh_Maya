from app.simulation.context import SimulationContext, mutate_json


class EconomyEngine:
    """Simple money/inventory movement. Not a national economy simulator."""

    def process_tick(self, ctx: SimulationContext) -> None:
        for business in ctx.businesses:
            if business.business_type != "cafe":
                continue
            inventory = (business.resources or {}).get("inventory") or {}
            if "coffee" not in inventory:
                continue
            if (business.states or {}).get("operational") != "open":
                continue
            if (business.states or {}).get("morning_prep_applied"):
                continue

            def prep(data: dict) -> None:
                current_inventory = dict(data.get("inventory") or {})
                coffee = current_inventory.get("coffee")
                if isinstance(coffee, int) and coffee > 0:
                    current_inventory["coffee"] = coffee - 1
                data["inventory"] = current_inventory

            mutate_json(business, "resources", prep)
            mutate_json(
                business,
                "states",
                lambda data: data.update({"morning_prep_applied": True}),
            )
            ctx.note(f"{business.name} used a unit of inventory for morning prep")
