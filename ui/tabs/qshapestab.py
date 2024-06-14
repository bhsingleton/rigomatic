import os
import math

from maya.api import OpenMaya as om
from Qt import QtCore, QtWidgets, QtGui
from itertools import chain
from collections import namedtuple
from enum import IntEnum
from random import randint
from dcc.python import stringutils
from dcc.maya.libs import transformutils, shapeutils
from dcc.maya.decorators.undo import undo
from . import qabstracttab
from ..widgets import qcolorbutton
from ...libs import createutils, modifyutils, ColorMode

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


Dimensions = namedtuple('Dimensions', ('width', 'height', 'depth'))


class Dimension(IntEnum):
    """
    Enum class of all available dimensions.
    """

    WIDTH = 0
    HEIGHT = 1
    DEPTH = 2


class PivotType(IntEnum):
    """
    Enum class of all available pivots.
    """

    NONE = -1
    LOCAL = 0
    PARENT = 1
    DEPTH = 2


class QShapesTab(qabstracttab.QAbstractTab):
    """
    Overload of `QAbstractTab` that interfaces shape nodes.
    """

    # region Signals
    startColorChanged = QtCore.Signal(QtGui.QColor)
    endColorChanged = QtCore.Signal(QtGui.QColor)
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
        super(QShapesTab, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._startColor = None
        self._endColor = None

        # Declare public variables
        #
        self.createGroupBox = None
        self.filterWidget = None
        self.filterLineEdit = None
        self.saveShapePushButton = None
        self.refreshPushButton = None
        self.shapeListView = None
        self.shapeItemModel = None
        self.shapeFilterItemModel = None
        self.createCustomPushButton = None
        self.createStarPushButton = None
        self.edgeToCurvePushButton = None
        self.edgeToHelperPushButton = None
        self.degreeSpinBox = None
        self.offsetSpinBox = None
        self.renameShapesPushButton = None
        self.removeShapesPushButton = None

        self.transformGroupBox = None
        self.pivotWidget = None
        self.pivotLabel = None
        self.pivotButtonGroup =None
        self.localRadioButton = None
        self.parentRadioButton = None
        self.worldRadioButton = None
        self.scaleWidget = None
        self.scaleLabel = None
        self.scaleSpinBox = None
        self.growPushButton = None
        self.shrinkPushButton = None
        self.helperDivider = None
        self.helperLabel = None
        self.helperLine = None
        self.widthWidget = None
        self.widthLabel = None
        self.widthSpinBox = None
        self.heightWidget = None
        self.heightLabel = None
        self.heightSpinBox = None
        self.depthWidget = None
        self.depthLabel = None
        self.depthSpinBox = None
        self.fitPushButton = None
        self.resetPushButton = None

        self.parentGroupBox = None
        self.parentPushButton = None
        self.preservePositionCheckBox = None

        self.colorizeGroupBox = None
        self.gradientWidget = None
        self.startColorButton = None
        self.endColorButton = None
        self.gradient = None
        self.swatchesWidget = None
        self.swatchesLayout = None
        self.swatchesButtonGroup = None
        self.useSelectedNodesCheckBox = None
        self.applyPushButton = None
    # endregion

    # region Methods
    def postLoad(self, *args, **kwargs):
        """
        Called after the user interface has been loaded.

        :rtype: None
        """

        # Call parent method
        #
        super(QShapesTab, self).postLoad(*args, **kwargs)

        # Initialize shape item model
        #
        itemPrototype = QtGui.QStandardItem('')
        itemPrototype.setSizeHint(QtCore.QSize(100, 24))
        itemPrototype.setIcon(QtGui.QIcon(':data/icons/dict.svg'))

        self.shapeItemModel = QtGui.QStandardItemModel(parent=self.shapeListView)
        self.shapeItemModel.setObjectName('shapeItemModel')
        self.shapeItemModel.setColumnCount(1)
        self.shapeItemModel.setItemPrototype(itemPrototype)

        self.shapeFilterItemModel = QtCore.QSortFilterProxyModel(parent=self.shapeListView)
        self.shapeFilterItemModel.setSourceModel(self.shapeItemModel)
        self.filterLineEdit.textChanged.connect(self.shapeFilterItemModel.setFilterWildcard)

        self.shapeListView.setModel(self.shapeFilterItemModel)

        # Initialize pivot button group
        #
        self.pivotButtonGroup = QtWidgets.QButtonGroup(parent=self.pivotWidget)
        self.pivotButtonGroup.addButton(self.localRadioButton, id=0)
        self.pivotButtonGroup.addButton(self.parentRadioButton, id=1)
        self.pivotButtonGroup.addButton(self.worldRadioButton, id=2)

        # Connect start/end buttons to gradient
        #
        self.startColorChanged.connect(self.startColorButton.setColor)
        self.startColorButton.colorChanged.connect(self.gradient.setStartColor)

        self.endColorChanged.connect(self.endColorButton.setColor)
        self.endColorButton.colorChanged.connect(self.gradient.setEndColor)

        # Initialize swatch button group
        #
        self.swatchesLayout = self.swatchesWidget.layout()

        self.swatchesButtonGroup = QtWidgets.QButtonGroup(self.swatchesWidget)
        self.swatchesButtonGroup.setExclusive(False)

        numSwatches = QtWidgets.QColorDialog.customCount()
        numColors = 8  # TODO: Find a way to get QColorDialog's column quantity!
        numRows = math.ceil(float(numSwatches) / float(numColors))

        index = 0

        for column in range(numColors):

            for row in range(numRows):

                button = qcolorbutton.QColorButton('', parent=self.swatchesWidget)
                button.setObjectName(f'swatch{str(index + 1).zfill(2)}PushButton')
                button.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
                button.setMinimumHeight(24)
                button.setMaximumHeight(24)
                button.clicked.connect(self.on_swatchPushButton_clicked)
                button.doubleClicked.connect(self.on_swatchPushButton_doubleClicked)

                self.swatchesLayout.addWidget(button, row, column)
                self.swatchesButtonGroup.addButton(button, id=index)

                index += 1

        self.ensureSwatches()

        # Invalidate shape items
        #
        self.invalidateShapes()
        self.invalidateSwatches()

    def loadSettings(self, settings):
        """
        Loads the user settings.

        :type settings: QtCore.QSettings
        :rtype: None
        """

        # Call parent method
        #
        super(QShapesTab, self).loadSettings(settings)

        # Load user preferences
        #
        self.setCurveDegree(int(settings.value('tabs/shapes/curveDegree', defaultValue=1)))
        self.setCurveOffset(float(settings.value('tabs/shapes/curveOffset', defaultValue=0.0)))

        self.setPreservePosition(bool(settings.value('tabs/shapes/preservePosition', defaultValue=0)))

        self.setStartColor(settings.value('tabs/shapes/startColor', defaultValue=QtCore.Qt.black))
        self.setEndColor(settings.value('tabs/shapes/endColor', defaultValue=QtCore.Qt.white))
        self.setUseSelectedNodes(bool(settings.value('tabs/shapes/useSelectedNodes', defaultValue=0)))

    def saveSettings(self, settings):
        """
        Saves the user settings.

        :type settings: QtCore.QSettings
        :rtype: None
        """

        # Call parent method
        #
        super(QShapesTab, self).saveSettings(settings)

        # Save user preferences
        #
        settings.setValue('tabs/shapes/curveDegree', int(self.curveDegree()))
        settings.setValue('tabs/shapes/curveOffset', float(self.curveOffset()))

        settings.setValue('tabs/shapes/preservePosition', int(self.preservePosition()))

        settings.setValue('tabs/shapes/startColor', self.startColor())
        settings.setValue('tabs/shapes/endColor', self.endColor())
        settings.setValue('tabs/shapes/useSelectedNodes', int(self.useSelectedNodes()))

    def curveDegree(self):
        """
        Returns the curve degree.

        :rtype: int
        """

        return self.degreeSpinBox.value()

    def setCurveDegree(self, degree):
        """
        Updates the curve offset.

        :type degree: int
        :rtype: None
        """

        self.degreeSpinBox.setValue(degree)

    def curveOffset(self):
        """
        Returns the curve offset.

        :rtype: float
        """

        return self.offsetSpinBox.value()

    def setCurveOffset(self, offset):
        """
        Updates the curve offset.

        :type offset: float
        :rtype: None
        """

        self.offsetSpinBox.setValue(offset)

    def preservePosition(self):
        """
        Returns the `preservePosition` flag.

        :rtype: bool
        """

        return self.preservePositionCheckBox.isChecked()

    def setPreservePosition(self, preservePosition):
        """
        Updates the `preservePosition` flag.

        :type preservePosition: bool
        :rtype: None
        """

        self.preservePositionCheckBox.setChecked(preservePosition)

    def pivot(self):
        """
        Returns the current pivot.

        :rtype: PivotType
        """

        return PivotType(self.pivotButtonGroup.checkedId())

    def dimensions(self):
        """
        Returns the current dimensions.

        :rtype: Dimensions
        """

        return Dimensions(self.widthSpinBox.value(), self.heightSpinBox.value(), self.depthSpinBox.value())

    def setDimensions(self, dimensions):
        """
        Updates the current dimensions.

        :type dimensions: Dimensions
        :rtype: None
        """

        self.widthSpinBox.blockSignals(True)
        self.widthSpinBox.setValue(dimensions.width)
        self.widthSpinBox.blockSignals(False)

        self.heightSpinBox.blockSignals(True)
        self.heightSpinBox.setValue(dimensions.height)
        self.heightSpinBox.blockSignals(False)

        self.depthSpinBox.blockSignals(True)
        self.depthSpinBox.setValue(dimensions.depth)
        self.depthSpinBox.blockSignals(False)

    def useSelectedNodes(self):
        """
        Returns the `useSelectedNodes` flag.
        
        :rtype: bool
        """
        
        return self.useSelectedNodesCheckBox.isChecked()
    
    def setUseSelectedNodes(self, useSelectedNodes):
        """
        Updates the `useSelectedNodes` flag.

        :type useSelectedNodes: bool
        :rtype: None
        """
        
        self.useSelectedNodesCheckBox.setChecked(useSelectedNodes)
    
    def startColor(self):
        """
        Returns the current start color.

        :rtype: QtGui.QColor
        """

        return self.startColorButton.color()

    def setStartColor(self, startColor):
        """
        Updates the current start color.

        :type startColor: QtGui.QColor
        :rtype: None
        """

        self._startColor = QtGui.QColor(startColor)
        self.startColorChanged.emit(self._startColor)

    def endColor(self):
        """
        Returns the current end color.

        :rtype: QtGui.QColor
        """

        return self.endColorButton.color()

    def setEndColor(self, endColor):
        """
        Updates the current end color.

        :type endColor: QtGui.QColor
        :rtype: None
        """

        self._endColor = QtGui.QColor(endColor)
        self.endColorChanged.emit(self._endColor)

    def ensureSwatches(self):
        """
        Randomizes the custom swatches for first time users.

        :rtype: None
        """

        # Evaluate swatches
        #
        numSwatches = QtWidgets.QColorDialog.customCount()
        isWhite = all([QtWidgets.QColorDialog.customColor(i).lightnessF() == 1.0 for i in range(numSwatches)])

        if not isWhite:

            return

        # Randomize swatches
        #
        for i in range(numSwatches):
            
            red, green, blue = randint(0, 255), randint(0, 255), randint(0, 255)
            color = QtGui.QColor(red, green, blue)

            QtWidgets.QColorDialog.setCustomColor(i, color)

    @undo(name='Create Custom Shapes')
    def createCustomShapes(self, filename, name='', colorRGB=None, selection=None):
        """
        Creates the specified custom shape.
        Any selections supplied will have their transforms copied from.

        :type filename: str
        :type name: str
        :type colorRGB: Union[Tuple[float, float, float], None]
        :type selection: List[mpynode.MPyNode]
        :rtype: None
        """

        # Evaluate selection
        #
        if not stringutils.isNullOrEmpty(selection):

            # Iterate through selection
            #
            nodes = []

            for selectedNode in selection:

                # Evaluate selected node type
                #
                isTransform = selectedNode.hasFn(om.MFn.kTransform)
                isConstraint = selectedNode.hasFn(om.MFn.kConstraint, om.MFn.kPluginConstraintNode)

                if not isTransform or isConstraint:

                    continue

                # Create transform with shape
                #
                node = createutils.createNode('transform', name=name)
                node.copyTransform(selectedNode)
                node.addShape(filename, colorRGB=colorRGB)
                node.renameShapes()

                nodes.append(node)

            # Update active selection
            #
            self.scene.setSelection(nodes, replace=True)

            return nodes

        else:

            # Create transform with shape
            #
            node = createutils.createNode('transform', name=name)
            node.addShape(filename, colorRGB=colorRGB)
            node.renameShapes()

            return node

    @undo(name='Add Custom Shapes')
    def addCustomShapes(self, filename, nodes, colorRGB=None):
        """
        Adds the specified custom shape to the supplied nodes.

        :type filename: str
        :type nodes: List[mpynode.MPyNode]
        :type colorRGB: Union[Tuple[float, float, float], None]
        :rtype: None
        """

        # Iterate through nodes
        #
        for node in nodes:

            # Check if this is a transform node
            #
            if not node.hasFn(om.MFn.kTransform):

                continue

            # Add custom shape to node
            #
            node.addShape(filename, colorRGB=colorRGB)
            node.renameShapes()

    @undo(name='Create Star')
    def createStar(self, name='', numPoints=12, colorRGB=None, parent=None):
        """
        Adds a star to the supplied nodes.

        :type name: str
        :type numPoints: int
        :type colorRGB: Union[Tuple[float, float, float], None]
        :type parent: Union[mpynode.MPyNode, None]
        :rtype: None
        """

        # Evaluate parent
        #
        if parent is None:

            name = name if self.scene.isNameUnique(name) else ''
            parent = self.scene.createNode('transform', name=name)

        # Evaluate parent type
        #
        if parent.hasFn(om.MFn.kTransform):

            parent.addStar(10.0, numPoints=numPoints, colorRGB=colorRGB)
            self.renameShapes(parent)

            parent.select(replace=True)

        else:

            log.warning(f'Cannot add star to "{parent.typeName}" node!')

    @undo(name='Convert Edge to Curve')
    def convertEdgeToCurve(self, mesh, edgeComponent, degree=1, offset=0.0):
        """
        Converts the supplied mesh and edge component to a curve.

        :type mesh: mpynode.MPyNode
        :type edgeComponent: mpy.builtins.meshmixin.MeshEdgeComponent
        :type degree: int
        :type offset: float
        :rtype: Tuple[mpynode.MPyNode, mpynode.MPyNode]
        """

        # Convert edge component and sort elements
        #
        vertexIndices = edgeComponent.associatedVertices(ordered=True)
        success = len(vertexIndices) > 0

        if not success:

            log.warning('convertEdgeToCurve() expects 1 continuous edge path!')
            return

        # Collect vertex points
        #
        parentMatrix = mesh.parentMatrix()

        points = [(mesh.getPoint(vertexIndex) + (mesh.getVertexNormal(vertexIndex, True) * offset)) * parentMatrix for vertexIndex in vertexIndices]
        form = om.MFnNurbsCurve.kClosed if (degree == 1) else om.MFnNurbsCurve.kPeriodic

        if form == om.MFnNurbsCurve.kPeriodic:

            points.extend(tuple(map(om.MPoint, points[:degree])))  # A periodic curve requires overlapping points equal to the degree!

        elif form == om.MFnNurbsCurve.kClosed:

            points.append(om.MPoint(points[0]))  # A closed curve requires an overlapping point!

        else:

            pass

        # Create curve from points
        #
        node = self.scene.createNode('transform', name='curve1')
        curve = shapeutils.createCurveFromPoints(points, degree, form=form, parent=node.object())

        node.select(replace=True)

        return node, curve

    @undo(name='Convert Edge to Helper')
    def convertEdgeToHelper(self, mesh, edgeComponent, offset=0.0):
        """
        Converts the supplied mesh and edge component to a curve.

        :type mesh: mpynode.MPyNode
        :type edgeComponent: mpy.builtins.meshmixin.MeshEdgeComponent
        :type offset: float
        :rtype: Tuple[mpynode.MPyNode, mpynode.MPyNode]
        """

        # Convert edge component and sort elements
        #
        vertexIndices = edgeComponent.associatedVertices(ordered=True)
        success = len(vertexIndices) > 0

        if not success:

            log.warning('convertEdgeToHelper() expects 1 continuous edge path!')
            return

        # Collect vertex points
        #
        parentMatrix = mesh.parentMatrix()

        points = [(mesh.getPoint(vertexIndex) + (mesh.getVertexNormal(vertexIndex, True) * offset)) * parentMatrix for vertexIndex in vertexIndices]
        points.append(om.MPoint(points[0]))

        # Create curve from points
        #
        node = self.scene.createNode('transform', name='curve1')
        helper = node.addPointHelper('custom', size=1.0)
        helper.setAttr('controlPoints', points)

        node.select(replace=True)

        return node, helper

    @undo(name='Rename Shapes')
    def renameShapes(self, *nodes):
        """
        Renames all the shapes on the supplied nodes.

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

            # Rename shapes under transform
            #
            node.renameShapes()

    @undo(name='Remove Shapes')
    def removeShapes(self, *nodes):
        """
        Removes all the shapes from the supplied nodes.

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

            # Remove shapes from transform
            #
            log.info(f'Removing shapes from: {node}')
            node.removeShapes()

    @undo(name='Colorize Shapes')
    def colorizeShapes(self, *nodes, startColor=None, endColor=None):
        """
        Applies a gradient to the supplied nodes.

        :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
        :type startColor: QtGui.QColor
        :type endColor: QtGui.QColor
        :rtype: None
        """

        # Iterate through nodes
        #
        numNodes = len(nodes)
        factor = 1.0 / (numNodes - 1)

        for (i, node) in enumerate(nodes):

            # Calculate color
            #
            weight = float(i) * factor
            red = (startColor.redF() * (1.0 - weight)) + (endColor.redF() * weight)
            green = (startColor.greenF() * (1.0 - weight)) + (endColor.greenF() * weight)
            blue = (startColor.blueF() * (1.0 - weight)) + (endColor.blueF() * weight)

            color = (red, green, blue)

            # Recolor node
            #
            modifyutils.recolorNodes(node, color=color, colorMode=self.colorMode())

    @undo(name='Rescale Shapes')
    def rescaleShapes(self, *nodes, percentage=0.0):
        """
        Resizes the supplied shapes along the specified dimension.

        :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
        :type percentage: float
        :rtype: None
        """

        # Iterate through nodes
        #
        for node in nodes:

            # Evaluate node type
            #
            if not node.hasFn(om.MFn.kTransform):

                continue

            # Get pivot matrix
            #
            boundingBox = node.shapeBox()

            parentMatrix = node.worldMatrix()
            localMatrix = transformutils.createTranslateMatrix(boundingBox.center) * parentMatrix
            worldMatrix = om.MMatrix.kIdentity

            pivot = self.pivot()
            pivotMatrix = localMatrix if (pivot == PivotType.LOCAL) else parentMatrix if (pivot == PivotType.PARENT) else worldMatrix

            # Compose scale matrix
            #
            factor = percentage / 100.0
            width = boundingBox.width + (boundingBox.width * factor)
            height = boundingBox.height + (boundingBox.height * factor)
            depth = boundingBox.depth + (boundingBox.depth * factor)

            scaleX = (abs(width) / boundingBox.width) if (boundingBox.width != 0.0) else 1e-3
            scaleY = (abs(height) / boundingBox.height) if (boundingBox.height != 0.0) else 1e-3
            scaleZ = (abs(depth) / boundingBox.depth) if (boundingBox.depth != 0.0) else 1e-3
            scale = om.MVector(scaleX, scaleY, scaleZ)

            scaleMatrix = transformutils.createScaleMatrix(scale)

            # Iterate through shapes
            #
            for shape in node.iterShapes():

                # Evaluate shape type
                #
                isSurface = shape.hasFn(om.MFn.kSurface)
                isCurve = shape.hasFn(om.MFn.kCurve)

                if not (isSurface or isCurve):

                    log.warning(f'No scale support for {shape.apiTypeStr} shapes!')
                    continue

                # Update control points
                #
                controlPoints = [om.MPoint(point) * parentMatrix * pivotMatrix.inverse() * scaleMatrix * pivotMatrix * parentMatrix.inverse() for point in shape.controlPoints()]
                shape.setControlPoints(controlPoints)

    @undo(name='Resize Helpers')
    def resizeHelpers(self, *nodes, dimension=None, amount=0.0):
        """
        Resizes the supplied shapes along the specified dimension.

        :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
        :type dimension: Dimension
        :type amount: float
        :rtype: None
        """

        # Iterate through nodes
        #
        for node in nodes:

            # Evaluate node type
            #
            if not node.hasFn(om.MFn.kTransform):

                continue

            # Iterate through shapes
            #
            for locator in node.iterShapes(apiType=om.MFn.kLocator):

                # Check if size requires normalizing
                #
                size = locator.tryGetAttr('size', default=1.0)
                localScale = om.MVector(locator.localScale)

                if size != 1.0:

                    locator.size = 1.0
                    localScale *= size
                    locator.localScale = localScale

                # Update local-scale
                #
                localScale[dimension] = amount
                locator.localScale = localScale

        # Refresh dimension widgets
        #
        self.invalidateDimensions()

    @undo(name='Parent Shapes')
    def parentShapes(self, source, target, preservePosition=False):
        """
        Parents the shapes under the source node to the supplied target node.

        :type source: mpynode.MPyNode
        :type target: mpynode.MPyNode
        :type preservePosition: bool
        :rtype: None
        """

        # Evaluate supplied nodes
        #
        if not (source.hasFn(om.MFn.kTransform) and target.hasFn(om.MFn.kTransform)):

            return

        # Iterate through shapes
        #
        sourceMatrix = source.worldMatrix()
        targetMatrix = target.worldMatrix()
        shapes = source.shapes()

        isSurface, isCurve, isLocator = False, False, False
        controlPoints = None
        localMatrix = None

        for shape in shapes:

            # Check if position should be preserved
            #
            isSurface = shape.hasFn(om.MFn.kSurface)
            isCurve = shape.hasFn(om.MFn.kCurve)
            isLocator = shape.hasFn(om.MFn.kLocator)

            if preservePosition:

                if isSurface or isCurve:

                    controlPoints = [point * sourceMatrix for point in shape.controlPoints()]

                elif isLocator:

                    localMatrix = shape.localMatrix() * sourceMatrix

                else:

                    pass

            # Re-parent shape
            #
            shape.setParent(target)

            # Check if position requires updating
            #
            if preservePosition:

                if isSurface or isCurve:

                    controlPoints = [point * targetMatrix.inverse() for point in controlPoints]
                    shape.setControlPoints(controlPoints)

                elif isLocator:

                    localMatrix = localMatrix * targetMatrix.inverse()
                    shape.setLocalMatrix(localMatrix)

                else:

                    log.warning(f'No support for {shape.apiTypeStr} shapes!')

    @undo(name='Fit Helpers')
    def fitHelpers(self, *nodes):
        """
        Scales the supplied helpers to fit between each node.

        :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
        :rtype: None
        """

        # Iterate through nodes
        #
        numNodes = len(nodes)
        lastIndex = numNodes - 1

        for (i, node) in enumerate(nodes):

            # Iterate through shapes
            #
            for locator in node.iterShapes(apiType=om.MFn.kLocator):

                # Check if locator is compatible
                #
                if locator.typeName != 'pointHelper':

                    continue

                # Evaluate position in chain
                #
                if i == lastIndex:

                    locator.reorientAndScaleToFit()

                else:

                    locator.reorientAndScaleToFit(nodes[i + 1])

        # Refresh dimension widgets
        #
        self.invalidateDimensions()

    @undo(name='Reset Helpers')
    def resetHelpers(self, *nodes):
        """
        Resets the local matrix on the supplied helpers.

        :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
        :rtype: None
        """

        # Iterate through nodes
        #
        for node in nodes:

            # Iterate through shapes
            #
            for locator in node.iterShapes(apiType=om.MFn.kLocator):

                locator.resetLocalMatrix()

        # Refresh dimension widgets
        #
        self.invalidateDimensions()

    def invalidateShapes(self):
        """
        Repopulates the shape list widget.

        :rtype: None
        """

        directory = self.scene.getShapesDirectory()
        filenames = os.listdir(directory)

        numRows = len(filenames)
        self.shapeItemModel.setRowCount(numRows)

        for (i, filename) in enumerate(filenames):

            index = self.shapeItemModel.index(i, 0)
            self.shapeItemModel.setData(index, filename, role=QtCore.Qt.DisplayRole)

    def invalidateDimensions(self):
        """
        Refreshes the dimension spin boxes.

        :rtype: None
        """

        # Evaluate active selection
        #
        selection = [node for node in self.selection if node.hasFn(om.MFn.kTransform)]
        selectionCount = len(selection)

        if selectionCount == 0:

            self.setDimensions(Dimensions(0.0, 0.0, 0.0))
            return

        # Evaluate shapes
        #
        locators = list(chain(*[node.shapes(apiType=om.MFn.kLocator) for node in selection]))
        numLocators = len(locators)

        if numLocators == 0:

            self.setDimensions(Dimensions(0.0, 0.0, 0.0))
            return

        # Evaluate shapes under transform
        #
        weight = 1.0 / numLocators if (numLocators > 0) else 0.0
        width, height, depth = 0.0, 0.0, 0.0

        for locator in locators:

            size = locator.tryGetAttr('size', default=1.0)
            localScale = om.MVector(locator.localScale)

            width += (localScale.x * size) * weight
            height += (localScale.y * size) * weight
            depth += (localScale.z * size) * weight

        # Update bounding-box spinners
        #
        self.setDimensions(Dimensions(width, height, depth))

    def invalidateSwatches(self):
        """
        Refreshes the swatch button colours.

        :rtype: None
        """

        buttons = self.swatchesButtonGroup.buttons()

        for button in buttons:

            index = self.swatchesButtonGroup.id(button)
            color = QtWidgets.QColorDialog.customColor(index)

            button.setColor(color)

    def invalidateGradient(self):
        """
        Refreshes the gradient widgets.

        :rtype: None
        """

        # Check if selected nodes is enabled
        #
        colorMode = self.colorMode()
        useSelectedNodes = self.useSelectedNodes()

        if useSelectedNodes:

            # Evaluate active selection
            #
            selection = [node for node in self.selection if node.hasFn(om.MFn.kTransform)]
            selectionCount = len(selection)

            if selectionCount == 0:

                pass

            elif selectionCount == 1:

                node = selection[0]
                colorRGB = modifyutils.findWireframeColor(node, colorMode=colorMode)
                color = QtGui.QColor.fromRgbF(*colorRGB)
                self.startColorChanged.emit(color)

            else:

                startNode = selection[0]
                startColorRGB = modifyutils.findWireframeColor(startNode, colorMode=colorMode)
                startColor = QtGui.QColor.fromRgbF(*startColorRGB)
                self.startColorChanged.emit(startColor)

                endNode = selection[-1]
                endColorRGB = modifyutils.findWireframeColor(endNode, colorMode=colorMode)
                endColor = QtGui.QColor.fromRgbF(*endColorRGB)
                self.endColorChanged.emit(endColor)

        else:

            # Emit color change to force gradient update
            #
            self.startColorChanged.emit(self._startColor)
            self.endColorChanged.emit(self._endColor)

    def invalidate(self, reason=None):
        """
        Refreshes the user interface.

        :type reason: Union[InvalidateReason, None]
        :rtype: None
        """

        # Call parent method
        #
        super(QShapesTab, self).invalidate()

        # Invalidate user interface
        #
        self.invalidateDimensions()
        self.invalidateGradient()
    # endregion

    # region Slots
    @QtCore.Slot()
    def on_saveShapePushButton_clicked(self):
        """
        Slot method for the `saveShapePushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate active selection
        #
        if self.selectionCount == 0:

            QtWidgets.QMessageBox.warning(self, 'Save Shape', 'No controls selected to save shapes from!')
            return

        # Evaluate selected node
        #
        selectedNode = self.selection[0]

        if not selectedNode.hasFn(om.MFn.kTransform):

            QtWidgets.QMessageBox.warning(self, 'Save Shape', 'No controls selected to save shapes from!')
            return

        # Prompt user for shape name
        #
        nodeName = selectedNode.name()

        shapeName, success = QtWidgets.QInputDialog.getText(
            self,
            'Save Shape',
            'Enter a shape name:',
            text=nodeName
        )

        if success and not stringutils.isNullOrEmpty(shapeName):

            filePath = self.scene.getAbsoluteShapePath(shapeName)
            selectedNode.saveShapes(filePath)

            self.invalidateShapes()

    @QtCore.Slot()
    def on_refreshShapesPushButton_clicked(self):
        """
        Slot method for the `refreshShapesPushButton` widget's `clicked` signal.

        :rtype: None
        """

        self.invalidateShapes()

    @QtCore.Slot()
    def on_createCustomPushButton_clicked(self):
        """
        Slot method for the `createShapePushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate shape selection
        #
        rows = list({self.shapeFilterItemModel.mapToSource(index).row() for index in self.shapeListView.selectedIndexes()})
        numRows = len(rows)

        if numRows == 0:

            log.warning('No custom shape selected to create!')
            return

        # Evaluate keyboard modifiers
        #
        row = rows[0]
        filename = self.shapeItemModel.item(row).text()

        modifiers = QtWidgets.QApplication.keyboardModifiers()

        if modifiers == QtCore.Qt.ShiftModifier:

            self.addCustomShapes(filename, self.selection, colorRGB=self.currentColor())

        else:

            self.createCustomShapes(filename, name=self.currentName(), colorRGB=self.currentColor(), selection=self.selection)

    @QtCore.Slot()
    def on_createStarPushButton_clicked(self):
        """
        Slot method for the `createStarPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Prompt use for point quantity
        #
        numPoints, success = QtWidgets.QInputDialog.getInt(
            self,
            'Add Star',
            'Enter number of points',
            12,
            minValue=3,
            maxValue=100,
            step=1
        )

        if success:

            modifiers = QtWidgets.QApplication.keyboardModifiers()

            name = self.currentName()
            colorRGB = self.currentColor()
            parent = self.selectedNode if (modifiers == QtCore.Qt.ShiftModifier) else None

            self.createStar(name=name, numPoints=numPoints, colorRGB=colorRGB, parent=parent)

        else:

            log.info('Operation aborted...')

    @QtCore.Slot()
    def on_edgeToCurvePushButton_clicked(self):
        """
        Slot method for the `edgeToCurvePushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate selected node
        #
        selection = self.scene.componentSelection(apiType=om.MFn.kMesh)
        selectionCount = len(selection)

        if selectionCount == 0:

            log.warning('No meshes selected to convert!')
            return

        # Evaluate component selection
        #
        mesh, component = selection[0]

        if not component.hasFn(om.MFn.kMeshEdgeComponent):

            log.warning('No mesh edges selected to convert!')
            return

        # Evaluate selected edges
        #
        edgeComponent = mesh(component)

        if edgeComponent.numElements == 0:

            log.warning('No mesh edges selected to convert!')
            return

        self.convertEdgeToCurve(mesh, edgeComponent, degree=self.curveDegree(), offset=self.curveOffset())

    @QtCore.Slot()
    def on_edgeToHelperPushButton_clicked(self):
        """
        Slot method for the `edgeToHelperPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate selected node
        #
        selection = self.scene.componentSelection(apiType=om.MFn.kMesh)
        selectionCount = len(selection)

        if selectionCount == 0:

            log.warning('No meshes selected to convert!')
            return

        # Evaluate component selection
        #
        mesh, component = selection[0]

        if not component.hasFn(om.MFn.kMeshEdgeComponent):

            log.warning('No mesh edges selected to convert!')
            return

        # Evaluate selected edges
        #
        edgeComponent = mesh(component)

        if edgeComponent.numElements == 0:

            log.warning('No mesh edges selected to convert!')
            return

        self.convertEdgeToHelper(mesh, edgeComponent, offset=self.curveOffset())

    @QtCore.Slot()
    def on_renameShapesPushButton_clicked(self):
        """
        Slot method for the `renameShapesPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate active selection
        #
        if self.selectionCount > 0:

            self.renameShapes(*self.selection)

        else:

            log.warning(self, 'Add Helper', 'No controls selected to rename shapes on!')

    @QtCore.Slot()
    def on_removeShapesPushButton_clicked(self):
        """
        Slot method for the `clearShapesPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate active selection
        #
        if self.selectionCount > 0:

            self.removeShapes(*self.selection)

        else:

            log.warning('No controls selected to remove shapes from!')

    @QtCore.Slot()
    def on_growPushButton_clicked(self):
        """
        Slot method for the `growPushButton` widget's `clicked` signal.

        :rtype: None
        """

        if self.selectionCount > 0:

            self.rescaleShapes(*self.selection, percentage=self.scaleSpinBox.value())

    @QtCore.Slot()
    def on_shrinkPushButton_clicked(self):
        """
        Slot method for the `growPushButton` widget's `clicked` signal.

        :rtype: None
        """

        if self.selectionCount > 0:

            self.rescaleShapes(*self.selection, percentage=-self.scaleSpinBox.value())

    @QtCore.Slot()
    def on_widthSpinBox_editingFinished(self):
        """
        Slot method for the `widthSpinBox` widget's `editingFinished` signal.

        :rtype: None
        """

        sender = self.sender()

        if self.selectionCount > 0:

            self.resizeHelpers(*self.selection, dimension=Dimension.WIDTH, amount=sender.value())

        sender.clearFocus()

    @QtCore.Slot()
    def on_heightSpinBox_editingFinished(self):
        """
        Slot method for the `heightSpinBox` widget's `editingFinished` signal.

        :rtype: None
        """

        sender = self.sender()

        if self.selectionCount > 0:

            self.resizeHelpers(*self.selection, dimension=Dimension.HEIGHT, amount=sender.value())

        sender.clearFocus()

    @QtCore.Slot()
    def on_depthSpinBox_editingFinished(self):
        """
        Slot method for the `depthSpinBox` widget's `editingFinished` signal.

        :rtype: None
        """

        sender = self.sender()

        if self.selectionCount > 0:

            self.resizeHelpers(*self.selection, dimension=Dimension.DEPTH, amount=sender.value())

        sender.clearFocus()

    @QtCore.Slot()
    def on_fitPushButton_clicked(self):
        """
        Slot method for the `fitPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate active selection
        #
        if self.selectionCount > 0:

            self.fitHelpers(*self.selection)

        else:

            log.warning(f'Fit helpers expects at least 1 selected node ({self.selectionCount} selected)!')

    @QtCore.Slot()
    def on_resetPushButton_clicked(self):
        """
        Slot method for the `resetPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate active selection
        #
        if self.selectionCount > 0:

            self.resetHelpers(*self.selection)

        else:

            log.warning(f'Reset helpers expects at least 1 selected node ({self.selectionCount} selected)!')

    @QtCore.Slot()
    def on_startColorButton_clicked(self):
        """
        Slot method for the `startColourPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Prompt user for colour input
        #
        color = QtWidgets.QColorDialog.getColor(initial=self.startColor(), parent=self, title='Select Start Colour')
        success = color.isValid()

        if not success:

            return

        # Check if selected nodes require updating
        #
        colorMode = self.colorMode()
        useSelectedNodes = self.useSelectedNodes()

        if useSelectedNodes:

            # Evaluate active selection
            #
            if self.selectionCount == 0:

                return

            # Recolor first node
            #
            node = self.selection[0]
            modifyutils.recolorNodes(node, color=color, colorMode=colorMode)

            self.invalidateGradient()

        else:

            self.setStartColor(color)

    @QtCore.Slot(QtGui.QColor)
    def on_startColorButton_colorDropped(self, color):
        """
        Slot method for the `startColourPushButton` widget's `colorDropped` signal.

        :type color: QtGui.QColor
        :rtype: None
        """

        self._startColor = color

    @QtCore.Slot()
    def on_endColorButton_clicked(self):
        """
        Slot method for the `endColourPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Prompt user for colour input
        #
        color = QtWidgets.QColorDialog.getColor(initial=self.endColor(), parent=self, title='Select End Colour')
        success = color.isValid()

        if not success:

            return

        # Check if selected nodes require updating
        #
        colorMode = self.colorMode()
        useSelectedNodes = self.useSelectedNodes()

        if useSelectedNodes:

            # Evaluate active selection
            #
            if not (self.selectionCount >= 2):

                return

            # Recolor last node
            #
            node = self.selection[-1]
            modifyutils.recolorNodes(node, color=color, colorMode=colorMode)

            self.invalidateGradient()

        else:

            # Update end color
            #
            self.setEndColor(color)

    @QtCore.Slot(QtGui.QColor)
    def on_endColorButton_colorDropped(self, color):
        """
        Slot method for the `endColorButton` widget's `colorDropped` signal.

        :type color: QtGui.QColor
        :rtype: None
        """

        self._endColor = color

    @QtCore.Slot()
    def on_swatchPushButton_clicked(self):
        """
        Slot method for the `swatchPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate active selection
        #
        if self.selectionCount == 0:

            log.warning('No controls selected to copy from!')
            return

        # Copy wire-color from selection
        #
        node = self.selection[0]

        colorMode = self.colorMode()
        colorRGB = modifyutils.findWireframeColor(node, colorMode=colorMode)
        color = QtGui.QColor.fromRgbF(*colorRGB)

        sender = self.sender()
        index = self.swatchesButtonGroup.id(sender)
        QtWidgets.QColorDialog.setCustomColor(index, color)

        self.invalidateSwatches()

    @QtCore.Slot()
    def on_swatchPushButton_doubleClicked(self):
        """
        Slot method for the `swatchPushButton` widget's `doubleClicked` signal.

        :rtype: None
        """

        sender = self.sender()
        index = self.swatchesButtonGroup.id(sender)
        initialColor = QtWidgets.QColorDialog.customColor(index)

        color = QtWidgets.QColorDialog.getColor(initial=initialColor, parent=self, title='Select Swatch Colour')
        result = color.isValid()

        if result:

            QtWidgets.QColorDialog.setCustomColor(index, color)
            self.invalidateSwatches()

    @QtCore.Slot(bool)
    def on_useSelectedNodesCheckBox_toggled(self, checked):
        """
        Slot method for the `useSelectedNodesCheckBox` widget's `toggled` signal.

        :type checked: bool
        :rtype: None
        """

        self.invalidateGradient()

    @QtCore.Slot()
    def on_applyGradientPushButton_clicked(self):
        """
        Slot method for the `applyGradientPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate active selection
        #
        if self.selectionCount >= 2:

            self.colorizeShapes(*self.selection, startColor=self.startColor(), endColor=self.endColor())

        else:

            log.warning('Not enough controls selected to colorize!')

    @QtCore.Slot()
    def on_parentPushButton_clicked(self):
        """
        Slot method for the `parentPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate active selection
        #
        if not (self.selectionCount >= 2):

            log.warning(f'Re-parenting shapes expects at least 2 controls ({self.selectionCount} selected)!')
            return

        # Re-parent shapes
        #
        sources = self.selection[:-1]
        target = self.selection[-1]

        preservePosition = self.preservePosition()

        for source in sources:

            self.parentShapes(source, target, preservePosition=preservePosition)
    # endregion
