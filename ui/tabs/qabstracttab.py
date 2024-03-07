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
        Returns the active selection

        :rtype: List[mpynode.MPyNode]
        """

        return self.window().selection

    @property
    def selectionCount(self):
        """
        Returns the active selection count

        :rtype: int
        """

        return self.window().selectionCount

    @property
    def selectedNode(self):
        """
        Returns the active selection

        :rtype: mpynode.MPyNode
        """

        return self.window().selectedNode
    # endregion

    # region Callbacks
    def selectionChanged(self):
        """
        Callback method that notifies the tab of a selection change.

        :rtype: None
        """

        self.invalidate(reason=InvalidateReason.SELECTION_CHANGED)

    def sceneChanged(self):
        """
        Callback method that notifies the tab of a scene change.

        :rtype: None
        """

        self.invalidate(reason=InvalidateReason.SCENE_CHANGED)
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

    def invalidate(self, reason=None):
        """
        Refreshes the user interface.

        :type reason: Union[InvalidateReason, None]
        :rtype: None
        """

        pass
    # endregion
