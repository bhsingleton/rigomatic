import webbrowser

from maya import cmds as mc
from maya.api import OpenMaya as om
from mpy import mpyscene
from Qt import QtCore, QtWidgets, QtGui, QtCompat
from dcc.ui import quicwindow
from dcc.maya.libs import transformutils
from . import InvalidateReason
from ..libs import createutils, modifyutils, ColorType

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
        self._currentColor = (0.0, 0.0, 0.0)
        self._callbackIds = om.MCallbackIdArray()

        # Declare public variables
        #
        self.mainMenuBar = None
        self.settingsMenu = None
        self.nameConfigurationAction = None
        self.changeNameConfigurationAction = None
        self.colorTypeActionGroup = None
        self.colorTypeSection = None
        self.wireColorAction = None
        self.overrideColorAction = None
        self.helpMenu = None
        self.usingRigomaticAction = None

        self.nodeFrame = None
        self.namespaceComboBox = None
        self.namespaceLabel = None
        self.nameLineEdit = None
        self.nameRegex = None
        self.nameValidator = None
        self.wireColorButton = None
        self.createDivider = None
        self.createLabel = None
        self.createLine = None
        self.transformPushButton = None
        self.jointPushButton = None
        self.ikHandlePushButton = None
        self.locatorPushButton = None
        self.helperPushButton = None
        self.intermediatePushButton = None

        self.tabControl = None
        self.modifyTab = None
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

        self.invalidateSelection()
        self.currentTab().invalidate(reason=self.InvalidateReason.SCENE_CHANGED)

    def selectionChanged(self, *args, **kwargs):
        """
        Notifies all tabs of a selection change.

        :key clientData: Any
        :rtype: None
        """

        self.invalidateSelection()
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
    def postLoad(self, *args, **kwargs):
        """
        Called after the user interface has been loaded.

        :rtype: None
        """

        # Call parent method
        #
        super(QRigomatic, self).postLoad(*args, **kwargs)

        # Initialize settings menu
        #
        self.nameConfigurationAction = QtWidgets.QAction('Default', parent=self.settingsMenu)
        self.nameConfigurationAction.setObjectName('nameConfigurationAction')
        self.nameConfigurationAction.setEnabled(False)

        self.changeNameConfigurationAction = QtWidgets.QAction('Change Name Configuration', parent=self.settingsMenu)
        self.changeNameConfigurationAction.setObjectName('changeNameConfigurationAction')

        self.colorTypeSection = QtWidgets.QAction('Color Type:', parent=self.settingsMenu)
        self.colorTypeSection.setObjectName('colorSection')
        self.colorTypeSection.setSeparator(True)

        self.wireColorAction = QtWidgets.QAction('Wire Color', parent=self.settingsMenu)
        self.wireColorAction.setObjectName('wireColorAction')
        self.wireColorAction.setCheckable(True)
        self.wireColorAction.setChecked(True)
        self.wireColorAction.setWhatsThis('WIRE_COLOR_RGB')

        self.overrideColorAction = QtWidgets.QAction('Override Color', parent=self.settingsMenu)
        self.overrideColorAction.setObjectName('overrideColorAction')
        self.overrideColorAction.setCheckable(True)
        self.overrideColorAction.setWhatsThis('OVERRIDE_COLOR_RGB')

        self.colorTypeActionGroup = QtWidgets.QActionGroup(self.settingsMenu)
        self.colorTypeActionGroup.setObjectName('colorActionGroup')
        self.colorTypeActionGroup.setExclusive(True)
        self.colorTypeActionGroup.addAction(self.wireColorAction)
        self.colorTypeActionGroup.addAction(self.overrideColorAction)

        self.settingsMenu.addActions(
            [
                self.nameConfigurationAction,
                self.changeNameConfigurationAction,
                self.colorTypeSection,
                self.wireColorAction,
                self.overrideColorAction
            ]
        )

        # Initialize help menu
        #
        self.usingRigomaticAction = QtWidgets.QAction("Using Rig o'Matic", parent=self.helpMenu)
        self.usingRigomaticAction.setObjectName('usingRigomaticAction')
        self.usingRigomaticAction.triggered.connect(self.on_usingRigomaticAction_triggered)

        self.helpMenu.addActions([self.usingRigomaticAction])

        # Initialize name validator
        #
        self.nameRegex = QtCore.QRegExp(r'^[a-zA-Z0-9_]+$')
        self.nameValidator = QtGui.QRegExpValidator(self.nameRegex, parent=self.nodeFrame)
        self.nameValidator.setObjectName('nameValidator')

        self.nameLineEdit.setValidator(self.nameValidator)

        # Invalidate namespaces
        #
        self.invalidateNamespaces()

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
        color = settings.value('editor/color', defaultValue=QtGui.QColor(0, 0, 0))
        self._currentColor = (color.redF(), color.greenF(), color.blue())

        self.setColorType(settings.value('editor/colorType', defaultValue=2, type=int))
        self.tabControl.setCurrentIndex(settings.value('editor/currentTabIndex', defaultValue=0, type=int))

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
        settings.setValue('editor/color', QtGui.QColor.fromRgbF(*self._currentColor))
        settings.setValue('editor/colorType', int(self.colorType()))
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

    def currentName(self):
        """
        Returns the current node name.

        :rtype: str
        """

        return self.nameLineEdit.text()

    def currentColor(self):
        """
        Returns the current wire-color.

        :rtype: Tuple[float, float, float]
        """

        color = self.wireColorButton.color()
        return color.redF(), color.greenF(), color.blueF()

    def colorType(self):
        """
        Returns the current color type.

        :rtype: ColorType
        """

        return ColorType[self.colorTypeActionGroup.checkedAction().whatsThis()]

    def setColorType(self, colorType):
        """
        Updates the current color type.

        :type colorType: Union[ColorType, int]
        :rtype: None
        """

        colorType = ColorType(colorType)
        colorTypeName = colorType.name

        for action in self.colorTypeActionGroup.actions():

            if action.whatsThis() == colorTypeName:

                action.setChecked(True)
                break

            else:

                continue

    def wireColor(self):
        """
        Returns the current wire color.

        :rtype: Tuple[float, float, float]
        """

        color = self.wireColorButton.color()
        red, green, blue = color.redF(), color.greenF(), color.blueF()

        return (red, green, blue)

    def selectionPivot(self):
        """
        Returns the pivot of the active selection.

        :rtype: om.MMatrix
        """

        # Evaluate active selection
        #
        componentSelection = self.scene.componentSelection(apiType=om.MFn.kDagNode)
        hasSelection = len(componentSelection) > 0

        if not hasSelection:

            return om.MMatrix.kIdentity

        # Calculate active pivot
        #
        boundingBox = om.MBoundingBox()

        for (node, component) in componentSelection:

            # Check if component is valid
            #
            hasComponent = not component.isNull()

            if not hasComponent:

                # Expand bounding-box using world position
                #
                worldMatrix = node.worldMatrix()
                position = transformutils.breakMatrix(worldMatrix)[3]

                boundingBox.expand(position)
                continue

            # Evaluate shape type
            #
            if node.hasFn(om.MFn.kMesh):

                vertexComponent = node(component).convert(om.MFn.kMeshVertComponent)
                elements = vertexComponent.elements()

                parentMatrix = node.parentMatrix()

                for element in elements:

                    position = om.MPoint(node.getPoint(element)) * parentMatrix
                    boundingBox.expand(position)

            else:

                elements = om.MFnSingleIndexedComponent(component).getElements()
                controlPoints = node.controlPoints()

                parentMatrix = node.parentMatrix()

                for element in elements:

                    position = om.MPoint(controlPoints[element]) * parentMatrix
                    boundingBox.expand(position)

        # Compose transform matrix
        #
        firstNode = componentSelection[0][0]
        worldMatrix = firstNode.worldMatrix()

        translateMatrix = transformutils.createTranslateMatrix(boundingBox.center)
        rotateMatrix = transformutils.createRotationMatrix(worldMatrix)
        scaleMatrix = transformutils.createScaleMatrix(worldMatrix)
        matrix = scaleMatrix * rotateMatrix * translateMatrix

        return matrix

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

    def invalidateName(self):
        """
        Refreshes the current namespace item and name line-edit.

        :rtype: None
        """

        # Evaluate active selection
        #
        name = None
        namespace = -1

        if self.selectedNode is not None:

            name = self.selectedNode.name()
            namespace = self.namespaceComboBox.findText(self.selectedNode.namespace())

        # Update name widgets
        #
        self.namespaceComboBox.blockSignals(True)
        self.namespaceComboBox.setCurrentIndex(namespace)
        self.namespaceComboBox.blockSignals(False)

        self.nameLineEdit.blockSignals(True)
        self.nameLineEdit.setText(name)
        self.nameLineEdit.blockSignals(False)

    def invalidateNamespaces(self):
        """
        Refreshes the namespace combo-box items.

        :rtype: None
        """

        namespaces = om.MNamespace.getNamespaces(parentNamespace=':', recurse=True)
        namespaces.insert(0, '')

        self.namespaceComboBox.blockSignals(True)
        self.namespaceComboBox.clear()
        self.namespaceComboBox.addItems(namespaces)
        self.namespaceComboBox.blockSignals(False)

    def invalidateColor(self):
        """
        Refreshes the wire-color button.

        :rtype: None
        """

        # Evaluate current selection
        #
        selection = [node for node in self.selection if node.hasFn(om.MFn.kTransform)]
        selectionCount = len(selection)

        if selectionCount > 0:

            # Evaluate immediate shape
            #
            node = selection[0]

            colorType = self.colorType()
            colorRGB = modifyutils.findWireframeColor(node, colorType=colorType)
            color = QtGui.QColor.fromRgbF(*colorRGB)

            self.wireColorButton.blockSignals(True)
            self.wireColorButton.setColor(color)
            self.wireColorButton.blockSignals(False)

        else:

            # Revert back to internal color
            #
            color = QtGui.QColor.fromRgbF(*self._currentColor)

            self.wireColorButton.blockSignals(True)
            self.wireColorButton.setColor(color)
            self.wireColorButton.blockSignals(False)

    def invalidateSelection(self):
        """
        Refreshes the selection related widgets.

        :rtype: None
        """

        # Update internal selection trackers
        #
        self._selection = self.scene.selection(apiType=om.MFn.kDependencyNode)
        self._selectionCount = len(self._selection)
        self._selectedNode = self._selection[0] if (self._selectionCount > 0) else None

        # Refresh selection widgets
        #
        self.invalidateName()
        self.invalidateColor()
    # endregion

    # region Slots
    @QtCore.Slot(int)
    def on_namespaceComboBox_currentIndexChanged(self, index):
        """
        Slot method for the `namespaceComboBox` widget's `currentIndexChanged` signal.

        :type index: int
        :rtype: None
        """

        sender = self.sender()
        numNamespaces = sender.count()

        if (self.selectionCount > 0) and (0 <= index < numNamespaces):

            namespaces = [sender.itemText(i) for i in range(numNamespaces)]
            namespace = namespaces[index]

            modifyutils.renamespaceNodes(*self.selection, namespace=namespace)

    @QtCore.Slot(str)
    def on_nameLineEdit_textChanged(self, text):
        """
        Slot method for the `nameLineEdit` widget's `textChanged` signal.

        :type text: str
        :rtype: None
        """

        # Evaluate active selection
        #
        if self.selectedNode is None:

            return

        # Try and rename node
        #
        success = modifyutils.renameNode(self.selectedNode, text)

        if not success:

            self.invalidateName()

    @QtCore.Slot()
    def on_wireColorButton_clicked(self):
        """
        Slot method for the `wireColorButton` widget's `clicked` signal.

        :rtype: None
        """

        # Prompt user for colour input
        #
        sender = self.sender()
        color = QtWidgets.QColorDialog.getColor(initial=sender.color(), parent=self, title='Select Wire Colour')

        success = color.isValid()

        if success:

            sender.setColor(color)

    @QtCore.Slot(QtGui.QColor)
    def on_wireColorButton_colorChanged(self, color):
        """
        Slot method for the `wireColorButton` widget's `colorChanged` signal.

        :type color: QtGui.QColor
        :rtype: None
        """

        if self.selectionCount > 0:

            colorRGB = (color.redF(), color.greenF(), color.blueF())
            colorType = self.colorType()

            modifyutils.recolorNodes(*self.selection, color=colorRGB, colorType=colorType)

        else:

            self._currentColor = (color.redF(), color.greenF(), color.blueF())

    @QtCore.Slot()
    def on_transformPushButton_clicked(self):
        """
        Slot method for the `transformPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate keyboard modifiers
        #
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        averageSelection = modifiers == QtCore.Qt.AltModifier
        hasSelection = self.selectionCount > 0

        if averageSelection:

            # Create node from active selection pivot
            #
            createutils.createNode('transform', name=self.currentName(), matrix=self.selectionPivot())

        elif hasSelection:

            # Create nodes from active selection
            #
            createutils.createNodesFromSelection('transform', self.selection)

        else:

            # Create node at origin
            #
            createutils.createNode('transform', name=self.currentName())

    @QtCore.Slot()
    def on_jointPushButton_clicked(self):
        """
        Slot method for the `jointPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate keyboard modifiers
        #
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        averageSelection = modifiers == QtCore.Qt.AltModifier
        hasSelection = self.selectionCount > 0

        if averageSelection:

            # Create node from active selection pivot
            #
            createutils.createNode('joint', name=self.currentName(), matrix=self.selectionPivot())

        elif hasSelection:

            # Create nodes from active selection
            #
            createutils.createNodesFromSelection('joint', self.selection)

        else:

            # Create node at origin
            #
            createutils.createNode('joint', name=self.currentName())

    @QtCore.Slot()
    def on_ikHandlePushButton_clicked(self):
        """
        Slot method for the `ikHandlePushButton` widget's `clicked` signal.

        :rtype: None
        """

        joints = [node for node in self.selection if node.hasFn(om.MFn.kJoint)]
        numJoints = len(joints)

        if numJoints == 2:

            createutils.addIKSolver(joints[0], joints[1])

        else:

            log.warning(f'Adding IK requires a start and end joint ({numJoints} selected)!')

    @QtCore.Slot()
    def on_locatorPushButton_clicked(self):
        """
        Slot method for the `locatorPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate keyboard modifiers
        #
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        averageSelection = modifiers == QtCore.Qt.AltModifier
        hasSelection = self.selectionCount > 0

        if averageSelection:

            # Create node from active pivot
            #
            createutils.createNode('transform', name=self.currentName(), matrix=self.selectionPivot(), locator=True, colorRGB=self.wireColor())

        elif hasSelection:

            # Create nodes from active selection
            #
            createutils.createNodesFromSelection('transform', self.selection, locator=True, colorRGB=self.wireColor())

        else:

            # Create node at origin
            #
            createutils.createNode('transform', name=self.currentName(), locator=True, colorRGB=self.wireColor())

    @QtCore.Slot()
    def on_helperPushButton_clicked(self):
        """
        Slot method for the `helperPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate keyboard modifiers
        #
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        averageSelection = modifiers == QtCore.Qt.AltModifier
        hasSelection = self.selectionCount > 0

        if averageSelection:

            # Create node from active pivot
            #
            createutils.createNode('transform', name=self.currentName(), matrix=self.selectionPivot(), helper=True, colorRGB=self.wireColor())

        elif hasSelection:

            # Create nodes from active selection
            #
            createutils.createNodesFromSelection('transform', self.selection, helper=True, colorRGB=self.wireColor())

        else:

            # Create node at origin
            #
            createutils.createNode('transform', name=self.currentName(), helper=True, colorRGB=self.wireColor())

    @QtCore.Slot()
    def on_intermediatePushButton_clicked(self):
        """
        Slot method for the `intermediatePushButton` widget's `clicked` signal.

        :rtype: None
        """

        if self.selectionCount > 0:

            createutils.createIntermediate(*self.selection)

        else:

            log.warning(f'Creating an intermediate expects at least 1 selected node ({self.selectionCount} selected)!')

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

    @QtCore.Slot()
    def on_usingRigomaticAction_triggered(self):
        """
        Slot method for the usingRigomaticAction's `triggered` signal.

        :rtype: None
        """

        webbrowser.open('https://github.com/bhsingleton/rigomatic')
    # endregion
