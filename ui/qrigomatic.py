import webbrowser

from maya import cmds as mc
from maya.api import OpenMaya as om
from mpy import mpyscene
from dcc.vendor.Qt import QtCore, QtWidgets, QtGui, QtCompat
from dcc.ui import qsingletonwindow, qdivider, qsignalblocker
from dcc.maya.libs import transformutils, pluginutils
from . import InvalidateReason
from .tabs import qmodifytab, qrenametab, qshapestab, qattributestab, qspreadsheettab, qconstraintstab, qpublishtab
from .widgets import qcolorbutton
from ..libs import createutils, modifyutils, ColorMode

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


class QRigomatic(qsingletonwindow.QSingletonWindow):
    """
    Overload of `QUicWindow` used to edit rigs.
    """

    # region Enums
    InvalidateReason = InvalidateReason
    # endregion

    # region Dunderscores
    __plugins__ = (
        'PointHelper',
        'TransformConstraint',
        'PointOnCurveConstraint'
    )

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

    def __setup_ui__(self, *args, **kwargs):
        """
        Called after the user interface has been loaded.

        :rtype: None
        """

        # Call parent method
        #
        super(QRigomatic, self).__setup_ui__(*args, **kwargs)

        # Initialize main window
        #
        self.setWindowTitle("|| Rig o'Matic (Toolkit)")
        self.setMinimumSize(QtCore.QSize(400, 600))

        # Initialize menu-bar
        #
        mainMenuBar = QtWidgets.QMenuBar(self)
        mainMenuBar.setObjectName('mainMenuBar')

        self.setMenuBar(mainMenuBar)

        # Initialize settings menu
        #
        self.settingsMenu = mainMenuBar.addMenu('&Settings')
        self.settingsMenu.setObjectName('settingsMenu')

        self.nameConfigurationAction = QtWidgets.QAction('Default', parent=self.settingsMenu)
        self.nameConfigurationAction.setObjectName('nameConfigurationAction')
        self.nameConfigurationAction.setEnabled(False)

        self.changeNameConfigurationAction = QtWidgets.QAction('Change Name Configuration', parent=self.settingsMenu)
        self.changeNameConfigurationAction.setObjectName('changeNameConfigurationAction')

        self.colorModeSection = QtWidgets.QAction('Color Mode:', parent=self.settingsMenu)
        self.colorModeSection.setObjectName('colorSection')
        self.colorModeSection.setSeparator(True)

        self.wireColorAction = QtWidgets.QAction('Wire Color', parent=self.settingsMenu)
        self.wireColorAction.setObjectName('wireColorAction')
        self.wireColorAction.setWhatsThis('WIRE_COLOR_RGB')
        self.wireColorAction.setCheckable(True)
        self.wireColorAction.setChecked(True)

        self.overrideColorAction = QtWidgets.QAction('Override Color', parent=self.settingsMenu)
        self.overrideColorAction.setObjectName('overrideColorAction')
        self.overrideColorAction.setWhatsThis('OVERRIDE_COLOR_RGB')
        self.overrideColorAction.setCheckable(True)

        self.colorModeActionGroup = QtWidgets.QActionGroup(self.settingsMenu)
        self.colorModeActionGroup.setObjectName('colorModeActionGroup')
        self.colorModeActionGroup.setExclusive(True)
        self.colorModeActionGroup.addAction(self.wireColorAction)
        self.colorModeActionGroup.addAction(self.overrideColorAction)

        self.settingsMenu.addActions(
            [
                self.nameConfigurationAction,
                self.changeNameConfigurationAction,
                self.colorModeSection,
                self.wireColorAction,
                self.overrideColorAction
            ]
        )

        # Initialize help menu
        #
        self.helpMenu = mainMenuBar.addMenu('&Help')
        self.helpMenu.setObjectName('helpMenu')

        self.usingRigomaticAction = QtWidgets.QAction("Using Rig o'Matic", parent=self.helpMenu)
        self.usingRigomaticAction.setObjectName('usingRigomaticAction')
        self.usingRigomaticAction.triggered.connect(self.on_usingRigomaticAction_triggered)

        self.helpMenu.addActions([self.usingRigomaticAction])

        # Initialize central widget
        #
        centralLayout = QtWidgets.QVBoxLayout()
        centralLayout.setObjectName('centralLayout')

        centralWidget = QtWidgets.QWidget()
        centralWidget.setObjectName('centralWidget')
        centralWidget.setLayout(centralLayout)

        self.setCentralWidget(centralWidget)

        # Initialize selection frame
        #
        self.selectionFrameLayout = QtWidgets.QVBoxLayout()
        self.selectionFrameLayout.setObjectName('selectionFrameLayout')

        self.selectionFrame = QtWidgets.QFrame(parent=self)
        self.selectionFrame.setObjectName('nodeFrame')
        self.selectionFrame.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.selectionFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.selectionFrame.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.selectionFrame.setAutoFillBackground(True)
        self.selectionFrame.setLayout(self.selectionFrameLayout)

        centralLayout.addWidget(self.selectionFrame)

        # Initialize node name layout
        #
        self.namespaceComboBox = QtWidgets.QComboBox()
        self.namespaceComboBox.setObjectName('namespaceComboBox')
        self.namespaceComboBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.namespaceComboBox.setFixedHeight(24)
        self.namespaceComboBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.namespaceComboBox.currentIndexChanged.connect(self.on_namespaceComboBox_currentIndexChanged)

        self.namespaceLabel = QtWidgets.QLabel(':')
        self.namespaceLabel.setObjectName('namespaceLabel')
        self.namespaceLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.namespaceLabel.setFixedSize(QtCore.QSize(12, 24))
        self.namespaceLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.namespaceLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.nameLineEdit = QtWidgets.QLineEdit()
        self.nameLineEdit.setObjectName('nameLineEdit')
        self.nameLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.nameLineEdit.setFixedHeight(24)
        self.nameLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.nameLineEdit.textChanged.connect(self.on_nameLineEdit_textChanged)

        self.wireColorButton = qcolorbutton.QColorButton()
        self.wireColorButton.setObjectName('wireColorButton')
        self.wireColorButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.wireColorButton.setFixedSize(QtCore.QSize(24, 24))
        self.wireColorButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.wireColorButton.clicked.connect(self.on_wireColorButton_clicked)
        self.wireColorButton.colorChanged.connect(self.on_wireColorButton_colorChanged)

        self.nodeNameLayout = QtWidgets.QHBoxLayout()
        self.nodeNameLayout.setObjectName('nodeNameLayout')
        self.nodeNameLayout.setContentsMargins(0, 0, 0, 0)
        self.nodeNameLayout.addWidget(self.namespaceComboBox)
        self.nodeNameLayout.addWidget(self.namespaceLabel)
        self.nodeNameLayout.addWidget(self.nameLineEdit)
        self.nodeNameLayout.addWidget(self.wireColorButton)

        self.selectionFrameLayout.addLayout(self.nodeNameLayout)

        # Initialize node name validator
        #
        self.nameRegex = QtCore.QRegExp(r'^[a-zA-Z0-9_]+$')
        self.nameValidator = QtGui.QRegExpValidator(self.nameRegex, parent=self.selectionFrame)
        self.nameValidator.setObjectName('nameValidator')

        self.nameLineEdit.setValidator(self.nameValidator)

        # Initialize create divider
        #
        self.createDividerLayout = QtWidgets.QHBoxLayout()
        self.createDividerLayout.setObjectName('createDividerLayout')
        self.createDividerLayout.setContentsMargins(0, 0, 0, 0)

        self.createDivider = QtWidgets.QWidget()
        self.createDivider.setObjectName('createDivider')
        self.createDivider.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.createDivider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.createDivider.setLayout(self.createDividerLayout)

        self.createLabel = QtWidgets.QLabel('Create:')
        self.createLabel.setObjectName('createLabel')
        self.createLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred))
        self.createLabel.setFocusPolicy(QtCore.Qt.NoFocus)

        self.createLine = qdivider.QDivider(QtCore.Qt.Horizontal)
        self.createLine.setObjectName('createLine')
        self.createLine.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred))
        self.createLine.setFocusPolicy(QtCore.Qt.NoFocus)

        self.createDividerLayout.addWidget(self.createLabel)
        self.createDividerLayout.addWidget(self.createLine)

        self.selectionFrameLayout.addWidget(self.createDivider)

        # Initialize create node layout
        #
        self.transformPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/out_transform.png'), 'Transform')
        self.transformPushButton.setObjectName('transformPushButton')
        self.transformPushButton.setWhatsThis('transform')
        self.transformPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.transformPushButton.setFixedHeight(24)
        self.transformPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.transformPushButton.clicked.connect(self.on_transformPushButton_clicked)

        self.jointPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/out_joint.png'), 'Joint')
        self.jointPushButton.setObjectName('jointPushButton')
        self.jointPushButton.setWhatsThis('joint')
        self.jointPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.jointPushButton.setFixedHeight(24)
        self.jointPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.jointPushButton.clicked.connect(self.on_jointPushButton_clicked)

        self.ikHandlePushButton = QtWidgets.QPushButton(QtGui.QIcon(':/out_ikHandle.png'), 'IK-Handle')
        self.ikHandlePushButton.setObjectName('ikHandlePushButton')
        self.ikHandlePushButton.setWhatsThis('ikHandle')
        self.ikHandlePushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.ikHandlePushButton.setFixedHeight(24)
        self.ikHandlePushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.ikHandlePushButton.clicked.connect(self.on_ikHandlePushButton_clicked)

        self.locatorPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/out_locator.png'), 'Locator')
        self.locatorPushButton.setObjectName('locatorPushButton')
        self.locatorPushButton.setWhatsThis('locator')
        self.locatorPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.locatorPushButton.setFixedHeight(24)
        self.locatorPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.locatorPushButton.clicked.connect(self.on_locatorPushButton_clicked)

        self.helperPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/out_pointHelper.png'), 'Helper')
        self.helperPushButton.setObjectName('helperPushButton')
        self.helperPushButton.setWhatsThis('pointHelper')
        self.helperPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.helperPushButton.setFixedHeight(24)
        self.helperPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.helperPushButton.clicked.connect(self.on_helperPushButton_clicked)

        self.intermediatePushButton = QtWidgets.QPushButton(QtGui.QIcon(':/out_transform.png'), 'Intermediate')
        self.intermediatePushButton.setObjectName('intermediatePushButton')
        self.intermediatePushButton.setWhatsThis('intermediate')
        self.intermediatePushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.intermediatePushButton.setFixedHeight(24)
        self.intermediatePushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.intermediatePushButton.clicked.connect(self.on_intermediatePushButton_clicked)
        
        self.createNodeLayout = QtWidgets.QGridLayout()
        self.createNodeLayout.setObjectName('createNodeLayout')
        self.createNodeLayout.setContentsMargins(0, 0, 0, 0)
        self.createNodeLayout.addWidget(self.transformPushButton, 0, 0)
        self.createNodeLayout.addWidget(self.jointPushButton, 0, 1)
        self.createNodeLayout.addWidget(self.ikHandlePushButton, 0, 2)
        self.createNodeLayout.addWidget(self.locatorPushButton, 1, 0)
        self.createNodeLayout.addWidget(self.helperPushButton, 1, 1)
        self.createNodeLayout.addWidget(self.intermediatePushButton, 1, 2)

        self.selectionFrameLayout.addLayout(self.createNodeLayout)

        # Initialize tab control
        #
        self.tabControl = QtWidgets.QTabWidget(parent=self)
        self.tabControl.setObjectName('tabControl')
        self.tabControl.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.tabControl.setFocusPolicy(QtCore.Qt.NoFocus)
        self.tabControl.setTabPosition(QtWidgets.QTabWidget.West)
        self.tabControl.setTabShape(QtWidgets.QTabWidget.Rounded)

        self.modifyTab = qmodifytab.QModifyTab(parent=self.tabControl)
        self.renameTab = qrenametab.QRenameTab(parent=self.tabControl)
        self.shapesTab = qshapestab.QShapesTab(parent=self.tabControl)
        self.attributesTab = qattributestab.QAttributesTab(parent=self.tabControl)
        self.spreadsheetTab = qspreadsheettab.QSpreadsheetTab(parent=self.tabControl)
        self.constraintsTab = qconstraintstab.QConstraintsTab(parent=self.tabControl)
        self.publishTab = qpublishtab.QPublishTab(parent=self.tabControl)

        self.tabControl.addTab(self.modifyTab, 'Modify')
        self.tabControl.addTab(self.renameTab, 'Rename')
        self.tabControl.addTab(self.shapesTab, 'Shapes')
        self.tabControl.addTab(self.attributesTab, 'Attributes')
        self.tabControl.addTab(self.spreadsheetTab, 'Spreadsheet')
        self.tabControl.addTab(self.constraintsTab, 'Constraints')
        self.tabControl.addTab(self.publishTab, 'Publish')

        centralLayout.addWidget(self.tabControl)

        # Invalidate namespaces
        #
        self.invalidateNamespaces()
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

    # region Methods
    def addCallbacks(self):
        """
        Adds any callbacks required by this window.

        :rtype: None
        """

        # Call parent method
        #
        super(QRigomatic, self).addCallbacks()

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

    def removeCallbacks(self):
        """
        Removes any callbacks created by this window.

        :rtype: None
        """

        # Call parent method
        #
        super(QRigomatic, self).removeCallbacks()

        # Remove callbacks
        #
        hasCallbacks = len(self._callbackIds)

        if hasCallbacks:

            om.MMessage.removeCallbacks(self._callbackIds)
            self._callbackIds.clear()

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
        defaultColor = QtGui.QColor(0.0, 0.0, 0.0)
        color = settings.value('editor/color', defaultValue=defaultColor)
        self._currentColor = (color.redF(), color.greenF(), color.blue())

        self.setColorMode(settings.value('editor/colorMode', defaultValue=2, type=int))
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
        settings.setValue('editor/colorMode', int(self.colorMode()))
        settings.setValue('editor/currentColor', QtGui.QColor.fromRgbF(*self._currentColor))
        settings.setValue('editor/currentTabIndex', self.currentTabIndex())

        # Save tab settings
        #
        for tab in self.iterTabs():

            tab.saveSettings(settings)

    @classmethod
    def loadPlugins(cls):
        """
        Loads all the required plugins.

        :rtype: None
        """

        log.info('Loading required plugins...')

        for plugin in cls.__plugins__:

            pluginutils.tryLoadPlugin(plugin)

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

        return self.wireColorButton.color(asRGB=True, normalize=True)

    def colorMode(self):
        """
        Returns the current color type.

        :rtype: ColorMode
        """

        return ColorMode[self.colorModeActionGroup.checkedAction().whatsThis()]

    def setColorMode(self, colorMode):
        """
        Updates the current color type.

        :type colorMode: Union[ColorMode, int]
        :rtype: None
        """

        colorMode = ColorMode(colorMode)
        colorModeName = colorMode.name

        for action in self.colorModeActionGroup.actions():

            if action.whatsThis() == colorModeName:

                action.setChecked(True)
                break

            else:

                continue

    def wireColor(self):
        """
        Returns the current wire color.

        :rtype: Tuple[float, float, float]
        """

        return self.wireColorButton.color(asRGB=True, normalize=True)

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
        name = ''
        namespaceIndex = -1
        placeholderText =  f'{self.selectionCount} Nodes Selected'

        if self.selectedNode is not None:

            name = self.selectedNode.name() if (self.selectionCount == 1) else ''
            namespaceIndex = self.namespaceComboBox.findText(self.selectedNode.namespace())

        # Update name widgets
        #
        with qsignalblocker.QSignalBlocker(self.namespaceComboBox, self.nameLineEdit):

            self.namespaceComboBox.setCurrentIndex(namespaceIndex)
            self.nameLineEdit.setText(name)
            self.nameLineEdit.setPlaceholderText(placeholderText)

    def invalidateNamespaces(self):
        """
        Refreshes the namespace combo-box items.

        :rtype: None
        """

        namespaces = om.MNamespace.getNamespaces(parentNamespace=':', recurse=True)
        namespaces.insert(0, '')

        with qsignalblocker.QSignalBlocker(self.namespaceComboBox):

            self.namespaceComboBox.clear()
            self.namespaceComboBox.addItems(namespaces)

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

            colorMode = self.colorMode()
            colorRGB = modifyutils.findWireframeColor(node, colorMode=colorMode)
            color = QtGui.QColor.fromRgbF(*colorRGB)

            with qsignalblocker.QSignalBlocker(self.wireColorButton):

                self.wireColorButton.setColor(color)

        else:

            # Revert back to internal color
            #
            color = QtGui.QColor.fromRgbF(*self._currentColor)

            with qsignalblocker.QSignalBlocker(self.wireColorButton):

                self.wireColorButton.setColor(color)

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
            colorMode = self.colorMode()

            modifyutils.recolorNodes(*self.selection, color=colorRGB, colorMode=colorMode)

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

            # Create node from active pivot
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

            # Create node from active pivot
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
