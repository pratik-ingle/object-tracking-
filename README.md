# OptiTracker

A Python module for tracking rigid bodies and getting object orientations from an OptiTrack motion capture system using the NatNet SDK.

## Overview

OptiTracker provides a simple, class-based interface for connecting to OptiTrack's NatNet streaming server and retrieving real-time position and orientation data for tracked rigid bodies. The module handles the low-level NatNet communication and provides high-level methods for accessing tracking data.

## Features

- **Rigid Body Tracking**: Get position, orientation (quaternions), and pose data for tracked rigid bodies
- **Relative Positioning**: Calculate relative positions between rigid bodies in world or local coordinate frames
- **Marker Data**: Access labeled and unlabeled marker positions

## Known Issues

> **Warning:** There is currently a bug when using relative positions between objects, believed to be caused by OptiTrack's non-standard quaternion output. The output must be corrected as follows:
>
> ```python
> relative_position = (relative_position[0], relative_position[2], -relative_position[1])
> ```

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd object-tracking-
```

2. Install the package and dependencies:
```bash
pip install -e .
```

3. Set up your configuration (see [Configuration](#configuration) below).

## Requirements

- Python >= 3.8
- numpy
- python-dotenv
- OptiTrack Motive software with streaming enabled
- Network connection to the OptiTrack server

## Configuration

IP addresses and connection settings are stored in a `.env` file that is **not committed to git**.

1. Copy the example file:
```bash
cp .env.example .env
```

2. Edit `.env` with your actual values:
```
OPTITRACK_CLIENT_IP=192.168.x.x   # Your local machine's IP
OPTITRACK_SERVER_IP=192.168.x.x   # OptiTrack server IP
OPTITRACK_UNICAST=true             # true for unicast, false for multicast
```

The tracker will automatically read these values on startup. You can also override them by passing arguments directly to `OptiTracker()`.

Before connecting, ensure:
- **OptiTrack Motive is running** with streaming enabled
- **Rigid bodies are defined** in Motive and assigned IDs
- **Network settings** are correct for your environment (unicast vs multicast)

## Quick Start

### Basic Usage

```python
from dotenv import load_dotenv
from opti_tracker import OptiTracker

load_dotenv()  # Load IPs from .env

tracker = OptiTracker()
tracker.start_streaming()

try:
    # Get position for rigid body ID 3 (as defined in Motive)
    position = tracker.get_rigid_body_position(rigid_body_id=3)
    print(f"Position: {position}")

    # Get orientation (quaternion)
    orientation = tracker.get_rigid_body_orientation(rigid_body_id=3)
    print(f"Orientation: {orientation}")

    # Get both position and orientation
    position, orientation = tracker.get_rigid_body_pose(rigid_body_id=3)
    print(f"Pose: pos={position}, orient={orientation}")

    # Get position of rigid_body_id_2 in the local frame of rigid_body_id_1
    relative_position = tracker.get_relative_rigid_body_position_local_coordinate_frame(
        rigid_body_id_1=1, rigid_body_id_2=3
    )
    print(f"Relative position (local frame): {relative_position}")

finally:
    tracker.stop_streaming()
```

### Passing Connection Details Directly

If you prefer not to use `.env`, pass the addresses explicitly:

```python
tracker = OptiTracker(
    client_address="192.168.x.x",  # Your local IP
    server_address="192.168.x.x",  # OptiTrack server IP
    unicast=True
)
```

### Using Context Manager

```python
from dotenv import load_dotenv
from opti_tracker import OptiTracker

load_dotenv()

with OptiTracker() as tracker:
    position = tracker.get_rigid_body_position(rigid_body_id=3)
    print(f"Position: {position}")
```

## API Reference

### OptiTracker Class

#### Initialization

```python
OptiTracker(client_address=None, server_address=None, unicast=None)
```

**Parameters:**
- `client_address` (str): Local IP address for the client. Falls back to `OPTITRACK_CLIENT_IP` env var.
- `server_address` (str): NatNet server IP address. Falls back to `OPTITRACK_SERVER_IP` env var.
- `unicast` (bool): Use unicast instead of multicast. Falls back to `OPTITRACK_UNICAST` env var (default: `true`).

Raises `ValueError` if neither argument nor environment variable provides the IP addresses.

#### Methods

##### Streaming Control

- `start_streaming()`: Start persistent rigid body data streaming
- `stop_streaming()`: Stop the streaming connection
- `is_streaming()`: Check if streaming is currently active

##### Rigid Body Data

- `get_rigid_body_position(rigid_body_id, timeout=3.0)`: Get position `[x, y, z]`
- `get_rigid_body_orientation(rigid_body_id, timeout=3.0)`: Get orientation quaternion `[qx, qy, qz, qw]`
- `get_rigid_body_pose(rigid_body_id, timeout=3.0)`: Get `(position, orientation)` tuple
- `get_rigid_body_data(rigid_body_id, info_type="both", timeout=3.0)`: Get detailed data including marker error and tracking validity
  - `info_type`: `"position"`, `"orientation"`, or `"both"`

##### Relative Positioning

- `get_relative_rigid_body_position(rigid_body_id_1, rigid_body_id_2, timeout=3.0)`: Relative position between two rigid bodies in world coordinates
- `get_relative_rigid_body_position_local_coordinate_frame(rigid_body_id_1, rigid_body_id_2, timeout=3.0)`: Position of `rigid_body_id_2` expressed in the local frame of `rigid_body_id_1`
- `get_relative_rigid_body_orientation(rigid_body_id_1, rigid_body_id_2, timeout=3.0)`: Relative orientation between two rigid bodies

##### Marker Data

- `get_marker_sets(timeout=3.0)`: Labeled markers grouped by model name → `dict[str, list[[x,y,z]]]`
- `get_unlabeled_markers(timeout=3.0)`: Unlabeled marker positions → `list[[x,y,z]]`
- `get_labeled_markers(timeout=3.0)`: Labeled markers with IDs and attributes → `list[dict]` with keys: `id`, `model_id`, `marker_id`, `pos`, `size`, `residual`, `param`

##### Utility

- `list_available_rigid_bodies(timeout=5.0)`: List all rigid bodies currently being tracked → `list[dict]`

## Example Scripts

### `test_pos.py` — Basic Position Tracking

Reads connection config from `.env` and polls position in a loop.

### `get_marker_set.py` — Marker Data

Demonstrates accessing marker sets, labeled markers, and unlabeled markers.

## Coordinate System

OptiTrack uses a right-handed coordinate system:

- **Quaternion format**: `[qx, qy, qz, qw]`
- **Rotation order**: XYZ
- Positions are in metres by default (set in Motive)

## Error Handling

All data retrieval methods accept a `timeout` parameter (default 3 seconds). If no data arrives within that window a `TimeoutError` is raised. Wrap streaming operations in `try/finally` to ensure the connection is always closed:

```python
tracker = OptiTracker()
tracker.start_streaming()
try:
    # your code
finally:
    tracker.stop_streaming()
```
