import csv
import os
from datetime import datetime, timedelta
import json
import rasterstats
import utilities


def run_statistics(delta_days):
    try:

        forecast_definitions = utilities.get_forecast_definitions()

        file_date = (datetime.today() - timedelta(days=delta_days)).strftime('%Y%m%d')
        for forecast in forecast_definitions["forecasts"]:
            zs = rasterstats.zonal_stats(
                forecast["shapefile_path"],
                'NETCDF:"' + forecast["data_path"].replace("{{YYYYMMdd}}", file_date) + '":' + forecast[
                    "data_variable"],
                stats=['min', 'max', 'mean', 'median', 'std', 'sum', 'count'],
                geojson_out=True)
            csv_name = file_date + "_" + forecast["output_prefix"] + "_zonal_stats.csv"
            output_directory = forecast["output_directory"]
            os.makedirs(output_directory, exist_ok=True)
            with open(os.path.join(output_directory, csv_name), 'w') as f:
                writer = csv.writer(f)
                # write the header
                writer.writerow(["id", "min", "max", "mean", "median", "sd", "sum", "count"])
                for stat in zs:
                    data = [
                        stat['properties']["ADM2_PCODE"],
                        round(stat['properties']["min"], 2),
                        round(stat['properties']["max"], 2),
                        round(stat['properties']["mean"], 2),
                        round(stat['properties']["median"], 2),
                        round(stat['properties']["std"], 2),
                        round(stat['properties']["sum"], 2),
                        round(stat['properties']["count"], 2)]
                    writer.writerow(data)
        return True
    except Exception as e:
        print("Production failed, please check to confirm data exists.  The following is the system error: " + str(e))
        return False
