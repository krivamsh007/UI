# -----------------------------------------------------------------------------
# Copyright (c) [2025] [Vamshi Krishna Nagabhyru]
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------
#!/usr/bin/env python
import os, json, re, uuid, logging, time
from datetime import datetime, timedelta
from functools import lru_cache
from decimal import Decimal, InvalidOperation
import pandas as pd
from pandas import NamedAgg
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# -------------------- Split Column --------------------
def apply_transform_split_column(df, info):
    col_name = info.get("split_column")
    split_char = info.get("split_char")
    maxsplit = info.get("maxsplit", 1)
    registry = info.get("registry", {})
    if col_name and split_char:
        try:
            new_cols = df[col_name].astype(str).str.split(split_char, n=maxsplit, expand=True)
            friendly = internal_to_friendly(col_name, registry) if registry else col_name
            # If user provided new names, use them; otherwise use friendly defaults.
            new_col1 = info.get("new_col1") or f"{friendly} Part 1"
            if new_cols.shape[1] >= 2:
                new_col2 = info.get("new_col2") or f"{friendly} Part 2"
                df[new_col1] = new_cols[0]
                df[new_col2] = new_cols[1]
            else:
                df[new_col1] = new_cols[0]
        except Exception as e:
            logger.error("Split Column error for %s: %s", col_name, e)
    else:
        logger.warning("Split Column: missing required parameters.")
    return df

