from shapely import geometry
from shapely.geometry import (
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)

from meshkernel import GeometryList
from core.mesh import Network
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection


def multipolygon_to_geometrylist(multipolygon):
    total = []
    for i, polygon in enumerate(multipolygon):
        if i > 0:
            total.append(np.array([[-999.0, -999.0]]))
        gl = polygon_to_geometrylist(polygon)
        total.append(np.c_[gl.x_coordinates, gl.y_coordinates])
    xcrds, ycrds = np.vstack(total).T
    return GeometryList(xcrds.copy(), ycrds.copy())


def polygon_to_geometrylist(polygon):
    seqs = [polygon.exterior.coords[:]]
    for interior in polygon.interiors:
        seqs.append([[-998.0, -998.0]])
        seqs.append(interior.coords[:])
    xcrds, ycrds = np.vstack(seqs).T
    return GeometryList(xcrds.copy(), ycrds.copy())


if __name__ == "__main__":
    network = Network()

    mesh2d = network.mesh2d

    gdf = gpd.read_file(r"d:\Documents\4362.10 Windanalyses ECMWF\Data\GIS\clipgeo.shp")
    polygon = gdf.at[0, "geometry"]

    geometrylist = polygon_to_geometrylist(polygon[0])

    # Generate rectilinear withn polygon bounds
    mesh2d.create_rectilinear_within_polygon(polygon=geometrylist, dx=0.1, dy=0.1)

    # Clip to polygon
    mesh2d.clip_by_polygon(polygon=geometrylist)

    # Refine parts
    refinement = gpd.read_file(r"d:\Documents\4362.10 Windanalyses ECMWF\Data\GIS\verfijnen.shp")

    last_level = 0
    for row in refinement.itertuples():
        geometrylist = polygon_to_geometrylist(row.geometry.intersection(polygon))
        print(geometrylist)
        mesh2d.refine_within_polygon(geometrylist, level=1)
        break

    mesh2d_output = mesh2d.get_mesh2d_output()

    fig, ax = plt.subplots()
    edge_nodes = mesh2d_output.edge_nodes.reshape((-1, 2))
    edge_coords = np.dstack([mesh2d_output.node_x[edge_nodes], mesh2d_output.node_y[edge_nodes]])
    lc = LineCollection(edge_coords)
    ax.add_collection(lc)
    ax.autoscale_view()
    plt.show()

    print("klaar")
