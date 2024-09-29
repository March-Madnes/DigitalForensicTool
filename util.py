import psutil

def list_disks():
    """List available disks on the system."""
    print("Available Disks:")
    partitions = psutil.disk_partitions(all=False)
    for partition in partitions:
        print(f"Device: {partition.device}, Mountpoint: {partition.mountpoint}, File System Type: {partition.fstype}")

if __name__ == '__main__':
    list_disks()
