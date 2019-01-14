from enum import Enum

CHANNEL_TYPE_NAME = 'name'
CHANNEL_TYPE_DISPLAY_ORDER = 'display_order'


class ChannelType(Enum):
    """
    Channel type enum
    """
    BEDROCK = {
        CHANNEL_TYPE_NAME: 'Bedrock',
        CHANNEL_TYPE_DISPLAY_ORDER: 1
    }
    MIXED_BEDROCK_ALLUVIAL = {
        CHANNEL_TYPE_NAME: 'Mixed bedrock and alluvial - dominant type(s)',
        CHANNEL_TYPE_DISPLAY_ORDER: 2
    }
    ALLUVIAL = {
        CHANNEL_TYPE_NAME: 'Alluvial with dominant type(s)',
        CHANNEL_TYPE_DISPLAY_ORDER: 3
    }
