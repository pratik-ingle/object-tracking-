import cv2
import numpy as np

def calculate_homography(marker_centre_points, marker_coordinates):
    homography_matrix, _ = cv2.findHomography(np.array(marker_centre_points, dtype=np.float32), np.array(marker_coordinates, dtype=np.float32))
    return homography_matrix
