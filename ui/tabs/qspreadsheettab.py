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

        # Declare public variables
        #
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
        super(QSpreadsheetTab, self).postLoad(*args, **kwargs)

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
