import os
import json


def get_forecast_definitions():
    dir_path = os.path.dirname(os.path.abspath(__file__))
    f = open(os.path.join(dir_path, 'forecast_definitions.json'))
    forecast_definitions = json.load(f)
    f.close()
    return forecast_definitions
