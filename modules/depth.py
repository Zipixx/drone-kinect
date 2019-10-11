import cv2
import numpy as np


def set_range(min_depth_in, max_depth_in):
	global min_depth
	global max_depth
	min_depth = min_depth_in
	max_depth = max_depth_in

# kinect 3d position estimation translation parameters
fx_d = 5.9421434211923247e+02
fy_d = 5.9104053696870778e+02
cx_d = 3.3930780975300314e+02
cy_d = 2.4273913761751615e+02

def calc(data, render):
	global min_depth
	global max_depth

	in_range = np.where((data.depth > min_depth) & (data.depth < max_depth))
	if(len(in_range[0]) == 0):
		return None

	x_mean = int(in_range[0].mean())
	y_mean = int(in_range[1].mean())


	x = (x_mean - cx_d) * data.depth[x_mean,y_mean] / fx_d
	y = (y_mean - cy_d) * data.depth[x_mean,y_mean] / fy_d
	z = data.depth[x_mean, y_mean]

	if render:
		# scale to [0, 1] based on max distance & turn into rgb channels
		depth_rgb = cv2.cvtColor(data.depth / data.depth.max(), cv2.COLOR_GRAY2RGB)
		# render relevant in_range pixels blue
		depth_rgb[in_range] = [255, 0, 0]
		# draw red circle around mean
		cv2.circle(depth_rgb, (y_mean, x_mean), 10, (0, 0 , 255), 5)

		cv2.imshow(__name__, depth_rgb)

	if z < min_depth or z > max_depth:
		return None
	# return depth at pixel in meters (x,y dimensions flipped as usual)
	return np.array([y/1000.0, -1.0*x/1000.0, z/1000.0])

