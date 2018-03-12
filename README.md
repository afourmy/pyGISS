# Introduction

A Geographic Information System (GIS) software is a software designed to import, analyze and visualize geographic data.
PyGISS is a lightweight GIS software implemented both in tkinter and pyQt.
Users can display maps using any type of projection and create objects either by importing an Excel file containing GPS coordinates, or with a Drag & Drop system.

![pyGISS demo](https://github.com/afourmy/PyGISS/blob/master/readme/pyGISS.gif)

# PyGISS versions

## Standard version (pyGISS.py, < 100 lines)

![pyGISS](https://github.com/afourmy/PyGISS/blob/master/readme/pyGISS.png)

The standard version implements PyGISS in less than 100 lines of code.

It contains:
* a menu 'Import shapefile' for the user to choose a shapefile and draw the map.
* a menu 'Switch projection' to switch between the mercator and azimuthal orthographic projection.

The following bindings are implemented:
* the scroll wheel can be used for zooming in and out.
* pressing the left-click button on the map will print the associated geographical coordinates (longitude, latitude).

A few shapefiles are available for testing in the 'PyGISS/shapefiles' folder (world countries, continents, US).

## Extended version (extended_pyGISS.py, < 500 lines)

![extended pyGISS](https://github.com/afourmy/PyGISS/blob/master/readme/extended_pyGISS.png)

In the extended version, besides the import of shapefiles, nodes can be created with a "Drag & Drop" system, moved on the map, resized, and deleted.
They can also be imported by creating an Excel file that contains the longitude and latitude of the nodes. (an example is available in the 'PyGISS/projects' folder).

## Golf version (golf_pyGISS.py, 5 lines)

![pyGISS](https://github.com/afourmy/PyGISS/blob/master/readme/golf_pyGISS.png)

The golf version implements the core feature of PyGISS (import and drawing of shapefiles + zoom system) in 5 lines of code. 

# How it works

A point on the earth is defined as a longitude and a latitude.
Longitude and latitude are angles.

![pyGISS](https://github.com/afourmy/PyGISS/blob/master/readme/how_it_works_0.png)

We need to convert a point on a sphere (3D) into a point on a map (2D). This is called a "projection".
According to the [remarkable theorem](https://en.wikipedia.org/wiki/Theorema_Egregium), a projection always causes a distortion (distances, shapes, areas, and/or directions are not preserved).
For example, the Mercator projection preserves angles but fails to preserve area.

![pyGISS](https://github.com/afourmy/PyGISS/blob/master/readme/how_it_works_1.png)

To convert geographic coordinates (longitude and latitude) into projected coordinates (planar coordinates), we use a library called pyproj.

![pyGISS](https://github.com/afourmy/PyGISS/blob/master/readme/how_it_works_2.png)

The first thing that we need to create a GIS software is a GUI programming framework. There are many such frameworks in Python: tkinter, PyQt, pyside, wx_python, pyGTK, etc.
pyGISS is implemented on two different frameworks: tkinter and pyQt.

Once we've chosen a framework, we need a widget that supports the drawing of 2D graphical items. 
In tkinter, this widget is called a Canvas; in pyQt, it is a QGraphicsView.

This widget has functions to create rectangles, circles, and most importantly, polygons.
Indeed, as demonstrated below with Italy, a map can be represented as a set of polygons.

![pyGISS](https://github.com/afourmy/PyGISS/blob/master/readme/how_it_works_3.png)

To draw the polygons, we need their coordinates.
A shapefile (.shp) is a file that describes vector data as a set of shapes. For a map, there are two types of shapes: polygons and multipolygons.
Polygons and multipolygons are defined as a set of points (longitude, latitude) on the earth.

![pyGISS](https://github.com/afourmy/PyGISS/blob/master/readme/how_it_works_4.png)

To read the shapefile and extract the shapes it contains, we will use the pyshp library.
Once this is done, we have a set of shapes, polygons and mutipolygons.

![pyGISS](https://github.com/afourmy/PyGISS/blob/master/readme/how_it_works_5.png)

We can draw polygons with the GUI framework polygon function. A multipolygon is actually composed of multiple polygons.
To draw a multipolygon, we will decompose it into the polygons it is made of with the shapely library.

![pyGISS](https://github.com/afourmy/PyGISS/blob/master/readme/how_it_works_6.png)

The resulting algorithm is:

``` 
- Use pyshp to read the shapefile
- Extract the shapes of the shapefile
- When a shape is a multipolygon, decompose it into multiple polygons with shapely
- Use pyproj to convert the shape's geographic coordinates into projected coordinates
- Use the GUI framework method to draw the polygons
``` 

Below is the algorithm implemented with the pyQt framework:

```python
def draw_polygons(self):
    # create a Proj projection: we will use it later the convert longitudes and 
    # latitudes into projected coordinates
    # The EPSG 3395 code corresponds to the Mercator projection
    pyproj_projection = pyproj.Proj(init="epsg:3395")
    
    # use the pyshp library to open the shapefile
    shapefile = shapefile.Reader(self.shapefile)
    
    # extract all the shapes it contains
    polygons = shapefile.shapes() 
    
    for polygon in polygons:
        
        # convert shapefile geometries into shapely geometries
        # to extract the polygons contained in multipolygons
        polygon = shapely.geometry.shape(polygon)
        
        # if it is a polygon, we use a list to make it iterable
        if polygon.geom_type == 'Polygon':
            polygon = [polygon]
            
        for land in polygon:
            qt_polygon = QPolygonF()
            for lon, lat in land.exterior.coords:  
                # use the pyproj projection to convert geographic coordinates
                # into projected coordinates
                px, py = pyproj_projection(lon, lat)
                
                # if it's out of the map (for example for an azimuthal 
                # orthographic projection), ignore it
                if px > 1e+10:
                    continue
                qt_polygon.append(QPointF(px, py))
                
            # create the pyQt graphical item and return it
            yield QGraphicsPolygonItem(qt_polygon)
```

# PyGISS dependencies

PyGIS relies on three Python libraries:

* pyshp, used for reading shapefiles.
* shapely, used for converting a multipolygon into a set of polygons
* pyproj, used for translating geographic coordinates (longitude and latitude) into projected coordinates

Before using PyGISS, you must make sure all these libraries are properly installed:

```
pip install pyshp
pip install shapely
pip install pyproj
```

For the Qt version of pyGISS, pyQt5 is required: it can be download from the [Riverband website](https://www.riverbankcomputing.com/software/pyqt/download5)

For the tkinter version of the extended PyGISS, Pillow (ImageTk) is required: it can be installed directly via pip.

```
sudo apt-get install python3-tk (unix)
sudo apt-get install python3-pil.imagetk (unix)
pip install pillow (windows & unix)
```
