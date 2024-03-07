from enum import IntEnum


class InvalidateReason(IntEnum):
    """
    Collection of all available invalidation reasons.
    """

    NONE = -1
    TAB_CHANGED = 0
    SCENE_CHANGED = 1
    SELECTION_CHANGED = 2
