from maya.api import OpenMaya as om
from dcc.ui import quicwidget
from .. import InvalidateReason

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QAbstractTab(quicwidget.QUicWidget):
    """
    Overload of `QUicWidget` that outlines tab behaviour.
    """

    # region Enums
    InvalidateReason = InvalidateReason
    # endregion

    # region Properties
    @property
    def scene(self):
        """
        Returns the scene interface.

        :rtype: mpyscene.MPyScene
        """

        return self.window().scene

    @property
    def selection(self):
        """
        Getter method that returns the current selection.

        :rtype: List[mpynode.MPyNode]
        """

        return self.window().selection

    @property
    def selectionCount(self):
        """
        Getter method that returns the current selection count.

        :rtype: int
        """

        return self.window().selectionCount

    @property
    def selectedNode(self):
        """
        Getter method that returns the first selected node.

        :rtype: Union[mpynode.MPyNode, None]
        """

        return self.window().selectedNode
    # endregion

    # region Methods
    def loadSettings(self, settings):
        """
        Loads the user settings.

        :type settings: QtCore.QSettings
        :rtype: None
        """

        pass

    def saveSettings(self, settings):
        """
        Saves the user settings.

        :type settings: QtCore.QSettings
        :rtype: None
        """

        pass

    def currentName(self):
        """
        Returns the current node name.

        :rtype: str
        """

        return self.window().currentName()

    def currentColor(self):
        """
        Returns the current wire-color.

        :rtype: Tuple[float, float, float]
        """

        return self.window().currentColor()

    def colorType(self):
        """
        Returns the current color type.

        :rtype: ColorType
        """

        return self.window().colorType()

    def invalidate(self, reason=None):
        """
        Refreshes the user interface.

        :type reason: Union[InvalidateReason, None]
        :rtype: None
        """

        pass
    # endregion
