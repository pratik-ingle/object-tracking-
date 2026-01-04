from opti_tracker import OptiTracker
import time
from homography import calculate_homography

CLIENT_IP = "192.168.74.2"
SERVER_IP = "192.168.74.3"
UNICAST = True

REFERENCE_OBJECT_ID = 1
TRACKING_OBJECT_ID = 3


tracker = OptiTracker(client_address=CLIENT_IP, server_address=SERVER_IP, unicast=UNICAST)
tracker.start_streaming()

try:
    # Now you can call methods multiple times efficiently
    while True:  # Example loop
        # Get only position
        
       # Get the reference object's orientation
        orientation_1 = tracker.get_rigid_body_orientation(REFERENCE_OBJECT_ID)
        print(f"Reference object quaternion: {orientation_1}")

        # Get the rotation matrix
        R = tracker._quaternion_to_rotation_matrix(orientation_1)
        print(f"Rotation matrix:\n{R}")

        # Check the coordinate frame axes
        print(f"X-axis (first column): {R[:, 0]}")
        print(f"Y-axis (second column): {R[:, 1]}")
        print(f"Z-axis (third column): {R[:, 2]}")
       
       
        # relative_position_world = tracker.get_relitive_rigid_body_position(rigid_body_id_1=REFERENCE_OBJECT_ID, rigid_body_id_2=TRACKING_OBJECT_ID)
        # print(f"Relative position world: {relative_position_world}")
        
        relative_position_local = tracker.get_relitive_rigid_body_position_local_coordinate_frame(rigid_body_id_1=REFERENCE_OBJECT_ID, rigid_body_id_2=TRACKING_OBJECT_ID)
        print(f"Relative position local: {relative_position_local}")
        # Get only orientation
        # orientation = tracker.get_orientation(rigid_body_id=3)
        # print(f"Orientation: {orientation}")
        
        # Get both position and orientation
        # pos, orient = tracker.get_pose(rigid_body_id=3)
        # print(f"Pose: pos={pos}, orient={orient}")
        
        time.sleep(0.5)  # Small delay between calls
        
finally:
    # Always stop the stream when done
    tracker.stop_streaming()
