from maya.api import OpenMaya as om
from mpy import mpyscene, mpynode
from dcc.maya.decorators.undo import undo
from . import ColorType

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@undo(name='Rename Node')
def renameNode(node, name):
    """
    Renames the supplied node to the specified name.

    :type node: mpynode.MPyNode
    :type name: str
    :rtype: bool
    """

    scene = mpyscene.MPyScene()

    if scene.isNameUnique(name):

        node.setName(name)
        return True

    else:

        return False


@undo(name='Renamespace Node')
def renamespaceNodes(*nodes, namespace=''):
    """
    Updates the namespace for the supplied nodes.

    :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
    :type namespace: str
    :rtype: None
    """

    for node in nodes:

        node.setNamespace(namespace)


def findWireframeColor(node, colorType=ColorType.NONE):
    """
    Returns the wireframe color from the supplied node.

    :type node:
    :type colorType: ColorType
    :rtype: Tuple[float, float, float]
    """

    # Evaluate node type
    #
    if not node.hasFn(om.MFn.kTransform):

        return (0.0, 0.0, 0.0)

    # Evaluate shapes under transform
    #
    shapes = node.shapes()
    numShapes = len(shapes)

    shape = shapes[0] if (numShapes > 0) else node if node.hasFn(om.MFn.kJoint) else None

    if shape is None:

        return (0.0, 0.0, 0.0)

    # Evaluate color type
    #
    if colorType == ColorType.WIRE_COLOR_RGB:

        return shape.wireColorRGB

    elif colorType == ColorType.OVERRIDE_COLOR_RGB:

        return shape.overrideColorRGB

    else:

        dormantColor = shape.dormantColor()
        return dormantColor.r, dormantColor.g, dormantColor.b


@undo(name='Recolor Node')
def recolorNodes(*nodes, color=(0.0, 0.0, 0.0), colorType=ColorType.NONE):
    """
    Recolors the supplied node to the specified color.

    :type nodes: Union[mpynode.MPyNode, List[mpynode.MPyNode]]
    :type color: Tuple[float, float, float]
    :type colorType: ColorType
    :rtype: None
    """

    # Iterate through nodes
    #
    for node in nodes:

        # Check if this is a transform node
        #
        if not node.hasFn(om.MFn.kTransform):

            continue

        # Evaluate shapes
        #
        shapes = node.shapes()
        numShapes = len(shapes)

        if numShapes == 0 and node.hasFn(om.MFn.kJoint):

            shapes = [node]

        # Iterate through shapes
        #
        for shape in shapes:

            # Evaluate color type
            #
            if colorType == ColorType.WIRE_COLOR_RGB:

                shape.useObjectColor = 2
                shape.wireColorRGB = color

            elif colorType == ColorType.OVERRIDE_COLOR_RGB:

                shape.overrideEnabled = True
                shape.overrideRGBColors = True
                shape.overrideColorRGB = color

            else:

                continue
