import json
from pathlib import Path

from sqlalchemy import create_engine

from shiny import *
import shinycomponents as sc
import shinycomponents.adminlte as sca

import pages

from datetime import datetime, date
import pandas as pd
import plotly.io as pio
import constants as co

pio.templates.default = "plotly_white"

app_ui = sca.page_dashboard(
    sca.dashboardHeader(
        ui.TagList(
            sca.menuItem("tab_history", "History", "content_history"),
            sca.menuItem("tab_comparison", "Comparison", "content_comparison"),
            sca.menuItem("tab_calendar", "Calendar", "content_calendar"),
            sca.menuItem("tab_stats", "Statistics", "content_stats")
        ),
        ui.input_action_button(
            "in_refresh",
            label=None,
            icon=sca.icon("bi-arrow-clockwise")
        ),
        title = "Enphase Enlighten",
    ),
    sca.dashboardBody(
        sca.dashboardTabContainer(
            sca.tabItem(
                "content_history",
                pages.history.history_ui("history"),
                selected=False
            ),
            sca.tabItem(
                "content_comparison",
                pages.comparison.comp_ui("comparison"),
                selected=False
            ),
            sca.tabItem(
                "content_calendar",
                pages.calendar.calendar_ui("calendar"),
                selected=False
            ),
            sca.tabItem(
                "content_stats",
                pages.stats.stats_ui("stats"),
                selected=True
            ),
        )
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

    db_con = reactive.Value(create_engine(f"postgresql+psycopg2://{username}:{password}@{host_name}:{port}/{db_name}", echo=True))

    data = reactive.Value(pd.DataFrame())

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

        df_all["Time of Day"] = df_all["Time"].apply(lambda x: datetime.combine(date.today(), x.time()))
        df_all["Hour"] = df_all["Time"].dt.floor("H")
        df_all["Day"] = df_all["Time"].dt.floor("D")
        df_all["Month"] = df_all["Day"].dt.month_name()
        df_all["Week"] = df_all["Day"].dt.day_of_year.apply(lambda x: x // 7)
        df_all["Year"] = df_all["Day"].dt.year

        print(df_all.info())

        data.set(df_all)

    @reactive.Calc
    def enriched_data():
        req(not data().empty)

        df_all = data().copy()
        # Remove dates from interventions. Outliers are possible for these dates
        df_all = df_all[~df_all["Day"].isin([date(2023,5,4),date(2023,5,17)])]

        # Overall maximum per quarter
        # Calculate max production per quarter
        # df_max_by_time = df_all \
        #     .groupby("Time of Day")["Produced"] \
        #     .max() \
        #     .reset_index() \
        #     .rename(columns={"Produced": "Max Produced"})
        #
        # # Correct by noting that quarter production cannot be less than
        # # max production in the quarters before and the max production in the quarters after at the same time
        # df_max_by_time["Cummax Left"] = df_max_by_time["Max Produced"].cummax()
        # df_max_by_time = df_max_by_time.set_index(df_max_by_time.index[::-1]).sort_index()
        # df_max_by_time["Cummax Right"] = df_max_by_time["Max Produced"].cummax()
        # df_max_by_time["Max Produced"] = df_max_by_time.apply(lambda x: min([x["Cummax Left"], x["Cummax Right"]]), axis=1)
        #
        # df_max_by_time = df_max_by_time[["Time of Day", "Max Produced"]]

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