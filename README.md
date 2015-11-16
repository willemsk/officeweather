# what & why?

Measuring indoor Co2 and Temperature

Especially in office environments employees are sensitive to high levels of Co2 and/or uncomfortably with hot office temperatures.
This projects consists of two parts, the monitor.py and the webinterface

* **monitor.py** to read the data from the TFA-Dostmann AirControl Mini CO2 sensor and generating the graphs
* **webinterface** to display the graphs

# requirements

## hardware

1) [TFA-Dostmann AirControl Mini CO2 Messgerät](http://www.amazon.de/dp/B00TH3OW4Q) -- 80 euro

2) [Raspberry PI 2 Model B](http://www.amazon.de/dp/B00T2U7R7I) -- 40 euro

3) case, 5v power supply, microSD card

## software

Download [Raspbian](https://www.raspberrypi.org/downloads/) and [install it on the microSD](https://www.raspberrypi.org/documentation/installation/installing-images/README.md).

# installation on the raspberry

0) Boot the raspberry with the raspbian and configure according to your needs.
monitor.py should not run as root, so we create a service user:

At the moment, monitor.py renders the graphs to _/var/www/html/images_, and creates the RRD database in _/var/local/monitor/co2-temp.rrd_.

To change this, change the variables *RRDDB_LOC* and *GRAPHOUT_DIR* in monitor.py.

```
sudo adduser --home /var/local/monitor --shell /usr/sbin/nologin --disabled-password monitor
```

1) install software
Other than Wooga this setup generates and serves the graphs locally, thus the following components are needed:
```
sudo apt-get install rrdtool python-rrdtool nginx ntp
cp /usr/share/zoneinfo/Europe/Vienna /etc/localtime                             

systemctl enable nginx                                                                                                                                        
systemctl start nginx

systemctl enable ntp                                                            
systemctl start ntp 
```

Copy monitor.py and the webinterface to their location:

```
sudo cp monitor.py /usr/bin
sudo mv /var/www/html/index.html /var/www/html/index.nginx-debian.html
sudo rsync -av --progress web/* /var/www/html
sudo chown -R monitor: /var/www/html/images
```

3) fix socket permissions
The python script reading the sensor should not run as root, so the device permissions need to be set accordingly.

For a non-permanent fix run as root:

```
sudo chmod a+rw /dev/hidraw0
```

The better way to deal with this sitaution is to set the permissions using udev rules:

```
echo 'ACTION=="add", KERNEL=="hidraw[0-9]*", MODE="0666"' > /etc/udev/rules.d/40-hidrwaw.rules
```

After plugging the TFA device in, at least one device file (e.g. /dev/hidraw0) should be generated with the correct permissions.

4) run the script
monitor.py can be tested by invoking:
```
monitor.py /dev/hidraw0
```

5) run on startup

monitor.py can safely be called via a cronjob; it will exit if another instance is already running. 

The cronjob can be added to /etc/crontab like this:

```
*/3 *   * * *   monitor /usr/bin/monitor.py /dev/hidraw0
```

# todo

* configure RRD database location and graph directory
* mobile webinterface navigation
* configuring webinterface strings
* notification via email

# credits

based on [Wooga Office Weather](https://github.com/wooga/office_weather)

# license

[MIT](http://opensource.org/licenses/MIT)