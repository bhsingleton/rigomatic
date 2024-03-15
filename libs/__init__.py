from enum import IntEnum


class ColorType(IntEnum):
    """
    Enum class of all available color types.
    """

    NONE = -1
    OBJECT_COLOR_INDEX = 0
    OBJECT_COLOR_RGB = 1
    WIRE_COLOR_RGB = 2
    OVERRIDE_COLOR_INDEX = 3
    OVERRIDE_COLOR_RGB = 4
