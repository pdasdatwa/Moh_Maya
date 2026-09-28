class EntityType:
    WORLD = "world"
    LOCATION = "location"
    PERSON = "person"
    HOUSEHOLD = "household"
    ORGANIZATION = "organization"
    BUSINESS = "business"
    INFRASTRUCTURE = "infrastructure"
    NATURAL_ENTITY = "natural_entity"
    ITEM = "item"
    EVENT = "event"


class RelationshipType:
    CONTAINS = "CONTAINS"
    LOCATED_AT = "LOCATED_AT"
    LIVES_IN = "LIVES_IN"
    MEMBER_OF = "MEMBER_OF"
    WORKS_AT = "WORKS_AT"
    OWNS = "OWNS"
    RELATED_TO = "RELATED_TO"
    KNOWS = "KNOWS"
    PARTICIPATES_IN = "PARTICIPATES_IN"
    LOCATED_IN = "LOCATED_IN"
    DEPENDS_ON = "DEPENDS_ON"
    SERVES = "SERVES"


class WorldStatus:
    PAUSED = "paused"
    ADVANCING = "advancing"


class EventOrigin:
    EMERGENT = "emergent"
    SCHEDULED = "scheduled"
    GOD = "god"


class EventState:
    PENDING = "pending"
    ACTIVE = "active"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class KnowledgeLayer:
    WORLD_TRUTH = "world_truth"
    PERSON = "person"
    PLAYER = "player"


class KnowledgeKind:
    FACT = "fact"
    BELIEF = "belief"
    RUMOR = "rumor"


class ActionType:
    WAIT = "WAIT"
    WALK_TO_CAFE = "WALK_TO_CAFE"
