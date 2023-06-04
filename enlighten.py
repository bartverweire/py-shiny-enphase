# Author:   Daniel Patenaude
# Date:     10/13/2020
# Desc:     API utilities for calling the Enphase Enlighten API v4

# import datetime
import json
import requests
import itertools

import http
from base64 import b64encode
from datetime import date, datetime, timedelta
from time import sleep

import logging
import pandas as pd

def concatenate(data, property):
    data[property] = list(itertools.chain(*data[property]))

    return data

class enlightenAPI_v4:

    telemetry_info = {
        "production_micro": {
            "path": "telemetry/production_micro",
            "column_names": None,
            "preprocess": None,
            "preprocess_property": None
        },
        "production_meter": {
            "path": "telemetry/production_meter",
            "column_names": None,
            "preprocess": None,
            "preprocess_property": None
        },
        "consumption": {
            "path": "telemetry/consumption_meter",
            "column_names": None,
            "preprocess": None,
            "preprocess_property": None
        },
        "battery": {
            "path": "telemetry/battery",
            "column_names": {
                "charge.enwh": "charge_enwh",
                "charge.devices_reporting" : "charge_devices_reporting",
                "discharge.enwh": "discharge_enwh",
                "discharge.devices_reporting": "discharge_devices_reporting",
                "soc.percent": "soc_percent",
                "soc.devices_reporting": "soc_devices_reporting"
            },
            "preprocess": None,
            "preprocess_property": None
        },
        "export": {
            "path": "energy_export_telemetry",
            "column_names": None,
            "preprocess": concatenate,
            "preprocess_property": "intervals"
        },
        "import": {
            "path": "energy_import_telemetry",
            "column_names": None,
            "preprocess": concatenate,
            "preprocess_property": "intervals"
        }
    }

    def __assert_success(self, res, exit_on_failure=False):
        '''
        Determine if the web request was successful (HTTP 200)
            Returns:
                If exit_on_failure, returned whether the web request was successful
        '''
        if res.status_code != 200:
            logging.error("Server Responded: " + str(res.status_code) + " - " + res.text)
            if exit_on_failure:
                quit()
            else:
                res.raise_for_status()
        return True

    def __log_time(self):
        return datetime.now().strftime('%Y-%m-%d %I:%M:%S') + ": "

    def authenticate(self):
        try:
            self.__refresh_access_token()
        except requests.HTTPError as e:
            self.__get_access_token()

    def get_systems(self):
        '''
        Run the enlighten API Fetch Systems route
            Returns:
                Returns a list of systems for which the user can make API requests. By default, systems are returned in batches of 10. The maximum size is 100.
        '''
        url = f'{self.config["api_url"]}api/v4/systems/?key={self.config["app_api_key"]}'
        response = requests.get(url, headers={'Authorization': 'Bearer ' + self.config["access_token"]})
        self.__assert_success(response)
        result = json.loads(response.text)
        self.__save_result(result, "data/systems.json")
        return result

    def get_system(self, system_id):
        '''
                Run the enlighten API Fetch Systems route
                    Returns:
                        Returns a list of systems for which the user can make API requests. By default, systems are returned in batches of 10. The maximum size is 100.
                '''
        url = f'{self.config["api_url"]}api/v4/systems/{system_id}?key={self.config["app_api_key"]}'
        response = requests.get(url, headers={'Authorization': 'Bearer ' + self.config["access_token"]})
        self.__assert_success(response)
        result = json.loads(response.text)
        self.__save_result(result, f"data/system_{system_id}.json")
        return result

    def get_system_summary(self, system_id):
        '''
        Run the enlighten API Fetch Systems route
            Returns:
                Returns a list of systems for which the user can make API requests. By default, systems are returned in batches of 10. The maximum size is 100.
        '''
        url = f'{self.config["api_url"]}api/v4/systems/{system_id}/summary/?key={self.config["app_api_key"]}'
        response = requests.get(url, headers={'Authorization': 'Bearer ' + self.config["access_token"]})
        self.__assert_success(response)
        result = json.loads(response.text)
        self.__save_result(result, f"data/system_{system_id}_summary.json")
        return result

    def get_system_devices(self, system_id):
        '''
                Run the enlighten API Fetch Systems route
                    Returns:
                        Returns a list of systems for which the user can make API requests. By default, systems are returned in batches of 10. The maximum size is 100.
                '''
        url = f'{self.config["api_url"]}api/v4/systems/{system_id}/devices/?key={self.config["app_api_key"]}'
        response = requests.get(url, headers={'Authorization': 'Bearer ' + self.config["access_token"]})
        self.__assert_success(response)
        result = json.loads(response.text)
        self.__save_result(result, f"data/system_{system_id}_devices.json")
        return result

    def inverter_summary(self):
        '''
        Run the enlighten API inverters_summary_by_envoy_or_site route (https://developer-v4.enphase.com/docs.html).
        This route returns the detailed information for each inverter (including lifetime power produced). Note: if your Envoy is connected via low
        bandwidth Cellular, data only refreshes to Enlighten every 6 hours. So perform this route the next day in the early morning to ensure you get
        complete data.
            Returns:
                Returns the microinverters summary based on the specified active envoy serial number or system.
        '''
        print(self.__log_time() + "Pulling EnlightenAPI inverter summary...")
        url = f'{self.config["api_url"]}api/v4/systems/inverters_summary_by_envoy_or_site?key={self.config["app_api_key"]}&site_id={self.config["system_id"]}'
        response = requests.get(url, headers={'Authorization': 'Bearer ' + self.config["access_token"]})
        self.__assert_success(response)
        result = json.loads(response.text)
        return result


    def load_monitoring_data(self, system_id, stat_name, start_date=None, end_date=None, start_at=None, end_at=None, **kwargs):
        '''
        Run the enlighten API inverters_summary_by_envoy_or_site route (https://developer-v4.enphase.com/docs.html).
        This route returns the detailed information for each inverter (including lifetime power produced). Note: if your Envoy is connected via low
        bandwidth Cellular, data only refreshes to Enlighten every 6 hours. So perform this route the next day in the early morning to ensure you get
        complete data.
            Returns:
                Returns the microinverters summary based on the specified active envoy serial number or system.
        '''
        start_at_cond = self.__get_timestamp_condition("start_at", start_at)
        end_at_cond = self.__get_timestamp_condition("end_at", end_at)

        start_date_cond = self.__get_date_condition("start_date", start_date)
        end_date_cond = self.__get_date_condition("end_date", end_date)

        url = f'{self.config["api_url"]}api/v4/systems/{system_id}/{stat_name}?key={self.config["app_api_key"]}{start_date_cond}{end_date_cond}{start_at_cond}{end_at_cond}'
        for key, value in kwargs.items():
            if value is not None:
                url += f"&{key}={value}"

        print(f"get stats for {stat_name}: {url}")

        response = requests.get(url, headers={'Authorization': 'Bearer ' + self.config["access_token"]})
        self.__assert_success(response)
        result = json.loads(response.text)

        # sleep(6)

        return result


    def production_summary(self, system_id, start_at=None, end_at=None):

        result = self.load_monitoring_data(system_id, "rgm_stats", start_at, end_at)
        self.__save_result(result, "data/prod_summary.json")

        df = pd.DataFrame.from_records(result["intervals"])
        df["Produced"] = df["wh_del"]
        df["Date"] = df["end_at"].apply(lambda x : datetime.fromtimestamp(x))

        return df[["Date","Produced"]]


    def energy_lifetime(self, system_id, start_at=None, end_at=None, all_production=False):
        result = self.load_monitoring_data(system_id, "energy_lifetime", start_at, end_at, production ="all" if all_production else "none")
        self.__save_result(result, "data/energy_lifetime_all.json" if all_production else "data/energy_lifetime.json")

        return result


    def telemetry(self, system_id, telemetry_type, start_at=None, granularity="week", as_type="json"):
        properties = self.telemetry_info[telemetry_type]
        result = None
        start_dates = self.__get_date_range(start_at, granularity=granularity)
        max_loaded_date = None

        for next_date in start_dates:
            if max_loaded_date is not None:
                start_at = max([dt for dt in [next_date, max_loaded_date] if dt is not None]) + timedelta(minutes=1)
            else:
                start_at = next_date

            tmp_result = self.load_monitoring_data(system_id,
                                                   properties["path"],
                                                   start_at=start_at,
                                                   end_at=None, granularity=granularity)

            self.__save_result(result, f"data/telemetry/{telemetry_type}_{start_at.strftime('%Y%m%d_%H%M%S')}.json")

            intervals = tmp_result["intervals"]
            if len(intervals) > 0:
                if type(intervals[0]) == list:
                    print(list(itertools.chain(*intervals)))
                    intervals = list(itertools.chain(*intervals))

                tmp_dates = [intv["end_at"] for intv in intervals]

                if len(tmp_dates) > 0:
                    max_loaded_date = datetime.fromtimestamp(max(tmp_dates))
                else:
                    pass
            else:
                pass

            if result is None:
                result = tmp_result
            else:
                result["intervals"] += tmp_result["intervals"]

        if as_type == "json":
            return result
        elif as_type == "dataframe":
            return self.__to_dataframe(result,
                                       ["intervals"],
                                       meta=["system_id"],
                                       timestamp_columns=["end_at"],
                                       index="end_at",
                                       column_names=properties["column_names"],
                                       preprocess=properties["preprocess"],
                                       preprocess_property=properties["preprocess_property"])


    # def telemetry_production_micro(self, system_id, start_at=None, granularity="week", as_type="json"):
    #     result = None
    #     start_dates = self.__get_date_range(start_at, granularity=granularity)
    #     max_loaded_date = None
    #
    #     for next_date in start_dates:
    #         start_at = max([dt for dt in [next_date, max_loaded_date] if dt is not None]) + timedelta(minutes=1)
    #
    #         tmp_result = self.load_monitoring_data(system_id, "telemetry/production_micro", start_at=start_at, end_at=None, granularity=granularity)
    #         max_loaded_date = datetime.fromtimestamp(max([intv["end_at"] for intv in tmp_result["intervals"]]))
    #
    #         if result is None:
    #             result = tmp_result
    #         else:
    #             result["intervals"] += tmp_result["intervals"]
    #
    #     self.__save_result(result, "data/telemetry_production_micro.json")
    #
    #     if as_type == "json":
    #         return result
    #     elif as_type == "dataframe":
    #         return self.__to_dataframe(result, ["intervals"], timestamp_columns=["end_at"], index="end_at")
    #
    #
    # def telemetry_production_meter(self, system_id, start_at=None, granularity="week", as_type="json"):
    #     result = None
    #     for s in self.__get_date_range(start_at, granularity=granularity):
    #         tmp_result = self.load_monitoring_data(system_id, "telemetry/production_meter", start_at=start_at, end_at=None, granularity=granularity)
    #         if result is None:
    #             result = tmp_result
    #         else:
    #             result["intervals"] += tmp_result["intervals"]
    #
    #     self.__save_result(result, "data/telemetry_production_meter.json")
    #
    #     if as_type == "json":
    #         return result
    #     elif as_type == "dataframe":
    #         return self.__to_dataframe(result, ["intervals"], timestamp_columns=["end_at"], index="end_at")


    # def telemetry_consumption(self, system_id, start_at=None, granularity="week"):
    #     result = self.load_monitoring_data(system_id, "telemetry/consumption_meter", start_at=start_at, end_at=None, granularity=granularity)
    #     self.__save_result(result, "data/telemetry_consumption_meter.json")
    #
    #     return result


    # def telemetry_battery(self, system_id, start_at=None, granularity="week"):
    #     result = self.load_monitoring_data(system_id, "telemetry/battery", start_at=start_at, end_at=None, granularity=granularity)
    #     self.__save_result(result, "data/telemetry_battery.json")
    #
    #     return result


    # def telemetry_import(self, system_id, start_at=None, granularity="week"):
    #     result = self.load_monitoring_data(system_id, "energy_import_telemetry", start_at=start_at, end_at=None, granularity=granularity)
    #     self.__save_result(result, "data/telemetry_import.json")
    #
    #     return result
    #
    #
    # def telemetry_export(self, system_id, start_at=None, granularity="week"):
    #     result = self.load_monitoring_data(system_id, "energy_export_telemetry", start_at=start_at, end_at=None, granularity=granularity)
    #     self.__save_result(result, "data/telemetry_export.json")
    #
    #     return result


    def consumption_lifetime(self, system_id, start_date=None, end_date=None):
        result = self.load_monitoring_data(system_id, "consumption_lifetime", start_date=start_date, end_date=end_date)
        self.__save_result(result, "data/consumption_lifetime.json")

        return result


    def __save_result(self, result, path):
        with open(path, 'w') as f:
            json.dump(result, f, indent=4)


    def __get_access_token(self):
        '''
        Refresh the access_token (1 day expiration) using the refresh_token (1 week expiration) using the steps detailed
        at: https://developer-v4.enphase.com/docs/quickstart.html#step_10.
        This will override the current self.config and save the new config to local disk to ensure we have the latest access
        and refresh tokens for the next use.

        Note: It's unclear from the Enlighten API docs how to refresh the refresh_token once it expires. If the refresh_token expires
        we're unable to call this route. Generating an access/refresh token via the API (https://developer-v4.enphase.com/docs/quickstart.html#step_8)
        seems to only be usable once per app auth_code.
            Returns:
                The full web request result of the token refresh
        '''
        print(self.__log_time() + "Refreshing access_token...")
        url = f'{self.config["api_url"]}oauth/token?grant_type=authorization_code&redirect_uri=https://api.enphaseenergy.com/oauth/redirect_uri&code={self.config["code"]}'
        # Enlighten API v4 Quickstart says this should be a GET request, but that seems to be incorrect. POST works.
        response = requests.post(url, auth=(self.config['app_client_id'], self.config['app_client_secret']))
        refresh_successful = self.__assert_success(response, False)
        if not refresh_successful:
            print(
                "Unable to refresh access_token. Please set a new access_token and refresh_token in the enlighten_v4_config.json. Quitting...")
            quit()

        result = json.loads(response.text)
        self.__save_result(result, "data/refresh_token.json")

        self.config['access_token'] = result['access_token']
        self.config['refresh_token'] = result['refresh_token']
        self.config['expiry_date'] = (datetime.now() + timedelta(seconds=int(result['expires_in']))).strftime("%Y-%m-%d %H:%M:%S")

        with open('config/enlighten_v4_config.json', 'w') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

        return result


    def __refresh_access_token(self):
        '''
        Refresh the access_token (1 day expiration) using the refresh_token (1 week expiration) using the steps detailed
        at: https://developer-v4.enphase.com/docs/quickstart.html#step_10.
        This will override the current self.config and save the new config to local disk to ensure we have the latest access
        and refresh tokens for the next use.

        Note: It's unclear from the Enlighten API docs how to refresh the refresh_token once it expires. If the refresh_token expires
        we're unable to call this route. Generating an access/refresh token via the API (https://developer-v4.enphase.com/docs/quickstart.html#step_8)
        seems to only be usable once per app auth_code.
            Returns:
                The full web request result of the token refresh
        '''
        print(self.__log_time() + "Refreshing access_token...")
        url = f'{self.config["api_url"]}oauth/token?grant_type=refresh_token&refresh_token={self.config["refresh_token"]}'
        # Enlighten API v4 Quickstart says this should be a GET request, but that seems to be incorrect. POST works.
        response = requests.post(url, auth=(self.config['app_client_id'], self.config['app_client_secret']))
        refresh_successful = self.__assert_success(response, False)
        if not refresh_successful:
            print(
                "Unable to refresh access_token. Please set a new access_token and refresh_token in the enlighten_v4_config.json. Quitting...")
            quit()

        result = json.loads(response.text)
        self.config['access_token'] = result['access_token']
        self.config['refresh_token'] = result['refresh_token']
        self.config['expiry_date'] = (datetime.now() + timedelta(seconds=int(result['expires_in']))).strftime("%Y-%m-%d %H:%M:%S")

        with open('config/enlighten_v4_config.json', 'w') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

        return result


    def __get_timestamp_condition(self, property, value):
        if value is not None:
            return f"&{property}={int(value.timestamp())}"

        return ""


    def __get_date_condition(self, property, value):
        if value is not None:
            return f'&{property}={value.strftime("%Y-%m-%d")}'

        return ""

    def __to_dataframe(self,
                       data,
                       record_path=None,
                       meta=None,
                       meta_prefix="",
                       timestamp_columns=None,
                       drop_duplicates=True,
                       index=None,
                       column_names=None,
                       preprocess=None,
                       postprocess=None,
                       **kwargs):
        if preprocess is not None:
            data = preprocess(data, kwargs["preprocess_property"])

        df = pd.json_normalize(
            data,
            record_path=record_path,
            meta=meta,
            meta_prefix=meta_prefix
        )

        if timestamp_columns is not None:
            for col in timestamp_columns:
                df[col] = df[col].apply(lambda x: datetime.fromtimestamp(x))

        if drop_duplicates:
            df = df.drop_duplicates()

        if column_names is not None:
            df = df.rename(columns=column_names)

        if index is not None:
            df = df.set_index(index)

        return df



    def __get_date_range(self, start_date, end_date = datetime.now(), granularity = "week"):
        dates = [start_date]
        if granularity == "day":
            period = timedelta(days=1)
        elif granularity == "week":
            period = timedelta(days=7)
        elif granularity == "15mins":
            period = timedelta(hours=1)
        else:
            None

        next_date = start_date + period

        while next_date < end_date:
            dates.append(next_date)
            next_date += period

        return dates


    def __init__(self, config):
        '''
        Initialize the englightAPI class
            Parameters:
                The API configuration (as a dictionary). Must contain api_url, api_key, and secrets
        '''
        self.config = config

        # It seems the v4 API allows you to only call the OAuth POST route with grant_type=authorization_code a SINGLE time for a auth_code.
        # So we need to make sure those already exist.
        if not "access_token" in self.config \
                or not "refresh_token" in self.config \
                or not "expiry_date" in self.config:
            print('Error: access_token or refresh_token not set in the enlighten_v4_config.json')
            # Refresh and save out the new config with the refreshed access_token/refresh_token
            self.__get_access_token()
            quit()

        if datetime.strptime(self.config["expiry_date"], "%Y-%m-%d %H:%M:%S") < datetime.now():
            print('Error: access_token expired. Trying refresh')
            try:
                self.__refresh_access_token()
            except requests.HTTPError as e:
                print('Error: refresh token failed. Trying to get new access token')
                self.__get_access_token()


