import json
from pathlib import Path

from sqlalchemy import create_engine, text

from shiny import *
import shinycomponents as sc
import shinycomponents.adminlte as sca

import pages

from enlighten import enlightenAPI_v4

from datetime import datetime, date, timedelta
import pandas as pd
import plotly.io as pio
import constants as co

import shinycomponents.busyindicator as scb

pio.templates.default = "plotly_white"

app_ui = ui.page_navbar(
    ui.nav(
        "Today",
        pages.today.today_ui("today"),
        value="id_today"
    ),
    ui.nav(
        "History",
        pages.history.history_ui("history"),
        value="id_history"
    ),
    ui.nav(
        "Comparison",
        pages.comparison.comp_ui("comparison"),
        value="id_comparison"
    ),
    ui.nav(
        "Calendar",
        pages.calendar.calendar_ui("calendar"),
        value="id_calendar"
    ),
    ui.nav(
        "Stats",
        pages.stats.stats_ui("stats"),
        value="id_stats"
    ),
    title="Enphase Enlighten",
    bg="var(--bs-dark)",
    inverse=True,
    position="fixed-top",
    id="app_navbar",
    selected="id_today",
    header=ui.tags.head(
        ui.tags.link(rel="stylesheet",
            type = "text/css",
            href = "css/styles.css"
        ),
        ui.tags.link(
            rel="stylesheet",
            type = "text/css",
            href = "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.3/font/bootstrap-icons.css"
        ),
    ),
    footer=ui.TagList(
        # sca.use_adminlte_components(),
        scb.busybar(color="#FF0000", height=4, type="auto"),
    )
)


def server(input, output, session):
    with open('config/enlighten_v4_config.json') as config_file:
        config = json.load(config_file)


    username = config["db_user"]
    password = config["db_pwd"]
    db_name = config["db_name"]
    host_name = config["host_name"]
    port = config["port"]

    pcon = create_engine(f"postgresql+psycopg2://{username}:{password}@{host_name}:{port}/{db_name}", echo=True)
    api = enlightenAPI_v4(config)

    data = reactive.Value(pd.DataFrame())

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

    db_con = reactive.Value(pcon)

    @reactive.Effect
    def load_data():
        req(db_con())



        df_production = pd.read_sql("select * from production_meter", db_con()).rename(
            columns=co.column_mapping["production"])
        df_consumption = pd.read_sql("select * from consumption", db_con()).rename(
            columns=co.column_mapping["consumption"])
        df_battery = pd.read_sql("select * from battery", db_con()).rename(columns=co.column_mapping["battery"])
        df_import = pd.read_sql("select * from import", db_con()).rename(columns=co.column_mapping["import"])
        df_export = pd.read_sql("select * from export", db_con()).rename(columns=co.column_mapping["export"])
        df_export["Exported"] = -df_export["Exported"]
        df_consumption["Consumed"] = - df_consumption["Consumed"]

        df_all = df_import \
            .merge(df_export, how="left", on=["System Id", "Time"]) \
            .merge(df_production, how="left", on=["System Id", "Time"]) \
            .merge(df_consumption, how="left", on=["System Id", "Time"])

        print(df_all.info())

        df_all["Time of Day"] = df_all["Time"].apply(lambda x: datetime.combine(date.today(), x.time()))
        df_all["Hour"] = df_all["Time"].dt.floor("H")
        df_all["Day"] = df_all["Time"].dt.date
        df_all["Day of Week"] = df_all["Time"].dt.dayofweek
        df_all["Day of Month"] = df_all["Time"].dt.day
        df_all["Month"] = df_all["Time"].dt.month
        df_all["Month Name"] = df_all["Time"].dt.month_name()
        df_all["Week"] = df_all["Time"].dt.day_of_year.apply(lambda x: x // 7)
        df_all["Year"] = df_all["Time"].dt.year

        print(df_all.info())

        data.set(df_all)

    @reactive.Calc
    def enriched_data():
        req(not data().empty)

        df_all = data().copy()
        # Remove dates from interventions. Outliers are possible for these dates
        df_all = df_all[~df_all["Day"].isin([date(2023,5,4),date(2023,5,17)])]

        df_max_global = calculate_maximum(df_all, "Produced", "Max Produced (Global)")
        df_max_by_month = calculate_maximum(df_all, "Produced", "Max Produced (Month)", "Month")
        df_max_by_week = calculate_maximum(df_all, "Produced", "Max Produced (Week)", "Week")

        df_enriched = data() \
            .merge(df_max_global, how="left", left_on="Time of Day", right_on="Time of Day") \
            .merge(df_max_by_month, how="left", left_on=["Month", "Time of Day"], right_on=["Month", "Time of Day"]) \
            .merge(df_max_by_week, how="left", left_on=["Week", "Time of Day"], right_on=["Week", "Time of Day"])

        return df_enriched


    pages.history.history_server("history", enriched_data)
    pages.comparison.comp_server("comparison", enriched_data)
    pages.calendar.calendar_server("calendar", enriched_data)
    pages.stats.stats_server("stats", enriched_data)
    pages.today.today_server("today", enriched_data)

app = App(app_ui, server, static_assets=Path.joinpath(Path(__file__).parent, "assets"))



def calculate_maximum(df, column_name, new_column_name="Max Produced", groupby_column=None):
    # Overall maximum per quarter
    # Calculate max production per quarter
    if groupby_column is None:
        df_max_by_time = df \
            .groupby("Time of Day")[column_name] \
            .max() \
            .reset_index() \
            .rename(columns={column_name: new_column_name})

        cummax_left = df_max_by_time[new_column_name].cummax()
        cummax_right = df_max_by_time[new_column_name] \
            .sort_index(inplace=False, ascending=False) \
            .cummax()

    else:
        df_max_by_time = df \
            .groupby([groupby_column, "Time of Day"])[column_name] \
            .max() \
            .reset_index() \
            .rename(columns={column_name: new_column_name})

        cummax_left = df_max_by_time \
            .groupby(groupby_column)[new_column_name] \
            .cummax() \
            .rename("Cummax Left")
        cummax_right = df_max_by_time \
            .sort_index(inplace=False, ascending=False) \
            .groupby(groupby_column)[new_column_name] \
            .cummax() \
            .rename("Cummax Right") \
            .sort_index(inplace=False, ascending=True)

    df_max_corrected = pd.concat([cummax_left, cummax_right], axis=1).min(axis=1)
    df_max_by_time[new_column_name] = df_max_corrected

    return df_max_by_time


def main():
    run_app(app)

if __name__ == "__main__":
    main()