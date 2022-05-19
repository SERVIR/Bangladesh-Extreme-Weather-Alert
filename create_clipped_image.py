import os
import xarray as xr
import regionmask as rm
import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from datetime import datetime, timedelta
import utilities


def create_forecast_map(delta_days):
    forecast_definitions = utilities.get_forecast_definitions()
    file_date = (datetime.today() - timedelta(days=delta_days)).strftime('%Y%m%d')

    try:
        for forecast in forecast_definitions["forecasts"]:
            hiwat_file = forecast["data_path"].replace("{{YYYYMMdd}}", file_date)
            ds = xr.open_dataset(hiwat_file)

            bmd_admin2 = gpd.read_file(forecast["shapefile_path"])

            var_to_plot = forecast["data_variable"]
            figure_file = file_date + "_" + forecast["output_prefix"] + "_forecast_map.jpg"

            bmd_lon_min, bmd_lat_min, bmd_lon_max, bmd_lat_max = bmd_admin2.total_bounds

            ds_bmd = ds.sel(latitude=slice(bmd_lat_min, bmd_lat_max), longitude=slice(bmd_lon_min, bmd_lon_max))

            all_bmd = bmd_admin2.assign(combine=1).dissolve(by='combine', aggfunc='sum')
            all_bmd.plot(figsize=(10, 10))

            bool_mask = rm.mask_3D_geopandas(all_bmd, ds_bmd, lon_name='longitude', lat_name='latitude').squeeze(
                dim='region',
                drop=True)

            bool_mask.plot.pcolormesh()

            masked_hiwat = ds_bmd.where(bool_mask)

            # Create figure
            plt.figure(figsize=([7.5, 10]))  # create a figure
            # Create axis with Plate Carree projection
            ax = plt.axes(projection=ccrs.PlateCarree())  # set the projection to Plate Carree
            # Set the desired extent of the axis
            ax.set_extent((
                masked_hiwat.longitude.min().values,
                masked_hiwat.longitude.max().values,
                masked_hiwat.latitude.min().values,
                masked_hiwat.latitude.max().values))  # set the extent

            ax.add_geometries(
                bmd_admin2.geometry,
                crs=ccrs.PlateCarree(),
                facecolor='none',
                edgecolor='k',
                zorder=4
            )
            # Add grid labels
            gl = ax.gridlines(
                crs=ccrs.PlateCarree(),
                linewidth=0.5,
                color='black',
                linestyle='-',
                draw_labels=True,
                zorder=4
            )
            gl.top_labels, gl.right_labels = True, True
            gl.xlabel_style, gl.ylabel_style = {'fontsize': 14}, {'fontsize': 14}
            # Plot the data.
            c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12, c13, c14 = [
                [0.0000, 0.9255, 0.9255], [0.0039, 0.6275, 0.9647],
                [0.0000, 0.0000, 0.9647],
                [0.0000, 1.0000, 0.0000], [0.0000, 0.7843, 0.0000],
                [0.0000, 0.5647, 0.0000],
                [1.0000, 1.0000, 0.0000], [0.9059, 0.7529, 0.0000],
                [1.0000, 0.5647, 0.0000],
                [1.0000, 0.0000, 0.0000], [0.8392, 0.0000, 0.0000],
                [0.7529, 0.0000, 0.0000],
                [1.0000, 0.0000, 1.0000], [0.6000, 0.3333, 0.7882]
            ]

            composite_map = (mpl.colors.ListedColormap([c3, c4, c5, c6, c7, c8, c9, c10])
                             .with_extremes(over='magenta', under='white'))

            norm = mpl.colors.BoundaryNorm([10, 20, 30, 40, 50, 60, 70, 80, 90], composite_map.N)
            image = masked_hiwat[var_to_plot].isel(time=0).plot.pcolormesh(ax=ax,
                                                                           transform=ccrs.PlateCarree(),
                                                                           cmap=composite_map,
                                                                           norm=norm,
                                                                           add_colorbar=False,
                                                                           extend='both',
                                                                           zorder=3)
            # Add a title
            ax.set_title(masked_hiwat[var_to_plot].attrs['long_name'].upper(),
                         {'fontsize': 16, 'fontweight': 'bold'})
            # Add the colorbar manually.
            cb = plt.colorbar(image,
                              orientation="horizontal",
                              pad=0.075,
                              shrink=0.65,
                              extend='both',
                              norm=norm,
                              extendfrac='auto')
            # Set the label to use.
            cb.set_label(label=masked_hiwat[var_to_plot].attrs['units'], size='large', weight='bold')
            # Set the labelsize
            cb.ax.tick_params(labelsize='large')
            # Make the figure a tight layout
            plt.tight_layout()

            # Save figure
            output_directory = forecast["output_directory"]
            os.makedirs(output_directory, exist_ok=True)
            plt.savefig(
                os.path.join(output_directory, figure_file),
                dpi=300,
                facecolor='w',
                edgecolor='w',
                bbox_inches='tight',
                pad_inches=0
            )

        return True
    except Exception as e:
        print("Production failed, please check to confirm data exists.  The following is the system error: " + str(e))
        return False
