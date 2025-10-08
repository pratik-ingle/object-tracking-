from opti_tracker import OptiTracker
import time
from homography import calculate_homography

CLIENT_IP = "192.168.74.4"
SERVER_IP = "192.168.74.2"
UNICAST = True

REFERENCE_OBJECT_ID = 1
TRACKING_OBJECT_ID = 4


tracker = OptiTracker(client_address=CLIENT_IP, server_address=SERVER_IP, unicast=UNICAST)
tracker.start_streaming()

try:
    # Now you can call methods multiple times efficiently
    while True:  # Example loop
        # Get only position
        
        relative_position_world = tracker.get_relitive_rigid_body_position(rigid_body_id_1=REFERENCE_OBJECT_ID, rigid_body_id_2=TRACKING_OBJECT_ID)
        print(f"Relative position world: {relative_position_world}")
        
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
