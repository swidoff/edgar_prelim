from sqlalchemy import text
import pandas as pd
from edgar_load import query_prelims
from edgar_validate import validate_prelims
from edgar_db import prelim_engine