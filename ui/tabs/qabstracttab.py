from abc import abstractmethod
from dcc.vendor.Qt import QtCore, QtWidgets, QtGui
from dcc.ui.abstract import qabcmeta
from .. import InvalidateReason

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QAbstractTab(QtWidgets.QWidget, metaclass=qabcmeta.QABCMeta):
    """
    Overload of `QWidget` that outlines tab behaviour.
    """

    # region Enums
    InvalidateReason = InvalidateReason
    # endregion

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key parent: QtWidgets.QWidget
        :key f: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        parent = kwargs.get('parent', None)
        f = kwargs.get('f', QtCore.Qt.WindowFlags())

        super(QAbstractTab, self).__init__(parent=parent, f=f)

    def __post_init__(self, *args, **kwargs):
        """
        Private method called after an instance has initialized.

        :rtype: None
        """

        # Setup user interface
        #
        self.__setup_ui__(*args, **kwargs)

    @abstractmethod
    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        pass
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

    def colorMode(self):
        """
        Returns the current color mode.

        :rtype: ColorMode
        """

        return self.window().colorMode()

    def invalidate(self, reason=None):
        """
        Refreshes the user interface.

        :type reason: Union[InvalidateReason, None]
        :rtype: None
        """

        pass
    # endregion
