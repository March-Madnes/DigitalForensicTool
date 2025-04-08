#!/bin/bash

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root (use sudo)."
    exit 1
fi

# Function to display available storage devices
list_devices() {
    echo "Available storage devices:"
    echo "-------------------------"
    lsblk -d -o NAME,SIZE,MODEL,TYPE | grep -v loop | grep -E 'disk|part'
    echo ""
}

# Function to validate device selection
validate_device() {
    local device=$1
    if [ ! -b "/dev/$device" ]; then
        echo "Error: /dev/$device is not a valid block device."
        return 1
    fi
    return 0
}

# Function to check available space at destination
check_space() {
    local source_device=$1
    local dest_path=$2
    
    # Get device size in bytes
    local device_size=$(blockdev --getsize64 "/dev/$source_device")
    
    # Get available space in destination directory
    local dest_dir=$(dirname "$dest_path")
    local avail_space=$(df -B1 "$dest_dir" | awk 'NR==2 {print $4}')
    
    if [ "$avail_space" -lt "$device_size" ]; then
        echo "Warning: Not enough space available at destination."
        echo "Device size: $(numfmt --to=iec-i --suffix=B $device_size)"
        echo "Available space: $(numfmt --to=iec-i --suffix=B $avail_space)"
        echo ""
        read -p "Do you want to continue anyway? (y/N): " confirm
        if [[ "$confirm" != [yY] ]]; then
            return 1
        fi
    fi
    return 0
}

# Main menu
clear
echo "====================================="
echo "      DISK CLONING UTILITY"
echo "  Bit-by-bit Storage Device Imager"
echo "====================================="
echo ""

# List available devices
list_devices

# Ask user to select a source device
read -p "Enter the device name to clone (e.g., sdb, sdc): " source_device

# Validate source device
if ! validate_device "$source_device"; then
    exit 1
fi

# Get device size for information
device_size=$(blockdev --getsize64 "/dev/$source_device")
human_size=$(numfmt --to=iec-i --suffix=B $device_size)

echo ""
echo "Selected device: /dev/$source_device ($human_size)"
echo ""

# Ask for confirmation
read -p "Are you sure you want to clone /dev/$source_device? (y/N): " confirm
if [[ "$confirm" != [yY] ]]; then
    echo "Operation cancelled."
    exit 0
fi

# Ask for destination path
echo ""
read -p "Enter the destination path for the image (e.g., /home/user/backup/device_clone.img): " dest_path

# Check destination space
if ! check_space "$source_device" "$dest_path"; then
    echo "Operation cancelled due to insufficient space."
    exit 1
fi

# Set block size
echo ""
echo "Select block size (larger is faster but uses more memory):"
echo "1) 1M (safe, works on all systems)"
echo "2) 4M (recommended for modern systems)"
echo "3) 8M (faster, requires more memory)"
read -p "Enter your choice [3]: " bs_choice

case $bs_choice in
    1) bs="1M" ;;
    3) bs="8M" ;;
    *) bs="4M" ;; # Default or option 2
esac

# Start the clone operation
echo ""
echo "Starting bit-by-bit copy operation..."
echo "Source: /dev/$source_device"
echo "Destination: $dest_path"
echo "Block size: $bs"
echo ""
echo "This may take a while depending on the device size."
echo "DO NOT disconnect the device during this operation!"
echo ""

dd if="/dev/$source_device" of="$dest_path" bs=$bs status=progress conv=noerror,sync

# Check if operation completed successfully
if [ $? -eq 0 ]; then
    echo ""
    echo "Disk cloning completed successfully!"
    echo "Image saved to: $dest_path"
    echo "Image size: $(numfmt --to=iec-i --suffix=B $(stat -c %s "$dest_path"))"
    echo ""
    
    # Calculate MD5 hash for verification (optional)
    read -p "Calculate MD5 checksum for verification? (y/N): " calc_md5
    if [[ "$calc_md5" == [yY] ]]; then
        echo "Calculating MD5 checksum (this may take a while)..."
        md5sum "/dev/$source_device" > "$dest_path.md5"
        md5sum "$dest_path" >> "$dest_path.md5"
        echo "MD5 checksums saved to: $dest_path.md5"
    fi
else
    echo ""
    echo "Error: Disk cloning operation failed."
fi

echo ""
echo "Thank you for using the Disk Cloning Utility."