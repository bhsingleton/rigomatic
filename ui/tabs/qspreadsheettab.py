from maya.api import OpenMaya as om
from Qt import QtCore, QtWidgets, QtGui
from dcc.maya.models import qplugitemmodel, qplugitemfiltermodel, qplugstyleditemdelegate
from . import qabstracttab

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QSpreadsheetTab(qabstracttab.QAbstractTab):
    """
    Overload of `QAbstractTab` that interfaces with scene node attributes.
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
        super(QSpreadsheetTab, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._currentNode = None

    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        # Call parent method
        #
        super(QSpreadsheetTab, self).__setup_ui__(*args, **kwargs)

        # Initialize central layout
        #
        centralLayout = QtWidgets.QVBoxLayout()
        centralLayout.setObjectName('centralLayout')

        self.setLayout(centralLayout)

        # Initialize attributes group-box
        #
        self.attributesLayout = QtWidgets.QVBoxLayout()
        self.attributesLayout.setObjectName('attributesLayout')

        self.attributesGroupBox = QtWidgets.QGroupBox('Attributes:')
        self.attributesGroupBox.setObjectName('attributesGroupBox')
        self.attributesGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.attributesGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.attributesGroupBox.setLayout(self.attributesLayout)

        self.attributeTreeView = QtWidgets.QTreeView()
        self.attributeTreeView.setObjectName('attributeTreeView')
        self.attributeTreeView.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.attributeTreeView.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.attributeTreeView.setMouseTracking(True)
        self.attributeTreeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.attributeTreeView.setStyleSheet('QTreeView::item { height: 24px; }')
        self.attributeTreeView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.attributeTreeView.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked | QtWidgets.QAbstractItemView.EditKeyPressed)
        self.attributeTreeView.setDragEnabled(False)
        self.attributeTreeView.setDragDropOverwriteMode(False)
        self.attributeTreeView.setDragDropMode(QtWidgets.QAbstractItemView.NoDragDrop)
        self.attributeTreeView.setDefaultDropAction(QtCore.Qt.IgnoreAction)
        self.attributeTreeView.setAlternatingRowColors(True)
        self.attributeTreeView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.attributeTreeView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.attributeTreeView.setUniformRowHeights(True)
        self.attributeTreeView.setAnimated(True)
        self.attributeTreeView.setExpandsOnDoubleClick(False)

        self.attributeItemModel = qplugitemmodel.QPlugItemModel(parent=self.attributeTreeView)
        self.attributeItemModel.setObjectName('attributeItemModel')

        self.attributeStyledItemDelegate = qplugstyleditemdelegate.QPlugStyledItemDelegate(parent=self.attributeTreeView)
        self.attributeStyledItemDelegate.setObjectName('attributeStyledItemDelegate')

        self.attributeItemFilterModel = qplugitemfiltermodel.QPlugItemFilterModel(parent=self.attributeTreeView)
        self.attributeItemFilterModel.setObjectName('attributeItemFilterModel')
        self.attributeItemFilterModel.setSourceModel(self.attributeItemModel)

        self.attributeTreeView.setModel(self.attributeItemFilterModel)
        self.attributeTreeView.setItemDelegate(self.attributeStyledItemDelegate)

        self.attributeHeader = self.attributeTreeView.header()
        self.attributeHeader.setVisible(True)
        self.attributeHeader.setMinimumSectionSize(100)
        self.attributeHeader.setDefaultSectionSize(200)
        self.attributeHeader.setStretchLastSection(True)

        self.editPushButton = QtWidgets.QPushButton('Nothing Selected')
        self.editPushButton.setObjectName('editPushButton')
        self.editPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.editPushButton.setFixedHeight(24)
        self.editPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.editPushButton.setStyleSheet('QPushButton:hover:checked { background-color: crimson; }\nQPushButton:checked { background-color: firebrick; border: none; }')
        self.editPushButton.setCheckable(True)
        self.editPushButton.clicked.connect(self.on_editPushButton_clicked)

        self.filterLineEdit = QtWidgets.QLineEdit()
        self.filterLineEdit.setObjectName('filterLineEdit')
        self.filterLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.filterLineEdit.setFixedHeight(24)
        self.filterLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.filterLineEdit.setPlaceholderText('Filter Attributes...')
        self.filterLineEdit.textChanged.connect(self.attributeItemFilterModel.setFilterWildcard)

        self.userDefinedCheckBox = QtWidgets.QCheckBox('User-Defined')
        self.userDefinedCheckBox.setObjectName('userDefinedCheckBox')
        self.userDefinedCheckBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))
        self.userDefinedCheckBox.setFixedHeight(24)
        self.userDefinedCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.userDefinedCheckBox.toggled.connect(self.attributeItemFilterModel.setHideStaticAttributes)

        self.filterLayout = QtWidgets.QHBoxLayout()
        self.filterLayout.setObjectName('userDefinedCheckBox')
        self.filterLayout.setContentsMargins(0, 0, 0, 0)
        self.filterLayout.addWidget(self.filterLineEdit)
        self.filterLayout.addWidget(self.userDefinedCheckBox)

        self.attributesLayout.addWidget(self.editPushButton)
        self.attributesLayout.addLayout(self.filterLayout)
        self.attributesLayout.addWidget(self.attributeTreeView)

        centralLayout.addWidget(self.attributesGroupBox)
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
        super(QSpreadsheetTab, self).invalidate()

        # Refresh attribute editor
        #
        self.invalidateEditor()
    # endregion

    # region Slots
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
