from enum import Enum

WATER_LEVEL_NAME = 'name'
WATER_LEVEL_DISPLAY_ORDER = 'display_order'


class WaterLevel(Enum):
    """
    Water level enum
    """
    DRY = {
        WATER_LEVEL_NAME: 'Dry',
        WATER_LEVEL_DISPLAY_ORDER: 1
    }
    ISOLATED_POOLS = {
        WATER_LEVEL_NAME: 'Isolated pools',
        WATER_LEVEL_DISPLAY_ORDER: 2
    }
    MODERATE_FLOW = {
        WATER_LEVEL_NAME: 'Moderate flow',
        WATER_LEVEL_DISPLAY_ORDER: 3
    }
    HIGH_FLOW = {
        WATER_LEVEL_NAME: 'High flow',
        WATER_LEVEL_DISPLAY_ORDER: 4
    }
    LOW_FLOW = {
        WATER_LEVEL_NAME: 'Low flow',
        WATER_LEVEL_DISPLAY_ORDER: 5
    }
    FLOOD = {
        WATER_LEVEL_NAME: 'Flood',
        WATER_LEVEL_DISPLAY_ORDER: 6
    }
