# mobile-base-sdk
High level interface to control the mobile
base
## Mobility commands
There are 2 ways to send mobility commands: 
1. Setting a speed (vx in m/s, vy in m/s, vtheta in deg/s, duration in s) for a fixed duration with the function '''set_speed'''
2. Setting a goal position (x in m, y in m, theta in deg) in the odometric frame

Note: using set_speed with a duration of 0 is a special case: the mobile base HAL will use the CMD_VEL drive mode instead of the usual SPEED mode. This is is useful when requesting speed commands very often.
The changing of modes is an automatic process and doesn't need xxx

## Utility commands

 
