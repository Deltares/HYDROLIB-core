# Dataframe handling
We can use `DataFrame`s from pandas together with hydrolib-core.

Note that this functionality can only work on files that are in essence tables
and are represented by a `List` of objects in hydrolib-core.

Examples of such `FileModel`s with their `List` fields are:
- ForcingModel.forcing
- CrossDefModel.definition
- CrossLocModel.crosssection
- ExtModel.boundary
- ExtModel.lateral

Say we load in a .bc file and want the resulting forcing in a dataframe.

```python
from hydrolib.core.io.bc.models import ForcingModel

filepath = (
    "tests/data/input/e02/f101_1D-boundaries/c01_steady-state-flow/BoundaryConditions.bc"
)
m = ForcingModel(filepath)
m.forcing

[Constant(comments=None, datablock=[[2.5]], name='T1_Dwn_Bnd', function='constant', quantity=['waterlevelbnd'], unit=['m'], offset=0.0, factor=1.0),
 Constant(comments=None, datablock=[[100.0]], name='T1_Up_Bnd', function='constant', quantity=['dischargebnd'], unit=['m³/s'], offset=0.0, factor=1.0),
 Constant(comments=None, datablock=[[2.5]], name='T2_Dwn_Bnd', function='constant', quantity=['waterlevelbnd'], unit=['m'], offset=0.0, factor=1.0),
 TimeSeries(comments=None, datablock=[[0.0, 0.0], [1800.0, 100.0], [4320.0, 100.0]], name='T2_Up_Bnd', function='timeseries', quantity=['time', 'dischargebnd'], unit=['minutes since 2015-01-01 00:00:00', 'm³/s'], timeinterpolation='linear', offset=0.0, factor=1.0),
 TimeSeries(comments=None, datablock=[[0.0, 0.0], [1800.0, 2.5], [4320.0, 2.5]], name='T3_Dwn_Bnd', function='timeseries', quantity=['time', 'waterlevelbnd'], unit=['minutes since 2015-01-01 00:00:00', 'm'], timeinterpolation='linear', offset=0.0, factor=1.0),
 Constant(comments=None, datablock=[[100.0]], name='T3_Up_Bnd', function='constant', quantity=['dischargebnd'], unit=['m³/s'], offset=0.0, factor=1.0),
 TimeSeries(comments=None, datablock=[[0.0, 0.0], [1800.0, 100.0], [4320.0, 100.0]], name='T4_Up_Bnd', function='timeseries', quantity=['time', 'dischargebnd'], unit=['minutes since 2015-01-01 00:00:00', 'm³/s'], timeinterpolation='linear', offset=0.0, factor=1.0),
 QHTable(comments=None, datablock=[[50.0, 1.25], [100.0, 2.5], [150.0, 3.75]], name='T4_Dwn_Bnd', function='qhtable', quantity=['qhbnd discharge', 'qhbnd waterlevel'], unit=['m³/s', 'm']),
 TimeSeries(comments=None, datablock=[[-2629440.0, 0.0]], name='model_wide', function='timeseries', quantity=['time', 'wind_speed'], unit=['minutes since 2015-01-01 00:00:00', 'm/s'], timeinterpolation='linear', offset=0.0, factor=1.0),
 TimeSeries(comments=None, datablock=[[-2629440.0, 0.0]], name='model_wide', function='timeseries', quantity=['time', 'wind_from_direction'], unit=['minutes since 2015-01-01 00:00:00', 'degree'], timeinterpolation='linear', offset=0.0, factor=1.0),
 TimeSeries(comments=None, datablock=[[-2629440.0, 0.0]], name='model_wide', function='timeseries', quantity=['time', 'air_temperature'], unit=['minutes since 2015-01-01 00:00:00', 'degrees C'], timeinterpolation='linear', offset=0.0, factor=1.0),
 TimeSeries(comments=None, datablock=[[-2629440.0, 0.0]], name='model_wide', function='timeseries', quantity=['time', 'humidity'], unit=['minutes since 2015-01-01 00:00:00', 'percentage'], timeinterpolation='linear', offset=0.0, factor=1.0),
 TimeSeries(comments=None, datablock=[[-2629440.0, 0.0]], name='model_wide', function='timeseries', quantity=['time', 'cloudiness'], unit=['minutes since 2015-01-01 00:00:00', 'percentage'], timeinterpolation='linear', offset=0.0, factor=1.0)]
```

We now have a list of forcings that we can convert into a DataFrame.
```python
import pandas as pd
df = pd.DataFrame([f.__dict__ for f in m.forcing])

   comments                                       datablock        name    function  ... offset factor  _header  timeinterpolation
0      None                                         [[2.5]]  T1_Dwn_Bnd    constant  ...    0.0    1.0  forcing             linear
1      None                                       [[100.0]]   T1_Up_Bnd    constant  ...    0.0    1.0  forcing             linear
2      None                                         [[2.5]]  T2_Dwn_Bnd    constant  ...    0.0    1.0  forcing             linear
3      None  [[0.0, 0.0], [1800.0, 100.0], [4320.0, 100.0]]   T2_Up_Bnd  timeseries  ...    0.0    1.0  forcing             linear
4      None      [[0.0, 0.0], [1800.0, 2.5], [4320.0, 2.5]]  T3_Dwn_Bnd  timeseries  ...    0.0    1.0  forcing             linear
5      None                                       [[100.0]]   T3_Up_Bnd    constant  ...    0.0    1.0  forcing             linear
6      None  [[0.0, 0.0], [1800.0, 100.0], [4320.0, 100.0]]   T4_Up_Bnd  timeseries  ...    0.0    1.0  forcing             linear
7      None     [[50.0, 1.25], [100.0, 2.5], [150.0, 3.75]]  T4_Dwn_Bnd     qhtable  ...    NaN    NaN  forcing                NaN
8      None                             [[-2629440.0, 0.0]]  model_wide  timeseries  ...    0.0    1.0  forcing             linear
9      None                             [[-2629440.0, 0.0]]  model_wide  timeseries  ...    0.0    1.0  forcing             linear
10     None                             [[-2629440.0, 0.0]]  model_wide  timeseries  ...    0.0    1.0  forcing             linear
11     None                             [[-2629440.0, 0.0]]  model_wide  timeseries  ...    0.0    1.0  forcing             linear
12     None                             [[-2629440.0, 0.0]]  model_wide  timeseries  ...    0.0    1.0  forcing             linear

[13 rows x 10 columns]
```
Note that because there are several types of forcings, with different fields, some values have become NaN.


We can also convert this DataFrame back to a `ForcingModel`.
```python
fm = ForcingModel(forcing=df.to_dict('records'))
fm.forcing == m.forcing

True
```
