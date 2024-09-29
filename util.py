import hashlib
import os
import platform
import subprocess

import psutil
from colorama import Fore, Style
from prettytable import PrettyTable

current_platform = platform.system()


def list_disks():
    """List available disks on the system in a cross-platform way."""
    disks = []

    table = PrettyTable()
    table.field_names = ["Index", "Device", "Mountpoint", "File System Type", "Size"]

    # Windows-specific disk listing
    if current_platform == "Windows":
        partitions = psutil.disk_partitions(all=False)
        print(Fore.CYAN + "\nAvailable Logical Partitions (Windows):")

        for idx, partition in enumerate(partitions):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                size = f"{usage.total / (1024 ** 3):.2f} GB"  # Convert size to GB
            except PermissionError:
                size = "N/A"

            table.add_row(
                [idx, partition.device, partition.mountpoint, partition.fstype, size]
            )

        print(Fore.WHITE)
        print(table)

        # Now, list physical drives using WMIC
        physical_disks = []
        try:
            output = subprocess.check_output(
                ["wmic", "diskdrive", "get", "DeviceID,Model,Size"],
                universal_newlines=True,
            )
            print(Fore.CYAN + "\n--- PHYSICAL DISKS (Windows) ---" + Style.RESET_ALL)
            print(output.strip())

            for line in output.strip().splitlines()[1:]:
                device_info = line.split()
                if len(device_info) > 1:
                    device_id = device_info[0]
                    size = int(device_info[-1])
                    physical_disks.append(device_id)
                    disks.append(device_id)
        except subprocess.CalledProcessError as e:
            print(Fore.RED + f"Error listing physical disks: {e}" + Style.RESET_ALL)

    # Linux-specific disk listing using lsblk
    elif current_platform == "Linux":
        try:
            output = subprocess.check_output(
                ["lsblk", "-o", "NAME,SIZE,TYPE,MOUNTPOINT"], universal_newlines=True
            )
            print(Fore.CYAN + "\nAvailable Disks (Linux):")
            print(output)

            for line in output.strip().splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 4 and parts[2] == "disk":
                    disk = f"/dev/{parts[0]}"
                    disks.append(disk)
        except subprocess.CalledProcessError as e:
            print(Fore.RED + f"Error listing disks on Linux: {e}" + Style.RESET_ALL)

    # macOS-specific disk listing using diskutil
    elif current_platform == "Darwin":
        try:
            output = subprocess.check_output(
                ["diskutil", "list"], universal_newlines=True
            )
            print(Fore.CYAN + "\nAvailable Disks (macOS):")
            print(output)

            for line in output.strip().splitlines():
                if "/dev/disk" in line:
                    disk = line.split()[0]
                    disks.append(disk)
        except subprocess.CalledProcessError as e:
            print(Fore.RED + f"Error listing disks on macOS: {e}" + Style.RESET_ALL)

    return disks


def list_folders(directory=None):
    """List available folders in the current directory."""
    folders = []
    if not directory:
        folders = [f for f in os.listdir() if os.path.isdir(f)]
    folders = [
        f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))
    ]
    for idx, folder in enumerate(folders):
        print(Fore.WHITE + f"[{idx}] Folder: {folder}")
    return folders


def generate_hash(image_file, algorithm="sha256"):
    """Generate a cryptographic hash of the image file."""
    print(f"Calculating {algorithm.upper()} hash for image file {image_file}...")
    hasher = hashlib.new(algorithm)
    with open(image_file, "rb") as f:
        while chunk := f.read(4096):
            hasher.update(chunk)
    return hasher.hexdigest()


if __name__ == "__main__":
    list_disks()
