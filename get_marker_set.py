from opti_tracker import OptiTracker
import time

CLIENT_IP = "192.168.74.4"
SERVER_IP = "192.168.74.2"
UNICAST = True


tracker = OptiTracker(client_address=CLIENT_IP, server_address=SERVER_IP, unicast=UNICAST)
tracker.start_streaming()

try:
    # Now you can call methods multiple times efficiently
    while True:  # Example loop
        # Get only position
        # position = tracker.get_position(rigid_body_id=3)
        # print(f"Position: {position}")
        
        rigid_bodies = tracker.list_available_rigid_bodies()
        print(f"Available rigid bodies: {len(rigid_bodies)}")
        for rb in rigid_bodies:
            print(f"ID: {rb['rigid_body_id']}, Position: {rb['position']}, Valid: {rb['tracking_valid']}\n")

        marker_sets = tracker.get_marker_sets()
        print(f"Marker sets: {marker_sets}\n")

        unlabeled_markers = tracker.get_unlabeled_markers()
        print(f"Unlabeled markers: {unlabeled_markers}\n")

        labeled_markers = tracker.get_labeled_markers()
        print(f"Labeled markers: {labeled_markers}\n")

        time.sleep(0.5) 
        
finally:
    # Always stop the stream when done
    tracker.stop_streaming()

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