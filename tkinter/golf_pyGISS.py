import tkinter as t, pyproj as p, tkinter.filedialog as d;c=t.Canvas();f=d.askopenfilenames();y=lambda g:p.Proj(init='epsg:3395')(*g)
for o in __import__('shapefile').Reader(f[0]).shapes():
 for l in map(lambda p: p.exterior.coords,__import__('shapely.geometry',(),(),['']).shape(o)):
  c.create_polygon(sum(((y(x)[0],-y(x)[1])for x in l),()))
c.bind('<MouseWheel>',lambda e:c.scale('all',e.x,e.y,(e.delta>0)*2or 0.5,(e.delta>0)*2or 0.5));c.pack();t.mainloop()