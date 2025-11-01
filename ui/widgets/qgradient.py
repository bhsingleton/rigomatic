from dcc.vendor.Qt import QtCore, QtWidgets, QtGui

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QGradient(QtWidgets.QWidget):
    """
    Overload of `QWidget` that displays linear gradients.
    """

    # region Signals
    startColorChanged = QtCore.Signal(QtGui.QColor)
    endColorChanged = QtCore.Signal(QtGui.QColor)
    # endregion

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
        parent = kwargs.pop('parent', None)
        f = kwargs.pop('f', QtCore.Qt.WindowFlags())

        super(QGradient, self).__init__(parent=parent, f=f)

        # Edit widget properties
        #
        self.setAutoFillBackground(True)

        # Declare private variables
        #
        self._direction = kwargs.get('direction', QtCore.Qt.Horizontal)
        self._startColor = QtGui.QColor(QtCore.Qt.black)
        self._endColor = QtGui.QColor(QtCore.Qt.white)

        # Evaluate supplied keyword arguments
        #
        startColor = kwargs.pop('startColor', None)

        if isinstance(startColor, QtGui.QColor):

            self.setStartColor(startColor)

        endColor = kwargs.pop('endColor', None)

        if isinstance(endColor, QtGui.QColor):

            self.setEndColor(endColor)
    # endregion

    # region Methods
    def direction(self):
        """
        Returns the gradient direction.

        :rtype: QtCore.Qt.Orientation
        """

        return self._direction

    def setDirection(self, direction):
        """
        Updates the gradient direction.

        :type direction: QtCore.Qt.Orientation
        :rtype: None
        """

        self._direction = direction
        self.repaint()

    def startColor(self):
        """
        Returns the start color.

        :rtype: QtGui.QColor
        """

        return self._startColor

    @QtCore.Slot(QtGui.QColor)
    def setStartColor(self, startColor):
        """
        Updates the start color.

        :type color: QtGui.QColor
        :rtype: None
        """

        self._startColor = QtGui.QColor(startColor)
        self.repaint()

        self.startColorChanged.emit(self._startColor)
    
    def endColor(self):
        """
        Returns the end color.

        :rtype: QtGui.QColor
        """

        return self._endColor

    @QtCore.Slot(QtGui.QColor)
    def setEndColor(self, endColor):
        """
        Updates the end color.

        :type color: QtGui.QColor
        :rtype: None
        """

        self._endColor = QtGui.QColor(endColor)
        self.repaint()

        self.endColorChanged.emit(self._endColor)
    # endregion

    # region Events
    def paintEvent(self, event):
        """
        The event for any paint requests made to this widget.

        :type event: QtGui.QPaintEvent
        :rtype: None
        """

        # Initialize painter
        #
        painter = QtGui.QPainter(self)
        self.initPainter(painter)

        # Calculate gradient points
        #
        rect = self.rect()
        center = rect.center()
        direction = self.direction()

        startPoint, endPoint = QtCore.QPointF(), QtCore.QPointF()

        if direction == QtCore.Qt.Horizontal:

            startPoint.setX(rect.left())
            startPoint.setY(center.y())

            endPoint.setX(rect.right())
            endPoint.setY(center.y())

        elif direction == QtCore.Qt.Vertical:

            startPoint.setX(center.x())
            startPoint.setY(rect.top())

            endPoint.setX(center.x())
            endPoint.setY(rect.bottom())

        else:

            raise TypeError(f'paintEvent() expects a valid direction ({direction} given)!')

        # Paint gradient
        #
        gradient = QtGui.QLinearGradient(startPoint, endPoint)
        gradient.setColorAt(0, self.startColor())
        gradient.setColorAt(1, self.endColor())

        painter.fillRect(rect, gradient)
    # endregion
