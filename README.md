# Mobile Base Python SDK for Reachy 2021

As of July 2022, the [Reachy robot](https://www.pollen-robotics.com/reachy/) gained mobility!

Reachy is now equipped with an omnidirectional open source mobile base allowing the robot to move in any direction, turn itself around, go through doors or squeeze through tight spaces.

<img src="https://www.pollen-robotics.com/img/reachy/packs/reachy-full-kit-mobile.png" width="400">

The mobile base Python SDK is a pure Python SDk library that let you control Reachy's mobile base even without having Reachy's motors turned on.

You can use the SDK over the network. The communication to the robot is done via [gRPC](https://grpc.io) and can thus work on most kind of network configurations. Local control of the mobile base directly on Reachy's computer can simply be done using the localhost IP.

## License

The mobile base SDK, and the rest of Reachy software, is open-source and released under an Apache-2.0 License.
 
## Installation

#### From PyPi
```bash
pip install mobile-base-sdk
```

#### From the source

```bash
git clone https://github.com/pollen-robotics/mobile-base-sdk
pip install -e mobile-base-sdk
```

We recommend using a [virtual environment](https://docs.python.org/3/tutorial/venv.html) for your development.

The SDK depends on [numpy](https://numpy.org), [grpc](https://grpc.io) and [reachy-sdk-api](https://github.com/pollen-robotics/reachy-sdk-api). 


## Getting Started

A section in our online documentation is dedicated to the [mobile base SDK](https://docs.pollen-robotics.com/sdk/mobile-base) to learn how to use it.


Connecting the SDK to Reachy's mobile base is as simple as:

```python
from mobile_base_sdk import MobileBaseSDK

mobile_base = MobileBaseSDK(host='my-reachy-ip')
```

### Examples
Examples are available in this repository as notebooks or Python scripts to show you how to use the mobile base Python SDK.

You will find:
*  
* 
*

## Connect to a Reachy
It is also possible to connect simultaneously to Reachy and its mobile base using [reachy-sdk](https://github.com/pollen-robotics/reachy-sdk).

```python
from reachy_sdk import ReachySDK

reachy = ReachySDK(host='my-reachy-ip', with_mobile_base=True)
reachy.mobile_base.goto(x=0.5, y=0.0, theta=0.0)
```

See the [dedicated notebook]() for an example of using both Reachy and its mobile base simultaneously.

## Support 

This project adheres to the Contributor [code of conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [contact@pollen-robotics.com](mailto:contact@pollen-robotics.com).

Visit [pollen-robotics.com](https://pollen-robotics.com) to learn more or join our [Dicord community](https://discord.com/invite/Kg3mZHTKgs) if you have any questions or want to share your ideas.
Follow [@PollenRobotics](https://twitter.com/pollenrobotics) on Twitter for important announcements.
