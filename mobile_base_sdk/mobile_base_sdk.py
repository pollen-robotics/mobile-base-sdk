"""MobileBaseSDK package.

This package provides remote access (via socket) to the mobile base of a Reachy robot.
You can have access to basic information from the mobile base such as the battery voltage
or the odometry. You can also easily make the mobile base move by setting a goal position
in cartesian coordinates (x, y, theta) or directly send velocities (x_vel, y_vel, theta_vel).
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from logging import getLogger
from queue import Queue
from typing import Optional


import grpc
from google.protobuf.empty_pb2 import Empty
from google.protobuf.wrappers_pb2 import BoolValue, FloatValue
from numpy import deg2rad, rad2deg, round
from reachy2_sdk_api import mobile_base_mobility_pb2 as mob_pb2
from reachy2_sdk_api import mobile_base_mobility_pb2_grpc as mob_pb2_grpc
from reachy2_sdk_api import mobile_base_utility_pb2 as util_pb2
from reachy2_sdk_api import mobile_base_utility_pb2_grpc as util_pb2_grpc

from .lidar import Lidar


class MobileBaseSDK:
    """The MobileBaseSDK class handles the connection with Reachy's mobile base.

    It holds:

    - the odometry of the base (you can also easily reset it),
    - the battery voltage to monitor the battery usage,
    - the control and drive mode of the base,
    - two methods to send target positions or target velocities.

    If you encounter a problem when using the base, you have access to an emergency shutdown method.
    """

    def __init__(self, host: str, mobile_base_port: int = 50051) -> None:
        """Set up the connection with the mobile base."""
        self._logger = getLogger()
        self._host = host
        self._mobile_base_port = mobile_base_port
        self._grpc_channel = grpc.insecure_channel(f"{self._host}:{self._mobile_base_port}")

        self._utility_stub = util_pb2_grpc.MobileBaseUtilityServiceStub(self._grpc_channel)
        self._mobility_stub = mob_pb2_grpc.MobileBaseMobilityServiceStub(self._grpc_channel)

        self._drive_mode = self._get_drive_mode().lower()
        self._control_mode = self._get_control_mode().lower()

        self._max_xy_vel = 1.0
        self._max_rot_vel = 180.0
        self._max_xy_goto = 1.0

        self.lidar = Lidar(self._grpc_channel)

    def __repr__(self) -> str:
        """Clean representation of a mobile base."""
        repr_template = (
            '<MobileBase host="{host}" on={on} \n'
            " lidar_safety_enabled={lidar_safety_enabled} \n"
            " battery_voltage={battery_voltage}>"
        )
        return repr_template.format(
            host=self._host,
            on=self.is_on(),
            lidar_safety_enabled=self.lidar.safety_enabled,
            battery_voltage=self.battery_voltage,
        )

    def _get_drive_mode(self):
        mode_id = self._utility_stub.GetZuuuMode(Empty()).mode
        return util_pb2.ZuuuModePossiblities.keys()[mode_id]

    def _get_control_mode(self):
        mode_id = self._utility_stub.GetControlMode(Empty()).mode
        return util_pb2.ControlModePossiblities.keys()[mode_id]

    @property
    def battery_voltage(self) -> float:
        """Return the battery voltage. Battery should be recharged if it reaches 24.5V or below."""
        return round(self._utility_stub.GetBatteryLevel(Empty()).level.value, 1)

    @property
    def odometry(self):
        """Return the odometry of the base. x, y are in meters and theta in degree."""
        response = self._utility_stub.GetOdometry(Empty())
        odom = {
            "x": round(response.x.value, 3),
            "y": round(response.y.value, 3),
            "theta": round(rad2deg(response.theta.value), 3),
        }
        return odom

    def _set_drive_mode(self, mode: str):
        """Set the base's drive mode."""
        all_drive_modes = [mode.lower() for mode in util_pb2.ZuuuModePossiblities.keys()][1:]
        possible_drive_modes = [mode for mode in all_drive_modes if mode not in ("speed", "goto")]
        if mode in possible_drive_modes:
            req = util_pb2.ZuuuModeCommand(mode=getattr(util_pb2.ZuuuModePossiblities, mode.upper()))
            self._utility_stub.SetZuuuMode(req)
            self._drive_mode = mode
        else:
            self._logger.warning(f"Drive mode requested should be in {possible_drive_modes}!")

    def _set_control_mode(self, mode: str):
        """Set the base's control mode."""
        possible_control_modes = [mode.lower() for mode in util_pb2.ControlModePossiblities.keys()][1:]
        if mode in possible_control_modes:
            req = util_pb2.ControlModeCommand(mode=getattr(util_pb2.ControlModePossiblities, mode.upper()))
            self._utility_stub.SetControlMode(req)
            self._control_mode = mode
        else:
            self._logger.warning(f"Control mode requested should be in {possible_control_modes}!")

    def reset_odometry(self):
        """Reset the odometry."""
        self._utility_stub.ResetOdometry(Empty())
        time.sleep(0.03)

    def set_speed(self, x_vel: float, y_vel: float, rot_vel: float):
        """Send target speed. x_vel, y_vel are in m/s and rot_vel in deg/s for 200ms.

        The 200ms duration is predifined at the ROS level of the mobile base's code.
        This mode is prefered if the user wants to send speed instructions frequently.
        """
        if self._drive_mode != "cmd_vel":
            self._set_drive_mode("cmd_vel")

        for vel, value in {"x_vel": x_vel, "y_vel": y_vel}.items():
            if abs(value) > self._max_xy_vel:
                raise ValueError(f"The asbolute value of {vel} should not be more than {self._max_xy_vel}!")

        if abs(rot_vel) > self._max_rot_vel:
            raise ValueError(f"The asbolute value of rot_vel should not be more than {self._max_rot_vel}!")

        req = mob_pb2.TargetDirectionCommand(
            direction=mob_pb2.DirectionVector(
                x=FloatValue(value=x_vel),
                y=FloatValue(value=y_vel),
                theta=FloatValue(value=deg2rad(rot_vel)),
            )
        )
        self._mobility_stub.SendDirection(req)

    def goto(
        self,
        x: float,
        y: float,
        theta: float,
        timeout: Optional[float] = None,
        tolerance: dict = {"delta_x": 0.1, "delta_y": 0.1, "delta_theta": 15, "distance": 0.1},
    ):
        """Send target position. x, y are in meters and theta is in degree.

        (x, y) will define the position of the mobile base in cartesian space
        and theta its orientation. The zero position is set when the mobile base is
        started or if the  reset_odometry method is called.
        A timeout in seconds is defined so that the mobile base does get stuck in a go
        to call.
        The tolerance represents the margin along x, y and theta for which we consider
        that the mobile base has arrived its goal.
        """
        if self.is_off():
            raise RuntimeError(("Mobile base is off. Goto not sent."))

        exc_queue: Queue[Exception] = Queue()

        if not timeout:
            # We consider that the max velocity for the mobile base is 0.5 m/s
            # timeout is 2*_max_xy_goto / max velocity
            timeout = 2 * self._max_xy_goto / 0.5

        def _wrapped_goto():
            try:
                asyncio.run(
                    self._goto_async(
                        x=x,
                        y=y,
                        theta=theta,
                        timeout=timeout,
                        tolerance=tolerance,
                    ),
                )
            except Exception as e:
                exc_queue.put(e)

        with ThreadPoolExecutor() as exec:
            exec.submit(_wrapped_goto)
        if not exc_queue.empty():
            raise exc_queue.get()

    async def _goto_async(
        self,
        x: float,
        y: float,
        theta: float,
        timeout: float,
        tolerance: dict = {"delta_x": 0.1, "delta_y": 0.1, "delta_theta": 15, "distance": 0.1},
    ):
        """Async version of the goto method."""
        for pos, value in {"x": x, "y": y}.items():
            if abs(value) > self._max_xy_goto:
                raise ValueError(f"The asbolute value of {pos} should not be more than {self._max_xy_goto}!")

        req = mob_pb2.GoToVector(
            x_goal=FloatValue(value=x),
            y_goal=FloatValue(value=y),
            theta_goal=FloatValue(value=deg2rad(theta)),
        )
        self._drive_mode = "go_to"
        self._mobility_stub.SendGoTo(req)

        tic = time.time()
        arrived: bool
        while time.time() - tic < timeout:
            arrived = True
            distance_to_goal = self._distance_to_goto_goal()
            for delta_key in tolerance.keys():
                if tolerance[delta_key] < abs(distance_to_goal[delta_key]):
                    arrived = False
                    break
            await asyncio.sleep(0.1)
            if arrived:
                break

        if not arrived and self.lidar.obstacle_detection_status == "OBJECT_DETECTED_STOP":
            self._logger.warning("Target not reached. Mobile base stopped because of obstacle.")

    def _distance_to_goto_goal(self):
        response = self._mobility_stub.DistanceToGoal(Empty())
        distance = {
            "delta_x": round(response.delta_x.value, 3),
            "delta_y": round(response.delta_y.value, 3),
            "delta_theta": round(rad2deg(response.delta_theta.value), 3),
            "distance": round(response.distance.value, 3),
        }
        return distance

    def turn_on(self) -> None:
        """Stop the mobile base immediately by changing its drive mode to 'brake'."""
        self._set_drive_mode("brake")

    def turn_off(self) -> None:
        """Set the mobile base in free wheel mode."""
        self._set_drive_mode("free_wheel")

    def is_on(self) -> bool:
        """Return True if the mobile base is not compliant."""
        self._drive_mode = self._get_drive_mode().lower()
        return not self._drive_mode == "free_wheel"

    def is_off(self) -> bool:
        """Return True if the mobile base is compliant."""
        self._drive_mode = self._get_drive_mode().lower()
        return self._drive_mode == "free_wheel"

    def _set_safety(self, safety_on):
        req = mob_pb2.SetZuuuSafetyRequest(safety_on=BoolValue(value=safety_on))
        self._utility_stub.SetZuuuSafety(req)
