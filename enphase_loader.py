import json
import requests

import pandas as pd
from sqlalchemy import create_engine, text

from enlighten import enlightenAPI_v4
from datetime import datetime, timedelta


# Load the user config
with open('config/enlighten_v4_config.json') as config_file:
    config = json.load(config_file)

api = enlightenAPI_v4(config)

pw = config["db_pwd"]
pcon = create_engine(f"postgresql+psycopg2://enl:{pw}@127.0.0.1:5432/enlighten", echo=True)

def load_telemetry(system_id, type):
    with pcon.connect() as connection:
        max_date = connection.execute(
            text(f"select max(end_at) + interval '1 minute' from {type}")).scalar()

    if max_date is None:
        start_at = datetime.now() - timedelta(days=50)
    else:
        start_at = max_date

    # do not call any api if the last data is only 2 hours old
    # this is quite conservative, but for testing purposes, we might run out of "call budget"
    if start_at < datetime.now() - timedelta(hours=2):
        df = api.telemetry(
            system_id,
            telemetry_type=type,
            start_at=start_at,
            granularity="week",
            as_type="dataframe"
        )

        df.to_sql(type, pcon, if_exists="append")

system_id = config["system_id"]

load_telemetry(system_id, "production_micro")
load_telemetry(system_id, "production_meter")
load_telemetry(system_id, "battery")
load_telemetry(system_id, "consumption")
load_telemetry(system_id, "export")
load_telemetry(system_id, "import")
