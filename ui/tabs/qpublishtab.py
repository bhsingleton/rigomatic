import os
import re
import math
import pyperclip

from maya import cmds as mc
from maya.api import OpenMaya as om
from Qt import QtCore, QtWidgets, QtGui
from collections import defaultdict
from scipy.spatial import cKDTree
from dcc.python import stringutils, pathutils
from dcc.fbx.libs import fbxio
from dcc.generators.consecutivepairs import consecutivePairs
from dcc.maya.libs import attributeutils, plugutils, plugmutators
from . import qabstracttab

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QPublishTab(qabstracttab.QAbstractTab):
    """
    Overload of `QAbstractTab` that validates rigs before publishing.
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
        super(QPublishTab, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._fbxIO = fbxio.FbxIO().weakReference()
        self._shapeRegex = re.compile(r'^[a-zA-Z0-9_]+Shape[0-9]*$')

        self._textureErrors = []
        self._referenceErrors = []
        self._nodeNameErrors = []
        self._animatableNodeErrors = []
        self._staticMeshErrors = []
        self._skeletalMeshErrors = []

        # Declare public variables
        #
        self.logTextEdit = None  # type: QtWidgets:QTextEdit
        self.interopWidget = None
        self.sceneSettingsCheckBox = None
        self.fbxSettingsCheckBox = None
        self.texturePathsCheckBox = None
        self.nonUniqueNamesCheckBox = None
        self.animatableNodesCheckBox = None
        self.referencePathsCheckBox = None
        self.staticMeshesCheckBox = None
        self.skeletalMeshesCheckBox = None
        self.checkPushButton = None
        self.fixPushButton = None
    # endregion

    # region Properties
    @property
    def fbxIO(self):
        """
        Returns the FBX interface.

        :rtype: fbxio.FbxIO
        """

        return self._fbxIO()
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
        super(QPublishTab, self).loadSettings(settings)

        # Load check box settings
        #
        checkBoxes = self.interopWidget.findChildren(QtWidgets.QCheckBox)

        for checkBox in checkBoxes:

            checkBox.setChecked(bool(settings.value(f'tabs/publish/{checkBox.objectName()}', defaultValue=1)))

    def saveSettings(self, settings):
        """
        Saves the user settings.

        :type settings: QtCore.QSettings
        :rtype: None
        """

        # Call parent method
        #
        super(QPublishTab, self).saveSettings(settings)

        # Save check box settings
        #
        checkBoxes = self.interopWidget.findChildren(QtWidgets.QCheckBox)

        for checkBox in checkBoxes:

            settings.setValue(f'tabs/publish/{checkBox.objectName()}', int(checkBox.isChecked()))

    def info(self, text):
        """
        Prints information to the logging widget.

        :type text: str
        :rtype: None
        """

        self.logTextEdit.insertHtml(f'<p style="font-size:14px;">{text}<br></p>')

    def success(self, text):
        """
        Prints a success prompt to the logging widget.

        :type text: str
        :rtype: None
        """

        self.logTextEdit.insertHtml(f'<p style="font-size:14px; color:green;">{text}<br><br></p>')

    def warning(self, text):
        """
        Prints a warning to the logging widget.

        :type text: str
        :rtype: None
        """

        self.logTextEdit.insertHtml(f'<p style="font-size:14px; color:orange;">{text}<br></p>')

    def error(self, text):
        """
        Prints an error to the logging widget.

        :type text: str
        :rtype: None
        """

        self.logTextEdit.insertHtml(f'<p style="font-size:14px; color:red;">{text}<br><br></p>')

    def newline(self):
        """
        Prints a newline to the logging widget.

        :rtype: None
        """

        self.logTextEdit.insertHtml('<p><br></p>')

    def clear(self):
        """
        Clears the log widget.

        :rtype: None
        """

        self.logTextEdit.clear()

    def iterAnimatableNodes(self):
        """
        Returns a generator that yields animatable nodes.

        :rtype: Iterator[mpynode.MPyNode]
        """

        # Iterate through transforms
        #
        for node in self.scene.iterNodesByApiType(om.MFn.kTransform):

            # Check if node is referenced
            #
            if node.isFromReferencedFile:

                continue

            # Check if node is selectable
            #
            shapes = [shape for shape in node.iterShapes() if not shape.hasFn(om.MFn.kMesh)]
            shapeCount = len(shapes)

            isVisible = any([shape.isVisible() and shape.isSelectable() for shape in shapes])

            if isVisible and shapeCount > 0:

                yield node

            else:

                continue

    def iterStaticMeshes(self):
        """
        Returns a generator that yields static meshes.

        :rtype: Iterator[mpynode.MPyNode]
        """

        # Iterate through meshes
        #
        for mesh in self.scene.iterNodesByApiType(om.MFn.kMesh):

            # Check if mesh is referenced
            #
            if mesh.isFromReferencedFile:

                continue

            # Check for non-deformed meshes
            #
            isStaticMesh = not mesh.isDeformed()
            isSkeletalMesh = mesh.isIntermediateObject

            if isStaticMesh or isSkeletalMesh:

                yield mesh

            else:

                continue

    def iterSkeletalMeshes(self):
        """
        Returns a generator that yields skeletal meshes.

        :rtype: Iterator[mpynode.MPyNode]
        """

        # Iterate through meshes
        #
        for mesh in self.scene.iterNodesByApiType(om.MFn.kMesh):

            # Check if mesh is referenced
            #
            if mesh.isFromReferencedFile:

                continue

            # Check if mesh contains skin clusters
            #
            skins = mesh.getDeformersByType(om.MFn.kSkinClusterFilter)
            numSkins = len(skins)

            if numSkins > 0:

                yield mesh

            else:

                continue

    def detectSceneErrors(self):
        """
        Searches for any scene errors.
        This checks for: invalid linear/angle/time units and playback speed

        :rtype: None
        """

        # Evaluate linear unit
        #
        linearUnit = mc.currentUnit(query=True, linear=True)
        errorCount = 0

        self.info('Inspecting scene settings...')

        if linearUnit not in ('cm', 'centimeter'):

            self.warning(f'Distance unit is not set to centimeters!')
            errorCount += 1

        # Evaluate angle unit
        #
        angleUnit = mc.currentUnit(query=True, angle=True)

        if angleUnit not in ('deg', 'degree'):

            self.warning(f'Angle unit is not set to degrees!')
            errorCount += 1

        # Evaluate time unit
        #
        timeUnit = mc.currentUnit(query=True, time=True)

        if timeUnit != 'ntsc':

            self.warning(f'Time unit is not set to NTSC (30fps)!')
            errorCount += 1

        # Evaluate playback speed
        #
        speed = mc.playbackOptions(query=True, playbackSpeed=True)

        if speed != 1.0:

            self.warning(f'Playback speed is not set to 1.0!')
            errorCount += 1

        # Evaluate errors
        #
        if errorCount > 0:

            self.error(f'{errorCount}/4 failed!')

        else:

            self.success('No scene setting errors detected!')

    def detectFbxErrors(self):
        """
        Searches for any FBX errors.

        :rtype: None
        """

        # Check if FBX asset exists
        #
        asset = self.fbxIO.loadAsset()
        errorCount = 0

        self.info('Inspecting FBX settings...')

        if asset is not None:

            # Check if asset path is valid
            #
            if not pathutils.isPathVariable(asset.directory):

                self.warning(f'"{asset.name}" FBX asset directory is missing an environment variable!')
                errorCount += 1

            # Check if asset contains export sets
            #
            numExportSets = len(asset.exportSets)

            if numExportSets == 0:

                self.warning(f'"{asset.name}" FBX asset contains no export sets!')
                errorCount += 1

            # Iterate through export sets
            #
            for exportSet in asset.exportSets:

                # Check if export-set directory is valid
                #
                if not pathutils.isPathRelative(exportSet.directory):

                    self.warning(f'"{exportSet.name}" FBX export-set directory is not relative!')
                    errorCount += 1

                # Check if export-set contains meshes
                #
                hasMeshName = not stringutils.isNullOrEmpty(exportSet.mesh.name)
                hasMeshList = len(exportSet.mesh.includeObjects) > 0

                if not (hasMeshName or hasMeshList):

                    self.warning(f'"{exportSet.name}" FBX export-set is missing meshes!')
                    errorCount += 1

                # Check if export-set contains bones
                #
                hasSkeletonName = not stringutils.isNullOrEmpty(exportSet.skeleton.name)
                hasSkeletonList = len(exportSet.skeleton.includeObjects) > 0

                if exportSet.mesh.includeSkins and not (hasSkeletonName or hasSkeletonList):

                    self.warning(f'"{exportSet.name}" FBX export-set is missing bones!')
                    errorCount += 1

        else:

            self.warning('Scene contains no FBX asset!')
            errorCount += 1

        # Evaluate errors
        #
        if errorCount > 0:

            self.error(f'{errorCount} failures!')

        else:

            self.success('No FBX errors detected!')

    def detectTextureErrors(self):
        """
        Searches the scene for any texture errors.
        This checks for: empty or absolute file paths!

        :rtype: List[mpynode.MPyNode]
        """

        # Iterate through file nodes
        #
        errors = []
        textureCount = 0

        self.info('Inspecting file-texture nodes...')

        for file in self.scene.iterNodesByApiType(om.MFn.kFileTexture):

            # Check if texture is referenced
            #
            if file.isFromReferencedFile:

                continue

            # Evaluate texture path
            #
            name = file.name()
            filename = file.getAttr('fileTextureName')

            if stringutils.isNullOrEmpty(filename):

                self.warning(f'"{name}.fileTextureName" contains no file path!')
                errors.append(file)

            elif os.path.isabs(filename):

                self.warning(f'"{name}.fileTextureName" contains an absolute file path!')
                errors.append(file)

            else:

                pass

            textureCount += 1

        # Evaluate errors
        #
        errorCount = len(errors)

        if errorCount > 0:

            self.error(f'{errorCount}/{textureCount} failed!')

        else:

            self.success('No texture errors detected!')

        return errors

    def detectReferenceErrors(self):
        """
        Searches the scene for any reference errors.
        This checks for: empty or absolute file paths!

        :rtype: List[mpynode.MPyNode]
        """

        # Iterate through reference nodes
        #
        errors = []
        referenceCount = 0

        self.info('Inspecting reference nodes...')

        for reference in self.scene.iterReferenceNodes(skipShared=True):

            # Check if reference is alive
            #
            referenceName = reference.name()

            if not reference.isAlive():

                self.warning(f'"{referenceName}" is no longer valid!')
                errors.append(reference)

            # Evaluate reference path
            #
            filePath = reference.filePath()

            if stringutils.isNullOrEmpty(filePath):

                self.warning(f'"{reference}" reference contains no file path!')
                errors.append(reference)

            elif os.path.isabs(filePath):

                self.warning(f'"{reference}" reference contains an absolute file path!')
                errors.append(reference)

            else:

                pass

            referenceCount += 1

        # Evaluate errors
        #
        errorCount = len(errors)

        if errorCount > 0:

            self.error(f'{errorCount}/{referenceCount} failed!')

        else:

            self.success('No reference errors detected!')

        return errors

    def detectNonUniqueNodeNameErrors(self):
        """
        Searches the scene for any non-unique node name errors.

        :rtype: List[mpynode.MPyNode]
        """

        # Iterate through scene nodes
        #
        names = defaultdict(list)
        nodeCount = 0

        self.info('Inspecting scene node names...')

        for node in self.scene.iterNodesByApiType(om.MFn.kTransform):

            # Check if node is referenced
            #
            if node.isFromReferencedFile:

                continue

            # Append absolute name to tracker
            #
            name = node.name(includeNamespace=True)
            names[name].append(node)

            nodeCount += 1

        # Evaluate track for non-unique node names
        #
        errors = []

        for (name, nodes) in names.items():

            # Evaluate name occurrences
            #
            nameCount = len(nodes)

            if nameCount > 1:

                self.warning(f'Multiple nodes named "{name}" detected!')
                errors.extend(nodes)

            else:

                continue

        # Evaluate errors
        #
        errorCount = len(errors)

        if errorCount > 0:

            self.error(f'{errorCount}/{nodeCount} failed!')

        else:

            self.success('No node name errors detected!')

        return errors

    def detectAnimatableNodeErrors(self):
        """
        Searches the scene for any animatable node errors.
        This checks for:
            - transform is non-identity
            - shapes are properly named
            - channel-box attributes have non-default values
            - channel-box attributes have keys on them
            - visibility attribute is keyable
            - rotate-order attribute is visible

        :rtype: List[mpynode.MPyNode]
        """

        # Iterate through file nodes
        #
        errors = set()
        nodeCount = 0

        self.info('Inspecting animatable nodes...')

        for node in self.iterAnimatableNodes():

            # Evaluate transform matrix
            #
            name = node.name(includeNamespace=True)

            matrix = node.matrix(asTransformationMatrix=True)
            isIdentity = matrix.isEquivalent(om.MTransformationMatrix.kIdentity)

            if not isIdentity:

                self.warning(f'"{name}" transform has not been zeroed out!')
                errors.add(node)

            # Check if shapes follow naming convention
            #
            hasValidNames = all([self._shapeRegex.match(shape.name()) is not None for shape in node.iterShapes()])

            if not hasValidNames:

                self.warning(f'"{name}" shapes do not follow the naming convention!')
                errors.add(node)

            # Evaluate channel-box plugs
            #
            for plug in node.iterPlugs(channelBox=True):

                # Check if plug has keys
                #
                plugName = plug.partialName(useLongNames=True, includeNodeName=True)

                if plugutils.isAnimated(plug):

                    self.warning(f'"{plugName}" plug has keyframes on it!')
                    errors.add(node)

                # Check if plug is constrained
                #
                if plugutils.isConstrained(plug):

                    self.warning(f'"{plugName}" plug has a constraint on it!')
                    errors.add(node)

                # Check if plug is non-default
                #
                defaultValue = attributeutils.getDefaultValue(plug, convertUnits=True)
                currentValue = plugmutators.getValue(plug)

                isDefault = math.isclose(currentValue, defaultValue, rel_tol=1e-6, abs_tol=1e-6)

                if not isDefault:

                    self.warning(f'"{plugName}" plug is not using its default value!')
                    errors.add(node)

            # Check if rotate-order is accessible
            #
            plug = node['rotateOrder']

            if not plug.isChannelBox:

                self.warning(f'"{name}.rotateOrder" plug is not accessible from the channel-box!')
                errors.add(node)

            # Check if visibility is keyable
            #
            plug = node['visibility']

            if plug.isKeyable:

                self.warning(f'"{name}.visibility" plug is keyable!')
                errors.add(node)

            nodeCount += 1

        # Evaluate errors
        #
        errorCount = len(errors)

        if errorCount > 0:

            self.error(f'{errorCount}/{nodeCount} failed!')

        else:

            self.success('No animatable node errors detected!')

        return errors

    def detectStaticMeshErrors(self):
        """
        Searches the scene for any static mesh errors.
        This checks for:
            - polygons with more than 4 vertices
            - polygons with no surface area
            - edges with zero length
            - uv faces with no surface area
            - vertices with no connected faces
            - overlapping vertices
            - non-default UV-Set and Color-Set names

        :rtype: List[mpynode.MPyNode]
        """

        # Iterate through meshes
        #
        errors = set()
        staticMeshCount = 0
        debugCommands = []

        self.info('Inspecting static meshes...')

        for mesh in self.iterStaticMeshes():

            # Initialize mesh iterators
            #
            meshName = mesh.name()
            meshObject = mesh.object()

            iterPolygons = om.MItMeshPolygon(meshObject)
            iterEdges = om.MItMeshEdge(meshObject)
            iterVertices = om.MItMeshVertex(meshObject)

            # Iterate through mesh components
            #
            numPolygons = mesh.numPolygons
            numEdges = mesh.numEdges
            numVertices = mesh.numVertices
            maxElements = max(numPolygons, numEdges, numVertices)

            uvSetNames = mesh.getUVSetNames()
            colorSetNames = mesh.getColorSetNames()

            vertexPositions = [None] * numVertices

            for i in range(maxElements):

                # Check if polygon index is in range
                #
                if i < numPolygons:

                    # Check if polygon-vertices are valid
                    #
                    iterPolygons.setIndex(i)
                    polygonVertexCount = iterPolygons.polygonVertexCount()

                    if polygonVertexCount > 4:

                        self.warning(f'"{meshName}.f[{i}]" has more than 4 face vertices!')
                        errors.add(mesh)

                    # Check if polygon area is valid
                    #
                    surfaceArea = iterPolygons.getArea()

                    if surfaceArea < 1e-3:

                        self.warning(f'"{meshName}.f[{i}]" has has no surface area!')
                        errors.add(mesh)

                    # Check if polygon's UV area is valid
                    #
                    for uvSetName in uvSetNames:

                        uvArea = iterPolygons.getUVArea(uvSet=uvSetName)

                        if uvArea < 1e-7:  # Any number with fewer decimal places raises too many false positives!

                            self.warning(f'"{meshName}.f[{i}]" @ {uvSetName} UV set has no surface area!')
                            errors.add(mesh)

                # Check if edge index is in range
                #
                if i < numEdges:

                    # Check if edge length is valid
                    #
                    iterEdges.setIndex(i)
                    edgeLength = iterEdges.length()

                    if edgeLength < 1e-3:

                        self.warning(f'"{meshName}.e[{i}]" has has zero length!')
                        errors.add(mesh)

                # Check if vertex index is in range
                #
                if i < numVertices:

                    # Check if vertex is valid
                    #
                    iterVertices.setIndex(i)
                    connectedFaces = iterVertices.getConnectedFaces()

                    if connectedFaces == 0:

                        self.warning(f'"{meshName}.vtx[{i}]" has has no connected faces!')
                        errors.add(mesh)

                    vertexPosition = iterVertices.position()
                    vertexPositions[i] = vertexPosition

            # Check for overlapping vertices
            #
            pointTree = cKDTree(vertexPositions)
            overlappingVertices = pointTree.query_ball_point(vertexPositions, 1e-3)

            vertexIndices = [i for (i, vertexIndices) in enumerate(overlappingVertices) if len(vertexIndices) > 1]
            consecutiveIndices = list(consecutivePairs(vertexIndices))

            numOverlapping = len(vertexIndices)

            if numOverlapping > 0:

                debugCommand = 'select -r'

                for (startIndex, endIndex) in consecutiveIndices:

                    if startIndex == endIndex:

                        fullComponentName = f'{meshName}.vtx[{startIndex}]'
                        debugCommand += f' {fullComponentName}'

                        self.warning(f'"{fullComponentName}" has overlapping vertices')

                    else:

                        fullComponentName = f'{meshName}.vtx[{startIndex}:{endIndex}]'
                        debugCommand += f' {fullComponentName}'

                        self.warning(f'"{fullComponentName}" has overlapping vertices')

                debugCommands.append(debugCommand)
                errors.add(mesh)

            # Inspect first UV set name
            #
            numUVSetNames = len(uvSetNames)
            firstUVSetName = uvSetNames[0] if numUVSetNames > 0 else ''

            if firstUVSetName != 'map1' and numUVSetNames > 0:

                self.warning(f'"{meshName}" first UV-set is named "{firstUVSetName}" instead of "map1"!')
                errors.add(mesh)

            # Inspect first color set name
            #
            numColorSetNames = len(colorSetNames)
            firstColorSetName = colorSetNames[0] if numColorSetNames > 0 else ''

            if firstColorSetName != 'colorSet1' and numColorSetNames > 0:

                self.warning(f'"{meshName}" first color-set is named "{firstColorSetName}" instead of "colorSet1"!')
                errors.add(mesh)

            staticMeshCount += 1

        # Evaluate debug commands
        #
        debugCount = len(debugCommands)

        if debugCount > 0:

            self.info('See clipboard for selection commands!')
            pyperclip.copy(';\n'.join(debugCommands))

        # Evaluate errors
        #
        errorCount = len(errors)

        if errorCount > 0:

            self.error(f'{errorCount}/{staticMeshCount} failed!')

        else:

            self.success('No static mesh errors detected!')

        return errors

    def detectSkeletalMeshErrors(self):
        """
        Searches the scene for any skeletal mesh errors.
        This checks for:
            - inherits transforms enabled
            - unlocked transform attributes
            - non-identity transform matrices
            - is selectable
            - is in bind-pose

        :rtype: List[mpynode.MPyNode]
        """

        # Iterate through meshes
        #
        errors = set()
        skeletalMeshCount = 0

        self.info('Inspecting skeletal meshes...')

        for mesh in self.iterSkeletalMeshes():

            # Check if `inheritsTransform` is enabled
            #
            node = mesh.parent()
            meshName = node.name(includeNamespace=True)

            inheritsTransform = bool(node.inheritsTransform)

            if inheritsTransform:

                self.warning(f'"{meshName}" has inherits transform enabled!')
                errors.add(mesh)

            # Evaluate transform matrix
            #
            matrix = node.matrix()
            isIdentity = matrix.isEquivalent(om.MMatrix.kIdentity, tolerance=1e-3)

            if not isIdentity:

                self.warning(f'"{meshName}" transform has not been reset!')
                errors.add(mesh)

            # Check if transform attributes are locked
            #
            translateLocked = all([node['translateX'].isLocked, node['translateY'].isLocked, node['translateZ'].isLocked])
            rotateLocked = all([node['rotateX'].isLocked, node['rotateY'].isLocked, node['rotateZ'].isLocked])
            scaleLocked = all([node['scaleX'].isLocked, node['scaleY'].isLocked, node['scaleZ'].isLocked])

            if not (translateLocked and rotateLocked and scaleLocked):

                self.warning(f'"{meshName}" transform attributes have not been locked!')
                errors.add(mesh)

            # Check if mesh is selectable
            #
            isSelectable = mesh.isSelectable()

            if isSelectable:

                self.warning(f'"{meshName}" skeletal mesh is selectable!')
                errors.add(mesh)

            # Evaluate skin clusters
            #
            skins = mesh.getDeformersByType(om.MFn.kSkinClusterFilter)
            numSkins = len(skins)

            if numSkins > 1:

                self.warning(f'"{meshName}" mesh contains multiple skin clusters!')
                errors.add(mesh)

            # Evaluate root joint
            #
            skin = skins[0]
            rootJoint = skin.rootInfluence()

            if rootJoint is None:

                self.warning(f'"{meshName}" mesh contains weighted influences under multiple roots!')
                errors.add(mesh)

                continue  # Can no longer perform export hierarchy tests!

            # Evaluate export hierarchy
            #
            influences = skin.influences()
            influenceObjects = list(influences.values())

            for descendant in rootJoint.descendants(apiType=om.MFn.kTransform, includeSelf=True):

                # Evaluate descendant
                #
                descendantName = descendant.name(includeNamespace=True)

                if descendant.hasFn(om.MFn.kConstraint, om.MFn.kPluginConstraintNode):

                    continue

                elif descendant.hasFn(om.MFn.kJoint):

                    preEulerRotation = descendant.preEulerRotation()
                    isIdentity = preEulerRotation.isEquivalent(om.MEulerRotation.kIdentity)

                    if not isIdentity:

                        self.warning(f'"{descendantName}" joint contains non-zero orientations!')
                        errors.add(descendant)

                else:

                    self.warning(f'"{descendantName}" non-joint type found in export hierarchy!')
                    errors.add(descendant)

                # Evaluate bind pose
                #
                try:

                    influenceId = influenceObjects.index(descendant)
                    preBindMatrix = skin.preBindMatrix(influenceId).inverse()
                    worldMatrix = descendant.worldMatrix()

                    inBindPose = preBindMatrix.isEquivalent(worldMatrix, tolerance=1e-3)

                    if not inBindPose:

                        self.warning(f'"{descendantName}" joint is not in bind pose!')
                        errors.add(mesh)

                except ValueError:

                    continue

            skeletalMeshCount += 1

        # Evaluate errors
        #
        errorCount = len(errors)

        if errorCount > 0:

            self.error(f'{errorCount}/{skeletalMeshCount} failed!')

        else:

            self.success('No skeletal mesh errors detected!')

        return errors

    def checkScene(self):
        """
        Reports any scene errors.

        :rtype: None
        """

        # Reset logger
        #
        self.clear()

        # Evaluate condition checks
        #
        if self.sceneSettingsCheckBox.isChecked():

            self.detectSceneErrors()

        if self.fbxSettingsCheckBox.isChecked():

            self.detectFbxErrors()

        if self.texturePathsCheckBox.isChecked():

            self._textureErrors = self.detectTextureErrors()

        if self.referencePathsCheckBox.isChecked():

            self._referenceErrors = self.detectReferenceErrors()

        if self.nonUniqueNamesCheckBox.isChecked():

            self._nodeNameErrors = self.detectNonUniqueNodeNameErrors()

        if self.animatableNodesCheckBox.isChecked():

            self._animatableNodeErrors = self.detectAnimatableNodeErrors()

        if self.staticMeshesCheckBox.isChecked():

            self._staticMeshErrors = self.detectStaticMeshErrors()

        if self.skeletalMeshesCheckBox.isChecked():

            self._skeletalMeshErrors = self.detectSkeletalMeshErrors()

    def fixScene(self):
        """
        Attempts to fix any scene errors

        :rtype: None
        """

        pass
    # endregion

    # region Slots
    @QtCore.Slot()
    def on_checkPushButton_clicked(self):
        """
        Slot method for the `checkPushButton` widget's `clicked` signal.

        :rtype: None
        """

        self.checkScene()

    @QtCore.Slot()
    def on_fixPushButton_clicked(self):
        """
        Slot method for the `fixPushButton` widget's `clicked` signal.

        :rtype: None
        """

        self.fixScene()
    # endregion
