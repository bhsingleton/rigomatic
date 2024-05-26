from maya.api import OpenMaya as om
from Qt import QtCore, QtWidgets, QtGui
from dcc.maya.decorators.undo import undo
from dcc.maya.models import qplugitemmodel, qplugitemfiltermodel, qplugstyleditemdelegate
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
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key parent: QtWidgets.QWidget
        :key f: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        super(QModifyTab, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._currentNode = None

        # Declare public variables
        #
        self.alignGroupBox = None
        self.translateXYZWidget = None
        self.rotateXYZWidget = None
        self.scaleXYZWidget = None
        self.preserveShapesCheckBox = None
        self.alignPushButton = None

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
    # endregion

    # region Methods
    def postLoad(self, *args, **kwargs):
        """
        Called after the user interface has been loaded.

        :rtype: None
        """

        # Call parent method
        #
        super(QModifyTab, self).postLoad(*args, **kwargs)

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
        self.userDefinedCheckBox.toggled.connect(self.attributeItemFilterModel.setHideStaticAttributes)

        self.attributeTreeView.setModel(self.attributeItemFilterModel)
        self.attributeTreeView.setItemDelegate(self.attributeStyledItemDelegate)

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
        super(QModifyTab, self).invalidate()

        # Refresh attribute editor
        #
        self.invalidateEditor()
    # endregion

    # region Slots
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
