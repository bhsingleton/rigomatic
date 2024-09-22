from maya.api import OpenMaya as om
from Qt import QtCore, QtWidgets, QtGui
from scipy.spatial import cKDTree
from dcc.ui import qxyzwidget, qdivider
from dcc.maya.libs import plugutils
from dcc.maya.decorators import undo
from . import qabstracttab

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QConstraintsTab(qabstracttab.QAbstractTab):
    """
    Overload of `QAbstractTab` that interfaces with constraint nodes.
    """

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
        super(QConstraintsTab, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._currentNode = None
        self._constraints = []
        self._currentConstraint = None
        self._targets = []
        self._targetCount = 0
        self._currentTarget = None
        self._muted = []

    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        # Call parent method
        #
        super(QConstraintsTab, self).__setup_ui__(*args, **kwargs)

        # Initialize central layout
        #
        centralLayout = QtWidgets.QVBoxLayout()
        centralLayout.setObjectName('centralLayout')

        self.setLayout(centralLayout)
        
        # Initialize create group-box
        #
        self.createLayout = QtWidgets.QGridLayout()
        self.createLayout.setObjectName('createLayout')

        self.createGroupBox = QtWidgets.QGroupBox('Create:')
        self.createGroupBox.setObjectName('createGroupBox')
        self.createGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.createGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.createGroupBox.setLayout(self.createLayout)

        self.translateXYZWidget = qxyzwidget.QXyzWidget('Translate')
        self.translateXYZWidget.setObjectName('translateXYZWidget')
        self.translateXYZWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.translateXYZWidget.setFixedHeight(24)
        self.translateXYZWidget.setFocusPolicy(QtCore.Qt.NoFocus)
        self.translateXYZWidget.setStyleSheet('QPushButton:hover:checked { background-color: green; }\nQPushButton:checked { background-color: darkgreen; border: none; }')
        self.translateXYZWidget.setCheckStates([True, True, True])

        self.rotateXYZWidget = qxyzwidget.QXyzWidget('Rotate')
        self.rotateXYZWidget.setObjectName('rotateXYZWidget')
        self.rotateXYZWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.rotateXYZWidget.setFixedHeight(24)
        self.rotateXYZWidget.setFocusPolicy(QtCore.Qt.NoFocus)
        self.rotateXYZWidget.setStyleSheet('QPushButton:hover:checked { background-color: green; }\nQPushButton:checked { background-color: darkgreen; border: none; }')
        self.rotateXYZWidget.setCheckStates([True, True, True])

        self.scaleXYZWidget = qxyzwidget.QXyzWidget('Scale')
        self.scaleXYZWidget.setObjectName('scaleXYZWidget')
        self.scaleXYZWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.scaleXYZWidget.setFixedHeight(24)
        self.scaleXYZWidget.setFocusPolicy(QtCore.Qt.NoFocus)
        self.scaleXYZWidget.setStyleSheet('QPushButton:hover:checked { background-color: green; }\nQPushButton:checked { background-color: darkgreen; border: none; }')
        self.scaleXYZWidget.setCheckStates([False, False, False])

        self.pointPushButton = QtWidgets.QPushButton('Point')
        self.pointPushButton.setObjectName('pointPushButton')
        self.pointPushButton.setWhatsThis('pointConstraint')
        self.pointPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.pointPushButton.setFixedHeight(24)
        self.pointPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.pointPushButton.clicked.connect(self.on_constraintPushButton_clicked)
        
        self.orientPushButton = QtWidgets.QPushButton('Orient')
        self.orientPushButton.setObjectName('orientPushButton')
        self.orientPushButton.setWhatsThis('orientConstraint')
        self.orientPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.orientPushButton.setFixedHeight(24)
        self.orientPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.orientPushButton.clicked.connect(self.on_constraintPushButton_clicked)
        
        self.scalePushButton = QtWidgets.QPushButton('Scale')
        self.scalePushButton.setObjectName('scalePushButton')
        self.scalePushButton.setWhatsThis('scaleConstraint')
        self.scalePushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.scalePushButton.setFixedHeight(24)
        self.scalePushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.scalePushButton.clicked.connect(self.on_constraintPushButton_clicked)
        
        self.aimPushButton = QtWidgets.QPushButton('Aim')
        self.aimPushButton.setObjectName('aimPushButton')
        self.aimPushButton.setWhatsThis('aimConstraint')
        self.aimPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.aimPushButton.setFixedHeight(24)
        self.aimPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.aimPushButton.clicked.connect(self.on_constraintPushButton_clicked)
        
        self.parentPushButton = QtWidgets.QPushButton('Parent')
        self.parentPushButton.setObjectName('parentPushButton')
        self.parentPushButton.setWhatsThis('parentConstraint')
        self.parentPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.parentPushButton.setFixedHeight(24)
        self.parentPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.parentPushButton.clicked.connect(self.on_constraintPushButton_clicked)
        
        self.transformPushButton = QtWidgets.QPushButton('Transform')
        self.transformPushButton.setObjectName('transformPushButton')
        self.transformPushButton.setWhatsThis('transformConstraint')
        self.transformPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.transformPushButton.setFixedHeight(24)
        self.transformPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.transformPushButton.clicked.connect(self.on_constraintPushButton_clicked)
        
        self.pointOnCurvePushButton = QtWidgets.QPushButton('Point on Curve')
        self.pointOnCurvePushButton.setObjectName('pointOnCurvePushButton')
        self.pointOnCurvePushButton.setWhatsThis('pointOnCurveConstraint')
        self.pointOnCurvePushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.pointOnCurvePushButton.setFixedHeight(24)
        self.pointOnCurvePushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.pointOnCurvePushButton.clicked.connect(self.on_pointOnCurvePushButton_clicked)
        
        self.pointOnPolyPushButton = QtWidgets.QPushButton('Point on Poly')
        self.pointOnPolyPushButton.setObjectName('pointOnPolyPushButton')
        self.pointOnPolyPushButton.setWhatsThis('pointOnPolyConstraint')
        self.pointOnPolyPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.pointOnPolyPushButton.setFixedHeight(24)
        self.pointOnPolyPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.pointOnPolyPushButton.clicked.connect(self.on_pointOnPolyPushButton_clicked)
        
        self.skinPushButton = QtWidgets.QPushButton('Skin')
        self.skinPushButton.setObjectName('skinPushButton')
        self.skinPushButton.setWhatsThis('transformConstraint')
        self.skinPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.skinPushButton.setFixedHeight(24)
        self.skinPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.skinPushButton.clicked.connect(self.on_skinPushButton_clicked)
        
        self.maintainOffsetCheckBox = QtWidgets.QCheckBox('Maintain Offset')
        self.maintainOffsetCheckBox.setObjectName('maintainOffsetCheckBox')
        self.maintainOffsetCheckBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.maintainOffsetCheckBox.setFixedHeight(24)
        self.maintainOffsetCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)
        
        self.createLayout.addWidget(self.translateXYZWidget, 0, 0)
        self.createLayout.addWidget(self.rotateXYZWidget, 0, 1)
        self.createLayout.addWidget(self.scaleXYZWidget, 0, 2)
        self.createLayout.addWidget(qdivider.QDivider(QtCore.Qt.Horizontal), 1, 0, 1, 3)
        self.createLayout.addWidget(self.pointPushButton, 2, 0)
        self.createLayout.addWidget(self.orientPushButton, 2, 1)
        self.createLayout.addWidget(self.scalePushButton, 2, 2)
        self.createLayout.addWidget(self.aimPushButton, 3, 0)
        self.createLayout.addWidget(self.parentPushButton, 3, 1)
        self.createLayout.addWidget(self.transformPushButton, 3, 2)
        self.createLayout.addWidget(self.pointOnCurvePushButton, 4, 0)
        self.createLayout.addWidget(self.pointOnPolyPushButton, 4, 1)
        self.createLayout.addWidget(self.skinPushButton, 4, 2)
        self.createLayout.addWidget(self.maintainOffsetCheckBox, 5, 2)

        centralLayout.addWidget(self.createGroupBox)

        # Initialize targets group-box
        #
        self.targetsLayout = QtWidgets.QGridLayout()
        self.targetsLayout.setObjectName('targetsLayout')

        self.targetsGroupBox = QtWidgets.QGroupBox('Targets:')
        self.targetsGroupBox.setObjectName('targetsGroupBox')
        self.targetsGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.targetsGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.targetsGroupBox.setLayout(self.targetsLayout)
        
        self.editPushButton = QtWidgets.QPushButton('Nothing Selected')
        self.editPushButton.setObjectName('editPushButton')
        self.editPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.editPushButton.setFixedHeight(24)
        self.editPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.editPushButton.clicked.connect(self.on_editPushButton_clicked)

        self.constraintComboBox = QtWidgets.QComboBox()
        self.constraintComboBox.setObjectName('constraintComboBox')
        self.constraintComboBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.constraintComboBox.setFixedHeight(24)
        self.constraintComboBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.constraintComboBox.currentIndexChanged.connect(self.on_constraintComboBox_currentIndexChanged)

        self.addTargetPushButton = QtWidgets.QPushButton('Add Target')
        self.addTargetPushButton.setObjectName('addTargetPushButton')
        self.addTargetPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.addTargetPushButton.setFixedHeight(24)
        self.addTargetPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.addTargetPushButton.clicked.connect(self.on_addTargetPushButton_clicked)

        self.removeTargetPushButton = QtWidgets.QPushButton('Remove Target')
        self.removeTargetPushButton.setObjectName('removeTargetPushButton')
        self.removeTargetPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.removeTargetPushButton.setFixedHeight(24)
        self.removeTargetPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.removeTargetPushButton.clicked.connect(self.on_removeTargetPushButton_clicked)

        self.renameTargetPushButton = QtWidgets.QPushButton('Rename Target')
        self.renameTargetPushButton.setObjectName('renameTargetPushButton')
        self.renameTargetPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.renameTargetPushButton.setFixedHeight(24)
        self.renameTargetPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.renameTargetPushButton.clicked.connect(self.on_renameTargetPushButton_clicked)

        self.selectTargetPushButton = QtWidgets.QPushButton('Select Target')
        self.selectTargetPushButton.setObjectName('selectTargetPushButton')
        self.selectTargetPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.selectTargetPushButton.setFixedHeight(24)
        self.selectTargetPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.selectTargetPushButton.clicked.connect(self.on_selectTargetPushButton_clicked)

        self.targetTableView = QtWidgets.QTableView()
        self.targetTableView.setObjectName('targetTableView')
        self.targetTableView.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.targetTableView.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.targetTableView.setStyleSheet('QTableView::item { height: 24px; }')
        self.targetTableView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.targetTableView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.targetTableView.setDragEnabled(False)
        self.targetTableView.setDragDropOverwriteMode(False)
        self.targetTableView.setDragDropMode(QtWidgets.QAbstractItemView.NoDragDrop)
        self.targetTableView.setDefaultDropAction(QtCore.Qt.IgnoreAction)
        self.targetTableView.setAlternatingRowColors(True)
        self.targetTableView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.targetTableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.targetTableView.setShowGrid(True)

        self.itemPrototype = QtGui.QStandardItem('')
        self.itemPrototype.setSizeHint(QtCore.QSize(100, 24))
        self.itemPrototype.setTextAlignment(QtCore.Qt.AlignCenter)

        self.targetItemModel = QtGui.QStandardItemModel(0, 2, parent=self.targetTableView)
        self.targetItemModel.setObjectName('targetItemModel')
        self.targetItemModel.setHorizontalHeaderLabels(['Target', 'Weight'])
        self.targetItemModel.setItemPrototype(self.itemPrototype)

        self.targetTableView.setModel(self.targetItemModel)

        self.previewHorizontalHeader = self.targetTableView.horizontalHeader()  # type: QtWidgets.QHeaderView
        self.previewHorizontalHeader.setVisible(True)
        self.previewHorizontalHeader.setMinimumSectionSize(100)
        self.previewHorizontalHeader.setDefaultSectionSize(200)
        self.previewHorizontalHeader.setStretchLastSection(True)

        self.previewVerticalHeader = self.targetTableView.verticalHeader()  # type: QtWidgets.QHeaderView
        self.previewVerticalHeader.setVisible(False)
        self.previewVerticalHeader.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.previewVerticalHeader.setMinimumSectionSize(24)
        self.previewVerticalHeader.setDefaultSectionSize(24)
        self.previewVerticalHeader.setStretchLastSection(False)

        self.weightLabel = QtWidgets.QLabel('Weight:')
        self.weightLabel.setObjectName('weightLabel')
        self.weightLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))
        self.weightLabel.setFixedHeight(24)
        self.weightLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.weightLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.weightSpinBox = QtWidgets.QDoubleSpinBox()
        self.weightSpinBox.setObjectName('weightSpinBox')
        self.weightSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.weightSpinBox.setFixedHeight(24)
        self.weightSpinBox.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.weightSpinBox.setAlignment(QtCore.Qt.AlignCenter)
        self.weightSpinBox.setDecimals(2)
        self.weightSpinBox.setMinimum(0.0)
        self.weightSpinBox.setMaximum(1.0)
        self.weightSpinBox.setSingleStep(0.1)
        self.weightSpinBox.setValue(1.0)
        self.weightSpinBox.valueChanged.connect(self.on_weightSpinBox_valueChanged)

        self.weightLayout = QtWidgets.QHBoxLayout()
        self.weightLayout.setObjectName('weightLayout')
        self.weightLayout.setContentsMargins(0, 0, 0, 0)
        self.weightLayout.addWidget(self.weightLabel)
        self.weightLayout.addWidget(self.weightSpinBox)

        self.mutePushButton = QtWidgets.QPushButton('Mute')
        self.mutePushButton.setObjectName('mutePushButton')
        self.mutePushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.mutePushButton.setFixedHeight(24)
        self.mutePushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.mutePushButton.setStyleSheet('QPushButton:hover:checked { background-color: crimson; }\nQPushButton:checked { background-color: firebrick; border: none; }')
        self.mutePushButton.clicked.connect(self.on_mutePushButton_clicked)

        self.updateOffsetsPushButton = QtWidgets.QPushButton('Remove Target')
        self.updateOffsetsPushButton.setObjectName('updateOffsetsPushButton')
        self.updateOffsetsPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.updateOffsetsPushButton.setFixedHeight(24)
        self.updateOffsetsPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.updateOffsetsPushButton.clicked.connect(self.on_updateOffsetsPushButton_clicked)

        self.resetOffsetsPushButton = QtWidgets.QPushButton('Remove Target')
        self.resetOffsetsPushButton.setObjectName('resetOffsetsPushButton')
        self.resetOffsetsPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.resetOffsetsPushButton.setFixedHeight(24)
        self.resetOffsetsPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.resetOffsetsPushButton.clicked.connect(self.on_resetOffsetsPushButton_clicked)

        self.targetsLayout.addWidget(self.editPushButton, 0, 0, 1, 2)
        self.targetsLayout.addWidget(self.constraintComboBox, 1, 0, 1, 2)
        self.targetsLayout.addWidget(self.addTargetPushButton, 2, 0)
        self.targetsLayout.addWidget(self.removeTargetPushButton, 2, 1)
        self.targetsLayout.addWidget(self.renameTargetPushButton, 3, 0)
        self.targetsLayout.addWidget(self.selectTargetPushButton, 3, 1)
        self.targetsLayout.addWidget(self.targetTableView, 4, 0, 1, 2)
        self.targetsLayout.addLayout(self.weightLayout, 5, 0, 1, 2)
        self.targetsLayout.addWidget(qdivider.QDivider(QtCore.Qt.Horizontal), 6, 0, 1, 2)
        self.targetsLayout.addWidget(self.mutePushButton, 7, 0, 1, 2)
        self.targetsLayout.addWidget(self.updateOffsetsPushButton, 8, 0)
        self.targetsLayout.addWidget(self.resetOffsetsPushButton, 8, 1)

        centralLayout.addWidget(self.targetsGroupBox)
    # region Properties
    @property
    def currentNode(self):
        """
        Getter method that returns the current node.

        :rtype: Union[mpynode.MPyNode, None]
        """

        return self._currentNode

    @property
    def constraints(self):
        """
        Getter method that returns the current node's constraints.

        :rtype: List[mpynode.MPyNode]
        """

        return self._constraints

    @property
    def currentConstraint(self):
        """
        Getter method that returns the current constraint.

        :rtype: Union[mpynode.MPyNode, None]
        """

        return self._currentConstraint

    @property
    def targets(self):
        """
        Getter method that returns the current constraint's targets.

        :rtype: List[mpy.builtins.constraintmixin.ConstraintTarget]
        """

        return self._targets

    @property
    def targetCount(self):
        """
        Getter method that returns the current constraint's target count.

        :rtype: int
        """

        return self._targetCount

    @property
    def currentTarget(self):
        """
        Getter method that returns the current constraint target.

        :rtype: mpy.builtins.constraintmixin.ConstraintTarget
        """

        return self._currentTarget
    # endregion

    # region Methods
    def saveSettings(self, settings):
        """
        Saves the user settings.

        :type settings: QtCore.QSettings
        :rtype: None
        """

        # Call parent method
        #
        super(QConstraintsTab, self).saveSettings(settings)

        # Check if current constraint is muted
        #
        if self.isMuted():

            self.mutePushButton.click()

    def maintainOffset(self):
        """
        Returns the `maintainOffset` flag.

        :rtype: bool
        """

        return self.maintainOffsetCheckBox.isChecked()

    def setMaintainOffset(self, maintainOffset):
        """
        Updates the `maintainOffset` flag.

        :type maintainOffset: bool
        :rtype: None
        """

        self.maintainOffsetCheckBox.setChecked(maintainOffset)

    def constraintFlags(self):
        """
        Returns the constraint flags.

        :rtype: Dict[str, Any]
        """

        skipTranslate = self.translateXYZWidget.flags(prefix='skipTranslate', inverse=True)
        skipRotate = self.rotateXYZWidget.flags(prefix='skipRotate', inverse=True)
        skipScale = self.scaleXYZWidget.flags(prefix='skipScale', inverse=True)
        maintainOffset = self.maintainOffset()

        return dict(maintainOffset=maintainOffset, **skipTranslate, **skipRotate, **skipScale)

    def isMuted(self):
        """
        Evaluates if the current constraint is muted.

        :rtype: bool
        """

        return self.mutePushButton.isChecked()

    @undo.Undo(name='Add Constraint')
    def addConstraint(self, node, typeName, targets, **kwargs):
        """
        Adds the specified constraint type to the supplied node.

        :type node: mpynode.MPyNode
        :type typeName: str
        :type targets: List[mpynode.MPyNode]
        :key maintainOffset: bool
        :rtype: mpynode.MPyNode
        """

        hasConstraint = node.hasConstraint(typeName)

        if hasConstraint:
            
            constraint = node.findConstraint(typeName)
            constraint.addTargets(targets, **kwargs)

            return constraint

        else:

            return node.addConstraint(typeName, targets, **kwargs)

    @undo.Undo(name='Add Skin Constraint')
    def addSkinConstraint(self, node, target, **kwargs):
        """
        Adds a transform constraint to the supplied node.
        Targets and weights are derived from the nearest skin weights.

        :type node: mpynode.MPyNode
        :type target: mpynode.MPyNode
        :key maintainOffset: bool
        :rtype: mpynode.MPyNode
        """

        # Get skin deformer from mesh
        #
        mesh = target.shape()

        skins = mesh.getDeformersByType(om.MFn.kSkinClusterFilter)
        numSkins = len(skins)

        if numSkins != 1:

            log.error(f'addSkinConstraint() require a mesh with a skin deformer ({numSkins} found)!')
            return

        # Get closest point on mesh
        #
        position = node.translation(space=om.MSpace.kWorld)
        controlPoints = list(map(om.MVector, mesh.controlPoints()))

        pointTree = cKDTree(controlPoints)
        closestDistances, closestIndices = pointTree.query([position])

        closestIndex = closestIndices[0]

        # Copy skin influences from closest vertex
        #
        skin = skins[0]
        influences = skin.influences()
        influenceWeights = skin.weightList(closestIndex)[closestIndex]

        targets = [influences[influenceId] for influenceId in influenceWeights.keys()]
        weights = list(influenceWeights.values())

        # Add transform constraint
        #
        constraint = node.addConstraint('transformConstraint', targets, **kwargs)

        for (i, target) in enumerate(constraint.iterTargets()):

            target.setWeight(weights[i])

        constraint.maintainOffset()

        return constraint

    def mute(self):
        """
        Disconnects the current constraint.

        :rtype: None
        """

        # Check if current node exists
        #
        if self.currentNode is None:

            return

        # Disconnect constrained plugs
        #
        self._muted = []

        for destination in self.currentNode.iterPlugs(channelBox=True):

            # Check if plug is constrained
            #
            if not plugutils.isConstrained(destination):

                continue

            # Cache connection
            #
            source = destination.source()
            pair = (source, destination)

            self._muted.append(pair)

            # Disconnect plugs
            #
            self.currentNode.disconnectPlugs(source, destination)

    def unmute(self):
        """
        Reconnects the current constraint.

        :rtype: None
        """

        # Check if current node exists
        #
        if self.currentNode is None:

            return

        # Disconnect constrained plugs
        #
        for (source, destination) in self._muted:

            self.currentNode.connectPlugs(source, destination)

        # Reset internal tracker
        #
        self._muted = []

    def invalidateEditor(self):
        """
        Refreshes the text on the edit button.

        :rtype: None
        """

        # Check if a node is being edited
        #
        if self.editPushButton.isChecked():

            return

        # Evaluate active selection
        #
        if self.selectedNode is not None:

            self.editPushButton.setText(f'Edit {self.selectedNode.name()}')

        else:

            self.editPushButton.setText('Nothing Selected')

    def invalidateConstraints(self):
        """
        Refreshes the constraint combo-box.

        :rtype: None
        """

        currentIndex = self.constraintComboBox.currentIndex()

        constraints = [constraint.name() for constraint in self._constraints]
        numConstraints = len(constraints)

        self.constraintComboBox.clear()
        self.constraintComboBox.addItems(constraints)

        if 0 <= currentIndex < numConstraints:

            self.constraintComboBox.setCurrentIndex(currentIndex)

    def invalidateTargets(self):
        """
        Refreshes the target table view.

        :rtype: None
        """

        # Check if current constraint exists
        #
        self._targets = []

        if self.currentConstraint is not None:

            self._targets.extend(self.currentConstraint.targets())

        # Update target item model
        #
        self._targetCount = len(self._targets)
        self.targetItemModel.setRowCount(self._targetCount)

        for (i, target) in enumerate(self.targets):

            verticalHeaderItem = QtGui.QStandardItem(str(target.index))
            verticalHeaderItem.setSizeHint(QtCore.QSize(24, 24))
            verticalHeaderItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.targetItemModel.setVerticalHeaderItem(i, verticalHeaderItem)

            index = self.targetItemModel.index(i, 0)
            self.targetItemModel.setData(index, target.name(), role=QtCore.Qt.DisplayRole)

            index = self.targetItemModel.index(i, 1)
            self.targetItemModel.setData(index, str(target.weight()), role=QtCore.Qt.DisplayRole)

    def invalidateWeight(self):
        """
        Refreshes the weight spin-box.

        :rtype: None
        """

        weight = self.currentTarget.weight() if self.currentTarget is not None else 1.0

        self.weightSpinBox.blockSignals(True)
        self.weightSpinBox.setValue(weight)
        self.weightSpinBox.blockSignals(False)

    def invalidate(self, reason=None):
        """
        Refreshes the user interface.

        :type reason: Union[InvalidateReason, None]
        :rtype: None
        """

        # Call parent method
        #
        super(QConstraintsTab, self).invalidate()

        # Evaluate invalidation reason
        #
        if reason == self.InvalidateReason.SELECTION_CHANGED:

            self.invalidateEditor()
    # endregion

    # region Slots
    @QtCore.Slot()
    def on_constraintPushButton_clicked(self):
        """
        Slot method for the `constraintPushButton` widget's `clicked` signal.

        :rtype: None
        """
        
        sender = self.sender()
        typeName = sender.whatsThis()
        
        if self.selectionCount >= 2:
            
            node, targets = self.selection[-1], self.selection[:-1]
            flags = self.constraintFlags()
            
            self.addConstraint(node, typeName, targets, **flags)

        else:

            log.warning(f'Point constraints requires a minimum of 2 selected nodes ({self.selectionCount} selected)!')

    @QtCore.Slot()
    def on_pointOnCurvePushButton_clicked(self):
        """
        Slot method for the `pointOnCurvePushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate active selection
        #
        if self.selectionCount != 2:

            log.warning(f'Point-On-Curve constraints requires 2 selected nodes ({self.selectionCount} selected)!')
            return

        # Evaluate target
        #
        node = self.selection[1]
        target = self.selection[0].shape()

        if target is None:

            log.warning(f'Point-On-Curve constraints requires a target with a shape node!')
            return

        # Evaluate target shape
        #
        sender = self.sender()

        if target.hasFn(om.MFn.kCurve):

            self.addConstraint(node, sender.whatsThis(), [target], **self.constraintFlags())

        else:

            log.warning(f'Point-On-Curve constraints requires a target with a nurbs-curve shape ({target.typeName} found)!')

    @QtCore.Slot()
    def on_pointOnPolyPushButton_clicked(self):
        """
        Slot method for the `pointOnPolyPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate active selection
        #
        if self.selectionCount != 2:

            log.warning(f'Point-On-Poly constraints requires 2 selected nodes ({self.selectionCount} selected)!')
            return

        # Evaluate target
        #
        node = self.selection[1]
        target = self.selection[0].shape()

        if target is None:

            log.warning(f'Point-On-Poly constraints requires a target with a shape node!')
            return

        # Evaluate target shape
        #
        sender = self.sender()

        if target.hasFn(om.MFn.kMesh):

            self.addConstraint(node, sender.whatsThis(), [target], **self.constraintFlags())

        else:

            log.warning(f'Point-On-Poly constraints requires a target with a mesh shape ({target.typeName} found)!')

    @QtCore.Slot()
    def on_skinPushButton_clicked(self):
        """
        Slot method for the `skinPushButton` widget's `clicked` signal.

        :rtype: None
        """

        if self.selectionCount == 2:

            self.addSkinConstraint(self.selection[1], self.selection[0], **self.constraintFlags())

        else:

            log.warning(f'Skin constraints requires 2 selected nodes ({self.selectionCount} selected)!')

    @QtCore.Slot(bool)
    def on_editPushButton_clicked(self, checked=False):
        """
        Slot method for the `editPushButton` widget's `clicked` signal.

        :type checked: bool
        :rtype: None
        """

        # Evaluate checked state
        #
        sender = self.sender()

        if checked:

            # Evaluate active selection
            #
            if self.selectionCount == 0:

                sender.setChecked(False)
                return

            # Evaluate selected node
            #
            selectedNode = self.selection[0]

            if not (selectedNode.hasFn(om.MFn.kTransform) and not selectedNode.hasFn(om.MFn.kConstraint, om.MFn.kPluginConstraintNode)):

                sender.setChecked(False)
                return

            # Update internal trackers
            #
            self._currentNode = self.selection[0]
            self._constraints = self._currentNode.constraints()
            self._currentConstraint = self._constraints[0] if len(self._constraints) > 0 else None

            # Invalidate user interface
            #
            self.editPushButton.setText(f'Editing {self._currentNode.name()}')
            self.invalidateConstraints()

        else:

            # Check if current node is muted
            #
            if self.isMuted():

                self.mutePushButton.click()

            # Reset user interface
            #
            self._currentNode = None
            self._constraints = []
            self._currentConstraint = None

            self.invalidateEditor()
            self.invalidateConstraints()

    @QtCore.Slot(int)
    def on_constraintComboBox_currentIndexChanged(self, index):
        """
        Slot method for the `constraintComboBox` widget's `currentIndexChanged` signal.

        :type index: bool
        :rtype: None
        """

        sender = self.sender()
        numConstraints = sender.count()

        if 0 <= index < numConstraints:

            self._currentConstraint = self.constraints[index]

        else:

            self._currentConstraint = None

        self.invalidateTargets()

    @QtCore.Slot()
    def on_addTargetPushButton_clicked(self):
        """
        Slot method for the `addTargetPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Check if current constraint exists
        #
        if self.currentConstraint is None:

            return

        # Evaluate active selection
        #
        if self.selectionCount == 0:

            log.warning('No nodes selected to add to constraint!')
            return

        # Add selection to constraint targets
        #
        currentTargets = [target.targetObject() for target in self.targets]
        targets = [node for node in self.selection if node not in currentTargets and node is not self.currentNode]

        self.currentConstraint.addTargets(targets, maintainOffset=self.maintainOffset())
        self.invalidateTargets()

    @QtCore.Slot()
    def on_removeTargetPushButton_clicked(self):
        """
        Slot method for the `removeTargetPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Check if current constraint exists
        #
        if self.currentConstraint is None:

            return

        # Evaluate selected rows
        #
        rows = list({index.row() for index in self.targetTableView.selectedIndexes()})
        numRows = len(rows)

        if numRows == 0:

            log.warning('No target selected to remove!')
            return

        # Remove targets
        #
        maintainOffset = self.maintainOffset()

        for row in reversed(rows):

            index = int(self.targets[row].index)
            self.currentConstraint.removeTarget(index, maintainOffset=maintainOffset)

        self.invalidateTargets()

    @QtCore.Slot()
    def on_renameTargetPushButton_clicked(self):
        """
        Slot method for the `renameTargetPushButton` widget's `clicked` signal.

        :rtype: None
        """

        for target in self.targets:

            target.resetName()
            self.invalidateTargets()

    @QtCore.Slot()
    def on_selectTargetPushButton_clicked(self):
        """
        Slot method for the `selectTargetPushButton` widget's `clicked` signal.

        :rtype: None
        """

        if self.currentTarget is not None:

            self.currentTarget.targetObject().select(replace=True)

    @QtCore.Slot(QtCore.QModelIndex)
    def on_targetTableView_clicked(self, index):
        """
        Slot method for the `targetTableView` widget's `selectionChanged` signal.

        :type index: QtCore.QModelIndex
        :rtype: None
        """

        # Evaluate selection change
        #
        row = index.row()

        if 0 <= row < self.targetCount:

            self._currentTarget = self._targets[row]

        else:

            self._currentTarget = None

        # Update targets
        #
        self.invalidateWeight()

    @QtCore.Slot(float)
    def on_weightSpinBox_valueChanged(self, value):
        """
        Slot method for the `weightSpinBox` widget's `valueChanged` signal.

        :type value: float
        :rtype: None
        """

        if self.currentTarget is not None:

            self.currentTarget.setWeight(value)
            self.invalidateTargets()

    @QtCore.Slot(bool)
    def on_mutePushButton_clicked(self, checked=False):
        """
        Slot method for the `mutePushButton` widget's `clicked` signal.

        :type checked: bool
        :rtype: None
        """

        sender = self.sender()

        if checked:

            if self.currentConstraint is not None:

                self.mute()

            else:

                sender.setChecked(False)

        else:

            self.unmute()

    @QtCore.Slot()
    def on_updateOffsetsPushButton_clicked(self):
        """
        Slot method for the `updateOffsetsPushButton` widget's `clicked` signal.

        :rtype: None
        """

        if self.currentConstraint is not None:

            self.currentConstraint.updateRestMatrix()
            self.currentConstraint.maintainOffset()

    @QtCore.Slot()
    def on_resetOffsetsPushButton_clicked(self):
        """
        Slot method for the `resetOffsetsPushButton` widget's `clicked` signal.

        :rtype: None
        """

        for target in self.targets:

            target.resetTargetOffsets()
    # endregion
