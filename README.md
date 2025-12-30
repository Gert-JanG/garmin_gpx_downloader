Garmin_GPX_Downloader 
This program enables a user to download all GPX files from all activities present in GarminConnect. It allows users to specify filters on 'Activity Type' (-t), 'Activity Name' (-n) or with a 'start coordinate (-c) within a radius (-r) from a specific coordinate'.

        Filters can be applied to only take GPX files:
        - With certain text strings in the activity name (-n).
            NOTE: When multiple strings are provided, every activity_name that contains any of the provided strings will be kept (and thus further processed)
        - With certain activity types (-t)
        - Within a certain radius (-r) of the start location from your last recorded activity
        - Within a certain radius (-r) of a specified start location coordinate (-c)
        Or any AND/OR combination (-f) of the above!

Example uses:
# Download all GPX's for activities

# with activity_type 'running'
`python3 garmin_gpx_downloader.py -t "running"`

# with the words 'vo2max' or 'antwerp' in the activity name
`python3 garmin_gpx_downloader.py -n "vo2max" "antwerp"`

# that STARTED within 10km radius of 'the start point of your last recorded activity'
`python3 garmin_gpx_downloader.py -r 10`

# that STARTED within 3.14km radius of the given coordinate (latitude, longitude)
`python3 garmin_gpx_downloader.py -r 3.14 -c "(50.9999999, 6.767676767)"`

# that have ("antwerp" OR "leuven" in the name) AND (the activity type is "running")
`python3 garmin_gpx_downloader.py -n "antwerp" "leuven" -t "running"`

# that STARTED within 1km radius of the given coordinate (latitude, longitude) AND activity_type is 'running'
`python3 garmin_gpx_downloader.py -r 1 -c "(51.3333333, 4.8888888888)" -t "running"`



Cool use: 
Load your GPX files on this site to create a heatmap:
`https://www.gpsheatmaps.com/generator/`
















# WIP, or behaviour not working as expected yet
# that have ("antwerp" in the name) AND (the activity type is "running") ==> (-f 'and') is default behaviour
`python3 garmin_gpx_downloader.py -n "antwerp" -t "running" -f 'and'` 

# that have ("antwerp" in the name) OR (the activity type is "walking") 
`python3 garmin_gpx_downloader.py -n "antwerp" -t "walking" -f 'or'`


