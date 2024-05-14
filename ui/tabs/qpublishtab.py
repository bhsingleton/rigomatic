import os
import re
import math

from maya import cmds as mc
from maya.api import OpenMaya as om
from Qt import QtCore, QtWidgets, QtGui
from collections import defaultdict
from dcc.python import stringutils, pathutils
from dcc.fbx.libs import fbxio
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
        self._nodeNameErrors = []
        self._animatableNodeErrors = []
        self._skeletalMeshErrors = []
        self._exportHierarchyErrors = []

        # Declare public variables
        #
        self.checkPushButton = None
        self.fixPushButton = None
        self.logTextEdit = None  # type: QtWidgets:QTextEdit
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

    def detectSkeletalMeshErrors(self):
        """
        Searches the scene for any skeletal mesh errors.
        This checks for:
            - inherits transforms enabled
            - unlocked transform attributes
            - non-identity transform matrices
            - is selectable
            - non-default UV-Set and Color-Set names
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
            name = node.name(includeNamespace=True)

            inheritsTransform = bool(node.inheritsTransform)

            if inheritsTransform:

                self.warning(f'"{name}" has inherits transform enabled!')
                errors.add(mesh)

            # Evaluate transform matrix
            #
            matrix = node.matrix()
            isIdentity = matrix.isEquivalent(om.MMatrix.kIdentity, tolerance=1e-3)

            if not isIdentity:

                self.warning(f'"{name}" transform has not been reset!')
                errors.add(mesh)

            # Check if transform attributes are locked
            #
            translateLocked = all([node['translateX'].isLocked, node['translateY'].isLocked, node['translateZ'].isLocked])
            rotateLocked = all([node['rotateX'].isLocked, node['rotateY'].isLocked, node['rotateZ'].isLocked])
            scaleLocked = all([node['scaleX'].isLocked, node['scaleY'].isLocked, node['scaleZ'].isLocked])

            if not (translateLocked and rotateLocked and scaleLocked):

                self.warning(f'"{name}" transform attributes have not been locked!')
                errors.add(mesh)

            # Check if mesh is selectable
            #
            isSelectable = mesh.isSelectable()

            if isSelectable:

                self.warning(f'"{name}" mesh is selectable!')
                errors.add(mesh)

            # Inspect first UV set name
            #
            uvSetNames = mesh.getUVSetNames()
            numUVSetNames = len(uvSetNames)

            firstUVSetName = uvSetNames[0] if numUVSetNames > 0 else ''

            if firstUVSetName != 'map1':

                self.warning(f'"{name}" first UV-set is named "{firstUVSetName}" instead of "map1"!')
                errors.add(mesh)

            # Inspect color set name
            #
            colorSetNames = mesh.getColorSetNames()
            numColorSetNames = len(colorSetNames)

            firstColorSetName = colorSetNames[0] if numColorSetNames > 0 else ''

            if firstColorSetName != 'colorSet1' and numColorSetNames > 0:

                self.warning(f'"{name}" first color-set is named "{firstColorSetName}" instead of "colorSet1"!')
                errors.add(mesh)

            # Evaluate skin clusters
            #
            skins = mesh.getDeformersByType(om.MFn.kSkinClusterFilter)
            numSkins = len(skins)

            if numSkins > 1:

                self.warning(f'"{name}" mesh contains multiple skin clusters!')
                errors.add(mesh)

            # Evaluate root joint
            #
            skin = skins[0]
            rootJoint = skin.rootInfluence()

            if rootJoint is None:

                self.warning(f'"{name}" mesh contains weighted influences under multiple roots!')
                errors.add(mesh)

            # Evaluate bind pose
            #
            inBindPose = False

            for (influenceId, influenceObject) in skin.iterInfluences():

                preBindMatrix = skin.preBindMatrix(influenceId).inverse()
                worldMatrix = influenceObject.worldMatrix()

                inBindPose = preBindMatrix.isEquivalent(worldMatrix, tolerance=1e-3)

                if not inBindPose:

                    break

            if not inBindPose:

                self.warning(f'"{name}" mesh is not in bind pose!')
                errors.add(mesh)

            skeletalMeshCount += 1

        # Evaluate errors
        #
        errorCount = len(errors)

        if errorCount > 0:

            self.error(f'{errorCount}/{skeletalMeshCount} failed!')

        else:

            self.success('No skeletal mesh errors detected!')

        return errors

    def detectExportHierarchyErrors(self):
        """
        Searches the scene for any export hierarchy errors.
        This checks for:
            - any skinned joints are not under root
            - any non-joint types are in the export hierarchy
            - any joints have non-zero orientations

        :rtype: List[mpynode.MPyNode]
        """

        # Iterate through meshes
        #
        hierarchy = set()
        errors = set()

        self.info('Inspecting export hierarchy...')

        for mesh in self.iterSkeletalMeshes():

            # Find root joint
            #
            skin = mesh.getDeformersByType(om.MFn.kSkinClusterFilter)[0]
            rootJoint = skin.rootInfluence()

            if rootJoint is None:

                continue

            # Evaluate export hierarchy
            #
            for descendant in rootJoint.descendants(apiType=om.MFn.kTransform, includeSelf=True):

                # Evaluate descendant
                #
                name = descendant.name(includeNamespace=True)

                if descendant.hasFn(om.MFn.kConstraint, om.MFn.kPluginConstraintNode):

                    continue

                elif descendant.hasFn(om.MFn.kJoint):

                    preEulerRotation = descendant.preEulerRotation()
                    isIdentity = preEulerRotation.isEquivalent(om.MEulerRotation.kIdentity)

                    if not isIdentity:

                        self.warning(f'"{name}" joint contains non-zero orientations!')
                        errors.add(descendant)

                else:

                    self.warning(f'"{name}" non-joint type found in export hierarchy!')
                    errors.add(descendant)

                hierarchy.add(descendant)

        # Evaluate errors
        #
        errorCount = len(errors)
        hierarchyCount = len(hierarchy)

        if errorCount > 0:

            self.error(f'{errorCount}/{hierarchyCount} failed!')

        else:

            self.success('No export hierarchy errors detected!')

        return errors

    def checkScene(self):
        """
        Reports any scene errors.

        :rtype: None
        """

        # Reset logger
        #
        self.clear()

        # Inspect scene settings
        #
        self.detectSceneErrors()
        self.detectFbxErrors()

        # Inspect scene nodes
        #
        self._textureErrors = self.detectTextureErrors()
        self._nodeNameErrors = self.detectNonUniqueNodeNameErrors()
        self._animatableNodeErrors = self.detectAnimatableNodeErrors()
        self._skeletalMeshErrors = self.detectSkeletalMeshErrors()
        self._exportHierarchyErrors = self.detectExportHierarchyErrors()

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
