from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyproj
import shapefile
import shapely.geometry
import sys

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

class PyQTGISS(QWidget):
    def __init__(self):
        super().__init__()
        self.view = View(self)
        layout = QGridLayout(self)
        layout.addWidget(self.view, 0, 0, 1, 1)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PyQTGISS()
    window.setGeometry(100, 100, 1500, 900)
    window.show()
    sys.exit(app.exec_())