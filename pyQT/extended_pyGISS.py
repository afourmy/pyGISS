from collections import OrderedDict
from inspect import stack
from os.path import abspath, dirname, join, pardir
from pyproj import Proj
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
                         QPen,
                         QPixmap,
                         QPolygonF
                         )
from PyQt5.QtWidgets import (
                             QAction,
                             QApplication, 
                             QComboBox,
                             QFileDialog,
                             QFrame,
                             QGraphicsEllipseItem,
                             QGraphicsItem,
                             QGraphicsPixmapItem,
                             QGraphicsPolygonItem,
                             QGraphicsRectItem,
                             QGraphicsScene,
                             QGraphicsView,
                             QGridLayout,
                             QGroupBox,
                             QHBoxLayout,
                             QLabel,
                             QLineEdit,
                             QMainWindow,
                             QPushButton, 
                             QStyleFactory,
                             QWidget,  
                             )
import shapefile
import shapely.geometry
import xlrd

## Structure of this file
# Controller: the main window
# View: the canvas where the map is displayed
# Node: the Python Software foundation icon that can be created in the view
# MainMenu: the left-side menu. Contains 3 QGroupBox
# - Node creation: create a node with the drag & drop system
# - GISParametersMenu: change the projection and the size of nodes in the view
# - Deletion: delete selected nodes, all nodes, or the map

class Controller(QMainWindow):
    
    def __init__(self, path_app):
        super().__init__()
        self.path_shapefiles = join(path_app, pardir, 'shapefiles')
        self.path_projects = join(path_app, pardir, 'projects')
        path_icon = join(path_app, pardir, 'images')
        self.setWindowIcon(QIcon(join(path_icon, 'globe.png')))
        
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        import_shapefile_icon = QIcon(join(path_icon, 'globe.png'))
        import_shapefile = QAction(import_shapefile_icon, 'Import a shapefile', self)
        import_shapefile.setStatusTip('Import a shapefile')
        import_shapefile.triggered.connect(self.import_shapefile)
        
        import_project_icon = QIcon(join(path_icon, 'import_project.png'))
        import_project = QAction(import_project_icon, 'Import a Excel project', self)
        import_project.setStatusTip('Import a project (Excel format)')
        import_project.triggered.connect(self.import_project)
        
        toolbar = self.addToolBar('')
        toolbar.resize(1500, 1500)
        toolbar.setIconSize(QSize(70, 70))
        toolbar.addAction(import_shapefile)
        toolbar.addAction(import_project)
        
        # paths to the icons (standard node and selected node)
        path_node = join(path_icon, 'node.png')
        path_selected_node = join(path_icon, 'selected_node.png')
        
        # used as a label for the menu
        self.node_pixmap = QPixmap(path_node)
        
        # used on the canvas
        self.gnode_pixmap = QPixmap(path_node).scaled(
                                                    QSize(100, 100), 
                                                    Qt.KeepAspectRatio,
                                                    Qt.SmoothTransformation
                                                    )
        self.selected_gnode_pixmap = QPixmap(path_selected_node).scaled(
                                                    QSize(100, 100), 
                                                    Qt.KeepAspectRatio,
                                                    Qt.SmoothTransformation
                                                    )
        
        self.view = View(self)
        self.main_menu = MainMenu(self)
        
        layout = QHBoxLayout(central_widget)
        layout.addWidget(self.main_menu) 
        layout.addWidget(self.view)
        
    def import_project(self):
        filepath = QFileDialog.getOpenFileName(
                                            self, 
                                            'Import project', 
                                            self.path_projects
                                            )[0]
        book = xlrd.open_workbook(filepath)
        sheet = book.sheet_by_index(0)
        for row_index in range(1, sheet.nrows):
            x, y = self.view.to_canvas_coordinates(*sheet.row_values(row_index))
            Node(self, QPointF(x, y))
        
    def import_shapefile(self):
        self.view.shapefile = QFileDialog.getOpenFileName(
                                            self, 
                                            'Import a shapefile', 
                                            self.path_shapefiles
                                            )[0]
        self.view.redraw_map()

class View(QGraphicsView):
    
    projections = OrderedDict([
    ('Spherical', Proj('+proj=ortho +lat_0=48 +lon_0=17')),
    ('Mercator', Proj(init='epsg:3395')),
    ('WGS84', Proj(init='epsg:3857')),
    ('ETRS89 - LAEA Europe', Proj("+init=EPSG:3035"))
    ])
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setRenderHint(QPainter.Antialiasing)
        self.proj = 'Spherical'
        self.ratio, self.offset = 1/400, (0, 0)
        self.display = True
        self.shapefile = join(controller.path_shapefiles, 'World countries_1.shp')
        
        # brush for water and lands
        self.water_brush = QBrush(QColor(64, 164, 223))
        self.land_brush = QBrush(QColor(52, 165, 111))
        self.land_pen = QPen(QColor(0, 0, 0))
        
        # draw the map 
        self.polygons = self.scene.createItemGroup(self.draw_polygons())
        self.draw_water()
        
        # set of graphical nodes
        self.nodes = set()

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
        
    ## Drag & Drop system
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('application/x-dnditemdata'):
            event.acceptProposedAction()

    dragMoveEvent = dragEnterEvent
        
    def dropEvent(self, event):
        pos = self.mapToScene(event.pos())
        geo_pos = self.to_geographical_coordinates(pos.x(), pos.y())
        if event.mimeData().hasFormat('application/x-dnditemdata'):
            new_node = Node(self.controller, pos)
            
    ## Map functions
    
    def to_geographical_coordinates(self, x, y):
        px, py = (x - self.offset[0])/self.ratio, (self.offset[1] - y)/self.ratio
        return self.projections[self.proj](px, py, inverse=True)
        
    def to_canvas_coordinates(self, longitude, latitude):
        px, py = self.projections[self.proj](longitude, latitude)
        return px*self.ratio + self.offset[0], -py*self.ratio + self.offset[1]
        
    def move_to_geographical_coordinates(self):
        for node in self.nodes:
            node.setPos(QPointF(*self.to_canvas_coordinates(
                                                            node.longitude, 
                                                            node.latitude
                                                            )))

    def draw_polygons(self):
        sf = shapefile.Reader(self.shapefile)       
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
                for lon, lat in land.exterior.coords:
                    print(lon, lat)
                    px, py = self.to_canvas_coordinates(lon, lat)
                    if px > 1e+10:
                        continue
                    qt_polygon.append(QPointF(px, py))
                polygon_item = QGraphicsPolygonItem(qt_polygon)
                polygon_item.setBrush(self.land_brush)
                polygon_item.setPen(self.land_pen)
                polygon_item.setZValue(1)
                yield polygon_item
                
    def draw_water(self):
        if self.proj in ('Spherical', 'ETRS89 - LAEA Europe'):
            cx, cy = self.to_canvas_coordinates(17, 48)
            # if the projection is ETRS89, we need the diameter and not the radius
            R = 6371000*self.ratio*(1 if self.proj == 'Spherical' else 2)
            earth_water = QGraphicsEllipseItem(cx - R, cy - R, 2*R, 2*R)
            earth_water.setZValue(0)
            earth_water.setBrush(self.water_brush)
            self.polygons.addToGroup(earth_water)
        else:
            # we compute the projected bounds of the Mercator (3395) projection
            # upper-left corner x and y coordinates:
            ulc_x, ulc_y = self.to_canvas_coordinates(-180, 84)
            # lower-right corner x and y coordinates
            lrc_x, lrc_y = self.to_canvas_coordinates(180, -84.72)
            # width and height of the map (required for the QRectItem)
            width, height = lrc_x - ulc_x, lrc_y - ulc_y
            earth_water = QGraphicsRectItem(ulc_x, ulc_y, width, height)
            earth_water.setZValue(0)
            earth_water.setBrush(self.water_brush)
            self.polygons.addToGroup(earth_water)
            
    def show_hide_map(self):
        self.display = not self.display
        self.polygons.show() if self.display else self.polygons.hide()
        
    def delete_map(self):
        self.scene.removeItem(self.polygons)
            
    def redraw_map(self):
        self.delete_map()
        self.polygons = self.scene.createItemGroup(self.draw_polygons())
        self.draw_water()
        # replace the nodes at their geographical location
        self.move_to_geographical_coordinates()
        
class Node(QGraphicsPixmapItem):
    
    def __init__(self, controller, position):
        self.controller = controller
        self.view = controller.view
        self.view.nodes.add(self)
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
        self.view.scene.addItem(self)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setPos(position)
        
    def itemChange(self, change, value):
        if change == self.ItemSelectedHasChanged:
            if self.isSelected():
                self.setPixmap(self.selection_pixmap)
            else:
                self.setPixmap(self.pixmap)
        if change == self.ItemPositionHasChanged:
            x, y = self.pos().x(), self.pos().y()
            lon, lat = self.view.to_geographical_coordinates(x, y)
            lon, lat = round(lon, 4), round(lat, 4)
            self.longitude, self.latitude = lon, lat
            # when the node is created, the ItemPositionHasChanged is triggered:
            # we create the label
            if not hasattr(self, 'label'):
                self.label = self.view.scene.addSimpleText('test')
                self.label.setZValue(15)
            self.label.setPos(self.pos() + QPoint(-70, 50))
            self.label.setText('({}, {})'.format(lon, lat))
        return QGraphicsPixmapItem.itemChange(self, change, value)
        
    def self_destruction(self):
        self.view.scene.removeItem(self.label)
        self.view.scene.removeItem(self)
        
class MainMenu(QWidget):
    
    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller
        self.setFixedSize(350, 800)
        self.setAcceptDrops(True)
                
        node_creation_groupbox = NodeCreation(self.controller)
        map_projection_groupbox = GISParametersMenu(self.controller)
        node_deletion_groupbox = Deletion(self.controller)
        
        layout = QGridLayout(self)
        layout.addWidget(node_creation_groupbox)
        layout.addWidget(map_projection_groupbox)
        layout.addWidget(node_deletion_groupbox)
        
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
        drag.setHotSpot(child.pos() + QPoint(10, 0))

        if drag.exec_(Qt.CopyAction | Qt.MoveAction, Qt.CopyAction) == Qt.MoveAction:
            child.close()
        else:
            child.show()
            child.setPixmap(pixmap)
        
class GISParametersMenu(QGroupBox):  

    def __init__(self, controller):
        super().__init__()
        self.view = controller.view
        
        # choose the projection and change it
        choose_projection = QLabel('Projection')
        self.projection_list = QComboBox(self)
        self.projection_list.addItems(View.projections)
        
        # choose the map/nodes ratio
        ratio = QLabel('Node size')
        self.ratio_edit = QLineEdit('400')
        self.ratio_edit.setMaximumWidth(120)
        
        draw_map_button = QPushButton('Redraw map')
        draw_map_button.clicked.connect(self.redraw_map)
        show_hide_map_button = QPushButton('Show / Hide map')
        show_hide_map_button.clicked.connect(self.show_hide_map)
        
        layout = QGridLayout(self)
        layout.addWidget(choose_projection, 0, 0)
        layout.addWidget(self.projection_list, 0, 1)
        layout.addWidget(ratio, 1, 0)
        layout.addWidget(self.ratio_edit, 1, 1)
        layout.addWidget(draw_map_button, 2, 0, 1, 2)
        layout.addWidget(show_hide_map_button, 3, 0, 1, 2)
        
    def redraw_map(self, _):
        self.view.ratio = 1/float(self.ratio_edit.text())
        self.view.proj = self.projection_list.currentText()
        self.view.redraw_map()
        
    def show_hide_map(self):
        self.view.show_hide_map()
        
class Deletion(QGroupBox):  

    def __init__(self, controller):
        super().__init__()
        self.view = controller.view
        
        delete_selection_button = QPushButton('Delete selected nodes')
        delete_selection_button.clicked.connect(self.delete_selection)
        delete_all_nodes_button = QPushButton('Delete all nodes')
        delete_all_nodes_button.clicked.connect(self.delete_all_nodes)
        delete_map_button = QPushButton('Delete the map')
        delete_map_button.clicked.connect(self.delete_map)
        
        layout = QGridLayout(self)
        layout.addWidget(delete_selection_button, 0, 0)
        layout.addWidget(delete_all_nodes_button, 1, 0)
        layout.addWidget(delete_map_button, 2, 0)
        
    def delete_selection(self):
        for node in self.view.scene.selectedItems():
            node.self_destruction()
        
    def delete_all_nodes(self):
        for node in self.view.nodes:
            node.self_destruction()
            
    def delete_map(self):
        self.view.delete_map()
        
if str.__eq__(__name__, '__main__'):
    import sys
    pyGISS = QApplication(sys.argv)
    pyGISS.setStyle(QStyleFactory.create('Fusion'))
    path_app = dirname(abspath(stack()[0][1]))
    controller = Controller(path_app)
    controller.setWindowTitle('pyGISS: a lightweight GIS software')
    controller.setGeometry(100, 100, 1500, 900)
    controller.show()
    sys.exit(pyGISS.exec_())