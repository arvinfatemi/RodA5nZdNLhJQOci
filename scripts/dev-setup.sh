#!/bin/bash

# BTC Trading Bot - Development Environment Setup Script
# This script automates the setup of a development environment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}${BOLD}============================================${NC}"
    echo -e "${BLUE}${BOLD}    BTC Trading Bot - Dev Environment Setup${NC}"
    echo -e "${BLUE}${BOLD}============================================${NC}"
    echo
}

print_section() {
    echo -e "${BOLD}$1${NC}"
    echo "----------------------------------------"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Check Python version
check_python() {
    print_section "Checking Python Environment"

    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        print_error "Python not found. Please install Python 3.10 or higher."
        exit 1
    fi

    # Check Python version
    PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    REQUIRED_VERSION="3.10"

    if (( $(echo "$PYTHON_VERSION >= $REQUIRED_VERSION" | bc -l) )); then
        print_success "Python $PYTHON_VERSION (✓ >= $REQUIRED_VERSION)"
    else
        print_error "Python $PYTHON_VERSION (✗ requires >= $REQUIRED_VERSION)"
        exit 1
    fi
}

# Setup virtual environment
setup_venv() {
    print_section "Setting up Virtual Environment"

    if [[ -d ".venv" ]]; then
        print_info "Virtual environment already exists"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf .venv
            print_info "Removed existing virtual environment"
        else
            print_success "Using existing virtual environment"
            return 0
        fi
    fi

    # Create virtual environment
    print_info "Creating virtual environment..."
    $PYTHON_CMD -m venv .venv

    # Determine activation script based on OS
    OS=$(detect_os)
    if [[ "$OS" == "windows" ]]; then
        ACTIVATE_SCRIPT=".venv/Scripts/activate"
        PIP_CMD=".venv/Scripts/pip"
        PYTHON_VENV_CMD=".venv/Scripts/python"
    else
        ACTIVATE_SCRIPT=".venv/bin/activate"
        PIP_CMD=".venv/bin/pip"
        PYTHON_VENV_CMD=".venv/bin/python"
    fi

    if [[ -f "$ACTIVATE_SCRIPT" ]]; then
        print_success "Virtual environment created successfully"
    else
        print_error "Failed to create virtual environment"
        exit 1
    fi

    # Upgrade pip
    print_info "Upgrading pip..."
    $PYTHON_VENV_CMD -m pip install --upgrade pip

    print_success "Virtual environment setup complete"
}

# Install dependencies
install_dependencies() {
    print_section "Installing Dependencies"

    # Install production dependencies
    if [[ -f "requirements.txt" ]]; then
        print_info "Installing production dependencies..."
        $PIP_CMD install -r requirements.txt
        print_success "Production dependencies installed"
    else
        print_warning "requirements.txt not found"
    fi

    # Install development dependencies
    if [[ -f "requirements-dev.txt" ]]; then
        print_info "Installing development dependencies..."
        $PIP_CMD install -r requirements-dev.txt
        print_success "Development dependencies installed"
    else
        print_warning "requirements-dev.txt not found"
    fi
}

# Setup data directories
setup_directories() {
    print_section "Setting up Data Directories"

    directories=(
        "data"
        "data/logs"
        "data/state"
        "data/history"
        "data/cache"
        "data/backups"
    )

    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            print_success "Created directory: $dir"
        else
            print_info "Directory already exists: $dir"
        fi
    done
}

# Setup environment file
setup_environment() {
    print_section "Setting up Environment Configuration"

    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            print_success "Created .env from .env.example"
            print_warning "Please edit .env file with your configuration"
        else
            print_error ".env.example not found"
            return 1
        fi
    else
        print_info ".env file already exists"
    fi
}

# Setup pre-commit hooks
setup_pre_commit() {
    print_section "Setting up Pre-commit Hooks"

    if command_exists pre-commit; then
        if [[ -f ".pre-commit-config.yaml" ]]; then
            print_info "Installing pre-commit hooks..."
            source $ACTIVATE_SCRIPT
            pre-commit install
            print_success "Pre-commit hooks installed"
        else
            print_warning ".pre-commit-config.yaml not found, skipping pre-commit setup"
        fi
    else
        print_info "Installing pre-commit..."
        $PIP_CMD install pre-commit

        # Create basic pre-commit config if it doesn't exist
        if [[ ! -f ".pre-commit-config.yaml" ]]; then
            cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
EOF
            print_success "Created .pre-commit-config.yaml"
        fi

        source $ACTIVATE_SCRIPT
        pre-commit install
        print_success "Pre-commit hooks installed"
    fi
}

# Run validation
run_validation() {
    print_section "Running Setup Validation"

    if [[ -f "scripts/setup.py" ]]; then
        print_info "Running setup validation..."
        source $ACTIVATE_SCRIPT
        $PYTHON_VENV_CMD scripts/setup.py
    else
        print_warning "Setup validation script not found"
    fi
}

# Test installation
test_installation() {
    print_section "Testing Installation"

    print_info "Testing import of main modules..."
    source $ACTIVATE_SCRIPT

    # Test basic imports
    if $PYTHON_VENV_CMD -c "import fastapi, uvicorn, pydantic_settings; print('✓ Core dependencies imported successfully')"; then
        print_success "Core dependencies working"
    else
        print_error "Failed to import core dependencies"
        return 1
    fi

    # Test app import
    if $PYTHON_VENV_CMD -c "from app.config import Settings; print('✓ App configuration loaded')"; then
        print_success "Application imports working"
    else
        print_error "Failed to import application modules"
        return 1
    fi
}

# Print usage instructions
print_usage() {
    print_section "Development Environment Ready!"

    echo -e "${GREEN}Your development environment has been set up successfully!${NC}"
    echo
    echo -e "${BOLD}To activate the virtual environment:${NC}"

    OS=$(detect_os)
    if [[ "$OS" == "windows" ]]; then
        echo -e "  ${BLUE}.venv\\Scripts\\activate${NC}"
    else
        echo -e "  ${BLUE}source .venv/bin/activate${NC}"
    fi

    echo
    echo -e "${BOLD}Next steps:${NC}"
    echo -e "1. Edit the ${BLUE}.env${NC} file with your configuration"
    echo -e "2. Add your Google service account credentials"
    echo -e "3. Test the setup: ${BLUE}python scripts/setup.py${NC}"
    echo -e "4. Start development server: ${BLUE}python -m app.main${NC}"
    echo -e "5. Visit: ${BLUE}http://localhost:8000${NC}"
    echo
    echo -e "${BOLD}Development commands:${NC}"
    echo -e "  ${BLUE}python -m app.main${NC}           # Start the application"
    echo -e "  ${BLUE}python scripts/run_app.py${NC}    # Legacy menu system"
    echo -e "  ${BLUE}docker-compose up -d${NC}        # Run with Docker"
    echo -e "  ${BLUE}pytest${NC}                      # Run tests"
    echo -e "  ${BLUE}black app/${NC}                  # Format code"
    echo -e "  ${BLUE}mypy app/${NC}                   # Type checking"
    echo
    echo -e "${BOLD}Documentation:${NC}"
    echo -e "  ${BLUE}docs/SETUP.md${NC}              # Detailed setup guide"
    echo -e "  ${BLUE}docs/CONTRIBUTING.md${NC}       # Development guide"
    echo -e "  ${BLUE}docs/ARCHITECTURE.md${NC}       # Architecture overview"
}

# Main function
main() {
    print_header

    # Check if we're in the right directory
    if [[ ! -f "app/main.py" ]]; then
        print_error "This script must be run from the project root directory"
        print_info "Make sure you're in the btc-trading-bot directory"
        exit 1
    fi

    # Run setup steps
    check_python
    setup_venv
    install_dependencies
    setup_directories
    setup_environment
    setup_pre_commit
    test_installation
    run_validation
    print_usage

    print_success "Development environment setup complete!"
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi