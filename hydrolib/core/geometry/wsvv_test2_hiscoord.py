import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xa
from shapely.geometry import LineString

# hisfile = r"D:\Work\Project\P1414\Models\Combined\V21_WBD_HD\run_model_changed_coords\dflowfm\output\DFM_his.nc"
hisfile = r"d:\dam_ar\dflowfm_models\WsVV\testmodel\output\DFM_his.nc"
ds = xa.open_dataset(hisfile)

da_name = "culvert_s1up"

da = getattr(ds, da_name)
print(ds.culvert_id.values)
print(da.coords["culvert"].__dir__())
obj_ids = getattr(da, da.coords.dims[1]).values
da_geom = getattr(ds, da.attrs["geometry"])
da_node_count = getattr(ds, da_geom.attrs["node_count"]).values
print(da_node_count)
da_node_count_cum = np.cumsum(da_node_count)
print(da_node_count_cum)
da_geom_coords = da_geom.attrs["node_coordinates"].split()
print(len(obj_ids))
coord_list = []

for coords in da_geom_coords:
    coord = getattr(ds, coords)
    coord_list.append(coord.values)

print(coord_list)

obj_list = []
for obj_id in obj_ids:
    # print(da.isel(culvert=obj_id))
    # coords_bounds = [da_node_count_cum[obj_id] - da_node_count[obj_id] da_node_count_cum[obj_id]]
    coord_ixs = range(
        da_node_count_cum[obj_id] - da_node_count[obj_id], da_node_count_cum[obj_id]
    )
    xs = coord_list[0][coord_ixs]
    ys = coord_list[1][coord_ixs]

    coords = list(zip(xs, ys))
    geom = LineString(coords)
    obj = dict([("id", obj_id), ("geometry", geom)])
    print(obj)
    break


df = da.to_dataframe().reset_index()
time = df.time.unique()
ids = df.culvert_id.unique()
print(time.shape, ids.shape)

# tuples = list(zip(*[ids, time]))
# indes = pd.MultiIndex(tuples)
df.set_index(keys=["culvert", "time"], inplace=True)


print(df.columns)
print(df.head())
print(df.shape)
print(df.groupby("culvert").head())
print(df.loc[0, :, :])

for obj in obj_ids:
    print(obj)
    obj_id = ids[obj]

    break
