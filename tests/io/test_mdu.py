from typing import List, Optional

import pytest
from pydantic import ValidationError

from hydrolib.core.io.ini.models import INIBasedModel
from hydrolib.core.io.ext.models import Lateral


class TestModels:
    """Test class to test all classes and methods contained in the
    hydrolib.core.io.mdu.models.py module"""

