from PIL import Image
import io
import zlib

from google.protobuf.empty_pb2 import Empty
from google.protobuf.wrappers_pb2 import BoolValue, FloatValue

from mobile_base_sdk_api.mobile_base_pb2 import LidarSafety


class Lidar:
    def __init__(self, stub) -> None:
        self._stub = stub

        self._update_safety_info()

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
    def safety_distance(self):
        """Safety distance in meters of the mobile base from obstacles.
        The mobile base's speed is slowed down if the direction of speed matches the direction of
        at least 1 LIDAR point in the safety_distance range.
        """
        return self._safety_distance

    @safety_distance.setter
    def safety_distance(self, value):
        self._stub.SetZuuuSafety(
            LidarSafety(
                safety_distance=FloatValue(value=value),
                critical_distance=FloatValue(value=self._critical_distance),
                safety_on=BoolValue(value=self._safety_enabled),
            ))
        self._update_safety_info()

    @property
    def critical_distance(self):
        """Critical distance in meters of the mobile base from obstacles.
        The mobile base's speed is changed to 0 if the direction of speed matches the direction of
        at least 1 LIDAR point in the critical_distance range.
        If at least 1 point is in the critical distance, then even motions that move away from the obstacles are
        slowed down to the "safety_zone" speed.
        """
        return self._critical_distance

    @critical_distance.setter
    def critical_distance(self, value):
        self._stub.SetZuuuSafety(
            LidarSafety(
                safety_distance=FloatValue(value=self._safety_distance),
                critical_distance=FloatValue(value=value),
                safety_on=BoolValue(value=self._safety_enabled),
            ))
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
            ))
        self._update_safety_info()