import os
import math

from maya.api import OpenMaya as om
from Qt import QtCore, QtWidgets, QtGui
from itertools import chain
from collections import namedtuple
from enum import IntEnum
from random import randint
from dcc.python import stringutils
from dcc.ui import qdivider
from dcc.maya.libs import transformutils, shapeutils
from dcc.maya.decorators import undo
from . import qabstracttab
from ..widgets import qcolorbutton, qgradient
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

    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        # Call parent method
        #
        super(QShapesTab, self).__setup_ui__(*args, **kwargs)

        # Initialize central layout
        #
        centralLayout = QtWidgets.QVBoxLayout()
        centralLayout.setObjectName('centralLayout')

        self.setLayout(centralLayout)

        # Initialize create group-box
        #
        self.createLayout = QtWidgets.QGridLayout()
        self.createLayout.setObjectName('createLayout')

        self.createGroupBox = QtWidgets.QGroupBox('')
        self.createGroupBox.setObjectName('createGroupBox')
        self.createGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.createGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.createGroupBox.setLayout(self.createLayout)

        self.shapeListView = QtWidgets.QListView()
        self.shapeListView.setObjectName('shapeListView')
        self.shapeListView.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.shapeListView.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.shapeListView.setStyleSheet('QListView::item { height: 24px; }')
        self.shapeListView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.shapeListView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.shapeListView.setDragEnabled(False)
        self.shapeListView.setDragDropOverwriteMode(False)
        self.shapeListView.setDragDropMode(QtWidgets.QAbstractItemView.NoDragDrop)
        self.shapeListView.setDefaultDropAction(QtCore.Qt.IgnoreAction)
        self.shapeListView.setAlternatingRowColors(True)
        self.shapeListView.setUniformItemSizes(True)
        self.shapeListView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.shapeListView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        self.itemPrototype = QtGui.QStandardItem('')
        self.itemPrototype.setSizeHint(QtCore.QSize(100, 24))
        self.itemPrototype.setIcon(QtGui.QIcon(':data/icons/dict.svg'))

        self.shapeItemModel = QtGui.QStandardItemModel(parent=self.shapeListView)
        self.shapeItemModel.setObjectName('shapeItemModel')
        self.shapeItemModel.setColumnCount(1)
        self.shapeItemModel.setItemPrototype(self.itemPrototype)

        self.shapeFilterItemModel = QtCore.QSortFilterProxyModel(parent=self.shapeListView)
        self.shapeFilterItemModel.setSourceModel(self.shapeItemModel)

        self.shapeListView.setModel(self.shapeFilterItemModel)

        self.filterLineEdit = QtWidgets.QLineEdit()
        self.filterLineEdit.setObjectName('filterLineEdit')
        self.filterLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.filterLineEdit.setFixedHeight(24)
        self.filterLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.filterLineEdit.setPlaceholderText('Filter Custom Shapes...')
        self.filterLineEdit.textChanged.connect(self.shapeFilterItemModel.setFilterWildcard)

        self.saveShapePushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/save_file.svg'), '')
        self.saveShapePushButton.setObjectName('saveShapePushButton')
        self.saveShapePushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.saveShapePushButton.setFixedSize(QtCore.QSize(24, 24))
        self.saveShapePushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.saveShapePushButton.clicked.connect(self.on_saveShapePushButton_clicked)

        self.refreshShapesPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/refresh.svg'), '')
        self.refreshShapesPushButton.setObjectName('refreshShapesPushButton')
        self.refreshShapesPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.refreshShapesPushButton.setFixedSize(QtCore.QSize(24, 24))
        self.refreshShapesPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.refreshShapesPushButton.clicked.connect(self.on_refreshShapesPushButton_clicked)

        self.filterLayout = QtWidgets.QHBoxLayout()
        self.filterLayout.setObjectName('filterLayout')
        self.filterLayout.setContentsMargins(0, 0, 0, 0)
        self.filterLayout.addWidget(self.filterLineEdit)
        self.filterLayout.addWidget(self.saveShapePushButton)
        self.filterLayout.addWidget(self.refreshShapesPushButton)

        self.createCustomPushButton = QtWidgets.QPushButton('Create Custom')
        self.createCustomPushButton.setObjectName('createCustomPushButton')
        self.createCustomPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.createCustomPushButton.setFixedHeight(24)
        self.createCustomPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.createCustomPushButton.clicked.connect(self.on_createCustomPushButton_clicked)

        self.createStarPushButton = QtWidgets.QPushButton('Create Star')
        self.createStarPushButton.setObjectName('createStarPushButton')
        self.createStarPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.createStarPushButton.setFixedHeight(24)
        self.createStarPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.createStarPushButton.clicked.connect(self.on_createStarPushButton_clicked)

        self.edgeToCurvePushButton = QtWidgets.QPushButton('Edge to Curve')
        self.edgeToCurvePushButton.setObjectName('edgeToCurvePushButton')
        self.edgeToCurvePushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.edgeToCurvePushButton.setFixedHeight(24)
        self.edgeToCurvePushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.edgeToCurvePushButton.clicked.connect(self.on_edgeToCurvePushButton_clicked)

        self.degreeSpinBox = QtWidgets.QSpinBox()
        self.degreeSpinBox.setObjectName('degreeSpinBox')
        self.degreeSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.degreeSpinBox.setFixedHeight(24)
        self.degreeSpinBox.setAlignment(QtCore.Qt.AlignCenter)
        self.degreeSpinBox.setPrefix('Degree: ')
        self.degreeSpinBox.setMinimum(1)
        self.degreeSpinBox.setMaximum(7)
        self.degreeSpinBox.setValue(1)

        self.edgeToHelperPushButton = QtWidgets.QPushButton('Edge to Helper')
        self.edgeToHelperPushButton.setObjectName('edgeToHelperPushButton')
        self.edgeToHelperPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.edgeToHelperPushButton.setFixedHeight(24)
        self.edgeToHelperPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.edgeToHelperPushButton.clicked.connect(self.on_edgeToHelperPushButton_clicked)

        self.offsetSpinBox = QtWidgets.QDoubleSpinBox()
        self.offsetSpinBox.setObjectName('offsetSpinBox')
        self.offsetSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.offsetSpinBox.setFixedHeight(24)
        self.offsetSpinBox.setAlignment(QtCore.Qt.AlignCenter)
        self.offsetSpinBox.setPrefix('Offset: ')
        self.offsetSpinBox.setDecimals(2)
        self.offsetSpinBox.setMinimum(0.0)
        self.offsetSpinBox.setMaximum(100.0)
        self.offsetSpinBox.setSingleStep(1.0)
        self.offsetSpinBox.setValue(0.0)

        self.renameShapesPushButton = QtWidgets.QPushButton('Rename Shapes')
        self.renameShapesPushButton.setObjectName('renameShapesPushButton')
        self.renameShapesPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.renameShapesPushButton.setFixedHeight(24)
        self.renameShapesPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.renameShapesPushButton.clicked.connect(self.on_renameShapesPushButton_clicked)

        self.mirrorShapesPushButton = QtWidgets.QPushButton('Mirror Shapes')
        self.mirrorShapesPushButton.setObjectName('mirrorShapesPushButton')
        self.mirrorShapesPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.mirrorShapesPushButton.setFixedHeight(24)
        self.mirrorShapesPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.mirrorShapesPushButton.clicked.connect(self.on_mirrorShapesPushButton_clicked)

        self.reparentShapesPushButton = QtWidgets.QPushButton('Reparent Shapes')
        self.reparentShapesPushButton.setObjectName('reparentShapesPushButton')
        self.reparentShapesPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.reparentShapesPushButton.setFixedHeight(24)
        self.reparentShapesPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.reparentShapesPushButton.clicked.connect(self.on_reparentShapesPushButton_clicked)

        self.preservePositionCheckBox = QtWidgets.QCheckBox('Preserve Shape Position')
        self.preservePositionCheckBox.setObjectName('preservePositionCheckBox')
        self.preservePositionCheckBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.preservePositionCheckBox.setFixedHeight(24)
        self.preservePositionCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)

        self.removeShapesPushButton = QtWidgets.QPushButton('Remove Shapes')
        self.removeShapesPushButton.setObjectName('removeShapesPushButton')
        self.removeShapesPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.removeShapesPushButton.setFixedHeight(24)
        self.removeShapesPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.removeShapesPushButton.clicked.connect(self.on_removeShapesPushButton_clicked)

        self.createLayout.addLayout(self.filterLayout, 0, 0, 1, 2)
        self.createLayout.addWidget(self.shapeListView, 1, 0, 1, 2)
        self.createLayout.addWidget(self.createCustomPushButton, 2, 0)
        self.createLayout.addWidget(self.createStarPushButton, 2, 1)
        self.createLayout.addWidget(qdivider.QDivider(QtCore.Qt.Horizontal), 3, 0, 1, 2)
        self.createLayout.addWidget(self.edgeToCurvePushButton, 4, 0)
        self.createLayout.addWidget(self.degreeSpinBox, 4, 1)
        self.createLayout.addWidget(self.edgeToHelperPushButton, 5, 0)
        self.createLayout.addWidget(self.offsetSpinBox, 5, 1)
        self.createLayout.addWidget(qdivider.QDivider(QtCore.Qt.Horizontal), 6, 0, 1, 2)
        self.createLayout.addWidget(self.renameShapesPushButton, 7, 0)
        self.createLayout.addWidget(self.mirrorShapesPushButton, 7, 1)
        self.createLayout.addWidget(self.reparentShapesPushButton, 8, 0)
        self.createLayout.addWidget(self.preservePositionCheckBox, 8, 1)
        self.createLayout.addWidget(qdivider.QDivider(QtCore.Qt.Horizontal), 9, 0, 1, 2)
        self.createLayout.addWidget(self.removeShapesPushButton, 10, 0, 1, 2)

        centralLayout.addWidget(self.createGroupBox)

        # Initialize swatches widget
        #
        self.swatchesLayout = QtWidgets.QGridLayout()
        self.swatchesLayout.setObjectName('swatchesLayout')
        self.swatchesLayout.setContentsMargins(0, 0, 0, 0)

        self.swatchesWidget = QtWidgets.QWidget()
        self.swatchesWidget.setObjectName('swatchesWidget')
        self.swatchesWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.swatchesWidget.setLayout(self.swatchesLayout)

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

        # Initialize colorize group-box
        #
        self.colorizeLayout = QtWidgets.QVBoxLayout()
        self.colorizeLayout.setObjectName('colorizeLayout')

        self.colorizeGroupBox = QtWidgets.QGroupBox('Recolor:')
        self.colorizeGroupBox.setObjectName('colorizeGroupBox')
        self.colorizeGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.colorizeGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.colorizeGroupBox.setLayout(self.colorizeLayout)

        self.gradient = qgradient.QGradient()
        self.gradient.setObjectName('gradient')
        self.gradient.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.gradient.setFixedHeight(24)
        self.gradient.setAutoFillBackground(True)

        self.startColorButton = qcolorbutton.QColorButton('Start')
        self.startColorButton.setObjectName('startColorButton')
        self.startColorButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.startColorButton.setFixedSize(QtCore.QSize(48, 24))
        self.startColorButton.setAcceptDrops(True)
        self.startColorButton.setAutoFillBackground(True)
        self.startColorButton.clicked.connect(self.on_startColorButton_clicked)
        self.startColorButton.colorDropped.connect(self.on_startColorButton_colorDropped)
        self.startColorButton.colorChanged.connect(self.gradient.setStartColor)

        self.endColorButton = qcolorbutton.QColorButton('End')
        self.endColorButton.setObjectName('endColorButton')
        self.endColorButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.endColorButton.setFixedSize(QtCore.QSize(48, 24))
        self.endColorButton.setAcceptDrops(True)
        self.endColorButton.setAutoFillBackground(True)
        self.endColorButton.clicked.connect(self.on_endColorButton_clicked)
        self.endColorButton.colorDropped.connect(self.on_endColorButton_colorDropped)
        self.endColorButton.colorChanged.connect(self.gradient.setEndColor)

        self.startColorChanged.connect(self.startColorButton.setColor)
        self.endColorChanged.connect(self.endColorButton.setColor)

        self.gradientLayout = QtWidgets.QHBoxLayout()
        self.gradientLayout.setObjectName('gradientLayout')
        self.gradientLayout.setContentsMargins(0, 0, 0, 0)
        self.gradientLayout.setSpacing(0)
        self.gradientLayout.addWidget(self.startColorButton)
        self.gradientLayout.addWidget(self.gradient)
        self.gradientLayout.addWidget(self.endColorButton)

        self.useSelectedNodesCheckBox = QtWidgets.QCheckBox('Use Selected Nodes')
        self.useSelectedNodesCheckBox.setObjectName('useSelectedNodesCheckBox')
        self.useSelectedNodesCheckBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))
        self.useSelectedNodesCheckBox.setFixedHeight(24)
        self.useSelectedNodesCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.useSelectedNodesCheckBox.toggled.connect(self.on_useSelectedNodesCheckBox_toggled)

        self.applyGradientPushButton = QtWidgets.QPushButton('Apply')
        self.applyGradientPushButton.setObjectName('applyGradientPushButton')
        self.applyGradientPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.applyGradientPushButton.setFixedHeight(24)
        self.applyGradientPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.applyGradientPushButton.clicked.connect(self.on_applyGradientPushButton_clicked)

        self.colorizeButtonsLayout = QtWidgets.QHBoxLayout()
        self.colorizeButtonsLayout.setObjectName('')
        self.colorizeButtonsLayout.setContentsMargins(0, 0, 0, 0)
        self.colorizeButtonsLayout.addWidget(self.useSelectedNodesCheckBox)
        self.colorizeButtonsLayout.addWidget(self.applyGradientPushButton)

        self.colorizeLayout.addLayout(self.gradientLayout)
        self.colorizeLayout.addWidget(self.swatchesWidget)
        self.colorizeLayout.addLayout(self.colorizeButtonsLayout)

        centralLayout.addWidget(self.colorizeGroupBox)

        # Initialize scale group-box
        #
        self.rescaleLayout = QtWidgets.QVBoxLayout()
        self.rescaleLayout.setObjectName('rescaleLayout')

        self.rescaleGroupBox = QtWidgets.QGroupBox('Rescale:')
        self.rescaleGroupBox.setObjectName('rescaleGroupBox')
        self.rescaleGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.rescaleGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.rescaleGroupBox.setLayout(self.rescaleLayout)

        self.pivotLabel = QtWidgets.QLabel('Pivot:')
        self.pivotLabel.setObjectName('pivotLabel')
        self.pivotLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.pivotLabel.setFixedSize(QtCore.QSize(40, 24))
        self.pivotLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.pivotLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.localRadioButton = QtWidgets.QRadioButton('Local')
        self.localRadioButton.setObjectName('localRadioButton')
        self.localRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.localRadioButton.setFixedHeight(24)
        self.localRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.localRadioButton.setChecked(True)

        self.parentRadioButton = QtWidgets.QRadioButton('Parent')
        self.parentRadioButton.setObjectName('parentRadioButton')
        self.parentRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.parentRadioButton.setFixedHeight(24)
        self.parentRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.worldRadioButton = QtWidgets.QRadioButton('World')
        self.worldRadioButton.setObjectName('worldRadioButton')
        self.worldRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.worldRadioButton.setFixedHeight(24)
        self.worldRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.pivotButtonGroup = QtWidgets.QButtonGroup(parent=self.rescaleGroupBox)
        self.pivotButtonGroup.setObjectName('pivotButtonGroup')
        self.pivotButtonGroup.setExclusive(True)
        self.pivotButtonGroup.addButton(self.localRadioButton, id=0)
        self.pivotButtonGroup.addButton(self.parentRadioButton, id=1)
        self.pivotButtonGroup.addButton(self.worldRadioButton, id=2)
        
        self.pivotLayout = QtWidgets.QHBoxLayout()
        self.pivotLayout.setObjectName('pivotLayout')
        self.pivotLayout.setContentsMargins(0, 0, 0, 0)
        self.pivotLayout.addWidget(self.pivotLabel)
        self.pivotLayout.addWidget(self.localRadioButton, alignment=QtCore.Qt.AlignCenter)
        self.pivotLayout.addWidget(self.parentRadioButton, alignment=QtCore.Qt.AlignCenter)
        self.pivotLayout.addWidget(self.worldRadioButton, alignment=QtCore.Qt.AlignCenter)

        self.scaleLabel = QtWidgets.QLabel('Scale:')
        self.scaleLabel.setObjectName('scaleLabel')
        self.scaleLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.scaleLabel.setFixedSize(QtCore.QSize(40, 24))
        self.scaleLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.scaleLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.scaleSpinBox = QtWidgets.QDoubleSpinBox()
        self.scaleSpinBox.setObjectName('scaleSpinBox')
        self.scaleSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.scaleSpinBox.setFixedHeight(24)
        self.scaleSpinBox.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.scaleSpinBox.setAlignment(QtCore.Qt.AlignCenter)
        self.scaleSpinBox.setSuffix('%')
        self.scaleSpinBox.setDecimals(2)
        self.scaleSpinBox.setMinimum(0.0)
        self.scaleSpinBox.setMaximum(100.0)
        self.scaleSpinBox.setSingleStep(0.25)
        self.scaleSpinBox.setValue(50.0)

        self.growPushButton = QtWidgets.QPushButton('+')
        self.growPushButton.setObjectName('growPushButton')
        self.growPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.growPushButton.setFixedSize(QtCore.QSize(24, 24))
        self.growPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.growPushButton.clicked.connect(self.on_growPushButton_clicked)

        self.shrinkPushButton = QtWidgets.QPushButton('-')
        self.shrinkPushButton.setObjectName('shrinkPushButton')
        self.shrinkPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.shrinkPushButton.setFixedSize(QtCore.QSize(24, 24))
        self.shrinkPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.shrinkPushButton.clicked.connect(self.on_shrinkPushButton_clicked)

        self.scaleButtonsLayout = QtWidgets.QHBoxLayout()
        self.scaleButtonsLayout.setObjectName('scaleButtonsLayout')
        self.scaleButtonsLayout.setContentsMargins(0, 0, 0, 0)
        self.scaleButtonsLayout.setSpacing(1)
        self.scaleButtonsLayout.addWidget(self.growPushButton)
        self.scaleButtonsLayout.addWidget(self.shrinkPushButton)

        self.scaleLayout = QtWidgets.QHBoxLayout()
        self.scaleLayout.setObjectName('scaleLayout')
        self.scaleLayout.setContentsMargins(0, 0, 0, 0)
        self.scaleLayout.addWidget(self.scaleLabel)
        self.scaleLayout.addWidget(self.scaleSpinBox)
        self.scaleLayout.addLayout(self.scaleButtonsLayout)

        self.rescaleLayout.addLayout(self.pivotLayout)
        self.rescaleLayout.addLayout(self.scaleLayout)

        centralLayout.addWidget(self.rescaleGroupBox)

        # Initialize bounding-box group-box
        #
        self.resizeLayout = QtWidgets.QGridLayout()
        self.resizeLayout.setObjectName('resizeLayout')

        self.resizeGroupBox = QtWidgets.QGroupBox('Resize:')
        self.resizeGroupBox.setObjectName('resizeGroupBox')
        self.resizeGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.resizeGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.resizeGroupBox.setLayout(self.resizeLayout)

        self.widthLabel = QtWidgets.QLabel('Width:')
        self.widthLabel.setObjectName('widthLabel')
        self.widthLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.widthLabel.setFixedSize(QtCore.QSize(40, 24))
        self.widthLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.widthLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.widthSpinBox = QtWidgets.QDoubleSpinBox()
        self.widthSpinBox.setObjectName('widthSpinBox')
        self.widthSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.widthSpinBox.setFixedHeight(24)
        self.widthSpinBox.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.widthSpinBox.setDecimals(2)
        self.widthSpinBox.setMinimum(0.0)
        self.widthSpinBox.setMaximum(1000.0)
        self.widthSpinBox.setSingleStep(1.0)
        self.widthSpinBox.setValue(0.0)
        self.widthSpinBox.editingFinished.connect(self.on_widthSpinBox_editingFinished)

        self.heightLabel = QtWidgets.QLabel('Height:')
        self.heightLabel.setObjectName('heightLabel')
        self.heightLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.heightLabel.setFixedSize(QtCore.QSize(40, 24))
        self.heightLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.heightLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.heightSpinBox = QtWidgets.QDoubleSpinBox()
        self.heightSpinBox.setObjectName('heightSpinBox')
        self.heightSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.heightSpinBox.setFixedHeight(24)
        self.heightSpinBox.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.heightSpinBox.setDecimals(2)
        self.heightSpinBox.setMinimum(0.0)
        self.heightSpinBox.setMaximum(1000.0)
        self.heightSpinBox.setSingleStep(1.0)
        self.heightSpinBox.setValue(0.0)
        self.heightSpinBox.editingFinished.connect(self.on_widthSpinBox_editingFinished)

        self.depthLabel = QtWidgets.QLabel('Depth:')
        self.depthLabel.setObjectName('depthLabel')
        self.depthLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.depthLabel.setFixedSize(QtCore.QSize(40, 24))
        self.depthLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.depthLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.depthSpinBox = QtWidgets.QDoubleSpinBox()
        self.depthSpinBox.setObjectName('depthSpinBox')
        self.depthSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.depthSpinBox.setFixedHeight(24)
        self.depthSpinBox.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.depthSpinBox.setDecimals(2)
        self.depthSpinBox.setMinimum(0.0)
        self.depthSpinBox.setMaximum(1000.0)
        self.depthSpinBox.setSingleStep(1.0)
        self.depthSpinBox.setValue(0.0)
        self.depthSpinBox.editingFinished.connect(self.on_widthSpinBox_editingFinished)

        self.dimensionsLayout = QtWidgets.QHBoxLayout()
        self.dimensionsLayout.setObjectName('dimensionsLayout')
        self.dimensionsLayout.setContentsMargins(0, 0, 0, 0)
        self.dimensionsLayout.addWidget(self.widthLabel)
        self.dimensionsLayout.addWidget(self.widthSpinBox)
        self.dimensionsLayout.addWidget(self.heightLabel)
        self.dimensionsLayout.addWidget(self.heightSpinBox)
        self.dimensionsLayout.addWidget(self.depthLabel)
        self.dimensionsLayout.addWidget(self.depthSpinBox)

        self.fitPushButton = QtWidgets.QPushButton('Fit')
        self.fitPushButton.setObjectName('fitPushButton')
        self.fitPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.fitPushButton.setFixedHeight(24)
        self.fitPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.fitPushButton.clicked.connect(self.on_fitPushButton_clicked)

        self.resetPushButton = QtWidgets.QPushButton('Reset')
        self.resetPushButton.setObjectName('resetPushButton')
        self.resetPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.resetPushButton.setFixedHeight(24)
        self.resetPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.resetPushButton.clicked.connect(self.on_resetPushButton_clicked)

        self.resizeLayout.addLayout(self.dimensionsLayout, 0, 0, 1, 2)
        self.resizeLayout.addWidget(self.fitPushButton, 1, 0)
        self.resizeLayout.addWidget(self.resetPushButton, 1, 1)

        centralLayout.addWidget(self.resizeGroupBox)

        # Invalidate user interface
        #
        self.invalidateShapes()
        self.invalidateSwatches()
    # endregion

    # region Methods
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
        self.setCurveDegree(settings.value('tabs/shapes/curveDegree', defaultValue=1, type=int))
        self.setCurveOffset(settings.value('tabs/shapes/curveOffset', defaultValue=0.0, type=float))

        self.setPreservePosition(bool(settings.value('tabs/shapes/preservePosition', defaultValue=0, type=int)))

        self.setStartColor(settings.value('tabs/shapes/startColor', defaultValue=QtCore.Qt.black))
        self.setEndColor(settings.value('tabs/shapes/endColor', defaultValue=QtCore.Qt.white))
        self.setUseSelectedNodes(bool(settings.value('tabs/shapes/useSelectedNodes', defaultValue=0, type=int)))

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

    @undo.Undo(name='Create Custom Shapes')
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

    @undo.Undo(name='Add Custom Shapes')
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

    @undo.Undo(name='Create Star')
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

    @undo.Undo(name='Convert Edge to Curve')
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

    @undo.Undo(name='Convert Edge to Helper')
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

    @undo.Undo(name='Rename Shapes')
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

    @undo.Undo(name='Mirror Shapes')
    def mirrorShapes(self, *nodes):
        """
        Mirrors all the shapes on the supplied nodes.

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

            # Check if opposite node exists
            #
            oppositeNode = node.getOppositeNode()
            hasOppositeNode = oppositeNode is not node

            if not hasOppositeNode:

                log.warning(f'Unable to find node opposite to {node}!')
                continue

            # Check if shape counts match
            #
            numShapes = node.numberOfShapesDirectlyBelow()
            requiredShapes = oppositeNode.numberOfShapesDirectlyBelow()

            if numShapes != requiredShapes:

                log.warning(f'Shape count mismatch between {node} and {oppositeNode}!')
                continue

            # Iterate through shapes
            #
            for (shape, oppositeShape) in zip(node.shapes(), oppositeNode.shapes()):

                # Check if shape types match
                #
                hasSameType = shape.apiType() == oppositeShape.apiType()

                if not hasSameType:

                    log.warning(f'Unable to mirror {shape} to {oppositeShape}!')
                    continue

                # Evaluate shape type
                #
                isLocator = shape.hasFn(om.MFn.kLocator)
                isNurbsCurve = shape.hasFn(om.MFn.kNurbsCurve) or shape.hasFn(om.MFn.kBezierCurve)

                mirrorTranslateX = node.userProperties.get('mirrorTranslateX', False)
                mirrorTranslateY = node.userProperties.get('mirrorTranslateY', False)
                mirrorTranslateZ = node.userProperties.get('mirrorTranslateZ', False)
                
                mirrorRotateX = node.userProperties.get('mirrorRotateX', False)
                mirrorRotateY = node.userProperties.get('mirrorRotateY', False)
                mirrorRotateZ = node.userProperties.get('mirrorRotateZ', False)
                
                if isLocator:
                    
                    localPositionX = -shape.localPositionX if mirrorTranslateX else shape.localPositionX
                    localPositionY = -shape.localPositionY if mirrorTranslateY else shape.localPositionY
                    localPositionZ = -shape.localPositionZ if mirrorTranslateZ else shape.localPositionZ
                    oppositeShape.localPosition = (localPositionX, localPositionY, localPositionZ)
                    oppositeShape.localScale = shape.localScale

                    isHelper = shape.hasFn(om.MFn.kPluginLocatorNode)

                    if isHelper:

                        localRotateX = -shape.localRotateX if mirrorRotateX else shape.localRotateX
                        localRotateY = -shape.localRotateY if mirrorRotateY else shape.localRotateY
                        localRotateZ = -shape.localRotateZ if mirrorRotateZ else shape.localRotateZ
                        oppositeShape.localRotate = (localRotateX, localRotateY, localRotateZ)

                        for attribute in shape.listAttr(category='Drawable'):

                            oppositeShape.setAttr(attribute, shape.getAttr(attribute))

                elif isNurbsCurve:

                    controlPoints = shape.controlPoints()

                    for controlPoint in controlPoints:

                        controlPoint.x *= -1.0 if mirrorTranslateX else 1.0
                        controlPoint.y *= -1.0 if mirrorTranslateY else 1.0
                        controlPoint.z *= -1.0 if mirrorTranslateZ else 1.0

                    oppositeShape.setControlPoints(controlPoints)

                else:

                    log.warning(f'Unable to mirror {shape.typeName} types!')
                    continue

    @undo.Undo(name='Remove Shapes')
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

    @undo.Undo(name='Colorize Shapes')
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

    @undo.Undo(name='Rescale Shapes')
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

    @undo.Undo(name='Resize Helpers')
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

    @undo.Undo(name='Parent Shapes')
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

    @undo.Undo(name='Fit Helpers')
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

    @undo.Undo(name='Reset Helpers')
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
    def on_mirrorShapesPushButton_clicked(self):
        """
        Slot method for the `renameShapesPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Evaluate active selection
        #
        if self.selectionCount > 0:

            self.mirrorShapes(*self.selection)

        else:

            log.warning(self, 'Add Helper', 'No controls selected to mirror shapes on!')

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
    def on_reparentShapesPushButton_clicked(self):
        """
        Slot method for the `reparentShapesPushButton` widget's `clicked` signal.

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
