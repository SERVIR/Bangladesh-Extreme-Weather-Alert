import csv
import json
import os

import numpy as np
from datetime import datetime, timedelta
from osgeo import gdal
from osgeo import ogr


def bounding_box_to_offsets(bbox, geotiff):
    col1 = int((bbox[0] - geotiff[0]) / geotiff[1])
    col2 = int((bbox[1] - geotiff[0]) / geotiff[1]) + 1
    row1 = int((bbox[3] - geotiff[3]) / geotiff[5])
    row2 = int((bbox[2] - geotiff[3]) / geotiff[5]) + 1
    return [row1, row2, col1, col2]


def geotiff_from_offsets(row_offset, col_offset, geotiff):
    return [
        geotiff[0] + (col_offset * geotiff[1]),
        geotiff[1],
        0.0,
        geotiff[3] + (row_offset * geotiff[5]),
        0.0,
        geotiff[5]
    ]


def set_feature_stats(fid, min, max, mean, median, sd, sum, count,
                      names=["id", "min", "max", "mean", "median", "sd", "sum", "count"]):
    feature_stats = {
        names[0]: fid,
        names[1]: min,
        names[2]: max,
        names[3]: mean,
        names[4]: median,
        names[5]: sd,
        names[6]: sum,
        names[7]: count,
    }
    return feature_stats


def run_statistics(delta_days):
    f = open('forecast_definitions.json')
    forecast_definitions = json.load(f)
    f.close()

    file_date = (datetime.today() - timedelta(days=delta_days)).strftime('%Y%m%d')

    mem_driver = ogr.GetDriverByName("Memory")
    mem_driver_gdal = gdal.GetDriverByName("MEM")
    shp_name = "temp"
    try:
        for forecast in forecast_definitions["forecasts"]:
            # Path of netCDF file will have to be calculated via available date
            netcdf_name = forecast["data_path"].replace("{{YYYYMMdd}}", file_date)

            # Specific variable to read
            layer_name = forecast["data_variable"]
            fn_zones = forecast["shapefile_path"]

            r_ds = gdal.Open("NETCDF:{0}:{1}".format(netcdf_name, layer_name))
            p_ds = ogr.Open(fn_zones)

            lyr = p_ds.GetLayer()
            geotiff = r_ds.GetGeoTransform()
            nodata = r_ds.GetRasterBand(1).GetNoDataValue()

            zstats = []

            p_feat = lyr.GetNextFeature()
            niter = 0

            while p_feat:
                if p_feat.GetGeometryRef() is not None:
                    if os.path.exists(shp_name):
                        mem_driver.DeleteDataSource(shp_name)
                    tp_ds = mem_driver.CreateDataSource(shp_name)
                    tp_lyr = tp_ds.CreateLayer('polygons', None, ogr.wkbPolygon)
                    tp_lyr.CreateFeature(p_feat.Clone())
                    offsets = bounding_box_to_offsets(p_feat.GetGeometryRef().GetEnvelope(),
                                                      geotiff)
                    new_geotiff = geotiff_from_offsets(offsets[0], offsets[2], geotiff)
                    tr_ds = mem_driver_gdal.Create(
                        "",
                        offsets[3] - offsets[2],
                        offsets[1] - offsets[0],
                        1,
                        gdal.GDT_Byte)
                    tr_ds.SetGeoTransform(new_geotiff)
                    gdal.RasterizeLayer(tr_ds, [1], tp_lyr, burn_values=[1])
                    tr_array = tr_ds.ReadAsArray()

                    r_array = r_ds.GetRasterBand(1).ReadAsArray(
                        offsets[2],
                        offsets[0],
                        offsets[3] - offsets[2],
                        offsets[1] - offsets[0])

                    id = p_feat.GetField('ADM2_PCODE')  # p_feat.GetFID()

                    if r_array is not None:
                        mask_array = np.ma.MaskedArray(
                            r_array,
                            mask=np.logical_or(r_array == nodata, np.logical_not(tr_array))
                        )

                        if mask_array is not None:
                            zstats.append(set_feature_stats(
                                id,
                                mask_array.min(),
                                mask_array.max(),
                                mask_array.mean(),
                                np.ma.median(mask_array),
                                mask_array.std(),
                                mask_array.sum(),
                                mask_array.count()))
                        else:
                            zstats.append(set_feature_stats(
                                id,
                                nodata,
                                nodata,
                                nodata,
                                nodata,
                                nodata,
                                nodata,
                                nodata))
                    else:
                        zstats.append(set_feature_stats(
                            id,
                            nodata,
                            nodata,
                            nodata,
                            nodata,
                            nodata,
                            nodata,
                            nodata))

                    tp_ds = None
                    tp_lyr = None
                    tr_ds = None

                    p_feat = lyr.GetNextFeature()
            # Will likely name the csv with date string

            csv_name = file_date + "_" + forecast["output_prefix"] + "zstats.csv"
            output_directory = forecast["output_directory"]
            os.makedirs(output_directory, exist_ok=True)
            col_names = zstats[0].keys()
            with open(os.path.join(output_directory, csv_name), 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, col_names)
                writer.writeheader()
                writer.writerows(zstats)
        return True
    except Exception as e:
        print("Production failed, please check to confirm data exists.  The following is the system error: " + str(e))
        return False
