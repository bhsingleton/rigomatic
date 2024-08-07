from maya.api import OpenMaya as om
from Qt import QtCore, QtWidgets, QtGui
from dcc.maya.decorators import undo
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

        self.resetGroupBox = None
        self.resetPivotsPushButton = None
        self.resetPreRotationsPushButton = None
        self.zeroTransformsPushButton = None
        self.sanitizeTransformsPushButton = None

        self.displayGroupBox = None
        self.localAxesPushButton = None
        self.selectionHandlesPushButton = None
        self.cvsPushButton = None
        self.editPointsPushButton = None
        self.verticesPushButton = None
        self.edgeHardnessPushButton = None
        self.faceNormalsPushButton = None
        self.vertexNormalsPushButton = None
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
        self.translateXYZWidget.setCheckStates([True, True, True])

        self.rotateXYZWidget.setText('Rotate')
        self.rotateXYZWidget.setCheckStates([True, True, True])

        self.scaleXYZWidget.setText('Scale')
        self.scaleXYZWidget.setCheckStates([False, False, False])

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
