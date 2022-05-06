import csv
import os
from datetime import datetime, timedelta
import json
import rasterstats


def run_statistics(delta_days):
    try:
        f = open('forecast_definitions.json')
        forecast_definitions = json.load(f)
        f.close()

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
                        stat['properties']["min"],
                        stat['properties']["max"],
                        stat['properties']["mean"],
                        stat['properties']["median"],
                        stat['properties']["std"],
                        stat['properties']["sum"],
                        stat['properties']["count"]]
                    writer.writerow(data)
        return True
    except Exception as e:
        print("Production failed, please check to confirm data exists.  The following is the system error: " + str(e))
        return False
