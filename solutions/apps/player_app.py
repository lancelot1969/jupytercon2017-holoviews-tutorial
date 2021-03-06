# -*- coding: utf-8 -*-
"""
Created on Wed Oct 10 19:58:59 2018

@author: akirakosyan
"""

import dask.dataframe as dd
import holoviews as hv
import geoviews as gv

from bokeh.models import Slider, Button, CustomJS
from bokeh.layouts import layout
from bokeh.io import curdoc
from bokeh.models import WMTSTileSource
from bokeh.models.callbacks import CustomJS

from holoviews.operation.datashader import datashade, aggregate, shade
from holoviews.plotting.util import fire
shade.cmap = fire

hv.extension('bokeh')
renderer = hv.renderer('bokeh').instance(mode='server')

# Load data
usecols = ['tpep_pickup_datetime', 'dropoff_x', 'dropoff_y']
ddf = dd.read_csv('../data/nyc_taxi.csv', parse_dates=['tpep_pickup_datetime'], usecols=usecols)
#ddf = dd.read_csv(r'C:\Users\akirakosyan\Documents\bokeh-cspire-app\temp\jupytercon2017-holoviews-tutorial\notebooks\data\nyc_taxi.csv', 
#parse_dates=['tpep_pickup_datetime'], usecols=usecols)
ddf['hour'] = ddf.tpep_pickup_datetime.dt.hour
ddf = ddf.persist()

from bokeh.models import WMTSTileSource
url = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{Z}/{Y}/{X}.jpg'
wmts = gv.WMTS(WMTSTileSource(url=url))

stream = hv.streams.Stream.define('HourSelect', hour=0)()
points = hv.Points(ddf, kdims=['dropoff_x', 'dropoff_y'])
dmap = hv.util.Dynamic(points, operation=lambda obj, hour: obj.select(hour=hour),
                       streams=[stream])

# Apply aggregation
aggregated = aggregate(dmap, link_inputs=True)

# Shade the data
shaded = shade(aggregated)

# Define PointerX stream, attach to points and declare DynamicMap for cross-section and VLine
pointer = hv.streams.PointerX(x=ddf.dropoff_x.loc[0].compute().iloc[0], source=points)
section = hv.util.Dynamic(aggregated, operation=lambda obj, x: obj.sample(dropoff_x=x),
                          streams=[pointer], link_inputs=False)
vline = hv.DynamicMap(lambda x: hv.VLine(x), streams=[pointer])

# Define options
hv.opts("RGB [width=800 height=600 xaxis=None yaxis=None] VLine (color='black' line_width=1)")
hv.opts("Curve [width=100 yaxis=None show_frame=False] (color='black') {+framewise} Layout [shared_axes=False]")

# Combine it all into a complex layout
hvobj = (wmts * shaded * vline) << section

### Pass the HoloViews object to the renderer
plot = renderer.get_plot(hvobj, doc=curdoc())

# Define a slider and button


def animate_update():
    year = slider.value + 1
    if year > end:
        year = start
    slider.value = year

def slider_update(attrname, old, new):
    stream.event(hour=new)

start, end = 0, 23
slider = Slider(start=start, end=end, value=0, step=1, title="Hour")
slider.on_change('value', slider_update)


callback_id = None
	
def animate():
    global callback_id
    if button.label == '\u25B6 Play':
        button.label = '\u23F8 Pause'
        callback_id = curdoc().add_periodic_callback(animate_update, 50)
    else:
        button.label = '\u25B6 Play'
        curdoc().remove_periodic_callback(callback_id)
		
				
button = Button(label='\u25B6 Play', width=60)
button.on_click(animate)
	

# Combine the bokeh plot on plot.state with the widgets
layout = layout([
    [plot.state],
    [slider, button],
], sizing_mode='fixed')

curdoc().add_root(layout)
