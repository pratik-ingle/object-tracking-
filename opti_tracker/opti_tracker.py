import time
import threading
from .NatNetSDK import NatNetClient
import numpy as np



class OptiTracker:
    """A class-based interface for tracking rigid bodies with OptiTrack NatNet."""
    
    def __init__(self, client_address: str = "192.168.74.4", server_address: str = "192.168.74.2", unicast: bool = True):
        """Initialize the rigid body tracker.
        
        Args:
            client_address (str): Local IP address for client
            server_address (str): NatNet server IP address
            unicast (bool): Use unicast instead of multicast
        """
        self.client_address = client_address
        self.server_address = server_address
        self.unicast = unicast
        
        # Streaming state
        self._client = None
        self._streaming_data = {}
        self._lock = None
        self._is_streaming = False
        self._marker_sets = {}            # {model_name(str): list[[x,y,z], ...]}
        self._unlabeled_markers = []      # list[[x,y,z], ...]
        self._labeled_markers = []        # list[{id, model_id, marker_id, pos, size, residual, param}]
    
    def start_streaming(self):
        """Start persistent rigid body data streaming.
        
        Raises:
            RuntimeError: If streaming cannot be started
        """

        
        if self._is_streaming:
            print("Warning: Streaming already started. Call stop_streaming() first.")
            return
        
        self._lock = threading.Lock()
        self._streaming_data = {}
        self._marker_sets = {}
        self._unlabeled_markers = []
        self._labeled_markers = []
        
        client = NatNetClient()
        client.set_client_address(self.client_address)
        client.set_server_address(self.server_address)
        client.set_use_multicast(False if self.unicast else True)
        client.set_print_level(0)

        def _to_str(val):
            if isinstance(val, bytes):
                try:
                    return val.decode('utf-8')
                except Exception:
                    return str(val)
            return str(val)

        def on_frame_with_data(data_dict):
            mocap_data = data_dict.get("mocap_data")
            if mocap_data is None:
                return
            
            with self._lock:
                # Rigid bodies
                if mocap_data.rigid_body_data is not None:
                    for rb in mocap_data.rigid_body_data.rigid_body_list:
                        self._streaming_data[rb.id_num] = {
                            "rigid_body_id": rb.id_num,
                            "position": [rb.pos[0], rb.pos[1], rb.pos[2]],
                            "orientation": [rb.rot[0], rb.rot[1], rb.rot[2], rb.rot[3]],
                            "marker_error": rb.error,
                            "tracking_valid": True if rb.tracking_valid else False,
                        }

                # Markerset (labeled) and unlabeled markers
                if mocap_data.marker_set_data is not None:
                    # Labeled marker sets grouped by model name
                    marker_sets = {}
                    for md in mocap_data.marker_set_data.marker_data_list:
                        model_name = _to_str(md.model_name)
                        positions = [[p[0], p[1], p[2]] for p in md.marker_pos_list]
                        marker_sets[model_name] = positions
                    self._marker_sets = marker_sets

                    # Unlabeled markers
                    unlabeled_list = []
                    if mocap_data.marker_set_data.unlabeled_markers is not None:
                        for p in mocap_data.marker_set_data.unlabeled_markers.marker_pos_list:
                            unlabeled_list.append([p[0], p[1], p[2]])
                    self._unlabeled_markers = unlabeled_list

                # Labeled markers (flat list with IDs)
                if mocap_data.labeled_marker_data is not None:
                    labeled_list = []
                    for lm in mocap_data.labeled_marker_data.labeled_marker_list:
                        lm_id = lm.id_num
                        model_id = (lm_id >> 16)
                        marker_id = (lm_id & 0x0000ffff)
                        labeled_list.append({
                            "id": lm_id,
                            "model_id": model_id,
                            "marker_id": marker_id,
                            "pos": [lm.pos[0], lm.pos[1], lm.pos[2]],
                            "size": float(lm.size),
                            "residual": float(lm.residual),
                            "param": int(lm.param),
                        })
                    self._labeled_markers = labeled_list

        client.new_frame_with_data_listener = on_frame_with_data

        # Try to start client, fallback to unicast if multicast fails
        is_running = client.run('d')
        if not is_running and not self.unicast:
            # Try unicast if multicast failed
            client.shutdown()
            client = NatNetClient()
            client.set_client_address(self.client_address)
            client.set_server_address(self.server_address)
            client.set_use_multicast(False)  # Force unicast
            client.set_print_level(0)
            client.new_frame_with_data_listener = on_frame_with_data
            is_running = client.run('d')
        
        if not is_running:
            raise RuntimeError("Could not start NatNet streaming client")
        
        time.sleep(0.3)
        if client.connected() is False:
            client.shutdown()
            raise RuntimeError("Could not connect. Ensure Motive streaming is enabled.")
        
        self._client = client
        self._is_streaming = True
        print("Rigid body streaming started successfully")

    def stop_streaming(self):
        """Stop the persistent rigid body data streaming."""
        if self._client is not None:
            self._client.shutdown()
            self._client = None
            self._streaming_data = {}
            self._lock = None
            self._is_streaming = False
            print("Rigid body streaming stopped")

    def get_rigid_body_data(self, rigid_body_id: int, info_type: str = "both", timeout: float = 3.0):
        """Get specific rigid body data from persistent stream.
        
        Args:
            rigid_body_id (int): ID of the rigid body to track
            info_type (str): Type of data to return - "position", "orientation", or "both"
            timeout (float): Timeout in seconds
            
        Returns:
            dict: Contains requested data with keys:
                - "position": [x, y, z] if info_type is "position" or "both"
                - "orientation": [qx, qy, qz, qw] if info_type is "orientation" or "both"
                - "marker_error": float (always included)
                - "tracking_valid": bool (always included)
                
        Raises:
            RuntimeError: If streaming is not started
            TimeoutError: If no sample is received within timeout
            ValueError: If info_type is not "position", "orientation", or "both"
        """
        if not self._is_streaming:
            raise RuntimeError("Streaming not started. Call start_streaming() first.")
        
        if info_type not in ["position", "orientation", "both"]:
            raise ValueError("info_type must be 'position', 'orientation', or 'both'")
        
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            with self._lock:
                if rigid_body_id in self._streaming_data:
                    sample = self._streaming_data[rigid_body_id]
                    
                    # Build result based on requested info_type
                    result = {
                        "marker_error": sample["marker_error"],
                        "tracking_valid": sample["tracking_valid"]
                    }
                    
                    if info_type in ["position", "both"]:
                        result["position"] = sample["position"]
                    
                    if info_type in ["orientation", "both"]:
                        result["orientation"] = sample["orientation"]
                    
                    return result
            
            time.sleep(0.01)  # Small delay to prevent busy waiting
        
        raise TimeoutError(f"No data received for rigid body {rigid_body_id} within {timeout} seconds")

    def get_marker_sets(self, timeout: float = 3.0):
        """Get latest labeled markers grouped by model name.
        
        Args:
            timeout (float): Timeout in seconds
        
        Returns:
            dict: {model_name: list of [x, y, z]}
        """
        if not self._is_streaming:
            raise RuntimeError("Streaming not started. Call start_streaming() first.")

        start_time = time.time()
        while (time.time() - start_time) < timeout:
            with self._lock:
                if self._marker_sets:
                    return {k: [pos[:] for pos in v] for k, v in self._marker_sets.items()}
            time.sleep(0.01)
        return {}

    def get_unlabeled_markers(self, timeout: float = 3.0):
        """Get latest unlabeled marker positions.
        
        Args:
            timeout (float): Timeout in seconds
        
        Returns:
            list: list of [x, y, z]
        """
        if not self._is_streaming:
            raise RuntimeError("Streaming not started. Call start_streaming() first.")

        start_time = time.time()
        while (time.time() - start_time) < timeout:
            with self._lock:
                if self._unlabeled_markers:
                    return [p[:] for p in self._unlabeled_markers]
            time.sleep(0.01)
        return []

    def get_labeled_markers(self, timeout: float = 3.0):
        """Get latest labeled markers with IDs and attributes.
        
        Args:
            timeout (float): Timeout in seconds
        
        Returns:
            list: list of dicts {id, model_id, marker_id, pos, size, residual, param}
        """
        if not self._is_streaming:
            raise RuntimeError("Streaming not started. Call start_streaming() first.")

        start_time = time.time()
        while (time.time() - start_time) < timeout:
            with self._lock:
                if self._labeled_markers:
                    # deep-ish copy to avoid mutation issues
                    out = []
                    for m in self._labeled_markers:
                        out.append({
                            "id": m["id"],
                            "model_id": m["model_id"],
                            "marker_id": m["marker_id"],
                            "pos": m["pos"][:],
                            "size": m["size"],
                            "residual": m["residual"],
                            "param": m["param"],
                        })
                    return out
            time.sleep(0.01)
        return []

    def get_rigid_body_position(self, rigid_body_id: int, timeout: float = 3.0):
        """Get position data for a rigid body.
        
        Args:
            rigid_body_id (int): ID of the rigid body to track
            timeout (float): Timeout in seconds
            
        Returns:
            list: Position [x, y, z]
        """
        data = self.get_rigid_body_data(rigid_body_id, "position", timeout)
        return data["position"]

    def get_relitive_rigid_body_position(self, rigid_body_id_1: int, rigid_body_id_2: int, timeout: float = 3.0)->list | None:
        """Get relitive position data for a rigid body.

        Returns:
            list | None: Relitive position [x, y, z] or None if unavailable
        """
        try:
            position_1 = self.get_rigid_body_position(rigid_body_id_1, timeout)
            position_2 = self.get_rigid_body_position(rigid_body_id_2, timeout)
        except (TimeoutError, RuntimeError):
            return None

        if position_1 is None or position_2 is None:
            return None

        return [position_2[i] - position_1[i] for i in range(3)]

    def get_relitive_rigid_body_position_local_coordinate_frame(self, rigid_body_id_1: int, rigid_body_id_2: int, timeout: float = 3.0):
        try:
            position_1 = self.get_rigid_body_position(rigid_body_id_1, timeout)
            position_2 = self.get_rigid_body_position(rigid_body_id_2, timeout)
            orientation_1 = self.get_rigid_body_orientation(rigid_body_id_1, timeout)
        except (TimeoutError, RuntimeError):
            return None

        if position_1 is None or position_2 is None:
            return None

        relative_position_world = [position_2[i] - position_1[i] for i in range(3)]

        R = self._quaternion_to_rotation_matrix(orientation_1)
        R_inv = R.T  # For unit quaternions, inverse = transpose
        relative_position_local = R_inv @ np.array(relative_position_world)

        return relative_position_local
        
    def get_rigid_body_orientation(self, rigid_body_id: int, timeout: float = 3.0):
        """Get orientation data for a rigid body.
        
        Args:
            rigid_body_id (int): ID of the rigid body to track
            timeout (float): Timeout in seconds
            
        Returns:
            list: Orientation [qx, qy, qz, qw]
        """
        data = self.get_rigid_body_data(rigid_body_id, "orientation", timeout)
        return data["orientation"]

    def get_relitive_rigid_body_orientation(self, rigid_body_id_1: int, rigid_body_id_2: int, timeout: float = 3.0):
        """Get relitive orientation data for a rigid body.
        
        Args:
            rigid_body_id_1 (int): ID of the first rigid body to track
            rigid_body_id_2 (int): ID of the second rigid body to track
            timeout (float): Timeout in seconds
        """
        orientation_1 = self.get_rigid_body_orientation(rigid_body_id_1, timeout)
        orientation_2 = self.get_rigid_body_orientation(rigid_body_id_2, timeout)
        return [orientation_2[i] - orientation_1[i] for i in range(4)]

    def get_rigid_body_pose(self, rigid_body_id: int, timeout: float = 3.0):
        """Get both position and orientation data for a rigid body.
        
        Args:
            rigid_body_id (int): ID of the rigid body to track
            timeout (float): Timeout in seconds
            
        Returns:
            tuple: (position, orientation) where position is [x, y, z] and orientation is [qx, qy, qz, qw]
        """
        data = self.get_rigid_body_data(rigid_body_id, "both", timeout)
        return data["position"], data["orientation"]

    def list_available_rigid_bodies(self, timeout: float = 5.0):
        """List all available rigid bodies being tracked.
        
        Args:
            timeout (float): Timeout in seconds
            
        Returns:
            list: List of dicts with rigid body information
        """
        if not self._is_streaming:
            raise RuntimeError("Streaming not started. Call start_streaming() first.")
        
        start_time = time.time()
        rigid_bodies_seen = set()
        result = []
        
        while (time.time() - start_time) < timeout:
            with self._lock:
                for rb_id, data in self._streaming_data.items():
                    if rb_id not in rigid_bodies_seen:
                        result.append(data.copy())
                        rigid_bodies_seen.add(rb_id)
            
            if result:
                break
            time.sleep(0.1)
        
        return result

    def _quaternion_to_rotation_matrix(self, quaternion):
        """Convert quaternion [qx, qy, qz, qw] to rotation matrix"""
        qx, qy, qz, qw = quaternion
        
        # Normalize quaternion
        norm = np.sqrt(qx*qx + qy*qy + qz*qz + qw*qw)
        qx, qy, qz, qw = qx/norm, qy/norm, qz/norm, qw/norm
        
        # Convert to rotation matrix
        R = np.array([
            [1 - 2*(qy*qy + qz*qz), 2*(qx*qy - qw*qz), 2*(qx*qz + qw*qy)],
            [2*(qx*qy + qw*qz), 1 - 2*(qx*qx + qz*qz), 2*(qy*qz - qw*qx)],
            [2*(qx*qz - qw*qy), 2*(qy*qz + qw*qx), 1 - 2*(qx*qx + qy*qy)]
        ])
        return R

    def is_streaming(self):
        """Check if streaming is active.
        
        Returns:
            bool: True if streaming is active, False otherwise
        """
        return self._is_streaming

    def __enter__(self):
        """Context manager entry."""
        self.start_streaming()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_streaming()
