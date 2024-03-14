from maya.api import OpenMaya as om
from Qt import QtCore, QtWidgets, QtGui
from dcc.python import stringutils
from dcc.maya.libs import transformutils
from dcc.maya.decorators.undo import undo
from . import qabstracttab
from ..models import qplugitemmodel, qplugitemfiltermodel, qplugstyleditemdelegate
from ...libs import kinematicutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QCreateTab(qabstracttab.QAbstractTab):
    """
    Overload of `QAbstractTab` that interfaces with scene nodes.
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
        super(QCreateTab, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._selection = []
        self._selectionCount = 0
        self._selectedNode = None
        self._currentNode = None
        self._currentColor = (0.5, 0.5, 0.5)
        self._currentMatrix = om.MMatrix.kIdentity

        # Declare public variables
        #
        self.nameGroupBox = None
        self.namespaceComboBox = None
        self.namespaceLabel = None
        self.nameWidget = None
        self.nameLineEdit = None
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

        self.freezeGroupBox = None
        self.freezeButtonGroup = None
        self.translateCheckBox = None
        self.rotateCheckBox = None
        self.scaleCheckBox = None
        self.freezePivotsPushButton = None
        self.meltPivotsPushButton = None
        self.freezeParentOffsetsPushButton = None
        self.meltParentOffsetsPushButton = None
        self.resetDivider = None
        self.resetLabel = None
        self.resetLine = None
        self.resetPivotsPushButton = None
        self.resetPreRotationsPushButton = None
        self.zeroTransformsPushButton = None
        self.sanitizeTransformsPushButton = None

        self.alignGroupBox = None
        self.translateXYZWidget = None
        self.rotateXYZWidget = None
        self.scaleXYZWidget = None
        self.preserveShapesCheckBox = None
        self.alignPushButton = None

        self.attributesGroupBox = None
        self.editPushButton = None
        self.filterWidget = None
        self.filterLineEdit = None
        self.userDefinedCheckBox = None
        self.attributeTreeView = None
        self.attributeItemModel = None
        self.attributeItemFilterModel = None
        self.attributeStyledItemDelegate = None
    # endregion

    # region Properties
    @property
    def currentNode(self):
        """
        Getter method that returns the current node.

        :rtype: Union[mpynode.MPyNode, None]
        """

        return self._currentNode

    @property
    def currentMatrix(self):
        """
        Getter method that returns the current transform matrix.

        :rtype: om.MMatrix
        """

        return self._currentMatrix
    # endregion

    # region Methods
    def postLoad(self, *args, **kwargs):
        """
        Called after the user interface has been loaded.

        :rtype: None
        """

        # Call parent method
        #
        super(QCreateTab, self).postLoad(*args, **kwargs)

        # Invalidate namespaces
        #
        self.invalidateNamespaces()

        # Initialize radio button group
        #
        self.freezeButtonGroup = QtWidgets.QButtonGroup(self.freezeGroupBox)
        self.freezeButtonGroup.setObjectName('freezeButtonGroup')
        self.freezeButtonGroup.setExclusive(False)
        self.freezeButtonGroup.addButton(self.translateCheckBox, id=0)
        self.freezeButtonGroup.addButton(self.rotateCheckBox, id=1)
        self.freezeButtonGroup.addButton(self.scaleCheckBox, id=2)

        # Initialize align widgets
        #
        self.translateXYZWidget.setText('Translate')
        self.translateXYZWidget.setMatches([True, True, True])

        self.rotateXYZWidget.setText('Rotate')
        self.rotateXYZWidget.setMatches([True, True, True])

        self.scaleXYZWidget.setText('Scale')
        self.scaleXYZWidget.setMatches([False, False, False])

        # Initialize attribute model
        #
        self.attributeItemModel = qplugitemmodel.QPlugItemModel(parent=self.attributeTreeView)
        self.attributeItemModel.setObjectName('attributeItemModel')

        self.attributeStyledItemDelegate = qplugstyleditemdelegate.QPlugStyledItemDelegate(parent=self.attributeTreeView)
        self.attributeStyledItemDelegate.setObjectName('attributeStyledItemDelegate')

        self.attributeItemFilterModel = qplugitemfiltermodel.QPlugItemFilterModel(parent=self.attributeTreeView)
        self.attributeItemFilterModel.setObjectName('attributeItemFilterModel')
        self.attributeItemFilterModel.setSourceModel(self.attributeItemModel)
        self.filterLineEdit.textChanged.connect(self.attributeItemFilterModel.setFilterWildcard)
        self.userDefinedCheckBox.toggled.connect(self.attributeItemFilterModel.setIgnoreStaticAttributes)

        self.attributeTreeView.setModel(self.attributeItemFilterModel)
        self.attributeTreeView.setItemDelegate(self.attributeStyledItemDelegate)

    def loadSettings(self, settings):
        """
        Loads the user settings.

        :type settings: QtCore.QSettings
        :rtype: None
        """

        # Call parent method
        #
        super(QCreateTab, self).loadSettings(settings)

        # Load user preferences
        #
        color = QtGui.QColor(settings.value('tabs/create/color', defaultValue=QtCore.Qt.black))
        self._currentColor = (color.redF(), color.greenF(), color.blueF())

    def saveSettings(self, settings):
        """
        Saves the user settings.

        :type settings: QtCore.QSettings
        :rtype: None
        """

        # Call parent method
        #
        super(QCreateTab, self).saveSettings(settings)

        # Save user preferences
        #
        color = QtGui.QColor.fromRgbF(*self._currentColor)
        settings.setValue('tabs/create/color', color)

    def wireColor(self):
        """
        Returns the current wire color.

        :rtype: Tuple[float, float, float]
        """

        color = self.wireColorButton.color()
        red, green, blue = color.redF(), color.greenF(), color.blueF()

        return (red, green, blue)

    def alignments(self):
        """
        Returns the alignments flags.

        :rtype: Dict[str, bool]
        """

        skipTranslate = {f'skipTranslate{axis}': not match for (match, axis) in zip(self.translateXYZWidget.matches(), ('X', 'Y', 'Z'))}
        skipRotate = {f'skipRotate{axis}': not match for (match, axis) in zip(self.rotateXYZWidget.matches(), ('X', 'Y', 'Z'))}
        skipScale = {f'skipScale{axis}': not match for (match, axis) in zip(self.scaleXYZWidget.matches(), ('X', 'Y', 'Z'))}

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

    @undo(name='Rename Node')
    def renameNode(self, node, name):
        """
        Renames the supplied node to the specified name.

        :type node: mpynode.MPyNode
        :type name: str
        :rtype: None
        """

        node.setName(name)

    @undo(name='Recolor Node')
    def recolorNodes(self, *nodes, wireColor=(0.0, 0.0, 0.0)):
        """
        Recolors the supplied node to the specified color.

        :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
        :type wireColor: Tuple[float, float, float]
        :rtype: None
        """

        # Iterate through nodes
        #
        for node in nodes:

            # Check if this is a transform node
            #
            if not node.hasFn(om.MFn.kTransform):

                continue

            # Iterate through shapes
            #
            for shape in node.iterShapes():

                shape.useObjectColor = 2
                shape.wireColorRGB = wireColor

    @undo(name='Create Node')
    def createNode(self, typeName, **kwargs):
        """
        Returns a new node derived from the specified type.

        :type typeName: str
        :key name: str
        :key matrix: om.MMatrix
        :key color = Tuple[float, float, float]
        :key locator: bool
        :key helper: bool
        :rtype: mpynode.MPyNode
        """

        # Create node
        #
        name = kwargs.get('name', '')
        cleanName = stringutils.slugify(name)
        uniqueName = cleanName if self.scene.isNameUnique(cleanName) and not stringutils.isNullOrEmpty(name) else f'{typeName}1'

        node = self.scene.createNode(typeName, name=uniqueName)

        # Update transform matrix
        #
        matrix = kwargs.get('matrix', om.MMatrix.kIdentity)
        node.setMatrix(matrix)

        # Add any requested shapes
        #
        locator = kwargs.get('locator', False)
        helper = kwargs.get('helper', False)
        colorRGB = kwargs.get('color', None)

        if locator:

            node.addLocator(colorRGB=colorRGB)

        elif helper:

            node.addPointHelper(colorRGB=colorRGB)

        else:

            pass

        # Update active selection
        #
        node.select(replace=True)

        return node

    @undo(name='Add IK-Solver')
    def addIKSolver(self, startJoint, endJoint):
        """
        Adds an IK solver to the supplied start and end joints.

        :type startJoint: mpynode.MPyNode
        :type endJoint: mpynode.MPyNode
        :rtype: None
        """

        # Evaluate supplied nodes
        #
        if not (startJoint.hasFn(om.MFn.kJoint) and endJoint.hasFn(om.MFn.kJoint)):

            return

        # Evaluate hierarchy
        #
        ancestors = endJoint.ancestors(apiType=om.MFn.kJoint)

        if startJoint not in ancestors:

            log.warning(f'Cannot trace hierarchy between {startJoint} and {endJoint}')
            return

        # Evaluate which solver to apply
        #
        index = ancestors.index(startJoint)

        joints = ancestors[index:] + [endJoint]
        numJoints = len(joints)

        if numJoints == 2:

            kinematicutils.applySingleChainSolver(startJoint, endJoint)

        elif numJoints == 3:

            kinematicutils.applyRotationPlaneSolver(startJoint, endJoint)

        else:

            kinematicutils.applySpringSolver(startJoint, endJoint)

    @undo(name='Create Intermediate')
    def createIntermediate(self, *nodes):
        """
        Returns an intermediate parent to the supplied node.

        :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
        :rtype: mpynode.MPyNode
        """

        # Iterate through nodes
        #
        intermediates = []

        for node in nodes:

            # Check if this is a transform node
            #
            if not node.hasFn(om.MFn.kTransform):

                continue

            # Create parent node
            #
            ancestor = node.parent()
            typeName = node.typeName

            parent = self.scene.createNode(typeName, name='group1', parent=ancestor)
            parent.copyTransform(node)

            # Re-parent node
            #
            node.setParent(parent)
            node.resetMatrix()

            intermediates.append(parent)

        return intermediates

    @undo(name='Freeze Parent-Offsets')
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

    @undo(name='Melt Pivots')
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

    @undo(name='Freeze Parent Offsets')
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

    @undo(name='Melt Parent Offsets')
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
            if not node.hasFn(om.MFn.kTransform):

                continue

            # Unfreeze transform
            #
            node.unfreezeTransform()

    @undo(name='Reset Pivots')
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
            if not node.hasFn(om.MFn.kTransform):

                continue

            # Reset pivots
            #
            node.resetPivots()

    @undo(name='Reset Pre-Rotations')
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

    @undo(name='Zero Transforms')
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

    @undo(name='Sanitize Transforms')
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
            intermediates = node.intermediateObjects()
            isDeformed = len(intermediates) > 0

            if isDeformed:

                for intermediate in intermediates:

                    controlPoints = [om.MPoint(controlPoint) * matrix for controlPoint in intermediate.controlPoints()]
                    intermediate.setControlPoints(controlPoints)

            else:

                for shape in node.iterShapes():

                    controlPoints = [om.MPoint(controlPoint) * matrix for controlPoint in shape.controlPoints()]
                    shape.setControlPoints(controlPoints)

            # Re-lock attributes if deformed
            #
            if isDeformed:

                node.lockAttr('translate', 'rotate', 'scale')

    @undo(name='Align Nodes')
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

    def invalidateName(self):
        """
        Refreshes the name line-edit.

        :rtype: None
        """

        # Evaluate active selection
        #
        if self.selectedNode is not None:

            self.namespaceComboBox.blockSignals(True)
            self.namespaceComboBox.setCurrentIndex(self.namespaceComboBox.findText(self.selectedNode.namespace()))
            self.namespaceComboBox.blockSignals(False)

            self.nameLineEdit.blockSignals(True)
            self.nameLineEdit.setText(self.selectedNode.name())
            self.nameLineEdit.blockSignals(False)

        else:

            self.nameLineEdit.blockSignals(True)
            self.nameLineEdit.setText('')
            self.nameLineEdit.blockSignals(False)

    def invalidateNamespaces(self):
        """
        Refreshes the namespace combo-box.

        :rtype: None
        """

        namespaces = om.MNamespace.getNamespaces(parentNamespace=':', recurse=True)
        namespaces.insert(0, '')

        self.namespaceComboBox.blockSignals(True)
        self.namespaceComboBox.clear()
        self.namespaceComboBox.addItems(namespaces)
        self.namespaceComboBox.blockSignals(False)

    def invalidateWireColor(self):
        """
        Refreshes the wire-color button.

        :rtype: None
        """

        # Evaluate current selection
        #
        selection = [node for node in self.selection if node.hasFn(om.MFn.kTransform)]
        selectionCount = len(selection)

        if selectionCount > 0:

            # Adopt selected node's wire-color
            #
            node = selection[0]
            shape = node.shape()
            color = QtGui.QColor.fromRgbF(*shape.wireColorRGB) if (shape is not None) else QtGui.QColor.fromRgbF(*node.wireColorRGB)

            self.wireColorButton.blockSignals(True)
            self.wireColorButton.setColor(color)
            self.wireColorButton.blockSignals(False)

        else:

            # Revert back to internal color
            #
            self.wireColorButton.blockSignals(True)
            self.wireColorButton.setColor(QtGui.QColor.fromRgbF(*self._currentColor))
            self.wireColorButton.blockSignals(False)

    def invalidatePivot(self):
        """
        Refreshes the internal pivot position.

        :rtype: None
        """

        # Evaluate active selection
        #
        componentSelection = self.scene.componentSelection(apiType=om.MFn.kDagNode)
        hasSelection = len(componentSelection) > 0

        if not hasSelection:

            self._currentMatrix = om.MMatrix.kIdentity
            return

        # Calculate active pivot
        #
        boundingBox = om.MBoundingBox()

        for (node, component) in componentSelection:

            # Check if component is valid
            #
            hasComponent = not component.isNull()

            if hasComponent:

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

            else:

                # Expand bounding-box using world position
                #
                worldMatrix = node.worldMatrix()
                position = transformutils.breakMatrix(worldMatrix)[3]

                boundingBox.expand(position)

        # Compose transform matrix
        #
        firstNode = componentSelection[0][0]
        worldMatrix = firstNode.worldMatrix()

        translateMatrix = transformutils.createTranslateMatrix(boundingBox.center)
        rotateMatrix = transformutils.createRotationMatrix(worldMatrix)
        scaleMatrix = transformutils.createScaleMatrix(worldMatrix)
        matrix = scaleMatrix * rotateMatrix * translateMatrix

        self._currentMatrix = matrix

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
        selectedNode = self.selection[0] if (len(self.selection) > 0) else None

        if selectedNode is not None:

            self.editPushButton.setText(f'Edit {selectedNode.name()}')

        else:

            self.editPushButton.setText('Nothing Selected')

    def invalidateAttributes(self):
        """
        Refreshes the attribute tree-view.

        :rtype: None
        """

        # Check if selected node is valid
        #
        if self.currentNode is not None:

            self.attributeItemModel.invisibleRootItem = self.currentNode.handle()

        else:

            self.attributeItemModel.invisibleRootItem = om.MObjectHandle()

        # Resize columns
        #
        self.attributeTreeView.resizeColumnToContents(0)

    def invalidate(self, reason=None):
        """
        Refreshes the user interface.

        :type reason: Union[InvalidateReason, None]
        :rtype: None
        """

        # Call parent method
        #
        super(QCreateTab, self).invalidate()

        # Evaluate invalidation reason
        #
        if reason == self.InvalidateReason.SCENE_CHANGED:

            self.invalidateNamespaces()
            self.invalidate(reason=self.InvalidateReason.SELECTION_CHANGED)

        elif reason == self.InvalidateReason.TAB_CHANGED:

            self.invalidate(reason=self.InvalidateReason.SELECTION_CHANGED)

        elif reason == self.InvalidateReason.SELECTION_CHANGED:

            self.invalidateName()
            self.invalidateWireColor()
            self.invalidatePivot()
            self.invalidateEditor()

        else:

            pass
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

            for node in self.selection:

                self.renameNode(node, f'{namespace}:{node.name()}')

    @QtCore.Slot(str)
    def on_nameLineEdit_textChanged(self, text):
        """
        Slot method for the `nameLineEdit` widget's `textChanged` signal.

        :type text: str
        :rtype: None
        """

        if self.selectedNode is not None:

            self.renameNode(self.selectedNode, text)

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

            self.recolorNodes(*self.selection, wireColor=(color.redF(), color.greenF(), color.blueF()))

        else:

            self._currentColor = (color.redF(), color.greenF(), color.blueF())

    @QtCore.Slot()
    def on_transformPushButton_clicked(self):
        """
        Slot method for the `transformPushButton` widget's `clicked` signal.

        :rtype: None
        """

        self.createNode('transform', name=self.nameLineEdit.text(), matrix=self.currentMatrix)

    @QtCore.Slot()
    def on_jointPushButton_clicked(self):
        """
        Slot method for the `jointPushButton` widget's `clicked` signal.

        :rtype: None
        """

        self.createNode('joint', name=self.nameLineEdit.text(), matrix=self.currentMatrix)

    @QtCore.Slot()
    def on_ikHandlePushButton_clicked(self):
        """
        Slot method for the `ikHandlePushButton` widget's `clicked` signal.

        :rtype: None
        """

        joints = [node for node in self.selection if node.hasFn(om.MFn.kJoint)]
        numJoints = len(joints)

        if numJoints == 2:

            self.addIKSolver(joints[0], joints[1])

        else:

            log.warning(f'Adding IK requires a start and end joint ({numJoints} selected)!')

    @QtCore.Slot()
    def on_locatorPushButton_clicked(self):
        """
        Slot method for the `locatorPushButton` widget's `clicked` signal.

        :rtype: None
        """

        self.createNode(
            'transform',
            name=self.nameLineEdit.text(),
            matrix=self.currentMatrix,
            color=self.wireColor(),
            locator=True
        )

    @QtCore.Slot()
    def on_helperPushButton_clicked(self):
        """
        Slot method for the `helperPushButton` widget's `clicked` signal.

        :rtype: None
        """

        self.createNode(
            'transform',
            name=self.nameLineEdit.text(),
            matrix=self.currentMatrix,
            color=self.wireColor(),
            helper=True
        )

    @QtCore.Slot()
    def on_intermediatePushButton_clicked(self):
        """
        Slot method for the `intermediatePushButton` widget's `clicked` signal.

        :rtype: None
        """

        if self.selectionCount > 0:

            self.createIntermediate(*self.selection)

        else:

            log.warning(f'Creating an intermediate expects at least 1 selected node ({self.selectionCount} selected)!')

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
    def on_alignPushButton_clicked(self):
        """
        Slot method for the `alignPushButton` widget's `clicked` signal.

        :rtype: None
        """

        if self.selectionCount == 2:

            alignments = self.alignments()
            preserveShapes = self.preserveShapes()

            self.alignNodes(self.selection[0], self.selection[1], preserveShapes=preserveShapes, **alignments)

        else:

            log.warning(f'Align expects 2 selected nodes ({self.selectionCount} selected)!')

    @QtCore.Slot(bool)
    def on_editPushButton_clicked(self, checked=False):
        """
        Slot method for the `editPushButton` widget's `clicked` signal.

        :type checked: bool
        :rtype: None
        """

        sender = self.sender()

        if checked:

            # Evaluate active selection
            #
            if self.selectionCount == 0:

                sender.setChecked(False)
                return

            # Update internal trackers
            #
            self._currentNode = self.selection[0]

            # Invalidate user interface
            #
            self.editPushButton.setText(f'Editing {self._currentNode.name()}')
            self.invalidateAttributes()

        else:

            # Reset user interface
            #
            self._currentNode = None

            self.invalidateEditor()
            self.invalidateAttributes()
    # endregion
