from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
                             QPushButton, 
                             QWidget, 
                             QApplication, 
                             QLabel, 
                             QGraphicsPixmapItem
                             )
import sys

class PhotoViewer(QtWidgets.QGraphicsView):
    def __init__(self, parent):
        super(PhotoViewer, self).__init__(parent)
        self._scene = QtWidgets.QGraphicsScene(self)
        pixmap = QPixmap('C:\\Users\minto\\Desktop\\pyGISS\\land_shallow_topo_21600.tif')
        self._photo = QGraphicsPixmapItem(pixmap)
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        # self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))

    # def fitInView(self):
    #     rect = QtCore.QRectF(self._photo.pixmap().rect())
        # if not rect.isNull():
        #     unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
        #     print('test')
        #     self.scale(1 / unity.width(), 1 / unity.height())
        #     viewrect = self.viewport().rect()
        #     scenerect = self.transform().mapRect(rect)
        #     factor = min(viewrect.width() / scenerect.width(),
        #                  viewrect.height() / scenerect.height())
        #     self.scale(factor, factor)
        #     self.centerOn(rect.center())
        #     self._zoom = 0

    # def setPhoto(self, pixmap=None):
    #     if pixmap and not pixmap.isNull():
    #         self.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
    #         self._photo.setPixmap(pixmap)
    #         # self.fitInView()
    #     else:
    #         self.setDragMode(QtGui.QGraphicsView.NoDrag)
    #         self._photo.setPixmap(QtGui.QPixmap())

    # def zoomFactor(self):
    #     return self._zoom

    def wheelEvent(self, event):
        factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self.scale(factor, factor)

class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.viewer = PhotoViewer(self)
        self.edit = QtWidgets.QLineEdit(self)
        self.edit.setReadOnly(True)
        self.button = QtWidgets.QToolButton(self)
        self.button.setText('...')
        self.button.clicked.connect(self.handleOpen)
        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(self.viewer, 0, 0, 1, 2)
        layout.addWidget(self.edit, 1, 0, 1, 1)
        layout.addWidget(self.button, 1, 1, 1, 1)

    def handleOpen(self):
        path = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Choose Image', self.edit.text())
        if path:
            self.edit.setText(path)
            self.viewer.setPhoto(QtGui.QPixmap(path))

if __name__ == '__main__':


    app = QApplication(sys.argv)
    window = Window()
    window.setGeometry(500, 300, 800, 600)
    window.show()
    sys.exit(app.exec_())