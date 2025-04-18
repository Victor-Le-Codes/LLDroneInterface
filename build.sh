#!/bin/bash

set -e  # Stop script on error

echo "🚀 Starting LLDroneInterface Setup..."

# Detect platform
OS_TYPE=$(uname)
PYTHON_CMD="python3"

if [[ "$OS_TYPE" == "Darwin" || "$OS_TYPE" == "Linux" ]]; then
    echo "🧠 Detected OS: $OS_TYPE"
else
    echo "🪟 Detected Windows or WSL/Git Bash"
    PYTHON_CMD="python"
fi

# Check Docker
if ! command -v docker &>/dev/null; then
    echo "❌ Docker is not installed. Please install Docker: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Build and run SITL container
echo "🐳 Building and starting SITL Docker container..."
docker build -t ll-sitl .
docker rm -f sitl-sim >/dev/null 2>&1 || true
# publish TCP 14550
docker run -d -p 14550:5760 --name sitl-sim ll-sitl
echo "⌛ Waiting for SITL to initialize..."
sleep 10

# Create and activate virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Check and install PortAudio if on macOS, Linux, or Windows (PyAudio dependency)
if [[ "$OS_TYPE" == "Darwin" ]]; then
    echo "🔧 Installing portaudio via Homebrew (macOS)..."
    if ! command -v brew &>/dev/null; then
        echo "❌ Homebrew is not installed. Please install Homebrew first: https://brew.sh/"
        exit 1
    fi
    brew install portaudio
elif [[ "$OS_TYPE" == "Linux" ]]; then
    echo "🔧 Installing portaudio via apt (Linux)..."
    sudo apt update
    sudo apt install -y portaudio19-dev
elif [[ "$OS_TYPE" == *"MINGW"* || "$OS_TYPE" == *"MSYS"* || "$OS_TYPE" == *"CYGWIN"* ]]; then
    echo "⚠️ On native Windows, install PyAudio manually with a .whl file if needed:"
    echo "   https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio"
fi

# Install dependencies
echo "📥 Installing required Python libraries..."
pip install -r requirements.txt

# Install dependencies (customize if you have requirements.txt)
echo "📥 Installing required Python libraries..."
pip install -r requirements.txt

# Wait until SITL port is available
echo "⏳ Waiting for SITL (port 14550) to become available..."
for i in {1..30}; do
  if nc -z localhost 14550; then
    echo "✅ SITL is ready!"
    break
  fi
  sleep 1
done

# Run the drone control script
echo "🛫 Running drone voice controller..."
$PYTHON_CMD src/VC_test_user_controlled_drone_9.py
