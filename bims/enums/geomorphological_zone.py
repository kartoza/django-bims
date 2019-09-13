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
    UPLAND_TRANSITIONAL = 'Upland transitional'
    FOOTHILL_OR_TRANSITIONAL = 'Foothil/Transitional'
    UPLAND_PLATEAU = 'Upland plateau'
    FOOTHILL = 'Foothill'


GEOMORPHOLOGICAL_ZONE_CATEGORY_ORDER = [
    GeomorphologicalZoneCategory.SOURCE_ZONE,
    GeomorphologicalZoneCategory.MOUNTAIN_HEADWATER_STREAM,
    GeomorphologicalZoneCategory.MOUNTAIN_STREAM,
    GeomorphologicalZoneCategory.TRANSITIONAL,
    GeomorphologicalZoneCategory.UPPER_FOOTHILL,
    GeomorphologicalZoneCategory.LOWER_FOOTHILL,
    GeomorphologicalZoneCategory.LOWLAND_RIVER,
    GeomorphologicalZoneCategory.REJUVENATED_BEDROCK_FALL_CASCADES,
    GeomorphologicalZoneCategory.REJUVENATED_FOOTHILL,
    GeomorphologicalZoneCategory.UPLAND_FLOODPLAIN
]
