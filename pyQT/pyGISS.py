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
        self.water_brush = QBrush(QColor(64, 164, 223))
        self.land_brush = QBrush(QColor(52, 165, 111))
        
    def wheelEvent(self, event):
        factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self.scale(factor, factor)
        
    def mousePressEvent(self, event):
        pos = self.mapToScene(event.pos())
        print(*self.to_geographical_coordinates(pos.x(), pos.y()))
        
    def to_geographical_coordinates(self, x, y):
        px, py = (x - self.offset[0])/self.ratio, (self.offset[1] - y)/self.ratio
        return self.projections[self.proj](px, py, inverse=True)
        
    def to_canvas_coordinates(self, longitude, latitude):
        px, py = self.projections[self.proj](longitude, latitude)
        return px*self.ratio + self.offset[0], -py*self.ratio + self.offset[1]

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
                land = str(land)[10:-2].replace(', ', ',').replace(' ', ',')
                coords = land.replace('(', '').replace(')', '').split(',')
                for lon, lat in zip(coords[0::2], coords[1::2]):
                    px, py = self.to_canvas_coordinates(lon, lat)
                    if px > 1e+10:
                        continue
                    qt_polygon.append(QPointF(px, py))
                polygon_item = QGraphicsPolygonItem(qt_polygon)
                polygon_item.setBrush(self.land_brush)
                polygon_item.setZValue(1)
                yield polygon_item
                
    def draw_water(self):
        if self.proj in ('spherical'):
            cx, cy = self.to_canvas_coordinates(28, 47)
            R = 6371000*self.ratio
            earth_water = QGraphicsEllipseItem(cx - R, cy - R, 2*R, 2*R)
            earth_water.setZValue(0)
            earth_water.setBrush(self.water_brush)
            self.polygons.addToGroup(earth_water)
        else:
            ulc_x, ulc_y = self.to_canvas_coordinates(-180, 84)
            lrc_x, lrc_y = self.to_canvas_coordinates(180, -84.72)
            width, height = lrc_x - ulc_x, lrc_y - ulc_y
            earth_water = QGraphicsRectItem(ulc_x, ulc_y, width, height)
            earth_water.setZValue(0)
            earth_water.setBrush(self.water_brush)
            self.polygons.addToGroup(earth_water)
            
    def redraw_map(self):
        if hasattr(self, 'polygons'):
            self.scene.removeItem(self.polygons)
        self.polygons = self.scene.createItemGroup(self.draw_polygons())
        self.draw_water()

class PyQTGISS(QMainWindow):
    def __init__(self):
        super().__init__()
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        menu_bar = self.menuBar()
        import_shapefile = QAction('Import shapefile', self)
        import_shapefile.triggered.connect(self.import_shapefile)
        switch_projection = QAction('Switch projection', self)
        switch_projection.triggered.connect(self.switch_projection)
        menu_bar.addAction(import_shapefile)
        menu_bar.addAction(switch_projection)
        self.view = View(self)
        layout = QGridLayout(central_widget)
        layout.addWidget(self.view, 0, 0, 1, 1)
                
    def import_shapefile(self):
        self.view.shapefile = QFileDialog.getOpenFileName(self, 'Import')[0]
        self.view.redraw_map()
        
    def switch_projection(self):
        self.view.proj = 'mercator' if self.view.proj == 'spherical' else 'spherical'
        self.view.redraw_map()

if str.__eq__(__name__, '__main__'):
    import sys
    app = QApplication(sys.argv)
    window = PyQTGISS()
    window.setGeometry(100, 100, 1500, 900)
    window.show()
    sys.exit(app.exec_())