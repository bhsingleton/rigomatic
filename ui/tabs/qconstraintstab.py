from maya.api import OpenMaya as om
from Qt import QtCore, QtWidgets, QtGui
from scipy.spatial import cKDTree
from dcc.maya.libs import plugutils
from dcc.maya.decorators.undo import undo
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

        # Declare public variables
        #
        self.createGroupBox = None
        self.translateXYZWidget = None
        self.rotateXYZWidget = None
        self.scaleXYZWidget = None
        self.pointPushButton = None
        self.orientPushButton = None
        self.scalePushButton = None
        self.aimPushButton = None
        self.parentPushButton = None
        self.transformPushButton = None
        self.pointOnCurvePushButton = None
        self.pointOnPolyPushButton = None
        self.skinPushButton = None
        self.maintainOffsetCheckBox = None

        self.targetsGroupBox = None
        self.editPushButton = None
        self.constraintComboBox = None
        self.addTargetPushButton = None
        self.removeTargetPushButton = None
        self.targetTableView = None
        self.targetItemModel = None
        self.weightWidget = None
        self.weightLabel = None
        self.weightSpinBox = None

        self.offsetsGroupBox = None
        self.mutePushButton = None
        self.updateOffsetsPushButton = None
        self.resetOffsetsPushButton = None

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
    def postLoad(self, *args, **kwargs):
        """
        Called after the user interface has been loaded.

        :rtype: None
        """

        # Call parent method
        #
        super(QConstraintsTab, self).postLoad(*args, **kwargs)

        # Initialize align widgets
        #
        self.translateXYZWidget.setText('Translate')
        self.translateXYZWidget.setMatches([True, True, True])

        self.rotateXYZWidget.setText('Rotate')
        self.rotateXYZWidget.setMatches([True, True, True])

        self.scaleXYZWidget.setText('Scale')
        self.scaleXYZWidget.setMatches([False, False, False])

        # Initialize target item model
        #
        itemPrototype = QtGui.QStandardItem('')
        itemPrototype.setSizeHint(QtCore.QSize(100, 24))
        itemPrototype.setTextAlignment(QtCore.Qt.AlignCenter)

        self.targetItemModel = QtGui.QStandardItemModel(0, 2, parent=self.targetTableView)
        self.targetItemModel.setObjectName('targetItemModel')
        self.targetItemModel.setHorizontalHeaderLabels(['Target', 'Weight'])
        self.targetItemModel.setItemPrototype(itemPrototype)

        self.targetTableView.setModel(self.targetItemModel)

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

        skipTranslate = {f'skipTranslate{axis}': not match for (match, axis) in zip(self.translateXYZWidget.matches(), ('X', 'Y', 'Z'))}
        skipRotate = {f'skipRotate{axis}': not match for (match, axis) in zip(self.rotateXYZWidget.matches(), ('X', 'Y', 'Z'))}
        skipScale = {f'skipScale{axis}': not match for (match, axis) in zip(self.scaleXYZWidget.matches(), ('X', 'Y', 'Z'))}
        maintainOffset = self.maintainOffset()

        return dict(maintainOffset=maintainOffset, **skipTranslate, **skipRotate, **skipScale)

    def isMuted(self):
        """
        Evaluates if the current constraint is muted.

        :rtype: bool
        """

        return self.mutePushButton.isChecked()

    @undo(name='Add Constraint')
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

    @undo(name='Add Skin Constraint')
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
    def on_pointPushButton_clicked(self):
        """
        Slot method for the `pointPushButton` widget's `clicked` signal.

        :rtype: None
        """

        sender = self.sender()

        if self.selectionCount >= 2:

            self.addConstraint(self.selection[-1], sender.whatsThis(), self.selection[:-1], **self.constraintFlags())

        else:

            log.warning(f'Point constraints requires a minimum of 2 selected nodes ({self.selectionCount} selected)!')

    @QtCore.Slot()
    def on_orientPushButton_clicked(self):
        """
        Slot method for the `orientPushButton` widget's `clicked` signal.

        :rtype: None
        """

        sender = self.sender()

        if self.selectionCount >= 2:

            self.addConstraint(self.selection[-1], sender.whatsThis(), self.selection[:-1], **self.constraintFlags())

        else:

            log.warning(f'Orient constraints requires a minimum of 2 selected nodes ({self.selectionCount} selected)!')

    @QtCore.Slot()
    def on_scalePushButton_clicked(self):
        """
        Slot method for the `orientPushButton` widget's `clicked` signal.

        :rtype: None
        """

        sender = self.sender()

        if self.selectionCount >= 2:

            self.addConstraint(self.selection[-1], sender.whatsThis(), self.selection[:-1], **self.constraintFlags())

        else:

            log.warning(f'Scale constraints requires a minimum of 2 selected nodes ({self.selectionCount} selected)!')

    @QtCore.Slot()
    def on_parentPushButton_clicked(self):
        """
        Slot method for the `parentPushButton` widget's `clicked` signal.

        :rtype: None
        """

        sender = self.sender()

        if self.selectionCount >= 2:

            self.addConstraint(self.selection[-1], sender.whatsThis(), self.selection[:-1], **self.constraintFlags())

        else:

            log.warning(f'Parent constraints requires a minimum of 2 selected nodes ({self.selectionCount} selected)!')

    @QtCore.Slot()
    def on_transformPushButton_clicked(self):
        """
        Slot method for the `orientPushButton` widget's `clicked` signal.

        :rtype: None
        """

        sender = self.sender()

        if self.selectionCount >= 2:

            self.addConstraint(self.selection[-1], sender.whatsThis(), self.selection[:-1], **self.constraintFlags())

        else:

            log.warning(f'Transform constraints requires a minimum of 2 selected nodes ({self.selectionCount} selected)!')

    @QtCore.Slot()
    def on_aimPushButton_clicked(self):
        """
        Slot method for the `aimPushButton` widget's `clicked` signal.

        :rtype: None
        """

        sender = self.sender()

        if self.selectionCount >= 2:

            self.addConstraint(self.selection[-1], sender.whatsThis(), self.selection[:-1], **self.constraintFlags())

        else:

            log.warning(f'Aim constraints requires a minimum of 2 selected nodes ({self.selectionCount} selected)!')

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
