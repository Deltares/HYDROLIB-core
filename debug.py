from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

p = Path("d:/Documents/4390.10 TKI Hydrolib/data/hydamo_net.nc")

from hydrolib.core.models.net import Mesh
from meshkernel import GeometryList

m = Mesh.from_file(p)

gl = GeometryList(
    x_coordinates=np.array([140000, 142000, 142000, 140000, 140000], dtype=np.double),
    y_coordinates=np.array([393000, 393000, 394500, 394500, 393000], dtype=np.double),
)

# m._mk.contacts_compute_multiple(node_mask=np.full(m.mesh1d.node_x.size, True))

m._mk.contacts_compute_single(node_mask=np.full(m.mesh1d.node_x.size, True), polygons=gl)

fig, ax = plt.subplots(figsize=(10, 10))

mesh1d_kwargs = dict(lw=0.75, color="red")
mesh2d_kwargs = dict(lw=0.75, color="blue")
links1d2d_kwargs = dict(lw=0.75, color="black", zorder=3)

m.plot(ax, mesh1d_kwargs=mesh1d_kwargs, mesh2d_kwargs=mesh2d_kwargs, links1d2d_kwargs=links1d2d_kwargs)

ax.autoscale()
ax.set_aspect(1.0)

plt.show()

print()
