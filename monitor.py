#!/bin/python

import sys, fcntl, time, rrdtool, os, argparse, socket
from rrdtool import update as rrd_update
from CO2Meter import *

# System settings
RRDDB_LOC = "/var/local/monitor/co2-temp.rrd"
GRAPHOUT_DIR = "/usr/share/nginx/html/images"

def now():
    """Get the current time."""
    return int(time.time())

def graphout(period):
    """Create a graph with rrdtool."""

    # CO2 graph
    filename = GRAPHOUT_DIR + "/co2-" + period + "-graph.png" 
    rrdtool.graph(filename,
        "--start", "now-"+period, "--end", "now",
        "--title", "CO2",
        "--vertical-label", "CO2 PPM",
        "--width", "600",
        "-h 200",
        "-l 0",
        "DEF:co2_num="+RRDDB_LOC+":CO2:AVERAGE",
        "LINE1:co2_num#0000FF:CO2",
        "GPRINT:co2_num:LAST: Last\\:%8.2lf %s ",
        "GPRINT:co2_num:MIN: Min\\:%8.2lf %s ",
        "GPRINT:co2_num:AVERAGE: Avg\\:%8.2lf %s ",
        "GPRINT:co2_num:MAX: Max\\:%8.2lf %s\\n",
        "HRULE:500#16F50F:OK",
        "COMMENT: \\n",
        "HRULE:800#FF952B:DEV-WARN",
        "COMMENT: \\n",
        "HRULE:1000#3FC0EB:OFF-WARN",
        "COMMENT: \\n",
        "HRULE:1200#DE2C2F:CRIT"
    )

    # Temperature graph
    filename = GRAPHOUT_DIR + "/temp-" + period + "-graph.png" 
    rrdtool.graph(filename,
        "--start", "now-"+period, "--end", "now",
        "--title", "TEMP",
        "--vertical-label", "TEMP C",
        "--width", "600",
        "-h 200",
        "DEF:temp_num="+RRDDB_LOC+":TEMP:AVERAGE",
        "LINE1:temp_num#00FF00:TEMP",
        "GPRINT:temp_num:LAST: Last\\:%8.2lf %s ",
        "GPRINT:temp_num:MIN: Min\\:%8.2lf %s ",
        "GPRINT:temp_num:AVERAGE: Avg\\:%8.2lf %s ",
        "GPRINT:temp_num:MAX: Max\\:%8.2lf %s \\n"
    )

    return 0

def create_database(location):
    """Create RRD database at given location.

    Updated every 5 minutes (--step 300)
    Two datasources which can hold unlimit values min and max
    Saves 1 day in 5-minute resolution (288 * (300*1/60) / 60/24)
    Saves 1 week in in 15-minute resolution (672 * (300*3/60) / 60/24)
    Saves 1 month in 1-hour resolution (744 * (300*12/60) / 60/24)
    Saves 7 years in 1-hour resolution
	"""

    rddbh = rrdtool.create(location,
        "--step", "300", "--start", '0',
        "DS:CO2:GAUGE:600:U:U",
        "DS:TEMP:GAUGE:600:U:U",
        "RRA:AVERAGE:0.5:1:288",
        "RRA:AVERAGE:0.5:3:672",
        "RRA:AVERAGE:0.5:12:744",
        "RRA:AVERAGE:0.5:12:61320",
        "RRA:MIN:0.5:1:288",
        "RRA:MIN:0.5:3:672",
        "RRA:MIN:0.5:12:744",
        "RRA:MIN:0.5:12:61320",
        "RRA:MAX:0.5:1:288",
        "RRA:MAX:0.5:3:672",
        "RRA:MAX:0.5:12:744",
        "RRA:MAX:0.5:12:61320"
    )
    return rddbh


if __name__ == "__main__":

    # Set a lock on the socket to indicate that the script is already running
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        ## Create an abstract socket, by prefixing it with null.
        s.bind('\0postconnect_gateway_notify_lock')
    except socket.error as e:
        # if script is already running just exit silently
        sys.exit(0)

    if len(sys.argv) < 2:
        dev = "/dev/hidraw0"
    else:
        dev = sys.argv[1]

    values = {}
    stamp = now()

    # Create RRD database if needed
    if not os.path.isfile(RRDDB_LOC):
        print("RRD database not found, generating it ..")
        rddbh = create_database(RRDDB_LOC)

    # Open the sensor
    sensor = CO2Meter("/dev/hidraw0")

    # Primary program loop
    while True:
        # Poll every 0.25s, a reasonable load
        time.sleep(0.25)
        # Grab the data
        try:
            data = sensor.get_data()
        except IOError as e:
            # USB device disconnected or unavailable
            sys.stderr.write("ERROR: CO2 monitor no longer available!")
            sys.exit(1)

        # Check if all data is available
        if ("co2" in data) and ("temperature" in data):
            co2  = data["co2"]
            temp = data["temperature"]

            # Write output in standard output
            sys.stdout.write("CO2: {:4d} TMP: {:3.1f}    \r".format(co2, temp))
            sys.stdout.flush()

            # Store data in database
            if (now() - stamp) > 60:
                print(">>> sending dataset CO2: {:4d} TMP: {:3.1f} ..".format(co2, temp))
                # Update database
                rrd_update(RRDDB_LOC, "N:{:s}:{:s}".format(str(co2), str(temp)))
                # Create graphs
                graphout("8h")
                graphout("24h")
                graphout("7d")
                graphout("1m")
                graphout("1y")
                # Replace the 'now' time stamp
                stamp = now()
