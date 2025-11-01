import re

from maya import cmds as mc
from maya.api import OpenMaya as om
from dcc.vendor.Qt import QtCore, QtWidgets, QtGui
from dcc.python import stringutils
from dcc.maya.decorators import undo
from dcc.generators.consecutivepairs import consecutivePairs
from copy import copy
from enum import IntEnum
from . import qabstracttab

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Options(IntEnum):
    """
    Collection of all available rename options
    """

    NONE = -1
    SELECTED = 0
    HIERARCHY = 1
    TYPE = 2


class QRenameTab(qabstracttab.QAbstractTab):
    """
    Overload of `QAbstractTab` that renames scene nodes.
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
        super(QRenameTab, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._nodes = []
        self._before = []
        self._after = []

    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        # Call parent method
        #
        super(QRenameTab, self).__setup_ui__(*args, **kwargs)

        # Initialize central layout
        #
        centralLayout = QtWidgets.QVBoxLayout()
        centralLayout.setObjectName('centralLayout')

        self.setLayout(centralLayout)

        # Initialize rename group-box
        #
        self.renameLayout = QtWidgets.QHBoxLayout()
        self.renameLayout.setObjectName('renameLayout')

        self.renameGroupBox = QtWidgets.QGroupBox('Rename:')
        self.renameGroupBox.setObjectName('renameGroupBox')
        self.renameGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.renameGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.renameGroupBox.setLayout(self.renameLayout)

        self.selectedRadioButton = QtWidgets.QRadioButton('Selected')
        self.selectedRadioButton.setObjectName('selectedRadioButton')
        self.selectedRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))
        self.selectedRadioButton.setFixedHeight(24)
        self.selectedRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.selectedRadioButton.setChecked(True)

        self.hierarchyRadioButton = QtWidgets.QRadioButton('Hierarchy')
        self.hierarchyRadioButton.setObjectName('hierarchyRadioButton')
        self.hierarchyRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))
        self.hierarchyRadioButton.setFixedHeight(24)
        self.hierarchyRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.hierarchyRadioButton.setChecked(False)

        self.typeRadioButton = QtWidgets.QRadioButton('Type:')
        self.typeRadioButton.setObjectName('typeRadioButton')
        self.typeRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))
        self.typeRadioButton.setFixedHeight(24)
        self.typeRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.typeRadioButton.setChecked(False)

        self.typeComboBox = QtWidgets.QComboBox()
        self.typeComboBox.setObjectName('typeComboBox')
        self.typeComboBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.typeComboBox.setFixedHeight(24)
        self.typeComboBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.typeComboBox.currentIndexChanged.connect(self.on_typeComboBox_currentIndexChanged)

        self.radioButtonGroup = QtWidgets.QButtonGroup(parent=self.renameGroupBox)
        self.radioButtonGroup.setObjectName('')
        self.radioButtonGroup.setExclusive(True)
        self.radioButtonGroup.addButton(self.selectedRadioButton, id=Options.SELECTED)
        self.radioButtonGroup.addButton(self.hierarchyRadioButton, id=Options.HIERARCHY)
        self.radioButtonGroup.addButton(self.typeRadioButton, id=Options.TYPE)
        self.radioButtonGroup.idClicked.connect(self.on_radioButtonGroup_idClicked)

        self.renameLayout.addWidget(self.selectedRadioButton)
        self.renameLayout.addWidget(self.hierarchyRadioButton)
        self.renameLayout.addWidget(self.typeRadioButton)
        self.renameLayout.addWidget(self.typeComboBox)

        centralLayout.addWidget(self.renameGroupBox)

        # Initialize concatenate group-box
        #
        self.concatenateLayout = QtWidgets.QGridLayout()
        self.concatenateLayout.setObjectName('concatenateLayout')

        self.concatenateGroupBox = QtWidgets.QGroupBox('Concatenate:')
        self.concatenateGroupBox.setObjectName('concatenateGroupBox')
        self.concatenateGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.concatenateGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.concatenateGroupBox.setCheckable(True)
        self.concatenateGroupBox.setLayout(self.concatenateLayout)
        self.concatenateGroupBox.toggled.connect(self.on_concatenateGroupBox_toggled)

        self.prefixLabel = QtWidgets.QLabel('Prefix:')
        self.prefixLabel.setObjectName('prefixLabel')
        self.prefixLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.prefixLabel.setFixedSize(QtCore.QSize(40, 24))
        self.prefixLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.prefixLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.prefixLineEdit = QtWidgets.QLineEdit()
        self.prefixLineEdit.setObjectName('prefixLineEdit')
        self.prefixLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.prefixLineEdit.setFixedHeight(24)
        self.prefixLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.prefixLineEdit.textChanged.connect(self.on_prefixLineEdit_textChanged)

        self.nameLabel = QtWidgets.QLabel('Name:')
        self.nameLabel.setObjectName('nameLabel')
        self.nameLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.nameLabel.setFixedSize(QtCore.QSize(40, 24))
        self.nameLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.nameLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.nameLineEdit = QtWidgets.QLineEdit()
        self.nameLineEdit.setObjectName('nameLineEdit')
        self.nameLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.nameLineEdit.setFixedHeight(24)
        self.nameLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.nameLineEdit.textChanged.connect(self.on_nameLineEdit_textChanged)

        self.suffixLabel = QtWidgets.QLabel('Suffix:')
        self.suffixLabel.setObjectName('suffixLabel')
        self.suffixLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.suffixLabel.setFixedSize(QtCore.QSize(40, 24))
        self.suffixLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.suffixLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.suffixLineEdit = QtWidgets.QLineEdit()
        self.suffixLineEdit.setObjectName('suffixLineEdit')
        self.suffixLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.suffixLineEdit.setFixedHeight(24)
        self.suffixLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.suffixLineEdit.textChanged.connect(self.on_suffixLineEdit_textChanged)

        self.concatenateLayout.addWidget(self.prefixLabel, 0, 0)
        self.concatenateLayout.addWidget(self.prefixLineEdit, 0, 1)
        self.concatenateLayout.addWidget(self.nameLabel, 1, 0)
        self.concatenateLayout.addWidget(self.nameLineEdit, 1, 1)
        self.concatenateLayout.addWidget(self.suffixLabel, 2, 0)
        self.concatenateLayout.addWidget(self.suffixLineEdit, 2, 1)

        # Initialize numerate group-box
        #
        self.numerateLayout = QtWidgets.QGridLayout()
        self.numerateLayout.setObjectName('numerateLayout')

        self.numerateGroupBox = QtWidgets.QGroupBox('Numerate:')
        self.numerateGroupBox.setObjectName('numerateGroupBox')
        self.numerateGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.numerateGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.numerateGroupBox.setCheckable(True)
        self.numerateGroupBox.setLayout(self.numerateLayout)
        self.numerateGroupBox.toggled.connect(self.on_numerateGroupBox_toggled)

        self.paddingLabel = QtWidgets.QLabel('Padding:')
        self.paddingLabel.setObjectName('paddingLabel')
        self.paddingLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.paddingLabel.setFixedSize(QtCore.QSize(50, 24))
        self.paddingLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.paddingLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.paddingSpinBox = QtWidgets.QSpinBox()
        self.paddingSpinBox.setObjectName('paddingSpinBox')
        self.paddingSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.paddingSpinBox.setFixedHeight(24)
        self.paddingSpinBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.paddingSpinBox.setMinimum(0)
        self.paddingSpinBox.setMaximum(4)
        self.paddingSpinBox.setSingleStep(1)
        self.paddingSpinBox.setValue(2)
        self.paddingSpinBox.valueChanged.connect(self.on_paddingSpinBox_valueChanged)

        self.startLabel = QtWidgets.QLabel('Start:')
        self.startLabel.setObjectName('startLabel')
        self.startLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.startLabel.setFixedSize(QtCore.QSize(50, 24))
        self.startLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.startLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.startSpinBox = QtWidgets.QSpinBox()
        self.startSpinBox.setObjectName('startSpinBox')
        self.startSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.startSpinBox.setFixedHeight(24)
        self.startSpinBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.startSpinBox.setMinimum(0)
        self.startSpinBox.setMaximum(10000)
        self.startSpinBox.setSingleStep(1)
        self.startSpinBox.setValue(1)
        self.startSpinBox.valueChanged.connect(self.on_startSpinBox_valueChanged)

        self.stepLabel = QtWidgets.QLabel('Step:')
        self.stepLabel.setObjectName('stepLabel')
        self.stepLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.stepLabel.setFixedSize(QtCore.QSize(50, 24))
        self.stepLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.stepLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.stepSpinBox = QtWidgets.QSpinBox()
        self.stepSpinBox.setObjectName('stepSpinBox')
        self.stepSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.stepSpinBox.setFixedHeight(24)
        self.stepSpinBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.stepSpinBox.setMinimum(1)
        self.stepSpinBox.setMaximum(10)
        self.stepSpinBox.setSingleStep(1)
        self.stepSpinBox.setValue(1)
        self.stepSpinBox.valueChanged.connect(self.on_stepSpinBox_valueChanged)

        self.numerateLayout.addWidget(self.paddingLabel, 0, 0)
        self.numerateLayout.addWidget(self.paddingSpinBox, 0, 1)
        self.numerateLayout.addWidget(self.startLabel, 1, 0)
        self.numerateLayout.addWidget(self.startSpinBox, 1, 1)
        self.numerateLayout.addWidget(self.stepLabel, 2, 0)
        self.numerateLayout.addWidget(self.stepSpinBox, 2, 1)

        # Initialize name layout
        #
        self.nameLayout = QtWidgets.QHBoxLayout()
        self.nameLayout.setObjectName('')
        self.nameLayout.setContentsMargins(0, 0, 0, 0)
        self.nameLayout.addWidget(self.concatenateGroupBox)
        self.nameLayout.addWidget(self.numerateGroupBox)

        centralLayout.addLayout(self.nameLayout)

        # Initialize trim group-box
        #
        self.trimLayout = QtWidgets.QHBoxLayout()
        self.trimLayout.setObjectName('trimLayout')

        self.trimGroupBox = QtWidgets.QGroupBox('Trim:')
        self.trimGroupBox.setObjectName('trimGroupBox')
        self.trimGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.trimGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.trimGroupBox.setCheckable(True)
        self.trimGroupBox.setLayout(self.trimLayout)
        self.trimGroupBox.toggled.connect(self.on_trimGroupBox_toggled)

        self.leftLabel = QtWidgets.QLabel('Left:')
        self.leftLabel.setObjectName('leftLabel')
        self.leftLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.leftLabel.setFixedSize(QtCore.QSize(40, 24))
        self.leftLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.leftLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.leftSpinBox = QtWidgets.QSpinBox()
        self.leftSpinBox.setObjectName('leftSpinBox')
        self.leftSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.leftSpinBox.setFixedHeight(24)
        self.leftSpinBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.leftSpinBox.setMinimum(0)
        self.leftSpinBox.setMaximum(100)
        self.leftSpinBox.setSingleStep(1)
        self.leftSpinBox.setValue(0)
        self.leftSpinBox.valueChanged.connect(self.on_leftSpinBox_valueChanged)

        self.rightLabel = QtWidgets.QLabel('Right:')
        self.rightLabel.setObjectName('rightLabel')
        self.rightLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.rightLabel.setFixedSize(QtCore.QSize(40, 24))
        self.rightLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.rightLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.rightSpinBox = QtWidgets.QSpinBox()
        self.rightSpinBox.setObjectName('rightSpinBox')
        self.rightSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.rightSpinBox.setFixedHeight(24)
        self.rightSpinBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.rightSpinBox.setMinimum(0)
        self.rightSpinBox.setMaximum(100)
        self.rightSpinBox.setSingleStep(1)
        self.rightSpinBox.setValue(0)
        self.rightSpinBox.valueChanged.connect(self.on_rightSpinBox_valueChanged)

        self.trimLayout.addWidget(self.leftLabel)
        self.trimLayout.addWidget(self.leftSpinBox)
        self.trimLayout.addWidget(self.rightLabel)
        self.trimLayout.addWidget(self.rightSpinBox)

        centralLayout.addWidget(self.trimGroupBox)

        # Initialize replace group-box
        #
        self.replaceLayout = QtWidgets.QHBoxLayout()
        self.replaceLayout.setObjectName('replaceLayout')

        self.replaceGroupBox = QtWidgets.QGroupBox('Replace:')
        self.replaceGroupBox.setObjectName('replaceGroupBox')
        self.replaceGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.replaceGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.replaceGroupBox.setCheckable(True)
        self.replaceGroupBox.setLayout(self.replaceLayout)
        self.replaceGroupBox.toggled.connect(self.on_replaceGroupBox_toggled)

        self.searchLineEdit = QtWidgets.QLineEdit()
        self.searchLineEdit.setObjectName('searchLineEdit')
        self.searchLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.searchLineEdit.setFixedHeight(24)
        self.searchLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.searchLineEdit.setPlaceholderText('Search')
        self.searchLineEdit.textChanged.connect(self.on_searchLineEdit_textChanged)

        self.swapPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/refresh.svg'), '')
        self.swapPushButton.setObjectName('swapPushButton')
        self.swapPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.swapPushButton.setFixedSize(QtCore.QSize(24, 24))
        self.swapPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.swapPushButton.clicked.connect(self.on_swapPushButton_clicked)

        self.replaceLineEdit = QtWidgets.QLineEdit()
        self.replaceLineEdit.setObjectName('replaceLineEdit')
        self.replaceLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.replaceLineEdit.setFixedHeight(24)
        self.replaceLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.replaceLineEdit.setPlaceholderText('Replace')
        self.replaceLineEdit.textChanged.connect(self.on_replaceLineEdit_textChanged)

        self.replaceLayout.addWidget(self.searchLineEdit)
        self.replaceLayout.addWidget(self.swapPushButton)
        self.replaceLayout.addWidget(self.replaceLineEdit)

        centralLayout.addWidget(self.replaceGroupBox)

        # Initialize preview group-box
        #
        self.previewLayout = QtWidgets.QHBoxLayout()
        self.previewLayout.setObjectName('previewLayout')

        self.previewGroupBox = QtWidgets.QGroupBox('Preview:')
        self.previewGroupBox.setObjectName('previewGroupBox')
        self.previewGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.previewGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.previewGroupBox.setLayout(self.previewLayout)
        
        self.previewTableView = QtWidgets.QTableView()
        self.previewTableView.setObjectName('previewTableView')
        self.previewTableView.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.previewTableView.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.previewTableView.setStyleSheet('QTableView::item { height: 24px; }')
        self.previewTableView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.previewTableView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.previewTableView.setDragEnabled(False)
        self.previewTableView.setDragDropOverwriteMode(False)
        self.previewTableView.setDragDropMode(QtWidgets.QAbstractItemView.NoDragDrop)
        self.previewTableView.setDefaultDropAction(QtCore.Qt.IgnoreAction)
        self.previewTableView.setAlternatingRowColors(True)
        self.previewTableView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.previewTableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.previewTableView.setShowGrid(True)

        self.itemPrototype = QtGui.QStandardItem('')
        self.itemPrototype.setSizeHint(QtCore.QSize(100, 24))
        self.itemPrototype.setTextAlignment(QtCore.Qt.AlignCenter)

        self.previewTableModel = QtGui.QStandardItemModel(parent=self.previewTableView)
        self.previewTableModel.setObjectName('previewTableModel')
        self.previewTableModel.setColumnCount(2)
        self.previewTableModel.setHorizontalHeaderLabels(['Before', 'After'])
        self.previewTableModel.setItemPrototype(self.itemPrototype)

        self.previewTableView.setModel(self.previewTableModel)

        self.previewHorizontalHeader = self.previewTableView.horizontalHeader()  # type: QtWidgets.QHeaderView
        self.previewHorizontalHeader.setVisible(True)
        self.previewHorizontalHeader.setMinimumSectionSize(100)
        self.previewHorizontalHeader.setDefaultSectionSize(200)
        self.previewHorizontalHeader.setStretchLastSection(True)

        self.previewVerticalHeader = self.previewTableView.verticalHeader()  # type: QtWidgets.QHeaderView
        self.previewVerticalHeader.setVisible(False)
        self.previewVerticalHeader.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.previewVerticalHeader.setMinimumSectionSize(24)
        self.previewVerticalHeader.setDefaultSectionSize(24)
        self.previewVerticalHeader.setStretchLastSection(False)

        self.applyPushButton = QtWidgets.QPushButton('Apply')
        self.applyPushButton.setObjectName('applyPushButton')
        self.applyPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.applyPushButton.setFixedHeight(24)
        self.applyPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.applyPushButton.clicked.connect(self.on_applyPushButton_clicked)

        self.previewLayout.addWidget(self.previewTableView)

        centralLayout.addWidget(self.previewGroupBox)
        centralLayout.addWidget(self.applyPushButton)

        # Invalidate type combo-box
        #
        self.invalidateTypes()
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
        super(QRenameTab, self).loadSettings(settings)

        # Load user preferences
        #
        self.setOption(settings.value('tabs/rename/option', defaultValue=0, type=int))
        self.setCurrentType(settings.value('tabs/rename/type', defaultValue='transform', type=str))

        self.concatenateGroupBox.setChecked(bool(settings.value('tabs/rename/concatenateEnabled', defaultValue=1, type=int)))
        self.prefixLineEdit.setText(settings.value('tabs/rename/prefix', defaultValue='', type=str))
        self.nameLineEdit.setText(settings.value('tabs/rename/name', defaultValue='', type=str))
        self.suffixLineEdit.setText(settings.value('tabs/rename/suffix', defaultValue='', type=str))

        self.numerateGroupBox.setChecked(bool(settings.value('tabs/rename/numerateEnabled', defaultValue=1, type=int)))
        self.paddingSpinBox.setValue(settings.value('tabs/rename/padding', defaultValue=2, type=int))
        self.startSpinBox.setValue(settings.value('tabs/rename/start', defaultValue=1, type=int))
        self.stepSpinBox.setValue(settings.value('tabs/rename/step', defaultValue=1, type=int))

        self.trimGroupBox.setChecked(bool(settings.value('tabs/rename/trimEnabled', defaultValue=1, type=int)))
        self.leftSpinBox.setValue(settings.value('tabs/rename/leftTrim', defaultValue=0, type=int))
        self.rightSpinBox.setValue(settings.value('tabs/rename/rightTrim', defaultValue=0, type=int))

        self.replaceGroupBox.setChecked(bool(settings.value('tabs/rename/replaceEnabled', defaultValue=1, type=int)))
        self.searchLineEdit.setText(settings.value('tabs/rename/search', defaultValue='', type=str))
        self.replaceLineEdit.setText(settings.value('tabs/rename/replace', defaultValue='', type=str))

    def saveSettings(self, settings):
        """
        Saves the user settings.

        :type settings: QtCore.QSettings
        :rtype: None
        """

        # Call parent method
        #
        super(QRenameTab, self).saveSettings(settings)

        # Save user preferences
        #
        settings.setValue('tabs/rename/option', int(self.option()))
        settings.setValue('tabs/rename/type', self.currentType())

        settings.setValue('tabs/rename/concatenateEnabled', int(self.concatenateGroupBox.isChecked()))
        settings.setValue('tabs/rename/prefix', self.prefixLineEdit.text())
        settings.setValue('tabs/rename/name', self.nameLineEdit.text())
        settings.setValue('tabs/rename/suffix', self.suffixLineEdit.text())

        settings.setValue('tabs/rename/numerateEnabled', int(self.numerateGroupBox.isChecked()))
        settings.setValue('tabs/rename/padding', int(self.paddingSpinBox.value()))
        settings.setValue('tabs/rename/start', int(self.startSpinBox.value()))
        settings.setValue('tabs/rename/step', int(self.stepSpinBox.value()))

        settings.setValue('tabs/rename/trimEnabled', int(self.trimGroupBox.isChecked()))
        settings.setValue('tabs/rename/leftTrim', int(self.leftSpinBox.value()))
        settings.setValue('tabs/rename/rightTrim', int(self.rightSpinBox.value()))

        settings.setValue('tabs/rename/replaceEnabled', int(self.replaceGroupBox.isChecked()))
        settings.setValue('tabs/rename/search', self.searchLineEdit.text())
        settings.setValue('tabs/rename/replace', self.replaceLineEdit.text())

    def option(self):
        """
        Returns the current rename option.

        :rtype: Options
        """

        return Options(self.radioButtonGroup.checkedId())

    def setOption(self, option):
        """
        Updates the current rename option.

        :type option: Union[int, Option]
        :rtype: None
        """

        buttons = self.radioButtonGroup.buttons()
        numButtons = len(buttons)

        if 0 <= option < numButtons:

            buttons[option].setChecked(True)

    def evalOption(self):
        """
        Returns nodes based on the current option.

        :rtype: List[mpynode.MPyNode]
        """

        option = self.option()
        nodes = []

        if option == Options.SELECTED:

            nodes = self.scene.selection()

        elif option == Options.HIERARCHY:

            selection = self.scene.selection(apiType=om.MFn.kTransform)
            selectionCount = len(selection)

            if selectionCount > 0:

                selectedNode = selection[0]
                nodes = [selectedNode] + selectedNode.descendants()

        elif option == Options.TYPE:

            nodes = list(self.scene.iterNodesByTypeName(self.typeComboBox.currentText()))

        else:

            pass

        return nodes

    def currentType(self):
        """
        Returns the current type name.

        :rtype: str
        """

        return self.typeComboBox.currentText()

    def setCurrentType(self, typeName):
        """
        Updates the current type name.

        :type typeName: str
        :rtype: None
        """

        index = self.typeComboBox.findText(typeName)
        numItems = self.typeComboBox.count()

        if 0 <= index < numItems:

            self.typeComboBox.setCurrentIndex(index)

    @undo.Undo(name='Rename Nodes')
    def renameNodes(self, nodes, names):
        """
        Renames the supplied nodes with the specified names.

        :type nodes: List[mpynode.MPyNode]
        :type names: List[str]
        :rtype: None
        """

        for (node, name) in zip(nodes, names):

            node.setName(name)

    def invalidateTypes(self):
        """
        Refreshes the type combo-box items.

        :rtype: None
        """

        self.typeComboBox.blockSignals(True)
        self.typeComboBox.clear()
        self.typeComboBox.addItems(mc.allNodeTypes())
        self.typeComboBox.blockSignals(False)

    def invalidatePreview(self):
        """
        Refreshes the preview widgets.

        :rtype: None
        """

        # Evaluate active selection
        #
        self._nodes = self.evalOption()

        self._before = [node.name() for node in self._nodes]
        self._after = copy(self._before)

        # Check if trim is enabled
        #
        if self.trimGroupBox.isChecked():

            leftTrim = self.leftSpinBox.value()
            rightTrim = self.rightSpinBox.value()

            for (i, name) in enumerate(self._after):

                self._after[i] = name[leftTrim:(len(name) - rightTrim)]

        # Check if concatenate is enabled
        #
        if self.concatenateGroupBox.isChecked():

            prefix = self.prefixLineEdit.text()
            altName = self.nameLineEdit.text()
            suffix = self.suffixLineEdit.text()

            numerate = self.numerateGroupBox.isChecked()
            padding = self.paddingSpinBox.value()
            start = self.startSpinBox.value()
            step = self.stepSpinBox.value()
            digits = [start + (i * step) for i in range(len(self._after))]

            for (i, (name, digit)) in enumerate(zip(self._after, digits)):

                # Check if numeration is enabled
                #
                body = altName if not stringutils.isNullOrEmpty(altName) else name

                if numerate:

                    # Check if digit symbol exists
                    #
                    indices = [i for (i, char) in enumerate(body) if char == '#']
                    numIndices = len(indices)

                    if numIndices > 0:

                        # Insert digits into byte array
                        #
                        chars = bytearray(body, 'ascii')

                        for (startIndex, endIndex) in consecutivePairs(indices):

                            altPadding = (endIndex - startIndex) + 1
                            digit = str(digit).zfill(altPadding)

                            chars[startIndex:(endIndex + 1)] = bytearray(digit, 'ascii')

                        body = chars.decode()

                    else:

                        # Append digit
                        #
                        body += str(digit).zfill(padding)

                # Format full-name and sanitize
                #
                self._after[i] = stringutils.slugify(f'{prefix}{body}{suffix}', whitespace='_', illegal='_')

        # Check if replace is enabled
        #
        if self.replaceGroupBox.isChecked():

            search = self.searchLineEdit.text()
            replace = self.replaceLineEdit.text()

            for (i, name) in enumerate(self._after):

                escapedPattern = ''.join([f'\\{char}' if char in '(){}.,+|!-' else char for char in search])
                searchPattern = f'(^.*)({escapedPattern.replace("*", ".+")})(.*$)'
                replacePattern = f'\\1{replace}\\3'

                self._after[i] = re.sub(searchPattern, replacePattern, name)

        # Update list widgets
        #
        numItems = len(self._before)
        self.previewTableModel.setRowCount(numItems)

        for (i, (before, after)) in enumerate(zip(self._before, self._after)):

            index = self.previewTableModel.index(i, 0)
            self.previewTableModel.setData(index, before, role=QtCore.Qt.DisplayRole)

            index = self.previewTableModel.index(i, 1)
            self.previewTableModel.setData(index, after, role=QtCore.Qt.DisplayRole)

    def invalidate(self, reason=None):
        """
        Refreshes the user interface.

        :type reason: Union[InvalidateReason, None]
        :rtype: None
        """

        # Call parent method
        #
        super(QRenameTab, self).invalidate()

        # Invalidate user interface
        #
        self.invalidatePreview()
    # endregion

    # region Slots
    @QtCore.Slot(int)
    def on_radioButtonGroup_idClicked(self, id):
        """
        Slot method for the `radioButtonGroup` widget's `idClicked` signal.

        :type id: int
        :rtype: None
        """

        self.invalidate()

    @QtCore.Slot(int)
    def on_typeComboBox_currentIndexChanged(self, index):
        """
        Slot method for the `typeComboBox` widget's `currentIndexChanged` signal.

        :type index: int
        :rtype: None
        """

        sender = self.sender()
        numTypes = sender.count()

        if (self.option() == Options.TYPE) and (0 <= index < numTypes):

            self.invalidatePreview()

    @QtCore.Slot(bool)
    def on_concatenateGroupBox_toggled(self, checked):
        """
        Slot method for the `concatenateGroupBox` widget's `toggled` signal.

        :type checked: bool
        :rtype: None
        """

        self.invalidate()

    @QtCore.Slot(str)
    def on_prefixLineEdit_textChanged(self, text):
        """
        Slot method for the `prefixLineEdit` widget's `textChanged` signal.

        :type text: str
        :rtype: None
        """

        self.invalidate()

    @QtCore.Slot(str)
    def on_nameLineEdit_textChanged(self, text):
        """
        Slot method for the `nameLineEdit` widget's `textChanged` signal.

        :type text: str
        :rtype: None
        """

        self.invalidate()

    @QtCore.Slot(str)
    def on_suffixLineEdit_textChanged(self, text):
        """
        Slot method for the `suffixLineEdit` widget's `textChanged` signal.

        :type text: str
        :rtype: None
        """

        self.invalidate()

    @QtCore.Slot(bool)
    def on_numerateGroupBox_toggled(self, checked):
        """
        Slot method for the `numerateGroupBox` widget's `toggled` signal.

        :type checked: bool
        :rtype: None
        """

        self.invalidate()

    @QtCore.Slot(int)
    def on_paddingSpinBox_valueChanged(self, value):
        """
        Slot method for the `paddingSpinBox` widget's `valueChanged` signal.

        :type value: int
        :rtype: None
        """

        self.invalidate()

    @QtCore.Slot(int)
    def on_startSpinBox_valueChanged(self, value):
        """
        Slot method for the `startSpinBox` widget's `valueChanged` signal.

        :type value: int
        :rtype: None
        """

        self.invalidate()

    @QtCore.Slot(int)
    def on_stepSpinBox_valueChanged(self, value):
        """
        Slot method for the `stepSpinBox` widget's `valueChanged` signal.

        :type value: int
        :rtype: None
        """

        self.invalidate()

    @QtCore.Slot(bool)
    def on_trimGroupBox_toggled(self, checked):
        """
        Slot method for the `trimGroupBox` widget's `toggled` signal.

        :type checked: bool
        :rtype: None
        """

        self.invalidate()

    @QtCore.Slot(int)
    def on_leftSpinBox_valueChanged(self, value):
        """
        Slot method for the `leftSpinBox` widget's `valueChanged` signal.

        :type value: int
        :rtype: None
        """

        self.invalidate()

    @QtCore.Slot(int)
    def on_rightSpinBox_valueChanged(self, value):
        """
        Slot method for the `rightSpinBox` widget's `valueChanged` signal.

        :type value: int
        :rtype: None
        """

        self.invalidate()

    @QtCore.Slot(bool)
    def on_replaceGroupBox_toggled(self, checked):
        """
        Slot method for the `replaceGroupBox` widget's `toggled` signal.

        :type checked: bool
        :rtype: None
        """

        self.invalidate()

    @QtCore.Slot(str)
    def on_searchLineEdit_textChanged(self, text):
        """
        Slot method for the `searchLineEdit` widget's `textChanged` signal.

        :type text: str
        :rtype: None
        """

        self.invalidate()

    @QtCore.Slot()
    def on_swapPushButton_clicked(self):
        """
        Slot method for the `swapPushButton` widget's `clicked` signal.

        :rtype: None
        """

        search, replace = self.searchLineEdit.text(), self.replaceLineEdit.text()

        self.searchLineEdit.setText(replace)
        self.replaceLineEdit.setText(search)

    @QtCore.Slot(str)
    def on_replaceLineEdit_textChanged(self, text):
        """
        Slot method for the `replaceLineEdit` widget's `textChanged` signal.

        :type text: str
        :rtype: None
        """

        self.invalidate()

    @QtCore.Slot()
    def on_applyPushButton_clicked(self):
        """
        Slot method for the `applyPushButton` widget's `clicked` signal.

        :rtype: None
        """

        rows = list({index.row() for index in self.previewTableView.selectedIndexes()})
        numRows = len(rows)

        if numRows > 0:

            nodes = [self._nodes[row] for row in rows]
            names = [self._after[row] for row in rows]

            self.renameNodes(nodes, names)

        else:

            self.renameNodes(self._nodes, self._after)
    # endregion
