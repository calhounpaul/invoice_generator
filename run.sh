#!/bin/bash

FLAGFILE_INSTALL=".completed_installation"
MINICONDA_PATH="$HOME/miniconda3"

# Function to check if conda is available
check_conda() {
    if command -v conda &> /dev/null; then
        return 0
    elif [ -f "$MINICONDA_PATH/bin/conda" ]; then
        # Conda exists in home directory but not in PATH
        export PATH="$MINICONDA_PATH/bin:$PATH"
        return 0
    else
        return 1
    fi
}

# Install Miniconda if not present
if ! check_conda; then
    echo "Conda not found. Installing Miniconda..."

    # Download Miniconda installer
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda_installer.sh

    # Run installer in batch mode (silent, non-interactive)
    bash miniconda_installer.sh -b -p "$MINICONDA_PATH"

    # Clean up installer
    rm miniconda_installer.sh

    # Initialize conda for bash
    "$MINICONDA_PATH/bin/conda" init bash

    # Add conda to current PATH
    export PATH="$MINICONDA_PATH/bin:$PATH"

    # Source bashrc to activate conda in current session
    if [ -f "$HOME/.bashrc" ]; then
        source "$HOME/.bashrc"
    fi

    echo "Miniconda installed successfully at $MINICONDA_PATH"
fi

# Verify conda is now available
if ! command -v conda &> /dev/null; then
    echo "Error: Conda installation failed or not in PATH"
    exit 1
fi

# Create conda environment if it doesn't exist
if ! conda env list | grep -q "^invoice_generator "; then
    echo "Creating invoice_generator conda environment..."
    conda create -n invoice_generator python=3.11 -y
fi

# Install/update dependencies if needed
if [ ! -f $FLAGFILE_INSTALL ]; then
    echo "Installing Python packages..."
    conda run -n invoice_generator python -m pip install --upgrade pip
    conda run -n invoice_generator python -m pip install -U -r requirements.txt
    touch $FLAGFILE_INSTALL
fi

# Check and copy example configuration files if needed
if [ ! -f "company_config.json" ]; then
    if [ -f "example.company_config.json" ]; then
        echo "company_config.json not found. Copying from example.company_config.json..."
        cp example.company_config.json company_config.json
        echo "Please edit company_config.json with your actual company information."
    else
        echo "Warning: company_config.json not found and example.company_config.json does not exist."
    fi
fi

if [ ! -f "invoice_data.json" ]; then
    if [ -f "example.invoice_data.json" ]; then
        echo "invoice_data.json not found. Copying from example.invoice_data.json..."
        cp example.invoice_data.json invoice_data.json
        echo "Please edit invoice_data.json with your actual invoice data."
    else
        echo "Warning: invoice_data.json not found and example.invoice_data.json does not exist."
    fi
fi

# Run the invoice generator
conda run -n invoice_generator python ./invoice_generator.py