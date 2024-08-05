import re

from maya import cmds as mc
from maya.api import OpenMaya as om
from Qt import QtCore, QtWidgets, QtGui
from copy import copy
from enum import IntEnum
from dcc.python import stringutils
from dcc.maya.decorators import undo
from dcc.generators.consecutivepairs import consecutivePairs
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

        # Declare public variables
        #
        self.renameGroupBox = None
        self.radioButtonGroup = None
        self.selectedRadioButton = None
        self.hierarchyRadioButton = None
        self.typeRadioButton = None
        self.typeComboBox = None

        self.concatenateGroupBox = None
        self.prefixLabel = None
        self.prefixLineEdit = None
        self.nameLabel = None
        self.nameLineEdit = None
        self.suffixLabel = None
        self.suffixLineEdit = None

        self.numerateGroupBox = None
        self.paddingLabel = None
        self.paddingSpinBox = None
        self.startLabel = None
        self.startSpinBox = None
        self.stepLabel = None
        self.stepSpinBox = None

        self.trimGroupBox = None
        self.leftLabel = None
        self.leftSpinBox = None
        self.rightLabel = None
        self.rightSpinBox = None

        self.replaceGroupBox = None
        self.searchLineEdit = None
        self.replaceLineEdit = None
        self.swapPushButton = None

        self.previewGroupBox = None
        self.previewTableView = None
        self.previewTableModel = None

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
        super(QRenameTab, self).postLoad(*args, **kwargs)

        # Initialize radio button group
        #
        self.radioButtonGroup = QtWidgets.QButtonGroup(self.renameGroupBox)
        self.radioButtonGroup.setObjectName('radioButtonGroup')
        self.radioButtonGroup.setExclusive(True)
        self.radioButtonGroup.addButton(self.selectedRadioButton, id=0)
        self.radioButtonGroup.addButton(self.hierarchyRadioButton, id=1)
        self.radioButtonGroup.addButton(self.typeRadioButton, id=2)
        self.radioButtonGroup.idClicked.connect(self.on_radioButtonGroup_idClicked)

        # Invalidate type combo-box
        #
        self.invalidateTypes()

        # Initialize preview table view
        #
        itemPrototype = QtGui.QStandardItem('')
        itemPrototype.setSizeHint(QtCore.QSize(100, 24))
        itemPrototype.setTextAlignment(QtCore.Qt.AlignCenter)

        self.previewTableModel = QtGui.QStandardItemModel(parent=self.previewTableView)
        self.previewTableModel.setObjectName('previewTableModel')
        self.previewTableModel.setColumnCount(2)
        self.previewTableModel.setHorizontalHeaderLabels(['Before', 'After'])
        self.previewTableModel.setItemPrototype(itemPrototype)

        self.previewTableView.setModel(self.previewTableModel)

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
