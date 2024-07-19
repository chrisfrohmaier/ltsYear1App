import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import shapely.geometry
from matplotlib.patches import Ellipse
from shapely.geometry import Polygon 
import json
import numpy as np
from code_editor import code_editor
from io import StringIO
import math

def plotEllipseTissot(ra, dec, radius=20):
    theta = np.deg2rad(dec)
    phi = np.deg2rad(ra - 360 if ra > 180 else ra)
    ellipse = Ellipse((phi,theta), 2*np.deg2rad(radius)/ np.cos(theta),
                      2*np.deg2rad(radius))
    vertices = ellipse.get_verts()     # get the vertices from the ellipse object
    
    verticesDeg = np.rad2deg(vertices)
    
    ra_out = [i + 360 if i < 0  else i for i in verticesDeg[:,0]]
    dec_out = verticesDeg[:,1]

    return np.column_stack((ra_out, dec_out))

def makeEllipse(ra_center, dec_center, a,b,theta):
    sample = 20
    alpha = [x / 20.0 * 2.0 * math.pi for x in range(0, sample+1)]
    theta=theta
    x0=ra_center
    y0=dec_center
    x=x0+a*np.sin(theta)
    y=y0+b*np.cos(theta)
    xell=x0+a*np.cos(alpha)*np.cos(theta)-b*np.sin(alpha)*np.sin(theta)
    yell=y0+a*np.cos(alpha)*np.sin(theta)+b*np.sin(alpha)*np.cos(theta)
    return np.column_stack((xell, yell))

f = open('demoArea.json')
io = f.read()

xsize = 420
ysize = xsize/2
longitude = np.linspace(0,360, int(xsize))
latitude = np.linspace(-90, 90, int(ysize))
grid_map_nan = np.load('ltsVPSelfie453.npy')

zmin = 10
zmax = np.nanmax(grid_map_nan)

colours = iter(px.colors.sequential.Tealgrn)


dataDefault = json.loads(str(io))




st.set_page_config(layout="wide")

st.title("4MOST Year 1 Long Term Scheduler")

st.divider()
st.header("Define Areas here")


custom_btns = [{"name": "Copy", "hasText":True, "alwaysOn": True,"style": {"top": "0.46rem", "right": "0.4rem", "commands": ["copyAll"]}},
                {"name": "Run",
"feather": "Play",
"primary": True,
"alwaysOn":True,
"hasText": True,
"showWithIcon": True,
"commands": ["submit"],
"style": {"bottom": "0.44rem", "right": "0.4rem"}
}]
response_dict = code_editor(str(io), lang="json", buttons=custom_btns, height=[10, 20])



def colorbar(zmin, zmax, n = 6):
    return dict(
        title = "Total Exposure Time<br>in pixel (minutes)",
        tickmode = "array",
        tickvals = np.linspace(np.log10(zmin), np.log10(zmax), n),
        ticktext = np.round(10 ** np.linspace(np.log10(zmin), np.log10(zmax), n), 0)
    )




layout = go.Layout(
    autosize=False,
    width=800, 
    height=600,
    title='Year 1 Long Term Scheduler Preference',
    xaxis=dict(
        title='R.A.',

    ),
    yaxis=dict(
        title='Declination',

    ))


fig = go.Figure(go.Heatmap(
        x=longitude,
        y=latitude,
        z=np.ma.log10(grid_map_nan),
    text=grid_map_nan,
    hovertemplate = 
    "<i>4MOST VP Exposure Time</i><br>" +
    "<b>RA</b>: %{x}<br>" +
    "<b>Decl.</b>: %{y}<br>" +
    "<b>Total t_exp (min)</b>: %{text:.1f}",
    zmin = np.log10(zmin), zmax = np.log10(zmax),
    colorbar = colorbar(zmin, zmax, 6),
    colorscale = 'Plasma',
    name=""
    ), layout=layout)
try:
    data = json.loads(str(response_dict['text']))
except:
    data = dataDefault
for i in data["year1Areas"]:

    if i['type']=='box':
        RA = i['RA']
        Dec = i['Dec']
        tfrac = i['t_frac']
        convex_hull = np.array(
        shapely.geometry.MultiPoint(
            [xy for xy in zip(RA, Dec)]
        ).convex_hull.exterior.coords
        )
        fig.add_trace(go.Scatter(
            x=convex_hull[:, 0],
            y=convex_hull[:, 1],
            showlegend=False,
            mode="lines",
            fill="toself",
            line=dict(color=next(colours), width=2),
            name="t_frac: "+str(tfrac)
        )
                     )
    elif i['type']=='circle':
        ra_center = i['RA_center']
        dec_center = i['Dec_center']
        radius = i['radius']
        tfrac = i['t_frac']
        tissot = plotEllipseTissot(ra_center, dec_center, radius = radius)
        fig.add_trace(go.Scatter(
        x=tissot[:, 0],
        y=tissot[:, 1],
        showlegend=False,
        mode="lines",
        fill="toself",
        line=dict(color=next(colours), width=2),
        name="t_frac: "+str(tfrac)
    )
                 )
    
    elif i['type']=='ellipse':
        tfrac = i['t_frac']
        ellipse = makeEllipse(i['RA_center'], i['Dec_center'], i['a'],i['b'],np.deg2rad(i['theta']) )
        ellipse_convex_hull = np.array(
        shapely.geometry.MultiPoint(
            ellipse
        ).convex_hull.exterior.coords
        )
        fig.add_trace(go.Scatter(
        x=ellipse_convex_hull[:, 0],
        y=ellipse_convex_hull[:, 1],
        showlegend=False,
        mode="lines",
        fill="toself",
        line=dict(color=next(colours), width=2),
        name="t_frac: "+str(tfrac)
    )
                 )
        
    else:
        print("Please enter a valid shape: 'box', 'circle', 'ellispe'")
        continue

fig['layout']['xaxis']['autorange'] = "reversed"
fig.update_layout(yaxis_range=[-90,30])

st.divider()
st.header("Sky Plot of Year 1 Preference")
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.header("Example JSON inputs")
st.json({'fruit':'apple'})