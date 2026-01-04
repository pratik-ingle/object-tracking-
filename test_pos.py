from opti_tracker import OptiTracker
import time

CLIENT_IP = "192.168.74.2"
SERVER_IP = "192.168.74.3"
UNICAST = True


tracker = OptiTracker(client_address=CLIENT_IP, server_address=SERVER_IP, unicast=UNICAST)
tracker.start_streaming()

try:
    # Now you can call methods multiple times efficiently
    while True:  # Example loop
        # Get only position

        position = tracker.get_rigid_body_position(rigid_body_id=4)
        print(f"Position: {position}")
        
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

# print("\n=== Method 2: Using context manager ===")
# # Method 2: Using context manager (automatic cleanup)
# with ObjectTracker() as tracker:
#     for i in range(3):
#         position = tracker.get_position(rigid_body_id=3)
#         print(f"Position {i}: {position}")
#         time.sleep(0.1)

# print("\n=== Method 3: List available rigid bodies ===")
# # Method 3: List all available rigid bodies
# with ObjectTracker() as tracker:
#     rigid_bodies = tracker.list_available_rigid_bodies()
#     print(f"Available rigid bodies: {len(rigid_bodies)}")
#     for rb in rigid_bodies:
#         print(f"ID: {rb['rigid_body_id']}, Position: {rb['position']}, Valid: {rb['tracking_valid']}")

# print("\n=== Method 4: Legacy function interface (still works) ===")
# # Method 4: Legacy function interface still works for backward compatibility
# from object_tracking.PythonClient.RigidBodyMinimal import RigidBodyTracker, start_rigid_body_stream, stop_rigid_body_stream, get_rigid_body_data

# start_rigid_body_stream()
# try:
#     for i in range(2):
#         data = get_rigid_body_data(rigid_body_id=3, info_type="position")
#         print(f"Legacy Position {i}: {data['position']}")
#         time.sleep(0.1)
# finally:
#     stop_rigid_body_stream()