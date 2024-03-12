import os
import math

from maya.api import OpenMaya as om
from Qt import QtCore, QtWidgets, QtGui
from enum import IntEnum
from dcc.python import stringutils
from dcc.maya.libs import transformutils, shapeutils
from dcc.maya.json import mshapeparser
from dcc.maya.decorators.undo import undo
from . import qabstracttab
from ..widgets import qcolorbutton

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Dimensions(IntEnum):
    """
    Collections of all available dimensions.
    """

    WIDTH = 0
    HEIGHT = 1
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
        self.addShapePushButton = None
        self.addStarPushButton = None
        self.addLocatorPushButton = None
        self.addHelperPushButton = None
        self.edgeToCurvePushButton = None
        self.edgeToHelperPushButton = None
        self.degreeSpinBox = None
        self.offsetSpinBox = None
        self.renameShapesPushButton = None
        self.removeShapesPushButton = None

        self.transformGroupBox = None
        self.scaleWidget = None
        self.scaleLabel = None
        self.scaleSpinBox = None
        self.growPushButton = None
        self.shrinkPushButton = None
        self.widthWidget = None
        self.widthLabel = None
        self.widthSpinBox = None
        self.heightWidget = None
        self.heightLabel = None
        self.heightSpinBox = None
        self.depthWidget = None
        self.depthLabel = None
        self.depthSpinBox = None

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

    @undo(name='Add Custom Shape')
    def addCustomShape(self, filename, *nodes):
        """
        Adds the specified custom shape to the supplied nodes.

        :type filename: str
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

            # Add custom shape to transform
            #
            node.addShape(filename)

    @undo(name='Add Star')
    def addStar(self, *nodes, numPoints=12):
        """
        Adds a star to the supplied nodes.

        :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
        :type numPoints: int
        :rtype: None
        """

        # Iterate through nodes
        #
        for node in nodes:

            # Check if this is a transform node
            #
            if not node.hasFn(om.MFn.kTransform):

                continue

            # Add star to transform
            #
            node.addStar(numPoints=numPoints)

    @undo(name='Add Locator')
    def addLocator(self, *nodes):
        """
        Adds a locator to the supplied nodes.

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

            # Add locator to transform
            #
            node.addLocator()

    @undo(name='Add Point Helper')
    def addHelper(self, *nodes):
        """
        Adds a point helper to the supplied nodes.

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

            # Add point helper to transform
            #
            node.addPointHelper()

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
        periodic = degree > 1

        if periodic:

            points.extend([om.MPoint(x) for x in points[:degree]])  # A periodic curve requires N overlapping CVs!

        else:

            points.append(om.MPoint(points[0]))

        # Create curve from points
        #
        node = self.scene.createNode('transform', name='curve1')
        curve = shapeutils.createCurveFromPoints(points, degree, periodic=periodic, parent=node.object())

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
        helper = node.addPointHelper('custom')
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

            # Evaluate number of shapes
            #
            nodeName = node.name()

            shapes = node.shapes()
            numShapes = len(shapes)

            if numShapes == 0:

                continue

            elif numShapes == 1:

                shape = shapes[0]
                originalName = shape.name()
                newName = f'{nodeName}Shape'

                log.info(f'Renaming {originalName} > {newName}')
                shape.setName(newName)

            else:

                for (i, shape) in enumerate(shapes, start=1):

                    originalName = shape.name()
                    newName = f'{nodeName}Shape{i}'

                    log.info(f'Renaming {originalName} > {newName}')
                    shape.setName(newName)

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
    def colorizeShapes(self, startColor, endColor, *nodes):
        """
        Applies a gradient to the supplied nodes.

        :type startColor: QtGui.QColor
        :type endColor: QtGui.QColor
        :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
        :rtype: None
        """

        # Iterate through nodes
        #
        numNodes = len(nodes)
        factor = 1.0 / (numNodes - 1)

        for (i, node) in enumerate(nodes):

            # Check if this is a transform node
            #
            if not node.hasFn(om.MFn.kTransform):

                continue

            # Iterate through shapes
            #
            weight = float(i) * factor

            red = (startColor.redF() * (1.0 - weight)) + (endColor.redF() * weight)
            green = (startColor.greenF() * (1.0 - weight)) + (endColor.greenF() * weight)
            blue = (startColor.blueF() * (1.0 - weight)) + (endColor.blueF() * weight)

            for shape in node.iterShapes():

                shape.useObjectColor = 2
                shape.wireColorRGB = (red, green, blue)

    @undo(name='Rescale Shapes')
    def rescaleShapes(self, node, dimensions):
        """
        Resizes the supplied shapes along the specified dimension.

        :type node: mpynode.MPyNode
        :type dimensions: om.MBoundingBox
        :rtype: None
        """

        # Check if this is a transform node
        #
        if not node.hasFn(om.MFn.kTransform):

            return

        # Compose scale matrix
        #
        boundingBox = node.shapeBox()
        scaleX = (dimensions.width / boundingBox.width) if (boundingBox.width != 0.0) else 1e-3
        scaleY = (dimensions.height / boundingBox.height) if (boundingBox.height != 0.0) else 1e-3
        scaleZ = (dimensions.depth / boundingBox.depth) if (boundingBox.depth != 0.0) else 1e-3
        scale = om.MVector(scaleX, scaleY, scaleZ)

        scaleMatrix = transformutils.createScaleMatrix(scale)
        pivotMatrix = transformutils.createTranslateMatrix(boundingBox.center)

        matrix = scaleMatrix * pivotMatrix

        # Iterate through shapes
        #
        isSurface, isCurve, isLocator = False, False, False
        controlPoints = None
        localMatrix = None

        for shape in node.iterShapes():

            isSurface = shape.hasFn(om.MFn.kSurface)
            isCurve = shape.hasFn(om.MFn.kCurve)
            isLocator = shape.hasFn(om.MFn.kLocator)

            if isSurface or isCurve:

                controlPoints = [point * pivotMatrix.inverse() * matrix for point in shape.controlPoints()]
                shape.setControlPoints(controlPoints)

            elif isLocator:

                localMatrix = shape.localMatrix() * pivotMatrix.inverse() * matrix
                shape.setLocalMatrix(localMatrix)

            else:

                log.warning(f'No support for {shape.apiTypeStr} shapes!')
                continue

    @undo(name='Resize Shapes')
    def resizeShapes(self, node, dimension, value):
        """
        Resizes the supplied shapes along the specified dimension.

        :type node: mpynode.MPyNode
        :type dimension: Dimensions
        :type value: float
        :rtype: None
        """

        # Check if this is a transform node
        #
        if not node.hasFn(om.MFn.kTransform):

            return

        # Compose scale matrix
        #
        boundingBox = node.shapeBox()
        currentValue = getattr(boundingBox, dimension.name.lower())

        scale = om.MVector(1.0, 1.0, 1.0)
        scale[dimension] = (value / currentValue) if currentValue > 0.0 else 1e-3

        scaleMatrix = transformutils.createScaleMatrix(scale)
        pivotMatrix = transformutils.createTranslateMatrix(boundingBox.center)

        matrix = scaleMatrix * pivotMatrix

        # Iterate through shapes
        #
        isSurface, isCurve, isLocator = False, False, False
        controlPoints = None
        localMatrix = None

        for shape in node.iterShapes():

            isSurface = shape.hasFn(om.MFn.kSurface)
            isCurve = shape.hasFn(om.MFn.kCurve)
            isLocator = shape.hasFn(om.MFn.kLocator)

            if isSurface or isCurve:

                controlPoints = [point * pivotMatrix.inverse() * matrix for point in shape.controlPoints()]
                shape.setControlPoints(controlPoints)

            elif isLocator:

                localMatrix = shape.localMatrix() * pivotMatrix.inverse() * matrix
                shape.setLocalMatrix(localMatrix)

            else:

                log.warning(f'No support for {shape.apiTypeStr} shapes!')
                continue

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

        isSurface, isCurve, isLocator = False, False, False
        controlPoints = None
        localMatrix = None

        for shape in source.iterShapes():

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

    def invalidateBoundingBox(self):
        """
        Refreshes the bounding-box spin boxes.

        :rtype: None
        """

        # Evaluate active selection
        #
        if self.selectionCount == 0:

            return

        # Update spinners
        #
        if self.selectedNode.hasFn(om.MFn.kTransform):

            boundingBox = self.selectedNode.shapeBox()

            self.widthSpinBox.blockSignals(True)
            self.widthSpinBox.setValue(boundingBox.width)
            self.widthSpinBox.blockSignals(False)

            self.heightSpinBox.blockSignals(True)
            self.heightSpinBox.setValue(boundingBox.height)
            self.heightSpinBox.blockSignals(False)

            self.depthSpinBox.blockSignals(True)
            self.depthSpinBox.setValue(boundingBox.depth)
            self.depthSpinBox.blockSignals(False)

        else:

            self.widthSpinBox.blockSignals(True)
            self.widthSpinBox.setValue(0.0)
            self.widthSpinBox.blockSignals(False)

            self.heightSpinBox.blockSignals(True)
            self.heightSpinBox.setValue(0.0)
            self.heightSpinBox.blockSignals(False)

            self.depthSpinBox.blockSignals(True)
            self.depthSpinBox.setValue(0.0)
            self.depthSpinBox.blockSignals(False)

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
                shapes = node.shapes()
                numShapes = len(shapes)

                if numShapes > 0:

                    color = QtGui.QColor.fromRgbF(*shapes[0].wireColorRGB)
                    self.startColorChanged.emit(color)

            else:

                startNode = selection[0]
                shapes = startNode.shapes()
                numShapes = len(shapes)

                if numShapes > 0:

                    color = QtGui.QColor.fromRgbF(*shapes[0].wireColorRGB)
                    self.startColorChanged.emit(color)

                endNode = selection[-1]
                shapes = endNode.shapes()
                numShapes = len(shapes)

                if numShapes > 0:

                    color = QtGui.QColor.fromRgbF(*shapes[0].wireColorRGB)
                    self.endColorChanged.emit(color)

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
        self.invalidateBoundingBox()
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
            mshapeparser.createShapeTemplate(selectedNode.object(), filePath)

            self.invalidateShapes()

    @QtCore.Slot()
    def on_refreshShapesPushButton_clicked(self):
        """
        Slot method for the `refreshShapesPushButton` widget's `clicked` signal.

        :rtype: None
        """

        self.invalidateShapes()

    @QtCore.Slot()
    def on_addShapePushButton_clicked(self):
        """
        Slot method for the `addShapePushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate shape selection
        #
        rows = list({self.shapeFilterItemModel.mapToSource(index).row() for index in self.shapeListView.selectedIndexes()})
        numRows = len(rows)

        if numRows == 0:

            log.warning('No custom shape selected to add to active selection!')
            return

        # Evaluate active selection
        #
        if self.selectionCount == 0:

            log.warning('No nodes selected to add custom shape to!')
            return

        # Add custom shape
        #
        row = rows[0]
        filename = self.shapeItemModel.item(row).text()

        self.addCustomShape(filename, *self.selection)

    @QtCore.Slot()
    def on_addStarPushButton_clicked(self):
        """
        Slot method for the `addStarPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate active selection
        #
        if self.selectionCount == 0:

            log.warning('No controls selected to add star to!')
            return

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

            self.addStar(*self.selection, numPoints=numPoints)

    @QtCore.Slot()
    def on_addLocatorPushButton_clicked(self):
        """
        Slot method for the `addLocatorPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate active selection
        #
        if self.selectionCount > 0:

            self.addLocator(*self.selection)

        else:

            log.warning(self, 'Add Locator', 'No controls selected to add locator to!')

    @QtCore.Slot()
    def on_addHelperPushButton_clicked(self):
        """
        Slot method for the `addHelperPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate active selection
        #
        if self.selectionCount > 0:

            self.addHelper(*self.selection)

        else:

            log.warning(self, 'Add Helper', 'No controls selected to add helper to!')

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

        # Evaluate current selection
        #
        if self.selectedNode is None:

            return

        # Evaluate selected node
        #
        if self.selectedNode.hasFn(om.MFn.kTransform):

            boundingBox = self.selectedNode.shapeBox()
            scale = self.scaleSpinBox.value() / 100.0
            width = boundingBox.width + (boundingBox.width * scale)
            height = boundingBox.height + (boundingBox.height * scale)
            depth = boundingBox.depth + (boundingBox.depth * scale)

            minPoint = om.MPoint(-width * 0.5, -height * 0.5, -depth * 0.5)
            maxPoint = om.MPoint(width * 0.5, height * 0.5, depth * 0.5)
            scaledBox = om.MBoundingBox(minPoint, maxPoint)

            self.rescaleShapes(self.selectedNode, scaledBox)
            self.invalidateBoundingBox()

    @QtCore.Slot()
    def on_shrinkPushButton_clicked(self):
        """
        Slot method for the `growPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate current selection
        #
        if self.selectedNode is None:

            return

        # Evaluate selected node
        #
        if self.selectedNode.hasFn(om.MFn.kTransform):

            boundingBox = self.selectedNode.shapeBox()
            scale = self.scaleSpinBox.value() / 100.0
            width = boundingBox.width - (boundingBox.width * scale)
            height = boundingBox.height - (boundingBox.height * scale)
            depth = boundingBox.depth - (boundingBox.depth * scale)

            minPoint = om.MPoint(-width * 0.5, -height * 0.5, -depth * 0.5)
            maxPoint = om.MPoint(width * 0.5, height * 0.5, depth * 0.5)
            scaledBox = om.MBoundingBox(minPoint, maxPoint)

            self.rescaleShapes(self.selectedNode, scaledBox)
            self.invalidateBoundingBox()

    @QtCore.Slot(float)
    def on_widthSpinBox_valueChanged(self, value):
        """
        Slot method for the `widthSpinBox` widget's `valueChanged` signal.

        :type value: float
        :rtype: None
        """

        if self.selectionCount > 0:

            self.resizeShapes(self.selection[0], Dimensions.WIDTH, value)

    @QtCore.Slot(float)
    def on_heightSpinBox_valueChanged(self, value):
        """
        Slot method for the `heightSpinBox` widget's `valueChanged` signal.

        :type value: float
        :rtype: None
        """

        if self.selectionCount > 0:

            self.resizeShapes(self.selection[0], Dimensions.HEIGHT, value)

    @QtCore.Slot(float)
    def on_depthSpinBox_valueChanged(self, value):
        """
        Slot method for the `depthSpinBox` widget's `valueChanged` signal.

        :type value: float
        :rtype: None
        """

        if self.selectionCount > 0:

            self.resizeShapes(self.selection[0], Dimensions.DEPTH, value)

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
        useSelectedNodes = self.useSelectedNodes()

        if useSelectedNodes:

            # Evaluate active selection
            #
            if self.selectionCount == 0:

                return

            # Evaluate shapes
            #
            node = self.selection[0]

            for shape in node.iterShapes():

                shape.useObjectColor = 2
                shape.wireColorRGB = (color.redF(), color.greenF(), color.blueF())

            self.invalidateGradient()

        else:

            self.setStartColor(color)

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
        useSelectedNodes = self.useSelectedNodes()

        if useSelectedNodes:

            # Evaluate active selection
            #
            if not (self.selectionCount >= 2):

                return

            # Evaluate shapes
            #
            node = self.selection[-1]

            for shape in node.iterShapes():

                shape.useObjectColor = 2
                shape.wireColorRGB = (color.redF(), color.greenF(), color.blueF())

            self.invalidateGradient()

        else:

            # Update end color
            #
            self.setEndColor(color)

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

        # Check if selected node has any shapes
        #
        node = self.selection[0]
        shapes = node.shapes()
        numShapes = len(shapes)

        if numShapes == 0:

            log.warning('Selected control has no shapes to copy from!')
            return

        # Copy shape wire-color
        #
        sender = self.sender()
        index = self.swatchesButtonGroup.id(sender)

        shape = shapes[0]
        wireColor = QtGui.QColor.fromRgbF(*shape.wireColorRGB)

        QtWidgets.QColorDialog.setCustomColor(index, wireColor)
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

            self.colorizeShapes(self.startColor(), self.endColor(), *self.selection)

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
        if self.selectionCount == 2:

            self.parentShapes(self.selection[0], self.selection[1], preservePosition=self.preservePosition())

        else:

            log.warning(f'Re-parenting shapes expects 2 controls ({self.selectionCount} selected)!')
    # endregion
