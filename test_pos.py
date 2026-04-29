from dotenv import load_dotenv
from opti_tracker import OptiTracker
import time

load_dotenv()

tracker = OptiTracker()
tracker.start_streaming()

try:
    while True:
        position = tracker.get_rigid_body_position(rigid_body_id=2)
        print(f"Position: {position}")
        time.sleep(0.5)
finally:
    tracker.stop_streaming()
