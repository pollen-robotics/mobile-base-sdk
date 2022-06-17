"""."""
from matplotlib.pyplot import get
from numpy import round

import grpc
from google.protobuf.empty_pb2 import Empty
from google.protobuf.wrappers_pb2 import FloatValue

from reachy_sdk_api import mobile_platform_reachy_pb2 as mp_pb2, mobile_platform_reachy_pb2_grpc as mp_pb2_grpc


class MobileBaseSDK:
    """."""

    def __init__(self, host: str, mobile_base_port: int = 50061) -> None:
        self._host = host
        self._mobile_nase_port = mobile_base_port
        self._grpc_channel = grpc.insecure_channel(f'{self._host}:{self._mobile_nase_port}')

        self._stub = mp_pb2_grpc.MobilityServiceStub(self._grpc_channel)
        self._presence_stub = mp_pb2_grpc.MobileBasePresenceServiceStub(self._grpc_channel)

        def get_drive_mode():
            mode_id = self._stub.GetZuuuMode(Empty()).mode
            return mp_pb2.ZuuuModePossiblities.keys()[mode_id]

        def get_control_mode():
            mode_id = self._stub.GetControlMode(Empty()).mode
            return mp_pb2.ControlModePossiblities.keys()[mode_id]

        self._drive_mode = get_drive_mode()
        self._control_mode = get_control_mode()

    def __repr__(self) -> str:
        pass

    @property
    def model_version(self):
        return self._presence_stub.GetMobileBasePresence(Empty()).model_version.value

    @property
    def battery_level(self):
        return round(self._stub.GetBatteryLevel(Empty()).level.value, 1)

    @property
    def odometry(self):
        response = self._stub.GetOdometry(Empty())
        odom = {
            'x': response.x.value,
            'y': response.y.value,
            'theta': response.theta.value,
        }
        return odom

    @property
    def drive_mode(self):
        return self._drive_mode

    @drive_mode.setter
    def drive_mode(self, mode: str):
        possible_drive_modes = [mode.lower() for mode in mp_pb2.ZuuuModePossiblities.keys()][1:]
        if mode in possible_drive_modes:
            req = mp_pb2.ZuuuModeCommand(
                mode=getattr(mp_pb2.ZuuuModePossiblities, mode.upper())
            )
            self._stub.SetZuuuMode(req)
            self._drive_mode = mode
        else:
            print(f'Drive mode requested should be in {possible_drive_modes}!')

    @property
    def control_mode(self):
        return self._control_mode

    @control_mode.setter
    def control_mode(self, mode: str):
        possible_control_modes = [mode.lower() for mode in mp_pb2.ControlModePossiblities.keys()][1:]
        if mode in possible_control_modes:
            req = mp_pb2.ControlModeCommand(
                mode=getattr(mp_pb2.ControlModePossiblities, mode.upper())
            )
            self._stub.SetControlMode(req)
            self._control_mode = mode
        else:
            print(f'Drive mode requested should be in {possible_control_modes}!')

    def reset_odometry(self):
        self._stub.ResetOdometry(Empty())

    def set_speed(self, x_vel: float, y_vel: float, rot_vel: float, duration: float):
        if not duration:
            if self.drive_mode != 'cmd_vel':
                self.drive_mode = 'cmd_vel'

            req = mp_pb2.TargetDirectionCommand(
                direction=mp_pb2.DirectionVector(
                    x=FloatValue(value=x_vel),
                    y=FloatValue(value=y_vel),
                    theta=FloatValue(value=rot_vel),
                )
            )
            self._stub.SendDirection(req)
        else:
            req = mp_pb2.SetSpeedVector(
                duration=FloatValue(value=duration),
                x_vel=FloatValue(value=x_vel),
                y_vel=FloatValue(value=y_vel),
                rot_vel=FloatValue(value=rot_vel),
            )
            self._stub.SendSetSpeed(req)

    def go_to(self, x: float, y: float, theta: float):
        req = mp_pb2.GoToVector(
            x_goal=FloatValue(value=x),
            y_goal=FloatValue(value=y),
            theta_goal=FloatValue(value=theta),
        )
        self._stub.SendGoTo(req)

    def _distance_to_go_to_goal(self):
        response = self._stub.DistanceToGoal(Empty())
        distance = {
            'delta_x': round(response.delta_x.value, 3),
            'delta_y': round(response.delta_y.value, 3),
            'delta_theta': round(response.delta_theta.value, 3),
            'distance': round(response.distance.value, 3),
        }
        return distance

    def emergency_shutdown(self):
        self.drive_mode = 'emergency_stop'
