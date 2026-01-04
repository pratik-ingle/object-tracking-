# OptiTracker

A Python module for tracking rigid bodies and getting object orientations from an OptiTrack motion capture system using the NatNet SDK.

## Overview

OptiTracker provides a simple, class-based interface for connecting to OptiTrack's NatNet streaming server and retrieving real-time position and orientation data for tracked rigid bodies. The module handles the low-level NatNet communication and provides high-level methods for accessing tracking data.

## Features

- **Rigid Body Tracking**: Get position, orientation (quaternions), and pose data for tracked rigid bodies
- **Relative Positioning**: Calculate relative positions between rigid bodies in world or local coordinate frames
- **Marker Data**: Access labeled and unlabeled marker positions

## Bugs

**!! WARNING !!- There is currenty a bug which I believe is caused by the optritrack system using a non-standard output to their quaternions when using relitive positions between objects. It is neccicary to modify the output in the following way**

**relative_position = (relative_position[0], relative_position[2], -relative_position[1])**

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd object-tracking-
```

2. Install the package:
```bash
pip install -e .
```

Or install dependencies manually:
```bash
pip install numpy
```

## Requirements

- Python >= 3.8
- numpy
- OptiTrack Motive software with streaming enabled
- Network connection to the OptiTrack server

## Quick Start

### Basic Usage

```python
from opti_tracker import OptiTracker

# Initialize tracker with server connection details
tracker = OptiTracker(
    client_address="192.168.74.4",  # Your local IP
    server_address="192.168.74.2",  # OptiTrack server IP (!non static as ITU policy is breaking)
    unicast=True
)

# Start streaming
tracker.start_streaming()

try:
    # Get position for rigid body ID 3, defined in motive software
    position = tracker.get_rigid_body_position(rigid_body_id=3)
    print(f"Position: {position}")
    
    # Get orientation (quaternion) for rigid body ID 3
    orientation = tracker.get_rigid_body_orientation(rigid_body_id=3)
    print(f"Orientation: {orientation}")
    
    # Get both position and orientation
    position, orientation = tracker.get_rigid_body_pose(rigid_body_id=3)
    print(f"Pose: pos={position}, orient={orientation}")

    relative_position_local = tracker.get_relitive_rigid_body_position_local_coordinate_frame(rigid_body_id_1=REFERENCE_OBJECT_ID, rigid_body_id_2=TRACKING_OBJECT_ID)
    print(f"Pose: pos={position}, orient={orientation}")

    # **!! WARNING !!- There is currenty a bug which I believe is caused by the optritrack system using a non-standard output to their quaternions when using relitive positions between objects. It is neccicary to modify the output in the following way**

    # **relative_position = (relative_position[0], relative_position[2], -relative_position[1])**


    
finally:
    # Always stop streaming when done
    tracker.stop_streaming()
```

### Using Context Manager

```python
from opti_tracker import OptiTracker

# Automatic start/stop with context manager
with OptiTracker(client_address="192.168.74.4", server_address="192.168.74.2") as tracker:
    position = tracker.get_rigid_body_position(rigid_body_id=3)
    print(f"Position: {position}")
```

## API Reference

### OptiTracker Class

#### Initialization

```python
OptiTracker(client_address="192.168.74.4", server_address="192.168.74.2", unicast=True)
```

**Parameters:**
- `client_address` (str): Local IP address for the client
- `server_address` (str): NatNet server IP address (OptiTrack server)
- `unicast` (bool): Use unicast instead of multicast (default: True)

#### Methods

##### Streaming Control

- `start_streaming()`: Start persistent rigid body data streaming
- `stop_streaming()`: Stop the streaming connection
- `is_streaming()`: Check if streaming is currently active

##### Rigid Body Data

- `get_rigid_body_position(rigid_body_id, timeout=3.0)`: Get position [x, y, z] for a rigid body
- `get_rigid_body_orientation(rigid_body_id, timeout=3.0)`: Get orientation quaternion [qx, qy, qz, qw] for a rigid body
- `get_rigid_body_pose(rigid_body_id, timeout=3.0)`: Get both position and orientation as a tuple
- `get_rigid_body_data(rigid_body_id, info_type="both", timeout=3.0)`: Get detailed data including marker error and tracking validity
  - `info_type`: "position", "orientation", or "both"

##### Relative Positioning

- `get_relitive_rigid_body_position(rigid_body_id_1, rigid_body_id_2, timeout=3.0)`: Get relative position between two rigid bodies in world coordinates
- `get_relitive_rigid_body_position_local_coordinate_frame(rigid_body_id_1, rigid_body_id_2, timeout=3.0)`: Get relative position of rigid_body_id_2 in the local coordinate frame of rigid_body_id_1
- `get_relitive_rigid_body_orientation(rigid_body_id_1, rigid_body_id_2, timeout=3.0)`: Get relative orientation between two rigid bodies

##### Marker Data

- `get_marker_sets(timeout=3.0)`: Get labeled markers grouped by model name
  - Returns: `dict` with model names as keys and lists of [x, y, z] positions as values
- `get_unlabeled_markers(timeout=3.0)`: Get unlabeled marker positions
  - Returns: `list` of [x, y, z] positions
- `get_labeled_markers(timeout=3.0)`: Get labeled markers with IDs and attributes
  - Returns: `list` of dicts with keys: `id`, `model_id`, `marker_id`, `pos`, `size`, `residual`, `param`

##### Utility

- `list_available_rigid_bodies(timeout=5.0)`: List all available rigid bodies being tracked
  - Returns: `list` of dicts with rigid body information

## Example Scripts

The repository includes several example scripts demonstrating different use cases:

### 1. `test_pos.py` - Basic Position Tracking

Simple example of getting position data for a rigid body:

```python
from opti_tracker import OptiTracker
import time

tracker = OptiTracker(client_address="192.168.74.2", server_address="192.168.74.3")
tracker.start_streaming()

try:
    while True:
        position = tracker.get_rigid_body_position(rigid_body_id=4)
        print(f"Position: {position}")
        time.sleep(0.5)
finally:
    tracker.stop_streaming()
```

### 2. `get_relitive_position.py` - Relative Positioning

Calculate relative positions between two rigid bodies:

```python
from opti_tracker import OptiTracker
import time

REFERENCE_OBJECT_ID = 1
TRACKING_OBJECT_ID = 4

tracker = OptiTracker(client_address="192.168.74.2", server_address="192.168.74.3")
tracker.start_streaming()

try:
    while True:
        static_position = tracker.get_rigid_body_position(rigid_body_id=REFERENCE_OBJECT_ID)
        tracking_position = tracker.get_rigid_body_position(rigid_body_id=TRACKING_OBJECT_ID)
        
        relative_positions = [tracking_position[i] - static_position[i] for i in range(3)]
        print(f"Relative positions: {relative_positions}")
        
        time.sleep(0.5)
finally:
    tracker.stop_streaming()
```

### 3. `test_get-relitive_position_rotated.py` - Local Coordinate Frame

Get relative positions in a local coordinate frame:

```python
from opti_tracker import OptiTracker
import time

REFERENCE_OBJECT_ID = 1
TRACKING_OBJECT_ID = 3

tracker = OptiTracker(client_address="192.168.74.2", server_address="192.168.74.3")
tracker.start_streaming()

try:
    while True:
        # Get orientation and rotation matrix
        orientation_1 = tracker.get_rigid_body_orientation(REFERENCE_OBJECT_ID)
        R = tracker._quaternion_to_rotation_matrix(orientation_1)
        
        # Get relative position in local coordinate frame
        relative_position_local = tracker.get_relitive_rigid_body_position_local_coordinate_frame(
            rigid_body_id_1=REFERENCE_OBJECT_ID,
            rigid_body_id_2=TRACKING_OBJECT_ID
        )
        print(f"Relative position local: {relative_position_local}")
        
        time.sleep(0.5)
finally:
    tracker.stop_streaming()
```

### 4. `get_marker_set.py` - Marker Data

Access marker sets and labeled/unlabeled markers:

```python
from opti_tracker import OptiTracker
import time

tracker = OptiTracker(client_address="192.168.74.4", server_address="192.168.74.2")
tracker.start_streaming()

try:
    while True:
        # List available rigid bodies
        rigid_bodies = tracker.list_available_rigid_bodies()
        print(f"Available rigid bodies: {len(rigid_bodies)}")
        for rb in rigid_bodies:
            print(f"ID: {rb['rigid_body_id']}, Position: {rb['position']}, Valid: {rb['tracking_valid']}")

        # Get marker sets
        marker_sets = tracker.get_marker_sets()
        print(f"Marker sets: {marker_sets}")

        # Get unlabeled markers
        unlabeled_markers = tracker.get_unlabeled_markers()
        print(f"Unlabeled markers: {unlabeled_markers}")

        # Get labeled markers
        labeled_markers = tracker.get_labeled_markers()
        print(f"Labeled markers: {labeled_markers}")

        time.sleep(0.5)
finally:
    tracker.stop_streaming()
```

## Coordinate System

**!! WARNING !!- There is currenty a bug which I believe is caused by the optritrack system using a non-standard output to their quaternions when using relitive positions between objects. It is neccicary to modify the output in the following way**

**relative_position = (relative_position[0], relative_position[2], -relative_position[1])**

The module uses OptiTrack's coordinate system:

- **Right-handed coordinate system**
- **Quaternion format**: [qx, qy, qz, qw]
- **Rotation order**: XYZ
- Positions are in millimeters (mm) by default

## Configuration

Before using the module, ensure:

1. **OptiTrack Motive is running** with streaming enabled
2. **Network settings** match your setup:
   - Set `client_address` to your local machine's IP address
   - Set `server_address` to the OptiTrack server's IP address
   - Choose unicast or multicast based on your network configuration
3. **Rigid bodies are defined** in Motive and assigned IDs

## Error Handling

The module includes timeout handling for all data retrieval methods. If data is not received within the specified timeout (default 3 seconds), a `TimeoutError` will be raised. Always wrap streaming operations in try/finally blocks to ensure proper cleanup:

```python
tracker = OptiTracker(...)
tracker.start_streaming()
try:
    # Your code here
    pass
finally:
    tracker.stop_streaming()
```
