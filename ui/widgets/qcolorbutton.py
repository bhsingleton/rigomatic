from dcc.vendor.Qt import QtCore, QtWidgets, QtGui

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QColorButton(QtWidgets.QPushButton):
    """
    Overload of `QPushButton` that has an editable color attribute and separate clicked/double-clicked signals.
    """

    # region Signals
    colorChanged = QtCore.Signal(QtGui.QColor)
    colorDropped = QtCore.Signal(QtGui.QColor)
    doubleClicked = QtCore.Signal()
    # endregion

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key parent: QtWidgets.QWidget
        :rtype: None
        """

        # Call parent method
        #
        super(QColorButton, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._start = None
        self._clicks = 0

        # Initialize click timer
        #
        self._timer = QtCore.QTimer()
        self._timer.setObjectName('timer')
        self._timer.setSingleShot(True)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self.on_timer_timeout)
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

        # Paint background
        #
        rect = self.rect()  # type: QtCore.QRect
        palette = self.palette()  # type: QtGui.QPalette
        text = self.text()  # type: str

        if self.underMouse():

            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(palette.highlight())
            painter.fillRect(rect, palette.highlight())

            painter.setPen(QtGui.QPen(palette.highlightedText(), 1))
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawText(rect, QtCore.Qt.AlignCenter, text)

        else:

            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(palette.button())
            painter.fillRect(rect, palette.button())

            painter.setPen(QtGui.QPen(palette.text(), 1))
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawText(rect, QtCore.Qt.AlignCenter, text)

    def mousePressEvent(self, event):
        """
        This event handler can be reimplemented in a subclass to receive mouse press events for the widget.
        The default implementation implements the closing of popup widgets when you click outside the window.
        For other widget types it does nothing.

        :type event: QtGui.QMouseEvent
        :rtype: None
        """

        # Evaluate button press
        #
        button = event.button()

        if button == QtCore.Qt.LeftButton:

            # Check if timer requires starting
            #
            event.accept()

            if not self._timer.isActive():

                self._start = event.pos()
                self._clicks = 0
                self._timer.start()

            else:

                log.debug('Timer is already running...')

        else:

            # Pass event to parent class
            #
            event.ignore()

    def mouseMoveEvent(self, event):

        # Evaluate button press
        #
        buttons = event.buttons()

        if buttons & QtCore.Qt.LeftButton:

            # Evaluate drag distance
            #
            event.accept()

            if (event.pos() - self._start).manhattanLength() < QtWidgets.QApplication.startDragDistance():

                # Execute drag operation
                #
                mimeData = QtCore.QMimeData()
                mimeData.setColorData(self.color())

                drag = QtGui.QDrag(self)
                drag.setMimeData(mimeData)
                drag.exec_(QtCore.Qt.CopyAction | QtCore.Qt.MoveAction)

        else:

            # Pass event to parent class
            #
            event.ignore()

    def mouseReleaseEvent(self, event):
        """
        This event handler can be reimplemented in a subclass to receive mouse release events for the widget.

        :type event: QtGui.QMouseEvent
        :rtype: None
        """

        # Evaluate button press
        #
        button = event.button()

        if button == QtCore.Qt.LeftButton:

            # Accept event
            #
            event.accept()

            # Check if timer is running
            #
            if self._timer.isActive():

                self._clicks += 1

            else:

                self.clicked.emit()

        else:

            # Pass event to parent class
            #
            event.ignore()

    def dragEnterEvent(self, event):
        """
        This event handler is called when a drag is in progress and the mouse enters this widget.
        The event is passed in the event parameter.
        If the event is ignored, the widget won't receive any drag move events.

        :type event: QtGui.QDragEvent
        :rtype: None
        """

        if self.acceptDrops():

            event.acceptProposedAction()

        else:

            event.ignore()

    def dropEvent(self, event):
        """
        This event handler is called when the drag is dropped on this widget.
        The event is passed in the event parameter.

        :type event: QtGui.QDropEvent
        :rtype: None
        """

        mimeData = event.mimeData()
        hasColor = mimeData.hasColor()

        acceptsDrops = self.acceptDrops()

        if hasColor and acceptsDrops:

            event.accept()

            color = mimeData.colorData()
            self.colorDropped.emit(color)
            self.setColor(color)

        else:

            event.ignore()
    # endregion

    # region Methods
    def color(self, asRGB=False, normalize=False):
        """
        Returns the button color.

        :type asRGB: bool
        :type normalize: bool
        :rtype: Union[QtGui.QColor, Tuple[float, float, float]]
        """

        palette = self.palette()
        color = palette.color(QtGui.QPalette.Button)

        if asRGB:

            if normalize:

                return color.redF(), color.greenF(), color.blueF()

            else:

                return color.red(), color.green(), color.blue()

        else:

            return color

    @QtCore.Slot(QtGui.QColor)
    def setColor(self, color):
        """
        Updates the button color.

        :type color: QtGui.QColor
        :rtype: None
        """

        color = QtGui.QColor(color)
        highlightColor = color.darker() if color.lightnessF() > 0.5 else color.lighter()
        textColor = QtGui.QColor.fromHslF(0.0, 0.0, round(1.0 - color.lightnessF()))
        textHighlightColor = textColor.lighter() if textColor.lightnessF() > 0.5 else textColor.darker()
        
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Button, color)
        palette.setColor(QtGui.QPalette.ButtonText, textColor)
        palette.setColor(QtGui.QPalette.Highlight, highlightColor)
        palette.setColor(QtGui.QPalette.HighlightedText, textHighlightColor)

        self.setPalette(palette)
        self.repaint()

        self.colorChanged.emit(color)
    # endregion

    # region Slots
    @QtCore.Slot()
    def on_timer_timeout(self):
        """
        Slot method for the `timer` widget's `timeout` signal.

        :rtype: None
        """

        if self._clicks == 0:

            pass

        elif self._clicks == 1:

            self.clicked.emit()

        else:

            self.doubleClicked.emit()
    # endregion
