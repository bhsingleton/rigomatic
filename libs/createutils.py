from maya.api import OpenMaya as om
from mpy import mpyscene, mpynode
from dcc.python import stringutils
from dcc.maya.decorators.undo import undo
from . import kinematicutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@undo(name='Create Node')
def createNode(typeName, **kwargs):
    """
    Returns a new node derived from the specified type.

    :type typeName: str
    :key name: str
    :key matrix: om.MMatrix
    :key color = Tuple[float, float, float]
    :key locator: bool
    :key helper: bool
    :rtype: mpynode.MPyNode
    """

    # Create node
    #
    scene = mpyscene.MPyScene()
    name = kwargs.get('name', '')
    cleanName = stringutils.slugify(name)
    uniqueName = cleanName if scene.isNameUnique(cleanName) and not stringutils.isNullOrEmpty(name) else f'{typeName}1'

    node = scene.createNode(typeName, name=uniqueName)

    # Update transform matrix
    #
    matrix = kwargs.get('matrix', om.MMatrix.kIdentity)
    node.setMatrix(matrix)

    # Add any requested shapes
    #
    locator = kwargs.get('locator', False)
    helper = kwargs.get('helper', False)
    colorRGB = kwargs.get('color', None)

    if locator:

        node.addLocator(colorRGB=colorRGB)

    elif helper:

        node.addPointHelper(colorRGB=colorRGB)

    else:

        pass

    # Update active selection
    #
    node.select(replace=True)

    return node


@undo(name='Add IK-Solver')
def addIKSolver(startJoint, endJoint):
    """
    Adds an IK solver to the supplied start and end joints.

    :type startJoint: mpynode.MPyNode
    :type endJoint: mpynode.MPyNode
    :rtype: None
    """

    # Evaluate supplied nodes
    #
    if not (startJoint.hasFn(om.MFn.kJoint) and endJoint.hasFn(om.MFn.kJoint)):

        return

    # Evaluate hierarchy
    #
    ancestors = endJoint.ancestors(apiType=om.MFn.kJoint)

    if startJoint not in ancestors:

        log.warning(f'Cannot trace hierarchy between {startJoint} and {endJoint}')
        return

    # Evaluate which solver to apply
    #
    index = ancestors.index(startJoint)

    joints = ancestors[index:] + [endJoint]
    numJoints = len(joints)

    if numJoints == 2:

        kinematicutils.applySingleChainSolver(startJoint, endJoint)

    elif numJoints == 3:

        kinematicutils.applyRotationPlaneSolver(startJoint, endJoint)

    else:

        kinematicutils.applySpringSolver(startJoint, endJoint)


@undo(name='Create Intermediate')
def createIntermediate(*nodes):
    """
    Returns an intermediate parent to the supplied node.

    :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
    :rtype: mpynode.MPyNode
    """

    # Iterate through nodes
    #
    scene = mpyscene.MPyScene()
    intermediates = []

    for node in nodes:

        # Check if this is a transform node
        #
        if not node.hasFn(om.MFn.kTransform):

            continue

        # Create parent node
        #
        ancestor = node.parent()
        typeName = node.typeName

        parent = scene.createNode(typeName, name='group1', parent=ancestor)
        parent.copyTransform(node)

        # Re-parent node
        #
        node.setParent(parent)
        node.resetMatrix()

        intermediates.append(parent)

    return intermediates
