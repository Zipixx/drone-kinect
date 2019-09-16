#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#For Spyder: Swicht Matplot from inline to auto
#%matplotlib auto
#%matplotlib inline

import cv2
import cv2.aruco as aruco
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D #registers 3D projection, otherwise unused
import numpy as np
import time


## DEFINE LOCALIZATION ALGORITHMS ##
# They should all return np.array([x, y, z]) in meters

# For webcam, Kinect RGB cam and maybe when it's dark Kinect IR cam:
def localize_aruco(frame, matrix_coefficients, distortion_coefficients):
    # The following setup might be used once outside the function
    # Define Which ArUco Marker(s) We Use (here we use 6 by 6 bits)
    # aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_6X6_250)
    aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_250)
    # Define The Detector Parameters
    parameters =  cv2.aruco.DetectorParameters_create()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    
    # side length of the used ArUco marker: 0.105 meters
    rvec, tvec, markerPoints = aruco.estimatePoseSingleMarkers(corners, 0.105, matrix_coefficients, distortion_coefficients)
    if tvec is not None:
        return tvec[0,0] #assuming there is only one marker in the image
    else:
        return None
    
# For Kinect depth sensor
def localize_depth(frame):
    return np.array([42, 42, 42])

# For drone IMU
def localize_imu(frame):
    return np.array([42, 42, 42])



## DEFINE SENSOR FUSION ALGORITHM ##
#kalman_estimation expects a list of xyzt localizations of different sensors
def kalman_estimation(xyzt_list):
    if xyzt_list[0] is not None:
        return xyzt_list[0][:3] #for now it just returns the xyz of the first xyzt vector that it was given.
    else:
        return None


## SET UP PLOT ##
# The default is to plot 3d, although plotting only x,y dimensions is less buggy for now
plot2D = False
#plot2D = True


# -- 2D Plot (tested) --
# For now 2d scatter plot as live updates for 3D scatter plot don't work yet
if plot2D:
    plt.ion()
    fig, ax = plt.subplots()
    x, y = [],[]
    sc = ax.scatter(x,y)
    plt.xlim(-0.3,0.3)
    plt.ylim(-0.3,0.3)
    def update_2dplot(coords):
        if coords is not None:
            sc.set_offsets(-1 * coords[[0,1]]) #only select what is "links-rechts" and "oben-unten" axes and mirror it
            fig.canvas.draw_idle()
            plt.pause(0.01)
        
# -- 3D Plot --
if not plot2D:
    plt.ion()
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlabel('Links_Rechts')
    ax.set_ylabel('Entfernung')
    ax.set_zlabel('Unten_Oben')
    axes = plt.gca()
    axes.set_xlim([-0.5,0.5])
    axes.set_ylim([0, 7])
    axes.set_zlim([-0.3,0.3])
    scat = ax.scatter([], [], [], c='b', marker='o')       
    def update_3dplot(coords):
        if coords is not None:
            # for some reasons, "Links_Rechts"-values only give roughly half the meters and
            # "Entfernung"-values roughly give double the meters. Using 2 and 0.5 as prefactors solves this
            # now the coordinates are very roughly correct in all dimensions, they are given in meters.
            # but its still not perfect, probably the calibration is wrong.
            offsets = ([-1 * 2 * coords[0]],  [0.5 * coords[2]], [-1 * coords[1]])
            #print("offsets")
            #print(offsets)
            scat._offsets3d = offsets
            fig.canvas.draw_idle()
            plt.pause(0.01)


## INITIAL SENSOR SETTINGS ##
#read in webcam calibration data, created in camera_calibration.py
cv_file = cv2.FileStorage("camera_calibration/MBP13Late2015Distortion.yaml", cv2.FILE_STORAGE_READ)
wc_matrix_coefficients = cv_file.getNode("camera_matrix").mat()
wc_distortion_coefficients = cv_file.getNode("dist_coeff").mat()
cv_file.release()


## GET ALL SENSORS REDY ##
wc_cap = cv2.VideoCapture(0)


## REPETITIVE PROCESS OF OBTAINING AND PROCESSING SENSOR DATA ##
verbose = False
while True:
    ## READ ALL SENSORS, GET TIMESTAMPS ##
    # Sensor: WebCam
    wc_ret, wc_frame = wc_cap.read()
    wc_t = time.time()
    # Sensor: Kinect rgb Cam
    kc_frame = 42
    kc_t = time.time()
    # Sensor: Kinect Depth sensor -> kd
    kd_frame = 42
    kd_t = time.time()
    
    
    ## SENSOR READING ERRORS ##
    if not wc_ret:
        if verbose: print("Error: No Image Frame Obtained From The Webcam")
        break
    

    ## GET LOCALIZATIONS ACCORDING TO ERRORS, COMBINE WITH TIMESTAMPS ##
    wc_xyz = localize_aruco(wc_frame, wc_matrix_coefficients, wc_distortion_coefficients)
    if wc_xyz is None:
        if verbose: print("skipping Webcam frame: no translation vector could be obtained in this frame.")
        wc_xyzt = None
    else:
        wc_xyzt = np.append(wc_xyz, wc_t)
        if verbose: print(wc_xyzt)    
    #When just using Kinect cam and depth sensor: get kc_xyzt, kd_xyzt
    #For DRone IMU, get dr_xyzt
        
        
    ## FUSE ALL LOCALIZATIONS ##
    #example when just using Kinect cam and depth sensor:
    #kalman_estimation([kc_xyzt, kd_xyzt])
    
    #Just using wc_xyzt, which is already enough for a Kalman filter, as it
    #can fuse estimations from past values and current camera observations
    kalman_xyz = kalman_estimation([wc_xyzt])
    
    #For testing multiple sensor inputs
    #Simulating another sensor by transforming wc_xyzt
    if wc_xyz is not None:
        simsens_xyz = 1.2 * wc_xyz
        simsens_xyzt = np.append(simsens_xyz, wc_xyzt[-3])
    else:
        simsens_xyz = None
        simsens_xyzt = None
    
    kalman_xyz = kalman_estimation([wc_xyzt, simsens_xyzt])

    

    ## UPDATE THE PLOT ##
    # Just plot the Kalman estimation:
    if plot2D:
        update_2dplot(kalman_xyz)
    else:
        update_3dplot(kalman_xyz)
    
    #Plot sensor localizations and kalman estimation - 3 points with differnt colors
    #points = np.vstack([wc_xyz, simsens_xyz, kalman_xyz])
    #update_3dplot(points)
    
    
    
    
## TURN OFF / DISCONNECT ALL SENSORS ##    
wc_cap.release()