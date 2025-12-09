#!/bin/bash

# Physical AI & Humanoid Robotics - One-Click Setup Script
# This script installs Ubuntu packages, ROS 2 Humble, NVIDIA Isaac Sim, and Docusaurus
# Designed for Ubuntu 22.04 LTS

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_error "This script should not be run as root. Please run without sudo."
    exit 1
fi

# Check if running on Ubuntu 22.04
if ! grep -q "Ubuntu 22.04" /etc/os-release 2>/dev/null && ! grep -q "22.04" /etc/os-release 2>/dev/null; then
    log_error "This script is designed for Ubuntu 22.04 LTS only."
    log_error "Current OS: $(cat /etc/os-release | grep PRETTY_NAME)"
    exit 1
fi

log_info "Starting Physical AI & Humanoid Robotics environment setup..."

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install packages
install_packages() {
    log_info "Installing system packages..."
    sudo apt update
    sudo apt install -y curl wget gnupg lsb-release software-properties-common apt-transport-https
}

# Function to setup locale
setup_locale() {
    log_info "Setting up locale..."
    sudo locale-gen en_US.UTF-8
    export LANG=en_US.UTF-8
}

# Function to install ROS 2 Humble
install_ros2_humble() {
    log_info "Installing ROS 2 Humble Hawksbill..."

    # Add ROS 2 repository
    sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(source /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

    sudo apt update
    sudo apt install -y ros-humble-desktop
    sudo apt install -y python3-colcon-common-extensions python3-rosdep python3-rosinstall python3-rosinstall-generator python3-wstool build-essential

    # Initialize rosdep
    if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
        sudo rosdep init
    fi
    rosdep update

    # Add ROS 2 setup to bashrc if not already present
    if ! grep -q "source /opt/ros/humble/setup.bash" ~/.bashrc; then
        echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
    fi

    log_success "ROS 2 Humble installed successfully"
}

# Function to install Node.js and Docusaurus
install_nodejs_docusaurus() {
    log_info "Installing Node.js and Docusaurus dependencies..."

    # Install Node.js 18.x
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs

    # Verify installation
    node --version
    npm --version

    log_success "Node.js and npm installed successfully"
}

# Function to install NVIDIA drivers (if NVIDIA GPU detected)
install_nvidia_drivers() {
    log_info "Checking for NVIDIA GPU..."

    if lspci | grep -i nvidia > /dev/null; then
        log_info "NVIDIA GPU detected, installing drivers..."
        sudo apt install -y nvidia-driver-535 nvidia-utils-535
        log_success "NVIDIA drivers installed. A reboot may be required."
        log_warning "Please reboot your system after installation completes to load the new drivers."
    else
        log_info "No NVIDIA GPU detected, skipping driver installation."
    fi
}

# Function to install Isaac Sim prerequisites
install_isaac_sim_prerequisites() {
    log_info "Installing Isaac Sim prerequisites..."
    sudo apt install -y python3.10-venv python3-pip
    log_success "Isaac Sim prerequisites installed"
}

# Function to setup project directory
setup_project_directory() {
    log_info "Setting up project directory..."

    PROJECT_DIR="$HOME/physical-ai-humanoid-robotics"
    if [ ! -d "$PROJECT_DIR" ]; then
        mkdir -p "$PROJECT_DIR"
        cd "$PROJECT_DIR"

        # Create basic project structure if not already present
        if [ ! -f "package.json" ]; then
            cat > package.json << 'EOF'
{
  "name": "physical-ai-humanoid-robotics-book",
  "version": "0.0.0",
  "private": true,
  "scripts": {
    "docusaurus": "docusaurus",
    "start": "docusaurus start",
    "build": "docusaurus build",
    "swizzle": "docusaurus swizzle",
    "deploy": "docusaurus deploy",
    "clear": "docusaurus clear",
    "serve": "docusaurus serve",
    "write-translations": "docusaurus write-translations",
    "write-heading-ids": "docusaurus write-heading-ids"
  },
  "dependencies": {
    "@docusaurus/core": "3.1.0",
    "@docusaurus/plugin-content-docs": "^3.1.0",
    "@docusaurus/preset-classic": "3.1.0",
    "@mdx-js/react": "^3.0.0",
    "clsx": "^2.0.0",
    "prism-react-renderer": "^2.3.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  },
  "devDependencies": {
    "@docusaurus/module-type-aliases": "3.1.0",
    "@docusaurus/types": "3.1.0",
    "@docusaurus/tsconfig": "3.1.0",
    "@docusaurus/plugin-content-docs": "^3.1.0"
  },
  "browserslist": {
    "production": [
      ">0.5%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "engines": {
    "node": ">=18.0"
  }
}
EOF
        fi

        log_success "Project directory set up"
    else
        log_info "Project directory already exists"
    fi
}

# Function to install Docusaurus dependencies
install_docusaurus_dependencies() {
    PROJECT_DIR="$HOME/physical-ai-humanoid-robotics"
    cd "$PROJECT_DIR"

    log_info "Installing Docusaurus dependencies..."
    npm install
    log_success "Docusaurus dependencies installed"
}

# Function to verify installation
verify_installation() {
    log_info "Verifying installations..."

    # Verify ROS 2
    if command_exists ros2; then
        log_success "ROS 2 Humble is installed: $(ros2 --version)"
    else
        log_error "ROS 2 Humble installation failed"
        return 1
    fi

    # Verify Node.js
    if command_exists node; then
        log_success "Node.js is installed: $(node --version)"
    else
        log_error "Node.js installation failed"
        return 1
    fi

    # Verify npm
    if command_exists npm; then
        log_success "npm is installed: $(npm --version)"
    else
        log_error "npm installation failed"
        return 1
    fi

    # Check if project dependencies are installed
    PROJECT_DIR="$HOME/physical-ai-humanoid-robotics"
    if [ -d "$PROJECT_DIR/node_modules" ]; then
        log_success "Docusaurus dependencies are installed"
    else
        log_error "Docusaurus dependencies installation failed"
        return 1
    fi

    log_success "All installations verified successfully!"
}

# Function to display completion message
display_completion_message() {
    echo
    log_success "🎉 Physical AI & Humanoid Robotics environment setup completed successfully! 🎉"
    echo
    log_info "Next steps:"
    echo "1. If you installed NVIDIA drivers, please reboot your system:"
    echo "   sudo reboot"
    echo
    echo "2. After reboot (if applicable), navigate to your project directory:"
    echo "   cd ~/physical-ai-humanoid-robotics"
    echo
    echo "3. Start the Docusaurus development server:"
    echo "   npm start"
    echo
    echo "4. To work with ROS 2, either open a new terminal or source the environment:"
    echo "   source /opt/ros/humble/setup.bash"
    echo
    echo "5. The development environment is now ready for the Physical AI course!"
    echo
    log_info "For Isaac Sim installation, please follow the detailed instructions in the course materials after the system reboot."
    echo
}

# Main installation process
main() {
    log_info "Starting the Physical AI & Humanoid Robotics one-click setup..."
    log_info "This process may take 30-60 minutes depending on your system and internet connection."
    log_info "Please be patient and do not interrupt the process."
    echo

    install_packages
    setup_locale
    install_ros2_humble
    install_nodejs_docusaurus
    install_nvidia_drivers
    install_isaac_sim_prerequisites
    setup_project_directory
    install_docusaurus_dependencies
    verify_installation
    display_completion_message

    log_success "Setup script completed! Please follow the instructions above to complete the process."
}

# Run main function
main "$@"