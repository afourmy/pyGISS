# Introduction

A Geographic Information System (GIS) software is a software designed to import, analyze and visualize geographic data.
PyGISS is a lightweight GIS software implemented both in tkinter (the standard Python library for GUI programming) and pyQT.
It allows users to create maps by importing shapefiles, a format that describes maps as a set of polygons.

![extended pyGISS](https://github.com/afourmy/PyGISS/blob/master/images/extended_pyGISS.PNG)

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

The extended PyGISS version also uses ImageTk from Pillow:

```
sudo apt-get install python3-tk (unix)
sudo apt-get install python3-pil.imagetk (unix)
pip install pillow (windows & unix)
```

# PyGISS versions

## Standard version (pyGISS.py, < 100 lines)

![pyGISS](https://github.com/afourmy/PyGISS/blob/master/images/pyGISS.PNG)

The standard version implements PyGISS in less than 100 lines of code.

It contains:
* a menu 'Import shapefile' for the user to choose a shapefile and draw the map.
* a menu 'Switch projection' to switch between the mercator and azimuthal orthographic projection.

The following bindings are implemented:
* the right-click button allows the user to move the display in any direction
* the scroll wheel can be used for zooming in and out.
* pressing the left-click button on the map will print the associated geographical coordinates (longitude, latitude).

A few shapefiles are available for testing in the 'PyGISS/shapefiles' folder (world countries, continents, France, US).

## Extended version (extended_pyGISS.py, < 500 lines)

![extended pyGISS](https://github.com/afourmy/PyGISS/blob/master/images/extended_pyGISS.PNG)

The extended version shows how to use PyGISS to create a full-on GIS software.
Besides the import of shapefiles, nodes can be created with a "Drag & Drop" system, moved on the map, and deleted.
They can also be imported by creating an Excel file that contains the longitude and latitude of the nodes. (an example is available in the 'PyGISS/import' folder).

To create a node, press the left-click button on the Python Software Foundation icon in the menu, and hold it down until you've reached the desired location on the canvas.
Pressing the left-click button on the canvas allows the user to either select one or several nodes, or move all selected nodes.
The right-click button and the scroll wheel work like in PyGISS standard version.

The menu on the left allows the user to import a shapefile and draw the associated map ("Import map"), erase the map or a selection of nodes, and switch between the mercator and azimuthal orthographic projections. 

For each node on the canvas, the geographical coordinates (longitude and latitude) are displayed under the node, and the position is updated in real-time upon moving the node.

## Golf version (golf_pyGISS.py, 5 lines)

![pyGISS](https://github.com/afourmy/PyGISS/blob/master/images/golf_pyGISS.PNG)

The golf version implements the core feature of PyGISS (import of shapefiles) in 5 lines of code. 
Upon running golf_GISS.py, a window pops up for the user to choose a shapefile.
The shapefile is then imported and drawn on the canvas. 
The mouse wheel allows the user to move on the map by zooming in and zooming out.

# How it works

![pyGISS](https://github.com/afourmy/PyGISS/blob/master/readme/how_it_works_0.png)


```
def draw_polygons(self):
    # create a Proj projection: we will use it later the convert longitudes and 
    # latitudes into projected coordinates
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
            # parse the coordinates
            land = str(land)[10:-2].replace(', ', ',').replace(' ', ',')
            coords = land.replace('(', '').replace(')', '').split(',')
            for lon, lat in zip(coords[0::2], coords[1::2]):
                # use the pyproj projection to convert geographic coordinates
                # into projected coordinates
                px, py = pyproj_projection(lon, lat)
                # if it's out of the map (for example for an azimuthal 
                # orthographic projection), do not process it
                if px > 1e+10:
                    continue
                qt_polygon.append(QPointF(px, py))
            # create the pyQT graphical item
            polygon_item = QGraphicsPolygonItem(qt_polygon)
            polygon_item.setBrush(self.land_brush)
            polygon_item.setZValue(1)
            # and return it
            yield polygon_item
```

# Contact

You can contact me at my personal email address:
```
''.join(map(chr, (97, 110, 116, 111, 105, 110, 101, 46, 102, 111, 
117, 114, 109, 121, 64, 103, 109, 97, 105, 108, 46, 99, 111, 109)))
```

or on the [Network to Code slack](http://networktocode.herokuapp.com "Network to Code slack"). (@minto)

# Credits

[pyshp](https://github.com/GeospatialPython/pyshp): A library to read and write ESRI Shapefiles.

[shapely](https://github.com/Toblerity/Shapely): A library for the manipulation and analysis of geometric objects in the Cartesian plane.

[pyproj](https://github.com/jswhit/pyproj): Python interface to PROJ4 library for cartographic transformations
