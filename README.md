# LLDroneInterface
Large Language Interface For MAVProxy Drones using either the MAVUTIL library (like the Pixhawk 6 series) or the MAVSDK library (like the ModalAI Seeker).

Confirmed working for Windows 11; Unconfirmed for Windows 10

Contributors:
Victor Le (Team Lead) | Angel Gomez | Hieu Le | Nicolas Upshaw

Special Thanks to: Professor Bin Hu | Richie Ryu Suganda | Enlai Yii | Sal V So | University of Houston NAIL Lab



### Install Python/Python3

Go to https://www.python.org/downloads/

Download the latest Python stable version (as of 2-18-2025, that version is 3.13.2)

Before clicking install, check both "Use admin privileges when installing py.exe" and "Add python.exe" to PATH


### Install Visual Studio Code

Go to https://code.visualstudio.com/download

Install VS Code without changing any of the installer settings


### Setting up VS Code for Python Scripts

Make a new folder for LLM Testing. Ensure you know the directory to this folder.

If prompted, click "Yes, I trust the authors". You can click the check box above that says "Trust the authors of all files in the parent folder '<Folder Name>'

On the left side of the VS Code window, click the 5th icon from the top: Extensions


### Install Python first and Pylance second

On the left side of the VS Code window, click the 1st icon from the top: Explorer

Hover over the new folder you made and click the first icon directly to the right of the folder name: New File... 

Ensure the title of the new file ends with .py (to notate that it is a Python script)

Click on the hamburger symbol towards the top left, hover over Terminal, and click New Terminal

Disregard hamburger symbol if you do not see that

Run this in the terminal first: 
``` 
python.exe -m pip install --upgrade pip
```

Copy and paste the following:

```
pip install annotated-types, anyio, audioop-lts, certifi, charset-normalizer, click, colorama, coloredlogs, contourpy, cycler, dronekit, flatbuffers, fonttools, future, gTTS, h11, httpcore, httpx, humanfriendly, idna, iso8601, kiwisolver, lxml, matplotlib, MAVProxy, monotonic, mpmath, numpy, onnxruntime, opencv-python, packaging, pexpect, pillow, protobuf, ptyprocess, PyAudio, pyception, pydantic, pydantic_core, pygame, pymavlink, pynmeagps, pyparsing, pyreadline3, pyserial, python-dateutil, PyYAML, requests, scipy, serial, setuptools, six, sniffio, SpeechRecognition, standard-aifc, standard-chunk, sympy, tqdm, typing_extensions, urllib3, wheel, wxtools
```

Below is the updated PIP command with all of the additional libraries we installed:

```
pip install accelerate, aiohappyeyeballs, aiohttp, aiosignal, annotated-types, anyio, attrs, audioop-lts, bitsandbytes, catkin-pkg, certifi, charset-normalizer, click, colorama, coloredlogs, contourpy, ctransformers, cycler, datasets, dill, docutils, dronekit, empy, filelock, flatbuffers, fonttools, frozenlist, fsspec, future, gTTS, h11, httpcore, httpx, huggingface-hub, humanfriendly, idna, iso8601, Jinja2, kiwisolver, lark-parser, lxml, MarkupSafe, matplotlib, MAVProxy, monotonic, mpmath, multidict, multiprocess, networkx, numpy, onnxruntime, opencv-python, packaging, pandas, peft, pexpect, pillow, pip, propcache, protobuf, psutil, ptyprocess, py-cpuinfo, pyarrow, PyAudio, pyception, pydantic, pydantic_core, pydot, pygame, pymavlink, pynmeagps, pyparsing, PyQt5, PyQt5-Qt5, PyQt5_sip, pyreadline3, pyserial, python-dateutil, pytz, PyYAML, regex, requests, safetensors, scipy, serial, setuptools, six, sniffio, SpeechRecognition, standard-aifc, standard-chunk, sty, sympy, tello, tokenizers, torch, tqdm, transformers, typing_extensions, tzdata, urllib3, wheel, wxtools, xxhash, yarl
```

```
pip3 install accelerate aiohappyeyeballs aiohttp aiosignal annotated-types anyio attrs audioop-lts bitsandbytes catkin-pkg certifi charset-normalizer click colorama coloredlogs contourpy ctransformers cycler datasets dill docutils dronekit empy filelock flatbuffers fonttools frozenlist fsspec future gTTS h11 httpcore httpx huggingface-hub humanfriendly idna iso8601 Jinja2 kiwisolver lark-parser lxml MarkupSafe matplotlib MAVProxy monotonic mpmath multidict multiprocess networkx numpy onnxruntime opencv-python packaging pandas peft pexpect pillow pip propcache protobuf psutil ptyprocess py-cpuinfo pyarrow PyAudio pyception pydantic pydantic_core pydot pygame pymavlink pynmeagps pyparsing PyQt5 PyQt5-Qt5 PyQt5_sip pyreadline3 pyserial python-dateutil pytz PyYAML regex requests safetensors scipy serial setuptools six sniffio SpeechRecognition standard-aifc standard-chunk sty sympy tello tokenizers torch tqdm transformers typing_extensions tzdata urllib3 wheel wxtools xxhash yarl
```






# How to install Pixhawk 6 Series Adrupilot Gazebo Simulator

## Install SITL

### 1. Install Windows Subsystem for Linux(WSL)

Open PowerShell as Administrator and run:

```
wsl --install
```

Restart your computer



### 2.Install Ubuntu 22.04.5 from the Microsoft Store

Open the WSL Terminal

Make a username and password you will remember

Run this first: 

```
sudo hwclock -s 
```

OR 

```
sudo timedatectl set-ntp true
```


### 3. Run the following (copy and paste the 3 lines below and paste it into WSL)

```
sudo apt update && sudo apt upgrade -y
sudo apt install git python3 python3-pip python3-matplotlib python3-wxgtk4.0 python3-lxml python3-scipy python3-opencv ccache gawk git python3-pip python3-pexpect -y
pip3 install --user MAVProxy PyYAML
```

### 4. Clone the ArduPilot Repository

Copy and paste the 4 lines below and paste it into WSL

```
git clone https://github.com/ArduPilot/ardupilot.git 
cd ardupilot
Tools/environment_install/install-prereqs-ubuntu.sh -y
. ~/.profile
```

### Test SITL via below:

```
cd ~/ardupilot/Tools/autotest
python3 sim_vehicle.py -v ArduCopter --console --map
```

### Close and open a new terminal before continuing


### 5. Install OSRF Packages

```
sudo sh -c 'echo "deb http://packages.osrfoundation.org/gazebo/ubuntu-stable `lsb_release -cs` main" > /etc/apt/sources.list.d/gazebo-stable.list'
wget http://packages.osrfoundation.org/gazebo.key -O - | sudo apt-key add -
sudo apt-get update
```


### 6. Install dependencies for Gazebo Harmonic

```
sudo apt update
sudo apt install libgz-sim8-dev rapidjson-dev
sudo apt install libopencv-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-bad gstreamer1.0-libav gstreamer1.0-gl
```


### 7. Make a workspace folder and get clone the repository

```
mkdir -p gz_ws/src && cd gz_ws/src
```

Then do 

```
git clone https://github.com/ArduPilot/ardupilot_gazebo
```

### 8. Build plugin

```
export GZ_VERSION=harmonic
cd ardupilot_gazebo
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=RelWithDebInfo
make -j4

export GZ_SIM_SYSTEM_PLUGIN_PATH=$HOME/gz_ws/src/ardupilot_gazebo/build:$GZ_SIM_SYSTEM_PLUGIN_PATH
export GZ_SIM_RESOURCE_PATH=$HOME/gz_ws/src/ardupilot_gazebo/models:$HOME/gz_ws/src/ardupilot_gazebo/worlds:$GZ_SIM_RESOURCE_PATH

echo 'export GZ_SIM_SYSTEM_PLUGIN_PATH=$HOME/gz_ws/src/ardupilot_gazebo/build:${GZ_SIM_SYSTEM_PLUGIN_PATH}' >> ~/.bashrc
echo 'export GZ_SIM_RESOURCE_PATH=$HOME/gz_ws/src/ardupilot_gazebo/models:$HOME/gz_ws/src/ardupilot_gazebo/worlds:${GZ_SIM_RESOURCE_PATH}' >> ~/.bashrc

```

### 9. Start running Gazebo Sim 

```
gz sim -v4 -r iris_runway.sdf
```

Open a new terminal

If new terminal is using PowerShell, type in "wsl"

```
wsl
```

Then copy and paste the sim_vehicle.py line into that new terminal

If new terminal is Ubuntu 22.04, just copy and paste below:

```
sim_vehicle.py -v ArduCopter -f gazebo-iris --model JSON --map --console
```




To resume drone simulation, open either WSL or Ubuntu 22.04.5

```
gz sim -v4 -r iris_runway.sdf
```


New Terminal (WSL or Ubuntu 22.04.5)

```
cd
sim_vehicle.py -v ArduCopter -f gazebo-iris --model JSON --map --console
```







# Install PX4 Gazebo Simulator (Not needed if using PIXHAWK6)

### Open New Ubuntu 22.04 instance

```
cd
mkdir PX4-Autopilot && cd PX4-Autopilot
git clone https://github.com/PX4/Firmware.git --recursive
```



### You may need to cut everything from the "Firmware" directory and paste it under the "PX4-Autopilot" directory you created earlier.

### If using Windows 11 and Ubuntu 22.04 via WSL, under the Windows file explorer:

1. Navigate to the Linux panel, which is located towards the bottom of the Navigation Panel

2. Click "Ubuntu-22.04"

3. Go to home >> *user_folder* >> PX4-Autopilot >> Firmware

4. Cut everything from the Firmware Directory and paste it into the PX4-Autopilot you made previously

5. Proceed below to build the PX4 Gazebo Simulator




### If you are using Ubuntu 22.04 running natively on the computer, using the Files app:

1. Go to home >> PX4-Autopilot >> Firmware

2. Cut everything from the Firmware Directory and paste it into the PX4-Autopilot you made previously

3. Proceed below to build the PX4 Gazebo Simulator






### Then proceed with the below to make the PX4 Gazebo simulator

```
./Tools/setup/ubuntu.sh --no-sim-tools --no-nutty
make px4_sitl gz_x500
```

### Install pytorch

```
pip3 install torch torchvision torchaudio
```


## To Rerun the simulation, simply just copy and paste the two lines below in an Ubuntu Terminal

```
cd PX4-Autopilot
make px4_sitl gz_x500
```
