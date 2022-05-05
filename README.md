# Bangladesh Extreme Weather Alert

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![SERVIR: Global](https://img.shields.io/badge/SERVIR-Global-green)](https://servirglobal.net)
[![conda: conda-forge](https://shields.io/badge/conda%7Cconda--forge-v3.7.1-blue)](https://servirglobal.net)

This tool creates a CSV of Bangladesh extreme weather statistics for each feature in the configured shapefile
and a forecast map clipped to the boundary of the shapefile. These products are derived from the 
HIWAT model output by pointing the "data_path" in the configuration to the NetCDF.  The product will
be created for the current days date, so it needs to be run after the model is completed.  You can also 
pass in an argument when running the application to produce the data from (current day - n)

## Setup and Installation
The installation described here will make use of conda to ensure there are no package conflicts with 
existing or future applications on the machine.  It is highly recommended to use a dedicated environment 
for this application to avoid any issues.

### Recommended
Conda (To manage packages within the applications own environment)

### Environment
- Create the env

```shell
conda create --name bgd_ewa python=3.10.4
```

- enter the environment

```shell
conda activate bgd_ewa
```

- install requirements 
```shell
cd {your application base directory}
conda install --file requirements.txt 
```

- Create forecast definition file
```shell
cp forecast_definitions_example.json forecast_definitions.json
```

- Edit forecast_definitions.json

In your favorite text editor alter the variables in the forecast definitions file
to match your system.  The definitions are an array of forecasts, you may add as 
many or as few as you would like assuming that you have the appropriate data for each.
The forecast objects are defined as described in the following structure, you may 
also refer to the examples in the forecast_definitions_example.json.  
```json
{
      "name": "", 
      "data_path": "",
      "data_variable": "",
      "shapefile_path": "",
      "output_prefix": "",
      "output_directory": ""
 }
```
name: This variable is for reference purposes, give each forecast a unique name to help identify them

data_path: The full path to your NetCDF file which is produced from the HIWAT model run.  Your files
will have the date in the name like "hkhEnsemble_202205051200_day1_latlon.nc", replace the date portion
20220505 with {{YYYYMMdd}} to make the variable "hkhEnsemble_{{YYYYMMdd}}1200_day1_latlon.nc"

data_variable: The variable within the NetCDF you would like to use for the statistics and forecast map

shapefile_path: The full path to your shapefile that contains the features you want statistics for

output_prefix: A unique prefix for each forecast to avoid overwriting the outputs.  This will be used in the file naming.

output_directory: Full path to where you would like the output created. 

- Test the application

To confirm that all the variables are correct and the application is set up properly you will want to do a test run.
To do this while in the bgd_ewa environment run the following.

```shell
python main.py
```

If you do not have data for the current day yet, the prior test will fail and let you know the files do not exist.
You can still test using prior data that has been output by passing in a delta value representing the number of days 
prior to today that you would like to run the application for.  This value that you pass should be an integer 
as seen in the following example where we run the forecast for the data ten days prior to today.

```shell
python main.py 10
```

- Set up cron to automate the production of the forecast products
I recommend using the root cron, this is useful when working in a team where multiple may need to access or update 
the cron jobs.  It also helps to avoid and permission errors that could be caused by a specific user owning the data
or directory structure.

```shell
sudo crontab -e
```

Use the arrows to navigate to the bottom of this file then begin editing.  You will need the full path to your 
environments' python, the full path to the main.py file, and a full path to where you want log files to be written.
You will also need to decide when you would like to run the application.  With this information you can create the 
cron string to enter on the new line like:

```shell
0 16 * * * /home/username/conda/anaconda3/envs/bgd_ewa/bin/python /home/username/Bangladesh-Extreme-Weather-Alert/main.py >> /home/username/logs/bgd_ewa_`date +\%Y\%m\%d\%H\%M\%S`.log 2>&1
```

This example will run the application daily at 1600 hours, it doesn't pass in a delta day, so it will use the current
day as the file date, and it will output the log file to the log/ directory of the user "username".  You will need
to adjust these paths to fit your system structure and naming.