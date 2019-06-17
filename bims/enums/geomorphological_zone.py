from enum import Enum


class GeomorphologicalZoneCategory(Enum):
    """
    Geomorphological zone category.
    """

    SOURCE_ZONE = 'Source zone'
    MOUNTAIN_HEADWATER_STREAM = 'Mountain headwater stream'
    MOUNTAIN_STREAM = 'Mountain stream'
    TRANSITIONAL = 'Transitional'
    UPPER_FOOTHILL = 'Upper foothill'
    LOWER_FOOTHILL = 'Lower foothill'
    LOWLAND_RIVER = 'Lowland river'
    REJUVENATED_BEDROCK_FALL_CASCADES = 'Rejuvenated bedrock fall / cascades'
    REJUVENATED_FOOTHILL = 'Rejunevated foothill'
    UPLAND_FLOODPLAIN = 'Upland floodplain'
