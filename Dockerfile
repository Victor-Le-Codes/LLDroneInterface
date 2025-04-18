FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
    git python3 python3-pip python3-matplotlib \
    python3-wxgtk4.0 python3-lxml python3-scipy python3-opencv \
    ccache gawk wget gnupg software-properties-common \
    rapidjson-dev libopencv-dev libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-bad \
    gstreamer1.0-libav gstreamer1.0-gl screen && \
    pip3 install pexpect MAVProxy PyYAML

# Clone ArduPilot
RUN git clone https://github.com/ArduPilot/ardupilot.git && \
    cd ardupilot && \
    sed -i 's/if \[ "\$EUID" -eq 0 \ ]; then echo/#/' Tools/environment_install/install-prereqs-ubuntu.sh && \
    sed -i 's/exit 1/# exit 1/' Tools/environment_install/install-prereqs-ubuntu.sh && \
    sed -i 's/sudo //g' Tools/environment_install/install-prereqs-ubuntu.sh && \
    sed -i 's/usermod/# usermod/' Tools/environment_install/install-prereqs-ubuntu.sh && \
    Tools/environment_install/install-prereqs-ubuntu.sh -y

# Expose default MAVLink ports
EXPOSE 14550 14550

# Set working directory
WORKDIR /ardupilot/ArduCopter

# Default command to launch SITL
RUN cd /ardupilot && ./waf configure --board sitl && ./waf copter

CMD ["/ardupilot/build/sitl/bin/arducopter","--model","quad","-I0"]
