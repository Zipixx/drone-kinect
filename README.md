# Drone Kinect Tracking

## Project Description:
Localization of a drone in real time with the Kinect V2.

This project uses the RGB camera for ArUco tracking as well as the depth sensor to calculate an estimate of the drones 3D postition. A Kalman filter is then used on these coordinates for a more accurate estimate.


## Requirements
* python3
* python-numpy
* libfreenect2
* boost_python
* boost_numpy
