from maya import cmds as mc
from maya.api import OpenMaya as om
from Qt import QtCore, QtWidgets, QtGui
from dcc.python import stringutils
from dcc.maya.libs import attributeutils, plugutils, dagutils
from dcc.maya.decorators.undo import undo
from dcc.generators.inclusiverange import inclusiveRange
from . import qabstracttab

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QAttributesTab(qabstracttab.QAbstractTab):
    """
    Overload of `QAbstractTab` that interfaces with attribute definitions.
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
        super(QAttributesTab, self).__init__(*args, **kwargs)

        # Declare public variables
        #
        self.nameGroupBox = None
        self.longNameWidget = None
        self.longNameLabel = None
        self.longNameLineEdit = None
        self.shortNameWidget = None
        self.shortNameLabel = None
        self.shortNameLineEdit = None
        self.niceNameWidget = None
        self.niceNameLabel = None
        self.niceNameLineEdit = None
        self.overrideNiceNameCheckBox = None
        self.propertiesWidget = None
        self.propertyButtonGroup = None
        self.keyableRadiobutton = None
        self.displayableRadioButton = None
        self.hiddenRadioButton = None
        self.arrayCheckBox = None
        
        self.dataTypeGroupBox = None
        self.dataTypeButtonGroup = None
        self.booleanRadioButton = None
        self.integerRadioButton = None
        self.shortRadioButton = None
        self.longRadioButton = None
        self.byteRadioButton = None
        self.characterRadioButton = None
        self.addressRadioButton = None
        self.enumRadioButton = None
        self.floatRadioButton = None
        self.doubleRadioButton = None
        self.distanceRadioButton = None
        self.angleRadioButton = None
        self.timeRadioButton = None
        self.stringRadioButton = None
        self.messageRadioButton = None
        self.matrixRadioButton = None
        self.intArrayRadioButton = None
        self.doubleArrayRadioButton = None
        self.vectorArrayRadioButton = None
        self.pointArrayRadioButton = None
        self.stringArrayRadioButton = None
        self.nurbsCurveRadioButton = None
        self.nurbsSurfaceRadioButton = None
        self.meshRadioButton = None
        self.proxyWidget = None
        self.proxyLabel = None
        self.proxyLineEdit = None
        self.useProxyCheckBox = None
        
        self.numericRangeGroupBox = None
        self.numericValidator = None
        self.minimumWidget = None
        self.minimumLabel = None
        self.minimumLineEdit = None
        self.maximumWidget = None
        self.maximumLabel = None
        self.maximumLineEdit = None
        self.defaultWidget = None
        self.defaultLabel = None
        self.defaultLineEdit = None

        self.enumGroupBox = None
        self.fieldWidget = None
        self.fieldLabel = None
        self.fieldLineEdit = None
        self.fieldInteropWidget = None
        self.addFieldPushButton = None
        self.removeFieldPushButton = None
        self.fieldListWidget = None

        self.interopWidget = None
        self.addPushButton = None
        self.editDropDownButton = None
        self.editMenu = None
    # endregion

    # region Methods
    def postLoad(self, *args, **kwargs):
        """
        Called after the user interface has been loaded.

        :rtype: None
        """

        # Call parent method
        #
        super(QAttributesTab, self).postLoad(*args, **kwargs)

        # Initialize property button group
        #
        self.propertyButtonGroup = QtWidgets.QButtonGroup(self.propertiesWidget)
        self.propertyButtonGroup.setObjectName('propertyButtonGroup')
        self.propertyButtonGroup.setExclusive(True)
        self.propertyButtonGroup.addButton(self.keyableRadioButton, id=0)
        self.propertyButtonGroup.addButton(self.displayableRadioButton, id=1)
        self.propertyButtonGroup.addButton(self.hiddenRadioButton, id=2)

        # Initialize data type button group
        #
        self.dataTypeButtonGroup = QtWidgets.QButtonGroup(self.dataTypeGroupBox)
        self.dataTypeButtonGroup.setObjectName('dataTypeButtonGroup')
        self.dataTypeButtonGroup.setExclusive(True)
        self.dataTypeButtonGroup.addButton(self.booleanRadioButton, id=0)
        self.dataTypeButtonGroup.addButton(self.integerRadioButton, id=1)
        self.dataTypeButtonGroup.addButton(self.shortRadioButton, id=2)
        self.dataTypeButtonGroup.addButton(self.longRadioButton, id=3)
        self.dataTypeButtonGroup.addButton(self.byteRadioButton, id=4)
        self.dataTypeButtonGroup.addButton(self.characterRadioButton, id=5)
        self.dataTypeButtonGroup.addButton(self.addressRadioButton, id=6)
        self.dataTypeButtonGroup.addButton(self.enumRadioButton, id=7)
        self.dataTypeButtonGroup.addButton(self.floatRadioButton, id=8)
        self.dataTypeButtonGroup.addButton(self.doubleRadioButton, id=9)
        self.dataTypeButtonGroup.addButton(self.distanceRadioButton, id=10)
        self.dataTypeButtonGroup.addButton(self.angleRadioButton, id=11)
        self.dataTypeButtonGroup.addButton(self.timeRadioButton, id=12)
        self.dataTypeButtonGroup.addButton(self.stringRadioButton, id=13)
        self.dataTypeButtonGroup.addButton(self.messageRadioButton, id=14)
        self.dataTypeButtonGroup.addButton(self.matrixRadioButton, id=15)
        self.dataTypeButtonGroup.addButton(self.intArrayRadioButton, id=16)
        self.dataTypeButtonGroup.addButton(self.doubleArrayRadioButton, id=17)
        self.dataTypeButtonGroup.addButton(self.vectorArrayRadioButton, id=18)
        self.dataTypeButtonGroup.addButton(self.pointArrayRadioButton, id=19)
        self.dataTypeButtonGroup.addButton(self.stringArrayRadioButton, id=20)
        self.dataTypeButtonGroup.addButton(self.nurbsCurveRadioButton, id=21)
        self.dataTypeButtonGroup.addButton(self.nurbsSurfaceRadioButton, id=22)
        self.dataTypeButtonGroup.addButton(self.meshRadioButton, id=23)

        # Initialize text validators
        #
        self.numericValidator = QtGui.QDoubleValidator(-10000, 10000, 2, parent=self.numericRangeGroupBox)
        self.numericValidator.setObjectName('numericValidator')

        self.minimumLineEdit.setValidator(self.numericValidator)
        self.maximumLineEdit.setValidator(self.numericValidator)
        self.defaultLineEdit.setValidator(self.numericValidator)

        # Initialize edit menu
        #
        self.editMenu = QtWidgets.QMenu(parent=self.editDropDownButton)
        self.editMenu.setObjectName('editMenu')
        self.editMenu.aboutToShow.connect(self.on_editMenu_aboutToShow)

        self.editDropDownButton.setMenu(self.editMenu)

    def getDefinition(self):
        """
        Returns the current attribute definition.

        :rtype: Dict[str, Any]
        """

        # Get name parameters
        #
        longName = self.longNameLineEdit.text()
        definition = {}

        if not stringutils.isNullOrEmpty(longName):

            definition['longName'] = longName

        shortName = self.shortNameLineEdit.text()

        if not stringutils.isNullOrEmpty(shortName):

            definition['shortName'] = shortName

        niceName = self.niceNameLineEdit.text()
        niceNameEnabled = self.overrideNiceNameCheckBox.isChecked()

        if niceNameEnabled:

            definition['niceName'] = niceName

        # Check if proxies are enabled
        #
        useProxy = self.useProxyCheckBox.isChecked()

        if useProxy:

            definition['proxy'] = self.proxyLineEdit.text()

        else:

            # Get attribute parameters
            #
            checkedId = self.propertyButtonGroup.checkedId()

            definition['keyable'] = checkedId == 0
            definition['hidden'] = checkedId == 2
            definition['array'] = self.arrayCheckBox.isChecked()

            # Get attribute type
            #
            definition['attributeType'] = self.dataTypeButtonGroup.checkedButton().whatsThis()

            # Get numeric range
            #
            minValue = self.minimumLineEdit.text()

            if not stringutils.isNullOrEmpty(minValue):

                definition['min'] = stringutils.eval(minValue)

            maxValue = self.maximumLineEdit.text()

            if not stringutils.isNullOrEmpty(minValue):

                definition['max'] = stringutils.eval(maxValue)

            defaultValue = self.defaultLineEdit.text()

            if not stringutils.isNullOrEmpty(minValue):

                definition['default'] = stringutils.eval(defaultValue)

            # Get enum fields
            #
            fieldCount = self.fieldListWidget.count()
            fields = [self.fieldListWidget.item(row).text() for row in range(fieldCount)]

            if not stringutils.isNullOrEmpty(fields):

                definition['fields'] = fields

        return definition

    @undo(name='Add Attribute')
    def addAttribute(self, node, **kwargs):
        """
        Adds an attribute to the supplied node.

        :type node: mpynode.MPyNode
        :rtype: None
        """

        node.addAttr(**kwargs)

    @undo(name='Add Proxy Attribute')
    def addProxyAttribute(self, node, name, plug):
        """
        Adds a proxy attribute to the supplied node.

        :type node: mpynode.MPyNode
        :type name: str
        :type plug: om.MPlug
        :rtype: None
        """

        node.addProxyAttr(name, plug)

    @undo(name='Edit Attribute')
    def editAttribute(self, node, **kwargs):
        """
        Edits an attribute to the supplied node.

        :type node: mpynode.MPyNode
        :rtype: None
        """

        pass

    def invalidateDefinition(self, plug):
        """
        Refreshes the widgets using the supplied plug.

        :type plug: om.MPlug
        :rtype: None
        """

        # Update name widgets
        #
        attribute = plug.attribute()
        fnAttribute = om.MFnAttribute(attribute)

        self.longNameLineEdit.setText(fnAttribute.name)
        self.shortNameLineEdit.setText(fnAttribute.shortName)

        nodeName, attributeName = plug.info.split('.')
        niceName = mc.attributeQuery(attributeName, node=nodeName, niceName=True)

        self.niceNameLineEdit.setText(niceName)

        # Update property widgets
        #
        index = 0 if fnAttribute.keyable else 2 if fnAttribute.hidden else 1
        buttons = self.propertyButtonGroup.buttons()
        buttons[index].setChecked(True)

        self.arrayCheckBox.setChecked(fnAttribute.array)

        # Update data type widget
        #
        typeName = attributeutils.getAttributeTypeName(attribute)
        buttons = self.dataTypeButtonGroup.buttons()

        for button in buttons:

            if button.whatsThis() == typeName:

                button.setChecked(True)
                break

        # Update numeric range widgets
        #
        if attribute.hasFn(om.MFn.kNumericAttribute):

            fnNumericAttribute = om.MFnNumericAttribute(attribute)
            hasMin = fnNumericAttribute.hasMin()

            if hasMin:

                self.minimumLineEdit.setText(str(fnNumericAttribute.getMin()))

            hasMax = fnNumericAttribute.hasMax()

            if hasMax:

                self.maximumLineEdit.setText(str(fnNumericAttribute.getMax()))

            self.defaultLineEdit.setText(str(fnNumericAttribute.default))

        # Update field-name widgets
        #
        if attribute.hasFn(om.MFn.kEnumAttribute):

            fnEnumAttribute = om.MFnEnumAttribute(attribute)
            minValue, maxValue = fnEnumAttribute.getMin(), fnEnumAttribute.getMax()

            fieldNames = [fnEnumAttribute.fieldName(i) for i in inclusiveRange(minValue, maxValue)]
            self.fieldListWidget.addItems(fieldNames)
    # endregion

    # region Slots
    @QtCore.Slot(str)
    def on_fieldLineEdit_textChanged(self, text):
        """
        Slot method for the `fieldLineEdit` widget's `textChanged` signal.

        :type text: str
        :rtype: None
        """

        currentItem = self.fieldListWidget.currentItem()

        if currentItem is not None:

            currentItem.setText(text)

    @QtCore.Slot()
    def on_addFieldPushButton_clicked(self):
        """
        Slot method for the `addFieldPushButton` widget's `clicked` signal.

        :rtype: None
        """

        fieldName = self.fieldLineEdit.text()

        if not stringutils.isNullOrEmpty(fieldName):

            self.fieldListWidget.addItem(fieldName)

    @QtCore.Slot()
    def on_removeFieldPushButton_clicked(self):
        """
        Slot method for the `removeFieldPushButton` widget's `clicked` signal.

        :rtype: None
        """

        currentRow = self.fieldListWidget.currentRow()
        numRows = self.fieldListWidget.count()

        if 0 <= currentRow < numRows:

            self.fieldListWidget.takeItem(currentRow)

    @QtCore.Slot()
    def on_addPushButton_clicked(self):
        """
        Slot method for the `addPushButton` widget's `clicked` signal.

        :rtype: None
        """

        if self.selectedNode is None:

            log.warning('No node selected to add attribute to!')
            return

        kwargs = self.getDefinition()
        proxy = kwargs.get('proxy', None)

        if not stringutils.isNullOrEmpty(proxy):

            nodeName, plugPath = proxy.split('.')
            node = dagutils.getMObject(nodeName)
            plug = plugutils.findPlug(node, plugPath)
            longName = kwargs.get('longName', plug.partialName(useLongNames=True))

            self.addProxyAttribute(self.selectedNode, longName, plug)

        else:

            self.addAttribute(self.selectedNode, **kwargs)

    @QtCore.Slot()
    def on_editDropDownButton_clicked(self):
        """
        Slot method for the `editPushButton` widget's `clicked` signal.

        :rtype: None
        """

        pass

    @QtCore.Slot()
    def on_editAttributeAction_triggered(self):
        """
        Slot method for the `attributeAction` widget's `triggered` signal.

        :rtype: None
        """

        sender = self.sender()
        attributeName = sender.text()

        self.invalidateDefinition(self.selectedNode[attributeName])

    @QtCore.Slot()
    def on_editMenu_aboutToShow(self):
        """
        Slot method for the `editMenu` widget's `aboutToShow` signal.

        :rtype: None
        """

        sender = self.sender()
        sender.clear()

        if self.selectedNode is not None:

            for attribute in self.selectedNode.iterAttr(userDefined=True):

                action = QtWidgets.QAction(om.MFnAttribute(attribute).name, parent=sender)
                action.triggered.connect(self.on_editAttributeAction_triggered)

                sender.addAction(action)
    # endregion
