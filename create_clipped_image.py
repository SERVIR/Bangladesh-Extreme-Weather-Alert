import json
import os

import xarray as xr
import regionmask as rm
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from datetime import datetime, timedelta


def create_forecast_map(delta_days):

    f = open('forecast_definitions.json')
    forecast_definitions = json.load(f)
    f.close()

    file_date = (datetime.today() - timedelta(days=delta_days)).strftime('%Y%m%d')

    try:
        for forecast in forecast_definitions["forecasts"]:
            # Read in HIWAT Example File.
            hiwatFile = forecast["data_path"].replace("{{YYYYMMdd}}", file_date)
            ds = xr.open_dataset(hiwatFile)

            # Read in BMD Admin2 polygon/shapefile
            bmdAdmin2 = gpd.read_file(forecast["shapefile_path"])

            # Set the variable to plot, desired color range, and desired colormap
            varToPlot = forecast["data_variable"]
            scaleMin = 0
            scaleMax = 15
            colormap = 'terrain_r'  # use reversed terrain
            figureFile = file_date + "_" + forecast["output_prefix"] + "_forecast_map.jpg"

            bmdLonMin, bmdLatMin, bmdLonMax, bmdLatMax = bmdAdmin2.total_bounds

            ds_bmd = ds.sel(latitude=slice(bmdLatMin, bmdLatMax), longitude=slice(bmdLonMin, bmdLonMax))

            allBMD = bmdAdmin2.assign(combine=1).dissolve(by='combine', aggfunc='sum')
            # Now we can plot this. Note that the new mask does *not* have the sub-admin borders in this plot ... we have simply one polygon now.
            allBMD.plot(figsize=(10, 10))

            # Create a boolean Mask
            boolMask = rm.mask_3D_geopandas(allBMD, ds_bmd, lon_name='longitude', lat_name='latitude').squeeze(dim='region',
                                                                                                               drop=True)
            # Plot
            boolMask.plot.pcolormesh()

            # Apply the mask using "where"
            maskedHIWAT = ds_bmd.where(boolMask)

            # Get dataset bounds
            lonMin = maskedHIWAT.longitude.min().values
            lonMax = maskedHIWAT.longitude.max().values
            latMin = maskedHIWAT.latitude.min().values
            latMax = maskedHIWAT.latitude.max().values

            # Plot.
            # Create figure
            fig = plt.figure(figsize=([7.5, 10]))  # create a figure
            # Create axis with Plate Carree projection
            ax = plt.axes(projection=ccrs.PlateCarree())  # set the projection to Plate Carree
            # Set the desired extent of the axis
            ax.set_extent((lonMin, lonMax, latMin, latMax))  # set the extent

            ax.add_geometries(bmdAdmin2.geometry, crs=ccrs.PlateCarree(), facecolor='none', edgecolor='k', zorder=4)
            # Add grid labels
            gl = ax.gridlines(crs=ccrs.PlateCarree(), linewidth=0.5, color='black', linestyle='-', draw_labels=True, zorder=4)
            gl.top_labels, gl.right_labels = True, True
            gl.xlabel_style, gl.ylabel_style = {'fontsize': 14}, {'fontsize': 14}
            # Plot the data.
            image = maskedHIWAT[varToPlot].isel(time=0).plot.pcolormesh(ax=ax, transform=ccrs.PlateCarree(), vmin=scaleMin,
                                                                        vmax=scaleMax, cmap=plt.get_cmap(colormap),
                                                                        add_colorbar=False, zorder=3)
            # Add a title
            ax.set_title(maskedHIWAT[varToPlot].attrs['long_name'].upper(), {'fontsize': 16, 'fontweight': 'bold'})
            # Add the colorbar manually.
            cb = plt.colorbar(image,
                              orientation="horizontal",
                              pad=0.075,
                              shrink=0.65)
            # Set the label to use.
            cb.set_label(label=maskedHIWAT[varToPlot].attrs['units'], size='large', weight='bold')
            # Set the labelsize
            cb.ax.tick_params(labelsize='large')
            # Make the figure a tight layout
            plt.tight_layout()

            # Save figure
            output_directory = forecast["output_directory"]
            os.makedirs(output_directory, exist_ok=True)
            plt.savefig(os.path.join(output_directory, figureFile), dpi=300, facecolor='w', edgecolor='w', bbox_inches='tight', pad_inches=0)

        return True
    except Exception as e:
        print("Production failed, please check to confirm data exists.  The following is the system error: " + str(e))
        return False
