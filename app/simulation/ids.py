from uuid import UUID


def parse_uuid(value: object) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None


def participant_id(item: dict, role: str) -> UUID | None:
    for participant in item.get("participants") or []:
        if participant.get("role") == role:
            return parse_uuid(participant.get("entity_id"))
    return None


def person_participant_ids(item: dict) -> list[UUID]:
    ids: list[UUID] = []
    for participant in item.get("participants") or []:
        if participant.get("entity_type") != "person":
            continue
        parsed = parse_uuid(participant.get("entity_id"))
        if parsed is not None:
            ids.append(parsed)
    return ids
