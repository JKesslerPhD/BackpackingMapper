# BackpackingMapper

Coded to support Python3

# Getting Started (Setup)
- Install Python
- Install Dependencies:

>pip install networkx

> pip install fiona

> pip install lxml

> pip install ortools

> pip install shapely

> pip install gpxpy

> pip install geopy

- Define settings in config.ini

The BackpackingMapper utilizes the trail database affiliated with [HikingProject](http://hikingproject.com).  You will need to establish an account with hiking project, and find your [private developer API key](https://www.hikingproject.com/data).  For the program to work, the following HikingProject account information must be stored in the config.ini file:
* account email address
* api_key
* account password

# Planning a Trip
Once the dependencies have been installed and your HikingProject account information has been added to the config.ini file, you are ready to run the program.  The following will download all trails within 10 miles of the Santa Lucia Wilderness, and plan a backpacking trip up to 100 kilometers in length.

> python mapper.py -location Santa Lucia Wilderness -distance 10 -triplength 100
* **triplength** is specified in kilometers
* **distance** is specified in miles to search for trails from the specified location
* **location** can be a string, and will resolve based on the geopy module

# Details
The script is useful for downloading and identfying a subset of GPX files in a specified area, and connecting those trais in an attempt to make a backpacking trip plan (out and back) or a loop. This code is still in development, so any actions taken based on results are entirely at discretion of the user.  Blindly following trails in the area without additional research is strongly discouraged.

Once a backpacking network has been created (found in the 'saved_trips' folder), it can be imported into any topographic mapping program.  To investigate the trail, use of [caltopo](https://caltopo.com/map.html) is **strongly encouraged**

# Known bugs and Issues
Most issues I have encountered in trip planning are associated with the fact that many trail segments stored in the HikingProject database are not unique. That is:  a uniquely defined trail in HikingProject is often made up of 2 segments of trail that are also considered to be unique.  When this occurs, the optimization algorithm sometimes lets these smaller segments add together to cancel out a larger segment. This also can create problems in terms of calculating the total distance of trail segments.

Additonal development will be necessary to remove overlapping trail segments from the database, but I have not had time to develop that part of the code.  Please feel free to help in the development process!

The trip calculator works better in areas where there are fewer trails to consider, and there are fewer overlapping trails that have been added to the HikingProject database.  For instance, planning a trip where all trails within 40 miles of Boulder, Colorado are downloaded will definitely not give you the results you're looking for.
