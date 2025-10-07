import time
import threading
from .NatNetSDK import NatNetClient



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
        
        client = NatNetClient()
        client.set_client_address(self.client_address)
        client.set_server_address(self.server_address)
        client.set_use_multicast(False if self.unicast else True)
        client.set_print_level(0)

        def on_frame_with_data(data_dict):
            mocap_data = data_dict.get("mocap_data")
            if mocap_data is None or mocap_data.rigid_body_data is None:
                return
            
            with self._lock:
                for rb in mocap_data.rigid_body_data.rigid_body_list:
                    self._streaming_data[rb.id_num] = {
                        "rigid_body_id": rb.id_num,
                        "position": [rb.pos[0], rb.pos[1], rb.pos[2]],
                        "orientation": [rb.rot[0], rb.rot[1], rb.rot[2], rb.rot[3]],
                        "marker_error": rb.error,
                        "tracking_valid": True if rb.tracking_valid else False,
                    }

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

    def get_position(self, rigid_body_id: int, timeout: float = 3.0):
        """Get position data for a rigid body.
        
        Args:
            rigid_body_id (int): ID of the rigid body to track
            timeout (float): Timeout in seconds
            
        Returns:
            list: Position [x, y, z]
        """
        data = self.get_rigid_body_data(rigid_body_id, "position", timeout)
        return data["position"]

    def get_orientation(self, rigid_body_id: int, timeout: float = 3.0):
        """Get orientation data for a rigid body.
        
        Args:
            rigid_body_id (int): ID of the rigid body to track
            timeout (float): Timeout in seconds
            
        Returns:
            list: Orientation [qx, qy, qz, qw]
        """
        data = self.get_rigid_body_data(rigid_body_id, "orientation", timeout)
        return data["orientation"]

    def get_pose(self, rigid_body_id: int, timeout: float = 3.0):
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
