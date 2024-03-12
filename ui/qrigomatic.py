from maya import cmds as mc
from maya.api import OpenMaya as om
from mpy import mpyscene
from Qt import QtCore, QtWidgets, QtGui, QtCompat
from dcc.ui import quicwindow
from . import InvalidateReason

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def onSelectionChanged(*args, **kwargs):
    """
    Callback method for any selection changes.

    :rtype: None
    """

    # Check if instance exists
    #
    instance = QRigomatic.getInstance()

    if instance is None:

        return

    # Evaluate if instance is still valid
    #
    if QtCompat.isValid(instance):

        instance.selectionChanged(*args, **kwargs)

    else:

        log.warning('Unable to process selection changed callback!')


def onSceneChanged(*args, **kwargs):
    """
    Callback method for any scene IO changes.

    :rtype: None
    """

    # Check if instance exists
    #
    instance = QRigomatic.getInstance()

    if instance is None:

        return

    # Evaluate if instance is still valid
    #
    if QtCompat.isValid(instance):

        instance.sceneChanged(*args, **kwargs)

    else:

        log.warning('Unable to process scene changed callback!')


class QRigomatic(quicwindow.QUicWindow):
    """
    Overload of `QUicWindow` used to edit rigs.
    """

    # region Enums
    InvalidateReason = InvalidateReason
    # endregion

    # region Dunderscores
    __plugins__ = ('PointHelper', 'TransformConstraint', 'PointOnCurveConstraint')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key parent: QtWidgets.QWidget
        :key flags: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        super(QRigomatic, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._scene = mpyscene.MPyScene.getInstance(asWeakReference=True)
        self._selection = []
        self._selectionCount = 0
        self._selectedNode = None
        self._callbackIds = om.MCallbackIdArray()

        # Declare public variables
        #
        self.tabControl = None
        self.renameTab = None
        self.shapesTab = None
        self.attributesTab = None
        self.constraintsTab = None
        self.publishTab = None
    # endregion

    # region Properties
    @property
    def scene(self):
        """
        Returns the scene interface.

        :rtype: mpyscene.MPyScene
        """

        return self._scene()

    @property
    def selection(self):
        """
        Getter method that returns the current selection.

        :rtype: List[mpynode.MPyNode]
        """

        return self._selection

    @property
    def selectionCount(self):
        """
        Getter method that returns the current selection count.

        :rtype: int
        """

        return self._selectionCount

    @property
    def selectedNode(self):
        """
        Getter method that returns the first selected node.

        :rtype: Union[mpynode.MPyNode, None]
        """

        return self._selectedNode
    # endregion

    # region Callbacks
    def sceneChanged(self, *args, **kwargs):
        """
        Notifies all tabs of a scene change.

        :key clientData: Any
        :rtype: None
        """

        self.currentTab().invalidate(reason=self.InvalidateReason.SELECTION_CHANGED)

    def selectionChanged(self, *args, **kwargs):
        """
        Notifies all tabs of a selection change.

        :key clientData: Any
        :rtype: None
        """

        self._selection = self.scene.selection(apiType=om.MFn.kDependencyNode)
        self._selectionCount = len(self._selection)
        self._selectedNode = self._selection[0] if (self._selectionCount > 0) else None

        self.currentTab().invalidate(reason=self.InvalidateReason.SELECTION_CHANGED)
    # endregion

    # region Events
    def showEvent(self, event):
        """
        Event method called after the window has been shown.

        :type event: QtGui.QShowEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QRigomatic, self).showEvent(event)

        # Load required plugins
        #
        self.loadPlugins()

        # Add callbacks
        #
        hasCallbacks = len(self._callbackIds)

        if not hasCallbacks:

            callbackId = om.MSceneMessage.addCallback(om.MSceneMessage.kAfterNew, onSceneChanged)
            self._callbackIds.append(callbackId)

            callbackId = om.MSceneMessage.addCallback(om.MSceneMessage.kAfterOpen, onSceneChanged)
            self._callbackIds.append(callbackId)

            callbackId = om.MEventMessage.addEventCallback('SelectionChanged', onSelectionChanged)
            self._callbackIds.append(callbackId)

        # Update internal selection tracker
        #
        self.selectionChanged()

    def closeEvent(self, event):
        """
        Event method called after the window has been closed.

        :type event: QtGui.QCloseEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QRigomatic, self).closeEvent(event)

        # Remove callbacks
        #
        hasCallbacks = len(self._callbackIds)

        if hasCallbacks:

            om.MMessage.removeCallbacks(self._callbackIds)
            self._callbackIds.clear()
    # endregion

    # region Methods
    def loadSettings(self, settings):
        """
        Loads the user settings.

        :type settings: QtCore.QSettings
        :rtype: None
        """

        # Call parent method
        #
        super(QRigomatic, self).loadSettings(settings)

        # Load user preferences
        #
        self.tabControl.setCurrentIndex(settings.value('editor/currentTabIndex', defaultValue=0))

        # Load tab settings
        #
        for tab in self.iterTabs():

            tab.loadSettings(settings)

    def saveSettings(self, settings):
        """
        Saves the user settings.

        :type settings: QtCore.QSettings
        :rtype: None
        """

        # Call parent method
        #
        super(QRigomatic, self).saveSettings(settings)

        # Save user preferences
        #
        settings.setValue('editor/currentTabIndex', self.currentTabIndex())

        # Save tab settings
        #
        for tab in self.iterTabs():

            tab.saveSettings(settings)

    @staticmethod
    def getPluginExtension():
        """
        Returns the plugin file extension based on the user's operating system.

        :rtype: str
        """

        # Check system type
        #
        if mc.about(windows=True) or mc.about(win64=True):

            return 'mll'

        elif mc.about(macOS=True) or mc.about(macOSx86=True):

            return 'bundle'

        elif mc.about(linux=True) or mc.about(linxx64=True):

            return 'so'

        else:

            raise NotImplementedError()

    @classmethod
    def loadPlugins(cls):
        """
        Loads all the required plugins.

        :rtype: None
        """

        # Iterate through required plugins
        #
        log.info('Loading required plugins...')
        extension = cls.getPluginExtension()

        for plugin in cls.__plugins__:

            # Check if plugin has been loaded
            #
            filename = '{plugin}.{extension}'.format(plugin=plugin, extension=extension)

            if mc.pluginInfo(filename, query=True, loaded=True):

                log.info(f'"{filename}" plugin has already been loaded.')
                continue

            # Shit goes wrong, so try to load them...
            #
            try:

                log.info(f'Loading "{filename}" plugin...')
                mc.loadPlugin(filename)

            except RuntimeError as exception:

                log.error(exception)
                continue

    def currentTab(self):
        """
        Returns the tab widget that is currently open.

        :rtype: QAbstractTab
        """

        return self.tabControl.currentWidget()

    def currentTabIndex(self):
        """
        Returns the tab index that currently open.

        :rtype: int
        """

        return self.tabControl.currentIndex()

    def iterTabs(self):
        """
        Returns a generator that yields tab widgets.

        :rtype: Iterator[QtWidget.QWidget]
        """

        # Iterate through tab control
        #
        for i in range(self.tabControl.count()):

            # Check if widget is valid
            #
            widget = self.tabControl.widget(i)

            if QtCompat.isValid(widget):

                yield widget

            else:

                continue

    def tabs(self):
        """
        Returns a list of tab widgets.

        :rtype: List[QtWidget.QWidget]
        """

        return list(self.iterTabs())
    # endregion

    # region Slots
    @QtCore.Slot(int)
    def on_tabControl_currentChanged(self, index):
        """
        Slot method for the `tabControl` widget's `currentChanged` signal.

        :type index: int
        :rtype: None
        """

        tabs = self.tabs()
        numTabs = len(tabs)

        if 0 <= index < numTabs:

            tab = tabs[index]
            log.debug(f'Invalidating {tab.objectName()} tab!')

            tab.invalidate(reason=self.InvalidateReason.TAB_CHANGED)
    # endregion