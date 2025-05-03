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

Windows 11 with WSL and Ubuntu 22.04.5 LTS: Below is the updated PIP command with all of the additional libraries we installed:

```
pip install accelerate, aiohappyeyeballs, aiohttp, aiosignal, annotated-types, anyio, attrs, audioop-lts, bitsandbytes, catkin-pkg, certifi, charset-normalizer, click, colorama, coloredlogs, contourpy, ctransformers, cycler, datasets, dill, docutils, dronekit, empy, filelock, flatbuffers, fonttools, frozenlist, fsspec, future, gTTS, h11, httpcore, httpx, huggingface-hub, humanfriendly, idna, iso8601, Jinja2, kiwisolver, lark-parser, lxml, MarkupSafe, matplotlib, MAVProxy, monotonic, mpmath, multidict, multiprocess, networkx, numpy, onnxruntime, opencv-python, packaging, pandas, peft, pexpect, pillow, pip, propcache, protobuf, psutil, ptyprocess, py-cpuinfo, pyarrow, PyAudio, pyception, pydantic, pydantic_core, pydot, pygame, pymavlink, pynmeagps, pyparsing, PyQt5, PyQt5-Qt5, PyQt5_sip, pyreadline3, pyserial, python-dateutil, pytz, PyYAML, regex, requests, safetensors, scipy, serial, setuptools, six, sniffio, SpeechRecognition, standard-aifc, standard-chunk, sty, sympy, tello, tokenizers, torch, tqdm, transformers, typing_extensions, tzdata, urllib3, wheel, wxtools, xxhash, yarl
```
Ubuntu 22.04.5 LTS as the main operating system: Below is the updated PIP command with all of the additional libraries we installed

```
pip install \
absl-py==2.2.2 \
accelerate==1.6.0 \
appdirs==1.4.4 \
argcomplete==3.6.2 \
attrs==25.3.0 \
Babel==2.8.0 \
bcrypt==3.2.0 \
beautifulsoup4==4.10.0 \
beniget==0.4.1 \
bitsandbytes==0.45.5 \
bitsandbytes-cuda110==0.26.0.post2 \
blinker==1.4 \
Brotli==1.0.9 \
Cerberus==1.3.7 \
certifi==2020.6.20 \
chardet==4.0.0 \
charset-normalizer==3.4.1 \
click==8.0.3 \
colorama==0.4.4 \
coverage==7.8.0 \
cryptography==3.4.8 \
cycler==0.11.0 \
decorator==4.4.2 \
defer==1.0.6 \
distro==1.7.0 \
docopt==0.6.2 \
dronecan==1.0.26 \
dronekit==2.9.2 \
empy==3.3.4 \
fasteners==0.14.1 \
filelock==3.18.0 \
flake8==7.2.0 \
fonttools==4.29.1 \
fs==2.4.12 \
fsspec==2025.3.2 \
future==1.0.0 \
gast==0.5.2 \
gcovr==5.0 \
geocoder==1.38.1 \
grpcio==1.71.0 \
gTTS==2.5.4 \
h11==0.16.0 \
html5lib==1.1 \
httplib2==0.20.2 \
huggingface-hub==0.30.2 \
idna==3.3 \
importlib-metadata==4.6.4 \
importlib_resources==6.5.2 \
intelhex==2.3.0 \
jeepney==0.7.1 \
Jinja2==3.0.3 \
Js2Py==0.74 \
jsonschema==4.23.0 \
jsonschema-specifications==2025.4.1 \
junitparser==3.2.0 \
kconfiglib==14.1.0 \
keyring==23.5.0 \
kiwisolver==1.3.2 \
lazr.restfulclient==0.14.4 \
lazr.uri==1.0.6 \
lockfile==0.12.2 \
louis==3.20.0 \
lxml==5.4.0 \
macaroonbakery==1.3.1 \
Mako==1.1.3 \
Markdown==3.8 \
MarkupSafe==3.0.2 \
matplotlib==3.5.1 \
MAVProxy==1.8.71 \
mavsdk==3.0.1 \
mccabe==0.7.0 \
monotonic==1.6 \
more-itertools==8.10.0 \
mpmath==1.3.0 \
netifaces==0.11.0 \
networkx==3.4.2 \
numpy==1.23.5 \
nunavut==2.3.1 \
nvidia-cublas-cu12==12.6.4.1 \
nvidia-cuda-cupti-cu12==12.6.80 \
nvidia-cuda-nvrtc-cu12==12.6.77 \
nvidia-cuda-runtime-cu12==12.6.77 \
nvidia-cudnn-cu12==9.5.1.17 \
nvidia-cufft-cu12==11.3.0.4 \
nvidia-cufile-cu12==1.11.1.6 \
nvidia-curand-cu12==10.3.7.77 \
nvidia-cusolver-cu12==11.7.1.2 \
nvidia-cusparse-cu12==12.5.4.2 \
nvidia-cusparselt-cu12==0.6.3 \
nvidia-nccl-cu12==2.26.2 \
nvidia-nvjitlink-cu12==12.6.85 \
nvidia-nvtx-cu12==12.6.77 \
oauthlib==3.2.0 \
olefile==0.46 \
packaging==25.0 \
pandas==2.2.3 \
paramiko==2.9.3 \
peft==0.15.2 \
pexpect==4.8.0 \
Pillow==9.0.1 \
pipwin==0.5.2 \
pkgconfig==1.5.5 \
ply==3.11 \
protobuf==6.30.2 \
psutil==5.9.0 \
ptyprocess==0.7.0 \
PyAudio==0.2.14 \
pybind11==2.9.1 \
pycairo==1.20.1 \
pycodestyle==2.13.0 \
pycryptodome==3.22.0 \
pycups==2.0.1 \
pydsdl==1.22.2 \
pyflakes==3.3.2 \
pygame==2.6.1 \
Pygments==2.11.2 \
PyGObject==3.42.1 \
pyjsparser==2.7.1 \
PyJWT==2.3.0 \
pymacaroons==0.13.0 \
pymavlink==2.4.43 \
PyNaCl==1.5.0 \
pynmeagps==1.0.49 \
pyparsing==2.4.7 \
PyPrind==2.11.3 \
pyRFC3339==1.1 \
pyros-genmsg==0.5.8 \
pyserial==3.5 \
pySmartDL==1.3.4 \
python-dateutil==2.9.0.post0 \
pythran==0.10.0 \
pytz==2022.1 \
pyulog==1.2.0 \
pyxdg==0.27 \
PyYAML==5.4.1 \
ratelim==0.1.6 \
referencing==0.36.2 \
regex==2024.11.6 \
reportlab==3.6.8 \
requests==2.32.3 \
rpds-py==0.24.0 \
safetensors==0.5.3 \
scipy==1.8.0 \
SecretStorage==3.3.1 \
setuptools==79.0.1 \
six==1.16.0 \
soupsieve==2.3.1 \
SpeechRecognition==3.14.2 \
sympy==1.13.3 \
tabulate==0.9.0 \
tensorboard==2.19.0 \
tensorboard-data-server==0.7.2 \
tokenizers==0.21.1 \
toml==0.10.2 \
torch==2.7.0 \
torchaudio==2.7.0 \
torchvision==0.22.0 \
tqdm==4.67.1 \
transformers==4.51.3 \
triton==3.3.0 \
typing_extensions==4.13.2 \
tzdata==2025.2 \
tzlocal==5.3.1 \
ufoLib2==0.13.1 \
unicodedata2==14.0.0 \
urllib3==1.26.5 \
wadllib==1.3.6 \
webencodings==0.5.1 \
Werkzeug==3.1.3 \
wheel==0.45.1 \
wsproto==1.2.0 \
wxPython==4.0.7 \
xdg==5 \
zipp==1.0.0
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


Copy and paste this command into Ubuntu Terminal:

```
cd
git clone https://github.com/PX4/PX4-Autopilot.git --recursive

```




Then copy and paste this command into Ubuntu Terminal:

```
cd
cd PX4-Autopilot
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


### Having issues installing PyAudio?
# Copy and paste the below line into an Ubuntu terminal

```
sudo apt-get install libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0
sudo apt-get install ffmpeg libav-tools
sudo pip install pyaudio
```

### Having issues with Transformers?

# Copy and paste this into VS Code:

```
pip install numpy==1.23.5
pip install --upgrade transformers
```



### Login into Hugging Face to use the Meta-Llama-3-1B-Instruct Model

# Copy and paste the following info into an Ubuntu Terminal:

```
huggingface-cli login
```

After that, put in your Hugging Face Token
