from inspect import stack
from os.path import abspath, dirname, join, pardir
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyproj
import shapefile
import shapely.geometry

class View(QGraphicsView):
    
    projections = {
    'mercator': pyproj.Proj(init="epsg:3395"),
    'spherical': pyproj.Proj('+proj=ortho +lon_0=28 +lat_0=47')
    }
    
    def __init__(self, parent):
        super().__init__()
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

    def wheelEvent(self, event):
        factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self.scale(factor, factor)
        
    def mousePressEvent(self, event):
        pos = self.mapToScene(event.pos())
        print(*self.to_geographical_coordinates(pos.x(), pos.y()))

class pyGISS(QMainWindow):
    
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
        
        self.node_pixmap = QPixmap(join(path_icon, 'icon'))
        
        self.view = View(self)
        
        layout = QHBoxLayout(central_widget)
        # layout.addWidget(main_menu) 
        layout.addWidget(self.view)
        
    def add_project(self):
        pass
        
class NodeCreationPanel(QGroupBox):
    
    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller
        self.setTitle('Node creation')
        self.setMinimumSize(300, 300)
        self.setAcceptDrops(True)
                
        # exit connection lost because of the following lines
        layout = QtWidgets.QGridLayout(self)
        label = QLabel(self)
        pixmap = image.scaled(
                              label.size(), 
                              Qt.KeepAspectRatio,
                              Qt.SmoothTransformation
                              )
        label.setPixmap(self.controller.node_pixmap)
        label.show()
        label.setAttribute(Qt.WA_DeleteOnClose)
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
        # retrieve the label 
        child = self.childAt(event.pos())
        if not child:
            return
        
        pixmap = QPixmap(child.pixmap())
        item_data = QtCore.QByteArray()
        data_stream = QtCore.QDataStream(item_data, QtCore.QIODevice.WriteOnly)
        data_stream << pixmap << QtCore.QPoint(event.pos() - child.pos())

        mime_data = QtCore.QMimeData()
        mime_data.setData('application/x-dnditemdata', item_data)

        drag = QtGui.QDrag(self)
        drag.setMimeData(mime_data)
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos() - child.pos())

        if drag.exec_(Qt.CopyAction | Qt.MoveAction, Qt.CopyAction) == Qt.MoveAction:
            child.close()
        else:
            child.show()
            child.setPixmap(pixmap)

if str.__eq__(__name__, '__main__'):
    import sys
    app = QApplication(sys.argv)
    path_app = dirname(abspath(stack()[0][1]))
    window = pyGISS(path_app)
    window.setGeometry(100, 100, 1500, 900)
    window.show()
    sys.exit(app.exec_())