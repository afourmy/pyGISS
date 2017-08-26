from inspect import stack
from os.path import abspath, dirname, join, pardir
from PyQt5.QtCore import (
                          QByteArray,
                          QDataStream,
                          QIODevice,
                          QMimeData,
                          QPoint,
                          QPointF,
                          QSize,
                          Qt
                          )
from PyQt5.QtGui import (
                         QBrush,
                         QCursor,
                         QColor, 
                         QDrag, 
                         QIcon,
                         QPainter, 
                         QPixmap,
                         QPolygonF
                         )
from PyQt5.QtWidgets import (
                             QAction,
                             QApplication, 
                             QFrame,
                             QGraphicsEllipseItem,
                             QGraphicsItem,
                             QGraphicsPixmapItem,
                             QGraphicsPolygonItem,
                             QGraphicsScene,
                             QGraphicsView,
                             QGridLayout,
                             QGroupBox,
                             QHBoxLayout,
                             QLabel,
                             QMainWindow,
                             QPushButton, 
                             QWidget,  
                             )
import pyproj
import shapefile
import shapely.geometry

class View(QGraphicsView):
    
    projections = {
    'mercator': pyproj.Proj(init="epsg:3395"),
    'spherical': pyproj.Proj('+proj=ortho +lon_0=28 +lat_0=47')
    }
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setRenderHint(QPainter.Antialiasing)
        self.proj = 'spherical'
        self.ratio, self.offset = 1/1000, (0, 0)
        
        # brush for water and lands
        water_brush = QBrush(QColor(64, 164, 223))
        land_brush = QBrush(QColor(52, 165, 111))
        
        # draw the planet
        cx, cy = self.to_canvas_coordinates(28, 47)
        R = 6371000*self.ratio
        earth = QGraphicsEllipseItem(cx - R, cy - R, 2*R, 2*R)
        earth.setZValue(0)
        earth.setBrush(water_brush)
        
        self.path_to_shapefile = 'C:/Users/minto/Desktop/pyGISS/shapefiles/World countries.shp'
        for polygon in self.create_polygon():
            polygon.setBrush(land_brush)
            polygon.setZValue(1)
            self.scene.addItem(polygon)
            
        self.scene.addItem(earth)
        
    def to_geographical_coordinates(self, x, y):
        px, py = (x - self.offset[0])/self.ratio, (self.offset[1] - y)/self.ratio
        return self.projections[self.proj](px, py, inverse=True)
        
    def to_canvas_coordinates(self, longitude, latitude):
        px, py = self.projections[self.proj](longitude, latitude)
        return px*self.ratio + self.offset[0], -py*self.ratio + self.offset[1]

    def create_polygon(self):
        sf = shapefile.Reader(self.path_to_shapefile)       
        polygons = sf.shapes() 
        for polygon in polygons:
            # convert shapefile geometries into shapely geometries
            # to extract the polygons of a multipolygon
            polygon = shapely.geometry.shape(polygon)
            # if it is a polygon, we use a list to make it iterable
            if polygon.geom_type == 'Polygon':
                polygon = [polygon]
            for land in polygon:
                qt_polygon = QPolygonF() 
                land = str(land)[10:-2].replace(', ', ',').replace(' ', ',')
                coords = land.replace('(', '').replace(')', '').split(',')
                for lon, lat in zip(coords[0::2], coords[1::2]):
                    px, py = self.to_canvas_coordinates(lon, lat)
                    if px > 1e+10:
                        continue
                    qt_polygon.append(QPointF(px, py))
                yield QGraphicsPolygonItem(qt_polygon)

    ## Zoom system

    def zoom_in(self):
        self.scale(1.25, 1.25)
        
    def zoom_out(self):
        self.scale(1/1.25, 1/1.25)
        
    def wheelEvent(self, event):
        self.zoom_in() if event.angleDelta().y() > 0 else self.zoom_out()
        
    ## Mouse bindings
        
    def mouseMoveEvent(self, event):
        # sliding the scrollbar with the right-click button
        if event.buttons() == Qt.RightButton:
            self.trigger_menu = False
            offset = self.cursor_pos - event.pos()
            self.cursor_pos = event.pos()
            x_value = self.horizontalScrollBar().value() + offset.x()
            y_value = self.verticalScrollBar().value() + offset.y()
            self.horizontalScrollBar().setValue(x_value)
            self.verticalScrollBar().setValue(y_value)
        super().mouseMoveEvent(event)
        
    def mousePressEvent(self, event):
        # activate rubberband for selection
        # by default, the rubberband is active for both clicks, we have to
        # deactivate it explicitly for the right-click
        if event.buttons() == Qt.LeftButton:
            self.setDragMode(QGraphicsView.RubberBandDrag)
        if event.button() == Qt.RightButton:
            self.cursor_pos = event.pos()
        super().mousePressEvent(event)
        # pos = self.mapToScene(event.pos())
        # print(*self.to_geographical_coordinates(pos.x(), pos.y()))
        
    ## Drag & Drop system
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('application/x-dnditemdata'):
            event.acceptProposedAction()

    dragMoveEvent = dragEnterEvent
        
    def dropEvent(self, event):
        pos = self.mapToScene(event.pos())
        geo_pos = self.to_geographical_coordinates(pos.x(), pos.y())
        if event.mimeData().hasFormat('application/x-dnditemdata'):
            new_node = Node(self.controller)
            new_node.setPos(pos)

class Controller(QMainWindow):
    
    def __init__(self, path_app):
        super().__init__()
        path_icon = abspath(join(path_app, pardir, 'images'))
        
        # a QMainWindow needs a central widget for the layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        ## Menu bar
        menu_bar = self.menuBar()
        
        new_project = QAction('Add project', self)
        new_project.setStatusTip('Create a new project')
        new_project.triggered.connect(self.close)
        
        delete_project = QAction('Delete project', self)
        delete_project.setStatusTip('Delete the current project')
        delete_project.triggered.connect(self.close)
        
        self.statusBar()
        
        new_project_icon = QIcon(join(path_icon, 'new_project.png'))
        new_project = QAction(new_project_icon, 'New project', self)
        new_project.setStatusTip('Create a new project')
        new_project.triggered.connect(self.add_project)
        
        selection_icon = QIcon(join(path_icon, 'selection.png'))
        selection_mode = QAction(selection_icon, 'Selection mode', self)
        selection_mode.setStatusTip('Switch to selection mode')
        selection_mode.triggered.connect(self.add_project)
        
        self.node_pixmap = QPixmap(join(path_icon, 'node.png'))
        self.selected_node_pixmap = QPixmap(join(path_icon, 'selected_node.png'))
        self.gnode_pixmap = QPixmap(join(path_icon, 'node.png')).scaled(
                                                    QSize(100, 100), 
                                                    Qt.KeepAspectRatio,
                                                    Qt.SmoothTransformation
                                                    )
        self.selected_gnode_pixmap = QPixmap(join(path_icon, 'node.png')).scaled(
                                                    QSize(100, 100), 
                                                    Qt.KeepAspectRatio,
                                                    Qt.SmoothTransformation
                                                    )
        
        self.view = View(self)
        self.main_menu = MainMenu(self)
        
        layout = QHBoxLayout(central_widget)
        layout.addWidget(self.main_menu) 
        layout.addWidget(self.view)
        
    def add_project(self):
        pass
        
class MainMenu(QWidget):
    
    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller
        self.setMinimumSize(300, 300)
        self.setAcceptDrops(True)
                
        node_creation_groupbox = NodeCreation(self.controller)
                
        map_projection_groupbox = QGroupBox()
        
        layout = QGridLayout(self)
        layout.addWidget(node_creation_groupbox)
        layout.addWidget(map_projection_groupbox)
        
class NodeCreation(QGroupBox):
    
    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller
        
        label = QLabel()
        label.setMaximumSize(200, 200)
        label.setPixmap(self.controller.node_pixmap)
        label.setScaledContents(True)
        label.show()
        label.setAttribute(Qt.WA_DeleteOnClose)
        
        layout = QGridLayout(self)
        layout.addWidget(label, 0, 0)
        
    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat('application/x-dnditemdata'):
            if event.source() == self:
                event.setDropAction(Qt.MoveAction)
                event.accept()
            else:
                event.acceptProposedAction()
        else:
            event.ignore()

    dragEnterEvent = dragMoveEvent

    def mousePressEvent(self, event):

        child = self.childAt(event.pos())
        
        if not child:
            return
        
        pixmap = QPixmap(child.pixmap().scaled(
                                 QSize(100, 100), 
                                 Qt.KeepAspectRatio,
                                 Qt.SmoothTransformation
                                 ))
                        
        mime_data = QMimeData()
        mime_data.setData('application/x-dnditemdata', QByteArray())

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.setPixmap(pixmap)
        drag.setHotSpot(child.pos() + QPoint(10, -50))

        if drag.exec_(Qt.CopyAction | Qt.MoveAction, Qt.CopyAction) == Qt.MoveAction:
            child.close()
        else:
            child.show()
            child.setPixmap(pixmap)
            
class Node(QGraphicsPixmapItem):
    
    def __init__(self, controller):
        self.controller = controller

        # we retrieve the pixmap based on the subtype to initialize a QGPI
        self.pixmap = self.controller.gnode_pixmap
        self.selection_pixmap = self.controller.selected_gnode_pixmap                                                
        super().__init__(self.pixmap)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setOffset(
                       QPointF(
                               -self.boundingRect().width()/2, 
                               -self.boundingRect().height()/2
                               )
                       )
        self.setZValue(10)
        self.controller.view.scene.addItem(self)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
    def itemChange(self, change, value):
        if change == self.ItemSelectedHasChanged:
            if self.isSelected():
                self.setPixmap(self.selection_pixmap)
            else:
                self.setPixmap(self.pixmap)
        return QGraphicsPixmapItem.itemChange(self, change, value)
        
if str.__eq__(__name__, '__main__'):
    import sys
    pyGISS = QApplication(sys.argv)
    path_app = dirname(abspath(stack()[0][1]))
    controller = Controller(path_app)
    controller.setGeometry(100, 100, 1500, 900)
    controller.show()
    sys.exit(pyGISS.exec_())