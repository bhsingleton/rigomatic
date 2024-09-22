from maya.api import OpenMaya as om
from Qt import QtCore, QtWidgets, QtGui
from dcc.ui import qxyzwidget, qdivider
from dcc.maya.decorators import undo
from . import qabstracttab

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QModifyTab(qabstracttab.QAbstractTab):
    """
    Overload of `QAbstractTab` that interfaces with scene nodes.
    """

    # region Dunderscores
    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        # Call parent method
        #
        super(QModifyTab, self).__setup_ui__(*args, **kwargs)

        # Initialize central layout
        #
        centralLayout = QtWidgets.QVBoxLayout()
        centralLayout.setObjectName('centralLayout')
        centralLayout.setAlignment(QtCore.Qt.AlignTop)

        self.setLayout(centralLayout)

        # Initialize align group-box
        #
        self.alignLayout = QtWidgets.QVBoxLayout()
        self.alignLayout.setObjectName('alignLayout')

        self.alignGroupBox = QtWidgets.QGroupBox('Align:')
        self.alignGroupBox.setObjectName('alignGroupBox')
        self.alignGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.alignGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.alignGroupBox.setLayout(self.alignLayout)
        
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

        self.alignCheckBoxLayout = QtWidgets.QHBoxLayout()
        self.alignCheckBoxLayout.setObjectName('alignCheckBoxLayout')
        self.alignCheckBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.alignCheckBoxLayout.addWidget(self.translateXYZWidget)
        self.alignCheckBoxLayout.addWidget(self.rotateXYZWidget)
        self.alignCheckBoxLayout.addWidget(self.scaleXYZWidget)

        self.preserveShapesCheckBox = QtWidgets.QCheckBox('Preserve Shapes')
        self.preserveShapesCheckBox.setObjectName('preserveShapesCheckBox')
        self.preserveShapesCheckBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))
        self.preserveShapesCheckBox.setFixedHeight(24)
        self.preserveShapesCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)

        self.alignPushButton = QtWidgets.QPushButton('Align')
        self.alignPushButton.setObjectName('alignPushButton')
        self.alignPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.alignPushButton.setFixedHeight(24)
        self.preserveShapesCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.alignPushButton.clicked.connect(self.on_alignPushButton_clicked)

        self.alignButtonLayout = QtWidgets.QHBoxLayout()
        self.alignButtonLayout.setObjectName('alignButtonLayout')
        self.alignButtonLayout.setContentsMargins(0, 0, 0, 0)
        self.alignButtonLayout.addWidget(self.preserveShapesCheckBox)
        self.alignButtonLayout.addWidget(self.alignPushButton)

        self.alignLayout.addLayout(self.alignCheckBoxLayout)
        self.alignLayout.addLayout(self.alignButtonLayout)

        centralLayout.addWidget(self.alignGroupBox)

        # Initialize freeze group-box
        #
        self.freezeLayout = QtWidgets.QGridLayout()
        self.freezeLayout.setObjectName('freezeLayout')

        self.freezeGroupBox = QtWidgets.QGroupBox('Freeze:')
        self.freezeGroupBox.setObjectName('freezeGroupBox')
        self.freezeGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.freezeGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.freezeGroupBox.setLayout(self.freezeLayout)

        self.translateCheckBox = QtWidgets.QCheckBox('Translate')
        self.translateCheckBox.setObjectName('translateCheckBox')
        self.translateCheckBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.translateCheckBox.setFixedHeight(24)
        self.translateCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.translateCheckBox.setChecked(True)

        self.rotateCheckBox = QtWidgets.QCheckBox('Rotate')
        self.rotateCheckBox.setObjectName('rotateCheckBox')
        self.rotateCheckBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.rotateCheckBox.setFixedHeight(24)
        self.rotateCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.rotateCheckBox.setChecked(True)

        self.scaleCheckBox = QtWidgets.QCheckBox('Scale')
        self.scaleCheckBox.setObjectName('scaleCheckBox')
        self.scaleCheckBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.scaleCheckBox.setFixedHeight(24)
        self.scaleCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.scaleCheckBox.setChecked(False)

        self.freezeButtonGroup = QtWidgets.QButtonGroup(parent=self.freezeGroupBox)
        self.freezeButtonGroup.setObjectName('freezeButtonGroup')
        self.freezeButtonGroup.setExclusive(False)
        self.freezeButtonGroup.addButton(self.translateCheckBox, id=0)
        self.freezeButtonGroup.addButton(self.rotateCheckBox, id=1)
        self.freezeButtonGroup.addButton(self.scaleCheckBox, id=2)

        self.freezeCheckBoxLayout = QtWidgets.QHBoxLayout()
        self.freezeCheckBoxLayout.setObjectName('freezeCheckBoxLayout')
        self.freezeCheckBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.freezeCheckBoxLayout.addWidget(self.translateCheckBox, alignment=QtCore.Qt.AlignCenter)
        self.freezeCheckBoxLayout.addWidget(self.rotateCheckBox, alignment=QtCore.Qt.AlignCenter)
        self.freezeCheckBoxLayout.addWidget(self.scaleCheckBox, alignment=QtCore.Qt.AlignCenter)

        self.freezePivotsPushButton = QtWidgets.QPushButton('Freeze (Pivot)')
        self.freezePivotsPushButton.setObjectName('freezePivotsPushButton')
        self.freezePivotsPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.freezePivotsPushButton.setFixedHeight(24)
        self.freezePivotsPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.freezePivotsPushButton.clicked.connect(self.on_freezePivotsPushButton_clicked)

        self.meltPivotsPushButton = QtWidgets.QPushButton('Freeze (Pivot)')
        self.meltPivotsPushButton.setObjectName('meltPivotsPushButton')
        self.meltPivotsPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.meltPivotsPushButton.setFixedHeight(24)
        self.meltPivotsPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.meltPivotsPushButton.clicked.connect(self.on_meltPivotsPushButton_clicked)

        self.freezeParentOffsetsPushButton = QtWidgets.QPushButton('Freeze (Parent-Offset)')
        self.freezeParentOffsetsPushButton.setObjectName('freezeParentOffsetsPushButton')
        self.freezeParentOffsetsPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.freezeParentOffsetsPushButton.setFixedHeight(24)
        self.freezeParentOffsetsPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.freezeParentOffsetsPushButton.clicked.connect(self.on_freezeParentOffsetsPushButton_clicked)

        self.meltParentOffsetsPushButton = QtWidgets.QPushButton('Melt (Parent-Offset)')
        self.meltParentOffsetsPushButton.setObjectName('meltParentOffsetsPushButton')
        self.meltParentOffsetsPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.meltParentOffsetsPushButton.setFixedHeight(24)
        self.meltParentOffsetsPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.meltParentOffsetsPushButton.clicked.connect(self.on_meltParentOffsetsPushButton_clicked)

        self.freezeLayout.addLayout(self.freezeCheckBoxLayout, 0, 0, 1, 2)
        self.freezeLayout.addWidget(self.freezePivotsPushButton, 1, 0)
        self.freezeLayout.addWidget(self.meltPivotsPushButton, 1, 1)
        self.freezeLayout.addWidget(self.freezeParentOffsetsPushButton, 2, 0)
        self.freezeLayout.addWidget(self.meltParentOffsetsPushButton, 2, 1)

        centralLayout.addWidget(self.freezeGroupBox)

        # Initialize reset group-box
        #
        self.resetLayout = QtWidgets.QGridLayout()
        self.resetLayout.setObjectName('resetLayout')

        self.resetGroupBox = QtWidgets.QGroupBox('Reset:')
        self.resetGroupBox.setObjectName('resetGroupBox')
        self.resetGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.resetGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.resetGroupBox.setLayout(self.resetLayout)
        
        self.resetPivotsPushButton = QtWidgets.QPushButton('Reset Pivots')
        self.resetPivotsPushButton.setObjectName('resetPivotsPushButton')
        self.resetPivotsPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.resetPivotsPushButton.setFixedHeight(24)
        self.resetPivotsPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.resetPivotsPushButton.clicked.connect(self.on_resetPivotsPushButton_clicked)

        self.resetPreRotationsPushButton = QtWidgets.QPushButton('Reset Pre-Rotations')
        self.resetPreRotationsPushButton.setObjectName('resetPreRotationsPushButton')
        self.resetPreRotationsPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.resetPreRotationsPushButton.setFixedHeight(24)
        self.resetPreRotationsPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.resetPreRotationsPushButton.clicked.connect(self.on_resetPreRotationsPushButton_clicked)

        self.zeroTransformsPushButton = QtWidgets.QPushButton('Zero Transforms')
        self.zeroTransformsPushButton.setObjectName('zeroTransformsPushButton')
        self.zeroTransformsPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.zeroTransformsPushButton.setFixedHeight(24)
        self.zeroTransformsPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.zeroTransformsPushButton.clicked.connect(self.on_zeroTransformsPushButton_clicked)

        self.sanitizeTransformsPushButton = QtWidgets.QPushButton('Sanitize Transforms')
        self.sanitizeTransformsPushButton.setObjectName('sanitizeTransformsPushButton')
        self.sanitizeTransformsPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.sanitizeTransformsPushButton.setFixedHeight(24)
        self.sanitizeTransformsPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.sanitizeTransformsPushButton.clicked.connect(self.on_sanitizeTransformsPushButton_clicked)

        self.resetLayout.addWidget(self.resetPivotsPushButton, 0, 0)
        self.resetLayout.addWidget(self.resetPreRotationsPushButton, 0, 1)
        self.resetLayout.addWidget(self.zeroTransformsPushButton, 1, 0)
        self.resetLayout.addWidget(self.sanitizeTransformsPushButton, 1, 1)

        centralLayout.addWidget(self.resetGroupBox)

        # Initialize display group-box
        #
        self.displayLayout = QtWidgets.QGridLayout()
        self.displayLayout.setObjectName('displayLayout')

        self.displayGroupBox = QtWidgets.QGroupBox('Display:')
        self.displayGroupBox.setObjectName('displayGroupBox')
        self.displayGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.displayGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.displayGroupBox.setLayout(self.displayLayout)

        self.localAxesPushButton = QtWidgets.QPushButton('Local Axes')
        self.localAxesPushButton.setObjectName('localAxesPushButton')
        self.localAxesPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.localAxesPushButton.setFixedHeight(24)
        self.localAxesPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.localAxesPushButton.clicked.connect(self.on_localAxesPushButton_clicked)

        self.selectionHandlesPushButton = QtWidgets.QPushButton('Selection Handles')
        self.selectionHandlesPushButton.setObjectName('selectionHandlesPushButton')
        self.selectionHandlesPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.selectionHandlesPushButton.setFixedHeight(24)
        self.selectionHandlesPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.selectionHandlesPushButton.clicked.connect(self.on_selectionHandlesPushButton_clicked)

        self.displayLayout.addWidget(self.localAxesPushButton, 0, 0)
        self.displayLayout.addWidget(self.selectionHandlesPushButton, 0, 1)

        # Initialize curves display section
        #
        self.curvesDividerLayout = QtWidgets.QHBoxLayout()
        self.curvesDividerLayout.setObjectName('curvesDividerLayout')
        self.curvesDividerLayout.setContentsMargins(0, 0, 0, 0)

        self.curvesDivider = QtWidgets.QWidget()
        self.curvesDivider.setObjectName('curvesDivider')
        self.curvesDivider.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.curvesDivider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.curvesDivider.setLayout(self.curvesDividerLayout)

        self.curvesLabel = QtWidgets.QLabel('Curves:')
        self.curvesLabel.setObjectName('curvesLabel')
        self.curvesLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred))
        self.curvesLabel.setFocusPolicy(QtCore.Qt.NoFocus)

        self.curvesLine = qdivider.QDivider(QtCore.Qt.Horizontal)
        self.curvesLine.setObjectName('curvesLine')
        self.curvesLine.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred))
        self.curvesLine.setFocusPolicy(QtCore.Qt.NoFocus)

        self.curvesDividerLayout.addWidget(self.curvesLabel)
        self.curvesDividerLayout.addWidget(self.curvesLine)

        self.cvsPushButton = QtWidgets.QPushButton('CVs')
        self.cvsPushButton.setObjectName('cvsPushButton')
        self.cvsPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.cvsPushButton.setFixedHeight(24)
        self.cvsPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.cvsPushButton.clicked.connect(self.on_cvsPushButton_clicked)

        self.editPointsPushButton = QtWidgets.QPushButton('Edit Points')
        self.editPointsPushButton.setObjectName('editPointsPushButton')
        self.editPointsPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.editPointsPushButton.setFixedHeight(24)
        self.editPointsPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.editPointsPushButton.clicked.connect(self.on_editPointsPushButton_clicked)

        self.displayLayout.addWidget(self.curvesDivider, 1, 0, 1, 2)
        self.displayLayout.addWidget(self.cvsPushButton, 2, 0)
        self.displayLayout.addWidget(self.editPointsPushButton, 2, 1)

        # Initialize mesh display section
        #
        self.meshesDividerLayout = QtWidgets.QHBoxLayout()
        self.meshesDividerLayout.setObjectName('meshesDividerLayout')
        self.meshesDividerLayout.setContentsMargins(0, 0, 0, 0)

        self.meshesDivider = QtWidgets.QWidget()
        self.meshesDivider.setObjectName('meshesDivider')
        self.meshesDivider.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.meshesDivider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.meshesDivider.setLayout(self.meshesDividerLayout)

        self.meshesLabel = QtWidgets.QLabel('Meshes:')
        self.meshesLabel.setObjectName('meshesLabel')
        self.meshesLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred))
        self.meshesLabel.setFocusPolicy(QtCore.Qt.NoFocus)

        self.meshesLine = qdivider.QDivider(QtCore.Qt.Horizontal)
        self.meshesLine.setObjectName('meshesLine')
        self.meshesLine.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred))
        self.meshesLine.setFocusPolicy(QtCore.Qt.NoFocus)

        self.meshesDividerLayout.addWidget(self.meshesLabel)
        self.meshesDividerLayout.addWidget(self.meshesLine)
        
        self.verticesPushButton = QtWidgets.QPushButton('Vertices')
        self.verticesPushButton.setObjectName('verticesPushButton')
        self.verticesPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.verticesPushButton.setFixedHeight(24)
        self.verticesPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.verticesPushButton.clicked.connect(self.on_verticesPushButton_clicked)

        self.edgeHardnessPushButton = QtWidgets.QPushButton('Edge Hardness')
        self.edgeHardnessPushButton.setObjectName('edgeHardnessPushButton')
        self.edgeHardnessPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.edgeHardnessPushButton.setFixedHeight(24)
        self.edgeHardnessPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.edgeHardnessPushButton.clicked.connect(self.on_edgeHardnessPushButton_clicked)

        self.faceNormalsPushButton = QtWidgets.QPushButton('Face Normals')
        self.faceNormalsPushButton.setObjectName('faceNormalsPushButton')
        self.faceNormalsPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.faceNormalsPushButton.setFixedHeight(24)
        self.faceNormalsPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.faceNormalsPushButton.clicked.connect(self.on_faceNormalsPushButton_clicked)

        self.vertexNormalsPushButton = QtWidgets.QPushButton('Vertex Normals')
        self.vertexNormalsPushButton.setObjectName('vertexNormalsPushButton')
        self.vertexNormalsPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.vertexNormalsPushButton.setFixedHeight(24)
        self.vertexNormalsPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.vertexNormalsPushButton.clicked.connect(self.on_vertexNormalsPushButton_clicked)

        self.displayLayout.addWidget(self.meshesDivider, 3, 0, 1, 2)
        self.displayLayout.addWidget(self.verticesPushButton, 4, 0)
        self.displayLayout.addWidget(self.edgeHardnessPushButton, 4, 1)
        self.displayLayout.addWidget(self.faceNormalsPushButton, 5, 0)
        self.displayLayout.addWidget(self.vertexNormalsPushButton, 5, 1)

        centralLayout.addWidget(self.displayGroupBox)
    # endregion

    # region Methods
    def alignmentFlags(self):
        """
        Returns the alignments flags.

        :rtype: Dict[str, bool]
        """

        skipTranslate = self.translateXYZWidget.flags(prefix='skipTranslate', inverse=True)
        skipRotate = self.rotateXYZWidget.flags(prefix='skipRotate', inverse=True)
        skipScale = self.scaleXYZWidget.flags(prefix='skipScale', inverse=True)

        return {**skipTranslate, **skipRotate, **skipScale}

    def preserveShapes(self):
        """
        Returns the `preserveShapes` flag.

        :rtype: bool
        """

        return self.preserveShapesCheckBox.isChecked()

    def setPreserveShapes(self, preserveShapes):
        """
        Updates the `preserveShapes` flag.

        :type preserveShapes: bool
        :rtype: None
        """

        self.preserveShapesCheckBox.setChecked(preserveShapes)

    @undo.Undo(name='Align Nodes')
    def alignNodes(self, copyFrom, copyTo, **kwargs):
        """
        Aligns the second node to the first node.

        :type copyFrom: mpynode.MPyNode
        :type copyTo: mpynode.MPyNode
        :rtype: None
        """

        # Evaluate supplied nodes
        #
        if not (copyFrom.hasFn(om.MFn.kTransform) and copyTo.hasFn(om.MFn.kTransform)):

            return

        # Cache initial matrix for later use
        #
        preserveShapes = kwargs.get('preserveShapes', False)
        initialMatrix = copyTo.matrix()

        # Copy transform
        #
        copyTo.copyTransform(copyFrom, **kwargs)

        # Check if shapes should be preserved
        #
        if preserveShapes:

            matrix = copyTo.matrix()

            for shape in copyTo.iterShapes():

                isSurface = shape.hasFn(om.MFn.kSurface)
                isCurve = shape.hasFn(om.MFn.kCurve)
                isLocator = shape.hasFn(om.MFn.kLocator)

                if isSurface or isCurve:

                    controlPoints = [om.MPoint(point) * initialMatrix * matrix.inverse() for point in shape.controlPoints()]
                    shape.setControlPoints(controlPoints)

                elif isLocator:

                    localMatrix = shape.localMatrix() * initialMatrix * matrix.inverse()
                    shape.setLocalMatrix(localMatrix)

                else:

                    log.warning(f'No support for {shape.apiTypeStr} shapes!')
                    continue

    @undo.Undo(name='Freeze Parent-Offsets')
    def freezePivots(self, *nodes, includeTranslate=True, includeRotate=True, includeScale=False):
        """
        Freezes the pivots on the supplied nodes.

        :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
        :type includeTranslate: bool
        :type includeRotate: bool
        :type includeScale: bool
        :rtype: None
        """

        # Iterate through nodes
        #
        for node in nodes:

            # Check if this is a transform node
            #
            if not node.hasFn(om.MFn.kTransform):

                continue

            # Freeze transform
            #
            node.freezePivots(includeTranslate=includeTranslate, includeRotate=includeRotate, includeScale=includeScale)

    @undo.Undo(name='Melt Pivots')
    def meltPivots(self, *nodes):
        """
        Melts the pivots on the supplied nodes.

        :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
        :rtype: None
        """

        # Iterate through nodes
        #
        for node in nodes:

            # Check if this is a transform node
            #
            if not node.hasFn(om.MFn.kTransform):

                continue

            # Unfreeze transform
            #
            node.unfreezePivots()

    @undo.Undo(name='Freeze Parent Offsets')
    def freezeParentOffsets(self, *nodes, includeTranslate=True, includeRotate=True, includeScale=False):
        """
        Freezes the parent offsets on the supplied nodes.

        :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
        :type includeTranslate: bool
        :type includeRotate: bool
        :type includeScale: bool
        :rtype: None
        """

        # Iterate through nodes
        #
        for node in nodes:

            # Check if this is a transform node
            #
            if not node.hasFn(om.MFn.kTransform):

                continue

            # Freeze transform
            #
            node.freezeTransform(includeTranslate=includeTranslate, includeRotate=includeRotate, includeScale=includeScale)

    @undo.Undo(name='Melt Parent Offsets')
    def meltParentOffsets(self, *nodes):
        """
        Melts the parent offsets on the supplied nodes.

        :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
        :rtype: None
        """

        # Iterate through nodes
        #
        for node in nodes:

            # Check if this is a transform node
            #
            if node.hasFn(om.MFn.kTransform):

                node.unfreezeTransform()

            else:

                continue

    @undo.Undo(name='Reset Pivots')
    def resetPivots(self, *nodes):
        """
        Resets the pivots on the supplied nodes.

        :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
        :rtype: None
        """

        # Iterate through nodes
        #
        for node in nodes:

            # Check if this is a transform node
            #
            if node.hasFn(om.MFn.kTransform):

                node.resetPivots()

            else:

                continue

    @undo.Undo(name='Reset Pre-Rotations')
    def resetPreRotations(self, *nodes):
        """
        Resets any pre-rotations on the supplied nodes.

        :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
        :rtype: None
        """

        # Iterate through nodes
        #
        for node in nodes:

            # Check if this is a transform node
            #
            if not node.hasFn(om.MFn.kTransform):

                continue

            # Reset pre-rotations
            #
            matrix = node.matrix()

            node.resetPreEulerRotation()
            node.setMatrix(matrix, skipTranslate=True, skipScale=True)

    @undo.Undo(name='Zero Transforms')
    def zeroTransforms(self, *nodes):
        """
        Resets the transform matrix on the supplied nodes.

        :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
        :rtype: None
        """

        # Iterate through nodes
        #
        for node in nodes:

            # Check if this is a transform node
            #
            if not node.hasFn(om.MFn.kTransform):

                continue

            # Reset transform matrix
            #
            node.resetMatrix()

    @undo.Undo(name='Sanitize Transforms')
    def sanitizeTransforms(self, *nodes):
        """
        Cleans the transform matrix on the supplied nodes.

        :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
        :rtype: None
        """

        # Iterate through nodes
        #
        for node in nodes:

            # Check if this is a transform node
            #
            if not node.hasFn(om.MFn.kTransform):

                continue

            # Reset transform matrix
            #
            matrix = node.getAttr('dagLocalMatrix')

            node.unlockAttr('translate', 'rotate', 'scale')
            node.unfreezeTransform()
            node.resetPivots()
            node.resetMatrix()

            # Push change to any shapes
            #
            intermediates = node.intermediateObjects(apiType=om.MFn.kMesh)
            isDeformed = len(intermediates) > 0

            if isDeformed:

                for intermediate in intermediates:

                    controlPoints = [om.MPoint(controlPoint) * matrix for controlPoint in intermediate.controlPoints()]
                    intermediate.setControlPoints(controlPoints)

                    hasLockedNormals = intermediate.isNormalLocked(0)

                    if hasLockedNormals:

                        normals = [om.MVector(normal) * matrix for normal in intermediate.getNormals()]
                        intermediate.setNormals(normals)
                        intermediate.updateSurface()

            else:

                for shape in node.iterShapes(apiType=om.MFn.kMesh):

                    controlPoints = [om.MPoint(controlPoint) * matrix for controlPoint in shape.controlPoints()]
                    shape.setControlPoints(controlPoints)

                    hasLockedNormals = shape.isNormalLocked(0)

                    if hasLockedNormals:

                        normals = [om.MVector(normal) * matrix for normal in shape.getNormals()]
                        shape.setNormals(normals)
                        shape.updateSurface()

            # Re-lock attributes if deformed
            #
            if isDeformed:

                node.lockAttr('translate', 'rotate', 'scale')
    # endregion

    # region Slots
    @QtCore.Slot()
    def on_alignPushButton_clicked(self):
        """
        Slot method for the `alignPushButton` widget's `clicked` signal.

        :rtype: None
        """

        if self.selectionCount == 2:

            alignmentFlags = self.alignmentFlags()
            preserveShapes = self.preserveShapes()

            self.alignNodes(self.selection[0], self.selection[1], preserveShapes=preserveShapes, **alignmentFlags)

        else:

            log.warning(f'Align expects 2 selected nodes ({self.selectionCount} selected)!')

    @QtCore.Slot()
    def on_freezePivotsPushButton_clicked(self):
        """
        Slot method for the `freezePivotsPushButton` widget's `clicked` signal.

        :rtype: None
        """

        includeTranslate = self.translateCheckBox.isChecked()
        includeRotate = self.rotateCheckBox.isChecked()
        includeScale = self.scaleCheckBox.isChecked()

        if self.selectionCount > 0:

            self.freezePivots(
                *self.selection,
                includeTranslate=includeTranslate,
                includeRotate=includeRotate,
                includeScale=includeScale
            )

    @QtCore.Slot()
    def on_meltPivotsPushButton_clicked(self):
        """
        Slot method for the `meltPivotsPushButton` widget's `clicked` signal.

        :rtype: None
        """

        if self.selectionCount > 0:

            self.meltPivots(*self.selection)

    @QtCore.Slot()
    def on_freezeParentOffsetsPushButton_clicked(self):
        """
        Slot method for the `freezeParentOffsetsPushButton` widget's `clicked` signal.

        :rtype: None
        """

        includeTranslate = self.translateCheckBox.isChecked()
        includeRotate = self.rotateCheckBox.isChecked()
        includeScale = self.scaleCheckBox.isChecked()

        if self.selectionCount > 0:

            self.freezeParentOffsets(
                *self.selection,
                includeTranslate=includeTranslate,
                includeRotate=includeRotate,
                includeScale=includeScale
            )

    @QtCore.Slot()
    def on_meltParentOffsetsPushButton_clicked(self):
        """
        Slot method for the `meltParentOffsetsPushButton` widget's `clicked` signal.

        :rtype: None
        """

        if self.selectionCount > 0:

            self.meltParentOffsets(*self.selection)

    @QtCore.Slot()
    def on_resetPivotsPushButton_clicked(self):
        """
        Slot method for the `freezePushButton` widget's `clicked` signal.

        :rtype: None
        """

        if self.selectionCount > 0:

            self.resetPivots(*self.selection)

    @QtCore.Slot()
    def on_resetPreRotationsPushButton_clicked(self):
        """
        Slot method for the `resetPreRotationsPushButton` widget's `clicked` signal.

        :rtype: None
        """

        if self.selectionCount > 0:

            self.resetPreRotations(*self.selection)

    @QtCore.Slot()
    def on_zeroTransformsPushButton_clicked(self):
        """
        Slot method for the `resetTransformsPushButton` widget's `clicked` signal.

        :rtype: None
        """

        if self.selectionCount > 0:

            self.zeroTransforms(*self.selection)

    @QtCore.Slot()
    def on_sanitizeTransformsPushButton_clicked(self):
        """
        Slot method for the `resetScalePushButton` widget's `clicked` signal.

        :rtype: None
        """

        if self.selectionCount > 0:

            self.sanitizeTransforms(*self.selection)

    @QtCore.Slot()
    def on_localAxesPushButton_clicked(self):
        """
        Slot method for the `localAxesPushButton` widget's `clicked` signal.

        :rtype: None
        """

        for node in self.selection:

            if node.hasFn(om.MFn.kDagNode):

                node.displayLocalAxis = not node.displayLocalAxis

            else:

                continue

    @QtCore.Slot()
    def on_selectionHandlesPushButton_clicked(self):
        """
        Slot method for the `selectionHandlesPushButton` widget's `clicked` signal.

        :rtype: None
        """

        for node in self.selection:

            if node.hasFn(om.MFn.kDagNode):

                node.displayHandle = not node.displayHandle

            else:

                continue

    @QtCore.Slot()
    def on_cvsPushButton_clicked(self):
        """
        Slot method for the `cvsPushButton` widget's `clicked` signal.

        :rtype: None
        """

        for node in self.selection:

            if not node.hasFn(om.MFn.kTransform):

                continue

            for shape in node.iterShapes(apiType=om.MFn.kNurbsCurve):

                shape.dispCV = not shape.dispCV

    @QtCore.Slot()
    def on_editPointsPushButton_clicked(self):
        """
        Slot method for the `editPointsPushButton` widget's `clicked` signal.

        :rtype: None
        """

        for node in self.selection:

            if not node.hasFn(om.MFn.kTransform):

                continue

            for shape in node.iterShapes(apiType=om.MFn.kNurbsCurve):

                shape.dispEP = not shape.dispEP

    @QtCore.Slot()
    def on_verticesPushButton_clicked(self):
        """
        Slot method for the `verticesPushButton` widget's `clicked` signal.

        :rtype: None
        """

        for node in self.selection:

            if not node.hasFn(om.MFn.kTransform):

                continue

            for shape in node.iterShapes(apiType=om.MFn.kMesh):

                shape.displayVertices = not shape.displayVertices

    @QtCore.Slot()
    def on_edgeHardnessPushButton_clicked(self):
        """
        Slot method for the `edgeHardnessPushButton` widget's `clicked` signal.

        :rtype: None
        """

        for node in self.selection:

            if not node.hasFn(om.MFn.kTransform):

                continue

            for shape in node.iterShapes(apiType=om.MFn.kMesh):

                shape.displayEdges = 2 if (shape.displayEdges == 0) else 0

    @QtCore.Slot()
    def on_faceNormalsPushButton_clicked(self):
        """
        Slot method for the `faceNormalsPushButton` widget's `clicked` signal.

        :rtype: None
        """

        for node in self.selection:

            if not node.hasFn(om.MFn.kTransform):

                continue

            for shape in node.iterShapes(apiType=om.MFn.kMesh):

                shape.normalType = 1  # Face
                shape.displayNormal = not shape.displayNormal

    @QtCore.Slot()
    def on_vertexNormalsPushButton_clicked(self):
        """
        Slot method for the `vertexNormalsPushButton` widget's `clicked` signal.

        :rtype: None
        """

        for node in self.selection:

            if not node.hasFn(om.MFn.kTransform):

                continue

            for shape in node.iterShapes(apiType=om.MFn.kMesh):

                shape.normalType = 2  # Vtx
                shape.displayNormal = not shape.displayNormal
    # endregion
