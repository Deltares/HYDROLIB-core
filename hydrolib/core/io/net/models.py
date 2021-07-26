from pathlib import Path
from typing import Callable, List, Optional, Union

import matplotlib.pyplot as plt
import meshkernel
import netCDF4 as nc
import numpy as np

from hydrolib.core.basemodel import FileModel
from hydrolib.core.io.base import DummmyParser, DummySerializer
from hydrolib.core.models.net import Branch, Mesh1d, Mesh2d
from hydrolib.core.models.net import Network
