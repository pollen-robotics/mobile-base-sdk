"""LIDAR module for mobile base SDK.

Handles the LIDAR features:
    - get the map of the environment
    - set the safety distance
    - set the critical distance
    - enable/disable the safety feature
"""
import io
import zlib

from google.protobuf.empty_pb2 import Empty
from google.protobuf.wrappers_pb2 import BoolValue, FloatValue
from PIL import Image
from reachy2_sdk_api import mobile_base_lidar_pb2_grpc as lidar_pb2_grpc
from reachy2_sdk_api.mobile_base_lidar_pb2 import LidarObstacleDetectionEnum, LidarObstacleDetectionStatus, LidarSafety


class Lidar:
    """LIDAR class for mobile base SDK."""

    def __init__(self, grpc_channel) -> None:
        """Initialize the LIDAR class."""
        self._stub = lidar_pb2_grpc.MobileBaseLidarServiceStub(grpc_channel)

        self._update_safety_info()

    def __repr__(self) -> str:
        """Clean representation of a Reachy."""
        return f"""<Lidar safety_enabled={self.safety_enabled}>"""

    def get_map(self):
        """Get the current map of the environment."""
        compressed_map = self._stub.GetLidarMap(Empty()).data
        uncompressed_bytes = zlib.decompress(compressed_map)
        buf = io.BytesIO(uncompressed_bytes)
        self.map = Image.open(buf)
        return self.map

    def _update_safety_info(self):
        response = self._stub.GetZuuuSafety(Empty())
        self._safety_distance = round(response.safety_distance.value, 2)
        self._critical_distance = round(response.critical_distance.value, 2)
        self._safety_enabled = response.safety_on.value

    @property
    def safety_slowdown_distance(self):
        """Safety distance in meters of the mobile base from obstacles.

        The mobile base's speed is slowed down if the direction of speed matches the direction of
        at least 1 LIDAR point in the safety_distance range.
        """
        return self._safety_distance

    @safety_slowdown_distance.setter
    def safety_slowdown_distance(self, value):
        self._stub.SetZuuuSafety(
            LidarSafety(
                safety_distance=FloatValue(value=value),
                critical_distance=FloatValue(value=self._critical_distance),
                safety_on=BoolValue(value=self._safety_enabled),
            )
        )
        self._update_safety_info()

    @property
    def safety_critical_distance(self):
        """Critical distance in meters of the mobile base from obstacles.

        The mobile base's speed is changed to 0 if the direction of speed matches the direction of
        at least 1 LIDAR point in the critical_distance range.
        If at least 1 point is in the critical distance, then even motions that move away from the obstacles are
        slowed down to the "safety_zone" speed.
        """
        return self._critical_distance

    @safety_critical_distance.setter
    def safety_critical_distance(self, value):
        self._stub.SetZuuuSafety(
            LidarSafety(
                safety_distance=FloatValue(value=self._safety_distance),
                critical_distance=FloatValue(value=value),
                safety_on=BoolValue(value=self._safety_enabled),
            )
        )
        self._update_safety_info()

    @property
    def safety_enabled(self):
        """Enable or disable the safety feature."""
        return self._safety_enabled

    @safety_enabled.setter
    def safety_enabled(self, value):
        self._stub.SetZuuuSafety(
            LidarSafety(
                safety_distance=FloatValue(value=self._safety_distance),
                critical_distance=FloatValue(value=self._critical_distance),
                safety_on=BoolValue(value=value),
            )
        )
        self._update_safety_info()

    @property
    def obstacle_detection_status(self) -> LidarObstacleDetectionStatus:
        """Get status of the lidar obstacle detection.

        Can be either NO_OBJECT_DETECTED, OBJECT_DETECTED_SLOWDOWN, OBJECT_DETECTED_STOP or DETECTION_ERROR.
        """
        return LidarObstacleDetectionEnum.Name(self._stub.GetZuuuSafety(Empty()).obstacle_detection_status.status)

    def reset_safety_default_values(self) -> None:
        """Reset default distances values for safety detection.

        Reset values are:
        - safety_critical_distance
        - safety_slowdown_distance.
        """
        self.safety_critical_distance = 0.55
        self.safety_slowdown_distance = 0.7
