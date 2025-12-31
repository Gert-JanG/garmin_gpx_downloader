# Garmin GPX Downloader

A small utility to download **GPX files from your Garmin Connect activities**, with flexible filtering options.

You can filter activities by:

- **Activity type** (`-t`)
- **Activity name** (`-n`)
- **Start location radius** (`-r`)
- **Specific start coordinate** (`-c`) + (`-r`)

---

## Features

- Download GPX files from Garmin Connect
- Filter by:
  - Activity type (running, walking, etc.)
  - Activity name keywords
  - Distance from a location
  - Distance from your last recorded activity
- Combine multiple filters
- Logical filtering support (`AND` / `OR`) *(WIP)*

---
## Running it on Windows:
1. Make sure a python interpreter is installed
2. Open this directory in `Command Prompt`
3. Create and activate python venv
    ```bash
        python -m venv myvenv
        myvenv/bin/activate
    ```
4. Install all requirements from `requirements.txt`
    ```bash
        pip install -r requirements.txt
    ```
5. Checkout the help or the [example use cases](#Example-Usage)
    ```bash
        python garmin_gpx_downloader.py --help
    ```

## Filtering Rules

### Activity Name (`-n`)
- One or more strings
- If **any** string matches, the activity is included
- Case-insensitive

### Activity Type (`-t`)
Filter by activity type such as:
- running
- walking
- cycling

### Location Radius (`-r`)
- Filters activities by **start location**
- Radius is in **kilometers**

### Coordinate (`-c`)
- Used together with `-r`
- Format: "(latitude, longitude)" 

**NOTE: if (`r`) is used without specifiying a coordinate (`c`), it automatically fetches the start location of your last recorded activity**

---

## Example Usage

```bash
# Download all running activities
python garmin_gpx_downloader.py -t "running"

# Download activities with "vo2max" or "antwerp" in the name
python garmin_gpx_downloader.py -n "vo2max" "antwerp"

# Download activities started within 10 km of your last activity
python garmin_gpx_downloader.py -r 10

# Download activities within 3.14 km of a specific coordinate
python garmin_gpx_downloader.py -r 3.14 -c "(50.9999999, 6.767676767)"

# Name filter + activity type
python garmin_gpx_downloader.py -n "antwerp" "leuven" -t "running"

# Location filter + activity type
python garmin_gpx_downloader.py -r 1 -c "(51.3333333, 4.8888888888)" -t "running"
```

--- 

## Cool use

[https ://www.gpsheatmaps.com/generator/](This website) allows to upload GPX files to create a heatmap with them.
