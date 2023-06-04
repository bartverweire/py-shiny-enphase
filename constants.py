import plotly.colors as pc

column_mapping = {
    "production": {
        "system_id": "System Id",
        "end_at": "Time",
        "devices_reporting": "Devices",
        "wh_del": "Produced"
    },
    "consumption": {
        "system_id": "System Id",
        "end_at": "Time",
        "devices_reporting": "Devices",
        "enwh": "Consumed"
    },
    "import": {
        "system_id": "System Id",
        "end_at": "Time",
        "wh_imported": "Imported"
    },
    "export": {
        "system_id": "System Id",
        "end_at": "Time",
        "wh_exported": "Exported"
    },
    "battery": {
        "system_id": "System Id",
        "end_at": "Time",
        "charge_enwh": "Charged",
        "charge_devices_reporting": "Charging Devices",
        "discharge_enwh": "Discharged",
        "discharge_devices_reporting": "Discharging Devices",
        "soc_percent": "Charged (Pct)",
        "soc_devices_reporting": "Status"
    }
}

colors = {
    "Produced": "deepskyblue",
    "Consumed": "orangered",
    "Imported": "darkgray",
    "Exported": "lightgray",
    "Charged": "lime",
    "Discharged": "green",
    "Charged (Pct)": "lime"
}

def make_lighter(base_color, pct):
    rgb = matplotlib.colors.to_rgb(base_color)

    new_rgb = [v + (1.0 - v) * pct / 100 for v in rgb]

    return matplotlib.colors
