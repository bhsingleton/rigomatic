import math

from maya.api import OpenMaya as om
from mpy import mpyscene, mpynode
from enum import IntEnum
from dcc.maya.libs import transformutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class IkSolver(IntEnum):
    """
    Enum class of all the available IK systems.
    """

    SingleChain = 0
    RotationPlane = 1
    Spline = 2
    Spring = 3


def getIkSolver(solver):
    """
    Returns the IK solver associated with the given enum.

    :type solver: IkSolver
    :rtype: pynode.PyNode
    """

    # Query enum type
    #
    scene = mpyscene.MPyScene()

    if solver == IkSolver.SingleChain:

        # Check if solver already exists
        #
        if scene.doesNodeExist('ikSCsolver'):

            return scene.getNodeByName('ikSCsolver')

        else:

            return scene.createNode('ikSCsolver', name='ikSCsolver')

    elif solver == IkSolver.RotationPlane:

        # Check if solver already exists
        #
        if scene.doesNodeExist('ikRPsolver'):

            return scene.getNodeByName('ikRPsolver')

        else:

            return scene.createNode('ikRPsolver', name='ikRPsolver')

    elif solver == IkSolver.Spline:

        # Check if solver already exists
        #
        if scene.doesNodeExist('ikSplineSolver'):

            return scene.getNodeByName('ikSplineSolver')

        else:

            return scene.createNode('ikSplineSolver', name='ikSplineSolver')

    elif solver == IkSolver.Spring:

        # Check if solver already exists
        #
        if scene.doesNodeExist('ikSpringSolver'):

            return scene.getNodeByName('ikSpringSolver')

        else:

            return scene.createNode('ikSpringSolver', name='ikSpringSolver')

    return None


def applyEffector(joint):
    """
    Assigns an effector to the supplied joint.
    This joint is expected to have a parent!

    :type joint: mpynode.MPyNode
    :rtype: mpynode.MPyNode
    """

    # Create effector node
    #
    scene = mpyscene.MPyScene()
    parent = joint.parent()
    effector = scene.createNode('ikEffector', parent=parent)

    # Connect translate attributes
    #
    joint.connectPlugs('translate', effector['translate'])
    joint.connectPlugs('offsetParentMatrix', effector['offsetParentMatrix'])

    return effector


def applySingleChainSolver(startJoint, endJoint):
    """
    Assigns a single chain solver to the supplied joints.

    :type startJoint: mpynode.MPyNode
    :type endJoint: mpynode.MPyNode
    :rtype: Tuple[mpynode.MPyNode, mpynode.MPyNode]
    """

    # Create IK nodes
    #
    scene = mpyscene.MPyScene()

    ikHandle = scene.createNode('ikHandle')
    effector = applyEffector(endJoint)

    # Update IK-handle transform
    #
    startMatrix = startJoint.worldMatrix()
    endMatrix = endJoint.worldMatrix()
    matrix = transformutils.createRotationMatrix(startMatrix) * transformutils.createTranslateMatrix(endMatrix)

    ikHandle.setWorldMatrix(matrix)

    # Enable stickiness
    #
    ikHandle.setAttr('stickiness', True)

    # Connect IK attributes
    #
    startJoint.connectPlugs('message', ikHandle['startJoint'])
    effector.connectPlugs(f'handlePath[{effector.instanceNumber()}]', ikHandle['endEffector'])

    # Get rotation plane solver
    #
    solver = getIkSolver(IkSolver.SingleChain)
    solver.connectPlugs('message', ikHandle['ikSolver'])

    return ikHandle, effector


def applyRotationPlaneSolver(startJoint, endJoint):
    """
    Assigns a rotation plane solver to the supplied joints.

    :type startJoint: mpynode.MPyNode
    :type endJoint: mpynode.MPyNode
    :rtype: Tuple[mpynode.MPyNode, mpynode.MPyNode]
    """

    # Create IK nodes
    #
    scene = mpyscene.MPyScene()

    ikHandle = scene.createNode('ikHandle')
    ikHandle.copyTransform(endJoint)

    effector = applyEffector(endJoint)

    # Connect IK attributes
    #
    startJoint.connectPlugs('message', ikHandle['startJoint'])
    effector.connectPlugs(f'handlePath[{effector.instanceNumber()}]', ikHandle['endEffector'])

    # Get rotation plane solver
    #
    solver = getIkSolver(IkSolver.RotationPlane)
    solver.connectPlugs('message', ikHandle['ikSolver'])

    return ikHandle, effector


def iterInbetweenJoints(startJoint, endJoint, includeStart=False, includeEnd=False):
    """
    Returns a generator that yields inbetween joints.

    :type startJoint: mpynode.MPyNode
    :type endJoint: mpynode.MPyNode
    :type includeStart: bool
    :type includeEnd: bool
    :rtype: Iterator[mpynode.MPyNode]
    """

    ancestors = endJoint.ancestors(apiType=om.MFn.kJoint)

    try:

        index = ancestors.index(startJoint)
        inbetweenJoints = list(reversed(ancestors[:index]))

        if includeStart:

            yield startJoint

        yield from inbetweenJoints

        if includeEnd:

            yield endJoint

    except ValueError:

        return iter([])


def applySpringSolver(startJoint, endJoint):
    """
    Assigns a spring solver to the supplied joints.

    :type startJoint: mpynode.MPyNode
    :type endJoint: mpynode.MPyNode
    :rtype: Tuple[mpynode.MPyNode, mpynode.MPyNode]
    """

    # Create IK handle and effector
    #
    scene = mpyscene.MPyScene()

    ikHandle = scene.createNode('ikHandle')
    ikHandle.copyTransform(endJoint)

    effector = applyEffector(endJoint)

    # Add spring rest attributes
    #
    ikHandle.addAttr(
        longName='springRestPose',
        shortName='srp',
        attributeType='long',
        default=1,
        cachedInternally=True,
        hidden=True
    )

    ikHandle.addAttr(
        longName='springRestPoleVector',
        shortName='srpv',
        attributeType='double3',
        cachedInternally=True,
        hidden=True,
        children=[
            {
                'longName': 'springRestPoleVectorX',
                'shortName': 'srpvx',
                'attributeType': 'float',
                'cachedInternally': True,
                'hidden': True
            },
            {
                'longName': 'springRestPoleVectorY',
                'shortName': 'srpvy',
                'attributeType': 'float',
                'cachedInternally': True,
                'hidden': True
            },
            {
                'longName': 'springRestPoleVectorZ',
                'shortName': 'srpvz',
                'attributeType': 'float',
                'cachedInternally': True,
                'hidden': True
            }
        ]
    )

    ikHandle.addAttr(
        longName='springAngleBias',
        shortName='sab',
        attributeType='compound',
        cachedInternally=True,
        multi=True,
        children=[
            {
                'longName': 'springAngleBias_Position',
                'shortName': 'sbp',
                'attributeType': 'float',
                'cachedInternally': True
            },
            {
                'longName': 'springAngleBias_FloatValue',
                'shortName': 'sbfv',
                'attributeType': 'float',
                'default': 1.0,
                'cachedInternally': True
            },
            {
                'longName': 'springAngleBias_Interp',
                'shortName': 'sbi',
                'attributeType': 'enum',
                'min': 0,
                'max': 3,
                'default': 3,
                'fields': 'None:Linear:Smooth:Spline',
                'cachedInternally': True
            }
        ]
    )

    forwardVector = (endJoint.translation(space=om.MSpace.kWorld) - startJoint.translation(space=om.MSpace.kWorld)).normal()
    rightVector = transformutils.breakMatrix(startJoint.worldMatrix(), normalize=True)[2]
    poleVector = (forwardVector ^ rightVector).normal()

    ikHandle.setAttr('poleVector', poleVector)
    ikHandle.setAttr('rootOnCurve', True)
    ikHandle.setAttr('springRestPoleVector', poleVector)
    ikHandle.setAttr('springAngleBias', [(0, 0.5, 3), (1, 0.5, 3)])
    ikHandle.lockAttr('springAngleBias[0].springAngleBias_Position', 'springAngleBias[1].springAngleBias_Position')

    # Update preferred rotations
    #
    joints = list(iterInbetweenJoints(startJoint, endJoint, includeEnd=True))
    startJoint.preferEulerRotation()

    for joint in joints:

        joint.preferEulerRotation(skipPreferredAngleX=True, skipPreferredAngleY=True)

    # Connect joint chain and effector to IK handle
    #
    startJoint.connectPlugs('message', ikHandle['startJoint'])
    effector.connectPlugs(f'handlePath[{effector.instanceNumber()}]', ikHandle['endEffector'])

    # Connect IK handle to rotation plane solver
    #
    solver = getIkSolver(IkSolver.Spring)
    solver.connectPlugs('message', ikHandle['ikSolver'])

    return ikHandle, effector


def applySplineSolver(startJoint, endJoint, curve):
    """
    Assigns a spline solver to the supplied joints and curve.
    Be sure to supply a shape node and not a transform for the curve!

    :type startJoint: mpynode.MPyNode
    :type endJoint: mpynode.MPyNode
    :type curve: mpynode.MPyNode
    :rtype: Tuple[mpynode.MPyNode, mpynode.MPyNode]
    """

    # Create IK nodes
    #
    scene = mpyscene.MPyScene()

    ikHandle = scene.createNode('ikHandle')
    ikHandle.copyTransform(endJoint)

    effector = applyEffector(endJoint)

    # Connect IK attributes
    #
    startJoint.connectPlugs('message', ikHandle['startJoint'])
    effector.connectPlugs('handlePath[0]', ikHandle['endEffector'])
    curve.connectPlugs(f'worldSpace[{curve.instanceNumber()}]', ikHandle['inCurve'])

    # Get rotation plane solver
    #
    solver = getIkSolver(IkSolver.Spline)
    solver.connectPlugs('message', ikHandle['ikSolver'])

    return ikHandle, effector


def solveIk2BoneChain(startPoint, startLength, endPoint, endLength, poleVector, twist=0.0):
    """
    Solves for a 2-bone chain using the supplied variables.
    This method assumes that X is forward and -Y is up.
    Be sure to reorient these transforms in case your joint chain does not follow this convention.

    :type startPoint: om.MPoint
    :type startLength: float
    :type endPoint: om.MPoint
    :type endLength: float
    :type poleVector: om.MVector
    :type twist: float
    :rtype: om.MMatrixArray
    """

    # Compose aim matrix
    #
    twistMatrix = transformutils.createRotationMatrix([twist, 0.0, 0.0])

    forwardVector = om.MVector(endPoint - startPoint).normal()
    aimMatrix = twistMatrix * transformutils.createAimMatrix(0, forwardVector, 1, poleVector, origin=startPoint, upAxisSign=-1)

    # Calculate angles
    # Be sure to compensate for hyper-extension!
    #
    chainLength = startLength + endLength
    aimLength = startPoint.distanceTo(endPoint)

    matrices = om.MMatrixArray(3)

    if aimLength < chainLength:

        startRadian = math.acos((pow(startLength, 2.0) + pow(aimLength, 2.0) - pow(endLength, 2.0)) / (2.0 * startLength * aimLength))
        endRadian = math.acos((pow(endLength, 2.0) + pow(startLength, 2.0) - pow(aimLength, 2.0)) / (2.0 * endLength * startLength))

        matrices[0] = om.MEulerRotation(0.0, 0.0, -startRadian).asMatrix() * aimMatrix
        matrices[1] = om.MEulerRotation(0.0, 0.0, (math.pi - endRadian)).asMatrix() * transformutils.createTranslateMatrix([startLength, 0.0, 0.0]) * matrices[0]
        matrices[2] = transformutils.createTranslateMatrix([endLength, 0.0, 0.0]) * matrices[1]

    else:

        matrices[0] = aimMatrix
        matrices[1] = transformutils.createTranslateMatrix([startLength, 0.0, 0.0]) * matrices[0]
        matrices[2] = transformutils.createTranslateMatrix([endLength, 0.0, 0.0]) * matrices[1]

    return matrices


def solveSoftIk(startPoint, endPoint, chainLength, softDistance):
    """
    Solves for the soft end effector on any given IK system.
    This method returns the softened end point along with the soft scale for stretching.

    :type startPoint: om.MPoint
    :type endPoint: om.MPoint
    :type chainLength: float
    :type softDistance: float
    :rtype: om.MPoint, float
    """

    # Calculate aim vector
    #
    aimVector = om.MVector(endPoint - startPoint)
    distance = aimVector.length()

    # Calculate soft value
    #
    a = math.fabs(chainLength) - softDistance
    y = 0.0

    if 0.0 <= distance < a:

        y = distance

    else:

        y = ((softDistance * (1.0 - pow(math.e, (-(distance - a) / softDistance)))) + a)

    softOffset = distance - y

    # Calculate soft ratio for scaling
    #
    softScale = distance / y

    # Multiple output by direction vector
    #
    forwardVector = aimVector.normal()
    softEndPoint = endPoint + (forwardVector * -softOffset)

    return softEndPoint, softScale


def calculatePoleVector(nodes):
    """
    Calculates a pole vector from a chain of nodes.
    At least 3 nodes are required to derive a pole vector!

    :type nodes: list[om.MObject]
    :rtype: om.MVector
    """

    # Inspect number of nodes
    #
    numNodes = len(nodes)

    if numNodes < 3:

        raise TypeError(f'calculatePoleVector() expects at least 3 nodes ({numNodes} given)!')

    # Extract points
    #
    startPoint = transformutils.getTranslation(nodes[0], space=om.MSpace.kWorld)
    midPoint = transformutils.getTranslation(nodes[1], space=om.MSpace.kWorld)
    endPoint = transformutils.getTranslation(nodes[2], space=om.MSpace.kWorld)

    # Calculate pole vector
    #
    forwardVector = om.MVector(endPoint - startPoint).normal()
    crossProduct = om.MVector(midPoint - startPoint).normal() ^ om.MVector(endPoint - startPoint).normal()

    return forwardVector ^ crossProduct


def inverseToForward(fkNodes, startEffector, endEffector, poleVector=None):
    """
    Matches the inverse system to the forward system.

    :type fkNodes: list[om.MObject]
    :type startEffector: om.MObject
    :type endEffector: om.MObject
    :type poleVector: om.MObject
    :rtype: None
    """

    # Snap effects to fk nodes
    #
    transformutils.copyTransform(fkNodes[0], startEffector, skipRotateX=True, skipRotateY=True, skipRotateZ=True)
    transformutils.copyTransform(fkNodes[-1], endEffector, skipRotateX=True, skipRotateY=True, skipRotateZ=True)


def forwardToInverse(fkNodes, ikNodes):
    """
    Matches the forward system to the inverse system.

    :type fkNodes: list[om.MObject]
    :type ikNodes: list[om.MObject]
    :rtype: None
    """

    # Check if list lengths are identical
    #
    if len(fkNodes) != len(ikNodes):

        raise TypeError('forwardToInverse() expects 2 lists with the same length!')

    # Match transforms
    #
    for (fkNode, ikNode) in zip(fkNodes, ikNodes):

        transformutils.copyTransform(ikNode, fkNode, skipScaleX=True, skipScaleY=True, skipScaleZ=True)
