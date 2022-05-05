import process_zonal_statistics as pzs
import create_clipped_image as cci
import sys


if __name__ == '__main__':
    delta_days = 0
    if len(sys.argv) > 1:
        delta_days = int(sys.argv[1])

    print("Creating forecast product")
    if pzs.run_statistics(delta_days):
        print("csv creation is complete")
    if cci.create_forecast_map(delta_days):
        print("forecast maps are saved")
