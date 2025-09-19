from maya import cmds as mc
from maya.api import OpenMaya as om
from Qt import QtCore, QtWidgets, QtGui
from dcc.python import stringutils
from dcc.ui import qdropdownbutton, qdivider
from dcc.maya.libs import attributeutils, plugutils, dagutils
from dcc.maya.decorators import undo
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
    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        # Call parent method
        #
        super(QAttributesTab, self).__setup_ui__(*args, **kwargs)

        # Initialize central layout
        #
        centralLayout = QtWidgets.QVBoxLayout()
        centralLayout.setObjectName('centralLayout')

        self.setLayout(centralLayout)

        # Initialize name group-box
        #
        self.nameLayout = QtWidgets.QGridLayout()
        self.nameLayout.setObjectName('nameLayout')

        self.nameGroupBox = QtWidgets.QGroupBox('Name:')
        self.nameGroupBox.setObjectName('nameGroupBox')
        self.nameGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.nameGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.nameGroupBox.setLayout(self.nameLayout)

        self.longNameLabel = QtWidgets.QLabel('Long Name:')
        self.longNameLabel.setObjectName('longNameLabel')
        self.longNameLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.longNameLabel.setFixedSize(QtCore.QSize(70, 24))
        self.longNameLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.longNameLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.longNameLineEdit = QtWidgets.QLineEdit()
        self.longNameLineEdit.setObjectName('longNameLineEdit')
        self.longNameLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.longNameLineEdit.setFixedHeight(24)
        self.longNameLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)

        self.longNameLayout = QtWidgets.QHBoxLayout()
        self.longNameLayout.setObjectName('attributeNameLayout')
        self.longNameLayout.setContentsMargins(0, 0, 0, 0)
        self.longNameLayout.addWidget(self.longNameLabel)
        self.longNameLayout.addWidget(self.longNameLineEdit)

        self.shortNameLabel = QtWidgets.QLabel('Short Name:')
        self.shortNameLabel.setObjectName('shortNameLabel')
        self.shortNameLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.shortNameLabel.setFixedSize(QtCore.QSize(70, 24))
        self.shortNameLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.shortNameLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        
        self.shortNameLineEdit = QtWidgets.QLineEdit()
        self.shortNameLineEdit.setObjectName('shortNameLineEdit')
        self.shortNameLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.shortNameLineEdit.setFixedHeight(24)
        self.shortNameLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)

        self.shortNameLayout = QtWidgets.QHBoxLayout()
        self.shortNameLayout.setObjectName('shortNameLayout')
        self.shortNameLayout.setContentsMargins(0, 0, 0, 0)
        self.shortNameLayout.addWidget(self.shortNameLabel)
        self.shortNameLayout.addWidget(self.shortNameLineEdit)

        self.niceNameLabel = QtWidgets.QLabel('Nice Name:')
        self.niceNameLabel.setObjectName('niceNameLabel')
        self.niceNameLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.niceNameLabel.setFixedSize(QtCore.QSize(70, 24))
        self.niceNameLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.niceNameLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        
        self.niceNameLineEdit = QtWidgets.QLineEdit()
        self.niceNameLineEdit.setObjectName('niceNameLineEdit')
        self.niceNameLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.niceNameLineEdit.setFixedHeight(24)
        self.niceNameLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.niceNameLineEdit.setPlaceholderText('Enter Display Name')
        self.niceNameLineEdit.setEnabled(False)
        
        self.overrideNiceNameCheckBox = QtWidgets.QCheckBox('Override Nice Name')
        self.overrideNiceNameCheckBox.setObjectName('overrideNiceNameCheckBox')
        self.overrideNiceNameCheckBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.overrideNiceNameCheckBox.setFixedHeight(24)
        self.overrideNiceNameCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.overrideNiceNameCheckBox.toggled.connect(self.niceNameLineEdit.setEnabled)
        
        self.niceNameLayout = QtWidgets.QHBoxLayout()
        self.niceNameLayout.setObjectName('niceNameLayout')
        self.niceNameLayout.setContentsMargins(0, 0, 0, 0)
        self.niceNameLayout.addWidget(self.niceNameLabel)
        self.niceNameLayout.addWidget(self.niceNameLineEdit)
        self.niceNameLayout.addWidget(self.overrideNiceNameCheckBox)

        self.propertiesLabel = QtWidgets.QLabel('Properties:')
        self.propertiesLabel.setObjectName('propertiesLabel')
        self.propertiesLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.propertiesLabel.setFixedSize(QtCore.QSize(70, 24))
        self.propertiesLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.propertiesLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.keyableRadioButton = QtWidgets.QRadioButton('Keyable')
        self.keyableRadioButton.setObjectName('keyableRadiobutton')
        self.keyableRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.keyableRadioButton.setFixedHeight(24)
        self.keyableRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.keyableRadioButton.setChecked(True)
        
        self.displayableRadioButton = QtWidgets.QRadioButton('Displayable')
        self.displayableRadioButton.setObjectName('displayableRadioButton')
        self.displayableRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.displayableRadioButton.setFixedHeight(24)
        self.displayableRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.displayableRadioButton.setChecked(True)
        
        self.hiddenRadioButton = QtWidgets.QRadioButton('Hidden')
        self.hiddenRadioButton.setObjectName('hiddenRadioButton')
        self.hiddenRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.hiddenRadioButton.setFixedHeight(24)
        self.hiddenRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.hiddenRadioButton.setChecked(True)
        
        self.arrayCheckBox = QtWidgets.QCheckBox('Array')
        self.arrayCheckBox.setObjectName('arrayCheckBox')
        self.arrayCheckBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.arrayCheckBox.setFixedHeight(24)
        self.arrayCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)

        self.propertyButtonGroup = QtWidgets.QButtonGroup(self.nameGroupBox)
        self.propertyButtonGroup.setObjectName('propertyButtonGroup')
        self.propertyButtonGroup.setExclusive(True)
        self.propertyButtonGroup.addButton(self.keyableRadioButton, id=0)
        self.propertyButtonGroup.addButton(self.displayableRadioButton, id=1)
        self.propertyButtonGroup.addButton(self.hiddenRadioButton, id=2)

        self.propertiesLayout = QtWidgets.QHBoxLayout()
        self.propertiesLayout.setObjectName('propertiesLayout')
        self.propertiesLayout.setContentsMargins(0, 0, 0, 0)
        self.propertiesLayout.addWidget(self.propertiesLabel)
        self.propertiesLayout.addWidget(self.keyableRadioButton, alignment=QtCore.Qt.AlignCenter)
        self.propertiesLayout.addWidget(self.displayableRadioButton, alignment=QtCore.Qt.AlignCenter)
        self.propertiesLayout.addWidget(self.hiddenRadioButton, alignment=QtCore.Qt.AlignCenter)
        self.propertiesLayout.addWidget(qdivider.QDivider(QtCore.Qt.Vertical))
        self.propertiesLayout.addWidget(self.arrayCheckBox)
        
        self.nameLayout.addLayout(self.longNameLayout, 0, 0)
        self.nameLayout.addLayout(self.shortNameLayout, 0, 1)
        self.nameLayout.addLayout(self.niceNameLayout, 1, 0, 1, 2)
        self.nameLayout.addLayout(self.propertiesLayout, 2, 0, 1, 2)

        centralLayout.addWidget(self.nameGroupBox)

        # Initialize data type group-box
        #
        self.dataTypeLayout = QtWidgets.QGridLayout()
        self.dataTypeLayout.setObjectName('dataTypeLayout')

        self.dataTypeGroupBox = QtWidgets.QGroupBox('Data Type:')
        self.dataTypeGroupBox.setObjectName('dataTypeGroupBox')
        self.dataTypeGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.dataTypeGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.dataTypeGroupBox.setLayout(self.dataTypeLayout)

        self.booleanRadioButton = QtWidgets.QRadioButton('Boolean')
        self.booleanRadioButton.setObjectName('booleanRadioButton')
        self.booleanRadioButton.setWhatsThis('')
        self.booleanRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.booleanRadioButton.setFixedHeight(24)
        self.booleanRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.booleanRadioButton.setChecked(True)

        self.integerRadioButton = QtWidgets.QRadioButton('Integer')
        self.integerRadioButton.setObjectName('integerRadioButton')
        self.integerRadioButton.setWhatsThis('int')
        self.integerRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.integerRadioButton.setFixedHeight(24)
        self.integerRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.shortRadioButton = QtWidgets.QRadioButton('Short')
        self.shortRadioButton.setObjectName('shortRadioButton')
        self.shortRadioButton.setWhatsThis('short')
        self.shortRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.shortRadioButton.setFixedHeight(24)
        self.shortRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.longRadioButton = QtWidgets.QRadioButton('Long')
        self.longRadioButton.setObjectName('longRadioButton')
        self.longRadioButton.setWhatsThis('long')
        self.longRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.longRadioButton.setFixedHeight(24)
        self.longRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.byteRadioButton = QtWidgets.QRadioButton('Byte')
        self.byteRadioButton.setObjectName('byteRadioButton')
        self.byteRadioButton.setWhatsThis('byte')
        self.byteRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.byteRadioButton.setFixedHeight(24)
        self.byteRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.characterRadioButton = QtWidgets.QRadioButton('Character')
        self.characterRadioButton.setObjectName('characterRadioButton')
        self.characterRadioButton.setWhatsThis('char')
        self.characterRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.characterRadioButton.setFixedHeight(24)
        self.characterRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.addressRadioButton = QtWidgets.QRadioButton('Address')
        self.addressRadioButton.setObjectName('addressRadioButton')
        self.addressRadioButton.setWhatsThis('addr')
        self.addressRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.addressRadioButton.setFixedHeight(24)
        self.addressRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.enumRadioButton = QtWidgets.QRadioButton('Enum')
        self.enumRadioButton.setObjectName('enumRadioButton')
        self.enumRadioButton.setWhatsThis('enum')
        self.enumRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.enumRadioButton.setFixedHeight(24)
        self.enumRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.floatRadioButton = QtWidgets.QRadioButton('Float')
        self.floatRadioButton.setObjectName('floatRadioButton')
        self.floatRadioButton.setWhatsThis('float')
        self.floatRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.floatRadioButton.setFixedHeight(24)
        self.floatRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.doubleRadioButton = QtWidgets.QRadioButton('Double')
        self.doubleRadioButton.setObjectName('doubleRadioButton')
        self.doubleRadioButton.setWhatsThis('double')
        self.doubleRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.doubleRadioButton.setFixedHeight(24)
        self.doubleRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.distanceRadioButton = QtWidgets.QRadioButton('Distance')
        self.distanceRadioButton.setObjectName('distanceRadioButton')
        self.distanceRadioButton.setWhatsThis('doubleLinear')
        self.distanceRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.distanceRadioButton.setFixedHeight(24)
        self.distanceRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.angleRadioButton = QtWidgets.QRadioButton('Angle')
        self.angleRadioButton.setObjectName('angleRadioButton')
        self.angleRadioButton.setWhatsThis('doubleAngle')
        self.angleRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.angleRadioButton.setFixedHeight(24)
        self.angleRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.timeRadioButton = QtWidgets.QRadioButton('Time')
        self.timeRadioButton.setObjectName('timeRadioButton')
        self.timeRadioButton.setWhatsThis('time')
        self.timeRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.timeRadioButton.setFixedHeight(24)
        self.timeRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.stringRadioButton = QtWidgets.QRadioButton('String')
        self.stringRadioButton.setObjectName('stringRadioButton')
        self.stringRadioButton.setWhatsThis('str')
        self.stringRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.stringRadioButton.setFixedHeight(24)
        self.stringRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.messageRadioButton = QtWidgets.QRadioButton('Message')
        self.messageRadioButton.setObjectName('messageRadioButton')
        self.messageRadioButton.setWhatsThis('message')
        self.messageRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.messageRadioButton.setFixedHeight(24)
        self.messageRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.matrixRadioButton = QtWidgets.QRadioButton('Matrix')
        self.matrixRadioButton.setObjectName('matrixRadioButton')
        self.matrixRadioButton.setWhatsThis('matrix')
        self.matrixRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.matrixRadioButton.setFixedHeight(24)
        self.matrixRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.intArrayRadioButton = QtWidgets.QRadioButton('Int Array')
        self.intArrayRadioButton.setObjectName('intArrayRadioButton')
        self.intArrayRadioButton.setWhatsThis('intArray')
        self.intArrayRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.intArrayRadioButton.setFixedHeight(24)
        self.intArrayRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.doubleArrayRadioButton = QtWidgets.QRadioButton('Double Array')
        self.doubleArrayRadioButton.setObjectName('doubleArrayRadioButton')
        self.doubleArrayRadioButton.setWhatsThis('doubleArray')
        self.doubleArrayRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.doubleArrayRadioButton.setFixedHeight(24)
        self.doubleArrayRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.vectorArrayRadioButton = QtWidgets.QRadioButton('Vector Array')
        self.vectorArrayRadioButton.setObjectName('vectorArrayRadioButton')
        self.vectorArrayRadioButton.setWhatsThis('vectorArray')
        self.vectorArrayRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.vectorArrayRadioButton.setFixedHeight(24)
        self.vectorArrayRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.pointArrayRadioButton = QtWidgets.QRadioButton('Point Array')
        self.pointArrayRadioButton.setObjectName('pointArrayRadioButton')
        self.pointArrayRadioButton.setWhatsThis('pointArray')
        self.pointArrayRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.pointArrayRadioButton.setFixedHeight(24)
        self.pointArrayRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.stringArrayRadioButton = QtWidgets.QRadioButton('String Array')
        self.stringArrayRadioButton.setObjectName('stringArrayRadioButton')
        self.stringArrayRadioButton.setWhatsThis('stringArray')
        self.stringArrayRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.stringArrayRadioButton.setFixedHeight(24)
        self.stringArrayRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.nurbsCurveRadioButton = QtWidgets.QRadioButton('Nurbs Curve')
        self.nurbsCurveRadioButton.setObjectName('nurbsCurveRadioButton')
        self.nurbsCurveRadioButton.setWhatsThis('nurbsCurve')
        self.nurbsCurveRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.nurbsCurveRadioButton.setFixedHeight(24)
        self.nurbsCurveRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.nurbsSurfaceRadioButton = QtWidgets.QRadioButton('Nurbs Surface')
        self.nurbsSurfaceRadioButton.setObjectName('nurbsSurfaceRadioButton')
        self.nurbsSurfaceRadioButton.setWhatsThis('nurbsSurface')
        self.nurbsSurfaceRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.nurbsSurfaceRadioButton.setFixedHeight(24)
        self.nurbsSurfaceRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.meshRadioButton = QtWidgets.QRadioButton('Mesh')
        self.meshRadioButton.setObjectName('meshRadioButton')
        self.meshRadioButton.setWhatsThis('mesh')
        self.meshRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.meshRadioButton.setFixedHeight(24)
        self.meshRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)
        
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

        self.proxyLabel = QtWidgets.QLabel('Proxy Name:')
        self.proxyLabel.setObjectName('proxyLabel')
        self.proxyLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.proxyLabel.setFixedSize(QtCore.QSize(70, 24))
        self.proxyLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.proxyLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.proxyLineEdit = QtWidgets.QLineEdit()
        self.proxyLineEdit.setObjectName('proxyLineEdit')
        self.proxyLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.proxyLineEdit.setFixedHeight(24)
        self.proxyLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.proxyLineEdit.setPlaceholderText('Enter Node and Attribute Name')
        self.proxyLineEdit.setEnabled(False)

        self.useProxyCheckBox = QtWidgets.QCheckBox('Use Proxy')
        self.useProxyCheckBox.setObjectName('useProxyCheckBox')
        self.useProxyCheckBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.useProxyCheckBox.setFixedHeight(24)
        self.useProxyCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.useProxyCheckBox.toggled.connect(self.proxyLineEdit.setEnabled)

        self.proxyLayout = QtWidgets.QHBoxLayout()
        self.proxyLayout.setObjectName('proxyLayout')
        self.proxyLayout.setContentsMargins(0, 0, 0, 0)
        self.proxyLayout.addWidget(self.proxyLabel)
        self.proxyLayout.addWidget(self.proxyLineEdit)
        self.proxyLayout.addWidget(self.useProxyCheckBox)

        self.dataTypeLayout.addWidget(self.booleanRadioButton, 0, 0)
        self.dataTypeLayout.addWidget(self.integerRadioButton, 0, 1)
        self.dataTypeLayout.addWidget(self.shortRadioButton, 0, 2)
        self.dataTypeLayout.addWidget(self.longRadioButton, 0, 3)
        self.dataTypeLayout.addWidget(self.byteRadioButton, 1, 0)
        self.dataTypeLayout.addWidget(self.characterRadioButton, 1, 1)
        self.dataTypeLayout.addWidget(self.addressRadioButton, 1, 2)
        self.dataTypeLayout.addWidget(self.enumRadioButton, 1, 3)
        self.dataTypeLayout.addWidget(self.floatRadioButton, 2, 0)
        self.dataTypeLayout.addWidget(self.doubleRadioButton, 2, 1)
        self.dataTypeLayout.addWidget(self.distanceRadioButton, 2, 2)
        self.dataTypeLayout.addWidget(self.angleRadioButton, 2, 3)
        self.dataTypeLayout.addWidget(self.timeRadioButton, 3, 0)
        self.dataTypeLayout.addWidget(self.stringRadioButton, 3, 1)
        self.dataTypeLayout.addWidget(self.messageRadioButton, 3, 2)
        self.dataTypeLayout.addWidget(self.matrixRadioButton, 3, 3)
        self.dataTypeLayout.addWidget(self.intArrayRadioButton, 4, 0)
        self.dataTypeLayout.addWidget(self.doubleArrayRadioButton, 4, 1)
        self.dataTypeLayout.addWidget(self.vectorArrayRadioButton, 4, 2)
        self.dataTypeLayout.addWidget(self.pointArrayRadioButton, 4, 3)
        self.dataTypeLayout.addWidget(self.stringArrayRadioButton, 5, 0)
        self.dataTypeLayout.addWidget(self.nurbsCurveRadioButton, 5, 1)
        self.dataTypeLayout.addWidget(self.nurbsSurfaceRadioButton, 5, 2)
        self.dataTypeLayout.addWidget(self.meshRadioButton, 5, 3)
        self.dataTypeLayout.addWidget(qdivider.QDivider(QtCore.Qt.Horizontal), 6, 0, 1, 4)
        self.dataTypeLayout.addLayout(self.proxyLayout, 7, 0, 1, 4)

        centralLayout.addWidget(self.dataTypeGroupBox)
        
        # Initialize numeric range group-box
        #
        self.rangeLayout = QtWidgets.QGridLayout()
        self.rangeLayout.setObjectName('rangeLayout')

        self.rangeGroupBox = QtWidgets.QGroupBox('Numeric Range:')
        self.rangeGroupBox.setObjectName('rangeGroupBox')
        self.rangeGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.rangeGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.rangeGroupBox.setLayout(self.rangeLayout)

        self.numericValidator = QtGui.QDoubleValidator(-10000, 10000, 2, parent=self.rangeGroupBox)
        self.numericValidator.setObjectName('numericValidator')

        self.minimumLabel = QtWidgets.QLabel('Minimum:')
        self.minimumLabel.setObjectName('minimumLabel')
        self.minimumLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.minimumLabel.setFixedSize(QtCore.QSize(70, 24))
        self.minimumLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.minimumLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.minimumLineEdit = QtWidgets.QLineEdit()
        self.minimumLineEdit.setObjectName('minimumLineEdit')
        self.minimumLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.minimumLineEdit.setFixedHeight(24)
        self.minimumLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.minimumLineEdit.setValidator(self.numericValidator)

        self.minimumLayout = QtWidgets.QHBoxLayout()
        self.minimumLayout.setObjectName('minimumLayout')
        self.minimumLayout.setContentsMargins(0, 0, 0, 0)
        self.minimumLayout.addWidget(self.minimumLabel)
        self.minimumLayout.addWidget(self.minimumLineEdit)
        
        self.maximumLabel = QtWidgets.QLabel('Maximum:')
        self.maximumLabel.setObjectName('maximumLabel')
        self.maximumLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.maximumLabel.setFixedSize(QtCore.QSize(70, 24))
        self.maximumLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.maximumLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.maximumLineEdit = QtWidgets.QLineEdit()
        self.maximumLineEdit.setObjectName('maximumLineEdit')
        self.maximumLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.maximumLineEdit.setFixedHeight(24)
        self.maximumLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.maximumLineEdit.setValidator(self.numericValidator)

        self.maximumLayout = QtWidgets.QHBoxLayout()
        self.maximumLayout.setObjectName('maximumLayout')
        self.maximumLayout.setContentsMargins(0, 0, 0, 0)
        self.maximumLayout.addWidget(self.maximumLabel)
        self.maximumLayout.addWidget(self.maximumLineEdit)

        self.defaultLabel = QtWidgets.QLabel('Default:')
        self.defaultLabel.setObjectName('defaultLabel')
        self.defaultLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.defaultLabel.setFixedSize(QtCore.QSize(70, 24))
        self.defaultLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.defaultLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.defaultLineEdit = QtWidgets.QLineEdit()
        self.defaultLineEdit.setObjectName('defaultLineEdit')
        self.defaultLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.defaultLineEdit.setFixedHeight(24)
        self.defaultLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.defaultLineEdit.setValidator(self.numericValidator)

        self.defaultLayout = QtWidgets.QHBoxLayout()
        self.defaultLayout.setObjectName('defaultLayout')
        self.defaultLayout.setContentsMargins(0, 0, 0, 0)
        self.defaultLayout.addWidget(self.defaultLabel)
        self.defaultLayout.addWidget(self.defaultLineEdit)

        self.rangeLayout.addLayout(self.minimumLayout, 0, 0)
        self.rangeLayout.addLayout(self.maximumLayout, 0, 1)
        self.rangeLayout.addLayout(self.defaultLayout, 1, 0, 1, 2)
        
        centralLayout.addWidget(self.rangeGroupBox)
        
        # Initialize enum group-box
        #
        self.enumLayout = QtWidgets.QVBoxLayout()
        self.enumLayout.setObjectName('enumLayout')

        self.enumGroupBox = QtWidgets.QGroupBox('Enum Fields:')
        self.enumGroupBox.setObjectName('enumGroupBox')
        self.enumGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.enumGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.enumGroupBox.setLayout(self.enumLayout)

        self.addFieldPushButton = QtWidgets.QPushButton('+')
        self.addFieldPushButton.setObjectName('addFieldPushButton')
        self.addFieldPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.addFieldPushButton.setFixedSize(QtCore.QSize(24, 24))
        self.addFieldPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.addFieldPushButton.setEnabled(False)
        self.addFieldPushButton.clicked.connect(self.on_addFieldPushButton_clicked)

        self.removeFieldPushButton = QtWidgets.QPushButton('-')
        self.removeFieldPushButton.setObjectName('removeFieldPushButton')
        self.removeFieldPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.removeFieldPushButton.setFixedSize(QtCore.QSize(24, 24))
        self.removeFieldPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.removeFieldPushButton.setEnabled(False)
        self.removeFieldPushButton.clicked.connect(self.on_removeFieldPushButton_clicked)

        self.fieldButtonsLayout = QtWidgets.QHBoxLayout()
        self.fieldButtonsLayout.setObjectName('fieldButtonsLayout')
        self.fieldButtonsLayout.setContentsMargins(0, 0, 0, 0)
        self.fieldButtonsLayout.setSpacing(1)
        self.fieldButtonsLayout.addWidget(self.addFieldPushButton)
        self.fieldButtonsLayout.addWidget(self.removeFieldPushButton)

        self.fieldNameLabel = QtWidgets.QLabel('Field Name:')
        self.fieldNameLabel.setObjectName('fieldNameLabel')
        self.fieldNameLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.fieldNameLabel.setFixedSize(QtCore.QSize(70, 24))
        self.fieldNameLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.fieldNameLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.fieldNameLineEdit = QtWidgets.QLineEdit()
        self.fieldNameLineEdit.setObjectName('fieldNameLineEdit')
        self.fieldNameLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.fieldNameLineEdit.setFixedHeight(24)
        self.fieldNameLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.fieldNameLineEdit.setPlaceholderText('Enter Field Name')
        self.fieldNameLineEdit.setEnabled(False)
        self.fieldNameLineEdit.textChanged.connect(self.on_fieldLineEdit_textChanged)

        self.fieldNameLayout = QtWidgets.QHBoxLayout()
        self.fieldNameLayout.setObjectName('fieldNameLayout')
        self.fieldNameLayout.setContentsMargins(0, 0, 0, 0)
        self.fieldNameLayout.addWidget(self.fieldNameLabel)
        self.fieldNameLayout.addWidget(self.fieldNameLineEdit)
        self.fieldNameLayout.addLayout(self.fieldButtonsLayout)

        self.fieldListWidget = QtWidgets.QListWidget()
        self.fieldListWidget.setObjectName('fieldListWidget')
        self.fieldListWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.fieldListWidget.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.fieldListWidget.setStyleSheet('QListWidget::item { height: 24px; }')
        self.fieldListWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.fieldListWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.fieldListWidget.setDragEnabled(False)
        self.fieldListWidget.setDragDropOverwriteMode(False)
        self.fieldListWidget.setDragDropMode(QtWidgets.QAbstractItemView.NoDragDrop)
        self.fieldListWidget.setDefaultDropAction(QtCore.Qt.IgnoreAction)
        self.fieldListWidget.setAlternatingRowColors(True)
        self.fieldListWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.fieldListWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        self.enumRadioButton.toggled.connect(self.fieldNameLineEdit.setEnabled)
        self.enumRadioButton.toggled.connect(self.addFieldPushButton.setEnabled)
        self.enumRadioButton.toggled.connect(self.removeFieldPushButton.setEnabled)

        self.enumLayout.addLayout(self.fieldNameLayout)
        self.enumLayout.addWidget(self.fieldListWidget)

        centralLayout.addWidget(self.enumGroupBox)
        
        # Initialize buttons layout
        #
        self.addPushButton = QtWidgets.QPushButton('Add')
        self.addPushButton.setObjectName('addPushButton')
        self.addPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.addPushButton.setFixedHeight(24)
        self.addPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.addPushButton.clicked.connect(self.on_addPushButton_clicked)
        
        self.editDropDownButton = qdropdownbutton.QDropDownButton('Edit')
        self.editDropDownButton.setObjectName('editDropDownButton')
        self.editDropDownButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.editDropDownButton.setFixedHeight(24)
        self.editDropDownButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.editDropDownButton.clicked.connect(self.on_editDropDownButton_clicked)
        
        self.buttonsLayout = QtWidgets.QHBoxLayout()
        self.buttonsLayout.setObjectName('buttonsLayout')
        self.buttonsLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonsLayout.addWidget(self.addPushButton)
        self.buttonsLayout.addWidget(self.editDropDownButton)

        self.editMenu = QtWidgets.QMenu(parent=self.editDropDownButton)
        self.editMenu.setObjectName('editMenu')
        self.editMenu.aboutToShow.connect(self.on_editMenu_aboutToShow)

        self.editDropDownButton.setMenu(self.editMenu)

        centralLayout.addLayout(self.buttonsLayout)
    # endregion

    # region Methods
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

    @undo.Undo(name='Add Attribute')
    def addAttribute(self, node, **kwargs):
        """
        Adds an attribute to the supplied node.

        :type node: mpynode.MPyNode
        :rtype: None
        """

        node.addAttr(**kwargs)

    @undo.Undo(name='Add Proxy Attribute')
    def addProxyAttribute(self, node, name, plug):
        """
        Adds a proxy attribute to the supplied node.

        :type node: mpynode.MPyNode
        :type name: str
        :type plug: om.MPlug
        :rtype: None
        """

        node.addProxyAttr(name, plug)

    @undo.Undo(name='Edit Attribute')
    def editAttribute(self, node, **kwargs):
        """
        Edits an attribute to the supplied node.

        :type node: mpynode.MPyNode
        :rtype: None
        """

        # Check if attribute exists
        #
        nodeName = node.name()
        attributeName = kwargs['longName']

        if not node.hasAttr(attributeName):

            log.warning(f'Unable to locate "{nodeName}.{attributeName}" attribute to edit!')
            return

        # Edit attribute properties
        #
        attribute = node.attribute(longName)
        fnAttribute = om.MFnAttribute(attribute)

        keyable = self.keyableRadioButton.isChecked()
        channelBox = self.displayableRadioButton.isChecked()
        hidden = self.hiddenRadioButton.isChecked()

        if keyable:

            fnAttribute.hidden = False
            fnAttribute.channelBox = False
            fnAttribute.keyable = keyable

        elif channelBox:

            fnAttribute.keyable = False
            fnAttribute.channelBox = True
            fnAttribute.hidden = False

        elif hidden:

            fnAttribute.keyable = False
            fnAttribute.channelBox = False
            fnAttribute.hidden = True

        else:

            pass

        # Check if attribute ranges require editing
        #
        attribute = node.attribute(longName)

        isNumeric = attribute.hasFn(om.MFn.kNumericAttribute)
        isUnit = attribute.hasFn(om.MFn.kUnitAttribute)

        if isNumeric:

            fnAttribute = om.MFnNumericAttribute(attribute)
            minimum = self.minimumLineEdit.text()

            if not stringutils.isNullOrEmpty(minimum):

                fnAttribute.setMin(stringutils.eval(minimum))

            maximum = self.maximumLineEdit.text()

            if not stringutils.isNullOrEmpty(maximum):

                fnAttribute.setMax(stringutils.eval(maximum))

            default = self.defaultLineEdit.text()

            if not stringutils.isNullOrEmpty(default):

                fnAttribute.default = stringutils.eval(default)

        elif isUnit:

            fnAttribute = om.MFnUnitAttribute(attribute)
            unitType = fnAttribute.unitType()
            cls = om.MDistance if (unitType == om.MFnUnitAttribute.kDistance) else om.MAngle if (unitType == om.MFnUnitAttribute.kAngle) else om.MTime

            minimum = self.minimumLineEdit.text()

            if not stringutils.isNullOrEmpty(minimum):

                fnAttribute.setMin(cls.uiToInternal(stringutils.eval(minimum)))

            maximum = self.maximumLineEdit.text()

            if not stringutils.isNullOrEmpty(maximum):

                fnAttribute.setMax(cls.uiToInternal(stringutils.eval(maximum)))

            default = self.defaultLineEdit.text()

            if not stringutils.isNullOrEmpty(default):

                fnAttribute.default = cls(stringutils.eval(default), unit=cls.uiUnit())

        else:

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
        isNumeric = attribute.hasFn(om.MFn.kNumericAttribute)
        isUnit = attribute.hasFn(om.MFn.kUnitAttribute)

        if isNumeric:

            fnAttribute = om.MFnNumericAttribute(attribute)
            hasMin = fnAttribute.hasMin()

            if hasMin:

                self.minimumLineEdit.setText(str(fnAttribute.getMin()))

            hasMax = fnAttribute.hasMax()

            if hasMax:

                self.maximumLineEdit.setText(str(fnAttribute.getMax()))

            self.defaultLineEdit.setText(str(fnAttribute.default))

        elif isUnit:

            fnAttribute = om.MFnUnitAttribute(attribute)
            unitType = fnAttribute.unitType()
            cls = om.MDistance if (unitType == om.MFnUnitAttribute.kDistance) else om.MAngle if (unitType == om.MFnUnitAttribute.kAngle) else om.MTime

            hasMin = fnAttribute.hasMin()

            if hasMin:

                self.minimumLineEdit.setText(str(fnAttribute.getMin().asUnits(cls.uiUnit())))

            hasMax = fnAttribute.hasMax()

            if hasMax:

                self.maximumLineEdit.setText(str(fnAttribute.getMax().asUnits(cls.uiUnit())))

            self.defaultLineEdit.setText(str(fnAttribute.default.asUnits(cls.uiUnit())))

        else:

            pass

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

        if self.selectedNode is None:

            log.warning('No node selected to edit attribute on!')
            return

        kwargs = self.getDefinition()
        self.editAttribute(self.selectedNode, **kwargs)

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
