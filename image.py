import os

import click
from colorama import Fore, Style
from prettytable import PrettyTable
from tqdm import tqdm

from util import generate_hash, list_disks, list_folders


# Function to image a disk (cross-platform)
def image_disk(disk, output, block_size):
    try:
        # Ensure the output directory exists
        output_dir = os.path.dirname(output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output, "wb") as img_file:
            # Raw disk access for physical disks (requires admin privileges)
            with open(disk, "rb") as src_disk:
                total_bytes = os.path.getsize(disk) if os.path.exists(disk) else None
                with tqdm(
                    total=total_bytes,
                    unit="B",
                    unit_scale=True,
                    desc="Creating Disk Image Progress",
                ) as progress_bar:
                    while True:
                        data = src_disk.read(block_size)
                        if not data:
                            break
                        img_file.write(data)
                        progress_bar.update(len(data))

        print(Fore.GREEN + "\nDisk imaging completed." + Style.RESET_ALL)
        return True

    except Exception as e:
        print(Fore.RED + f"Error during disk imaging: {str(e)}" + Style.RESET_ALL)
        return False


def image_folder(input_folder, output, block_size):
    try:
        # Ensure the output directory exists
        output_dir = os.path.dirname(output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output, "wb") as img_file:
            print(f"Creating folder image from {input_folder} to {output} ...")

            # Recursively add files from the folder to the image file
            for root, _, files in os.walk(input_folder):
                for file in tqdm(files, desc="Imaging folder files", unit="file"):
                    file_path = os.path.join(root, file)

                    with open(file_path, "rb") as src_file:
                        while True:
                            data = src_file.read(block_size)
                            if not data:
                                break
                            img_file.write(data)

        print(Fore.GREEN + "\nFolder imaging completed." + Style.RESET_ALL)
        return True

    except Exception as e:
        print(Fore.RED + f"Error during folder imaging: {str(e)}" + Style.RESET_ALL)
        return False


@click.command()
@click.option(
    "--output",
    required=True,
    help="Path to the output destination image file (.img or .iso)",
)
@click.option(
    "--block-size", default=4096, help="Block size in bytes (default is 4096)"
)
@click.option(
    "--hash", default="sha256", help="Hash algorithm to use (default is sha256)"
)
def create_image(output, block_size, hash):
    """Creates a bit-by-bit image of a folder or disk in .img or .iso format."""

    # Ask user if they want to image a folder or a disk
    choice = click.prompt(
        Fore.YELLOW + "Do you want to create an image of a (1) Folder or (2) Disk?",
        type=int,
    )

    if choice == 1:

        print(Fore.CYAN + "\nPlease enter the input directory:")
        input_directory = input(Fore.CYAN + "Directory: ")

        if not os.path.isdir(input_directory):
            print(Fore.RED + "Error: The directory does not exist.")
            return

        # List all folders in the selected directory
        folders = list_folders(input_directory)
        print("\n")
        for idx, folder in enumerate(folders):
            print(f"{idx}. {folder}")

        selected_folder = click.prompt("\nSelect a folder by index", type=int)

        if selected_folder >= len(folders) or selected_folder < 0:
            print(Fore.RED + "Invalid selection. Please try again." + Style.RESET_ALL)
            return

        input_folder = os.path.join(input_directory, folders[selected_folder])

        # Confirm the folder imaging operation
        confirmation = click.prompt(
            f"Are you sure you want to create an image of this folder as {output}? (y/n)",
            type=str,
        )

        if confirmation.lower() != "y":
            print(Fore.YELLOW + "Operation cancelled by user." + Style.RESET_ALL)
            return

        # Start imaging the folder
        success = image_folder(input_folder, output, block_size)

    elif choice == 2:
        disks = list_disks()
        print("\n")
        for idx, disk in enumerate(disks):
            print(f"{idx}. {disk}")

        selected_disk = click.prompt("\nSelect a disk by index", type=int)

        if selected_disk >= len(disks) or selected_disk < 0:
            print(Fore.RED + "Invalid selection. Please try again." + Style.RESET_ALL)
            return

        selected_disk = disks[selected_disk]

        # Confirm the disk imaging operation
        confirmation = click.prompt(
            f"Are you sure you want to create an image of this disk ({selected_disk}) as {output}? (y/n)",
            type=str,
        )

        if confirmation.lower() != "y":
            print(Fore.YELLOW + "Operation cancelled by user." + Style.RESET_ALL)
            return

        # Start imaging the disk
        success = image_disk(selected_disk, output, block_size)

    else:
        print(
            Fore.RED
            + "Invalid option. Please select 1 for Folder or 2 for Disk."
            + Style.RESET_ALL
        )
        return

    if success:
        hash_value = generate_hash(output, hash)
        print(
            f"{hash.upper()} hash of the image file: {Fore.CYAN}{hash_value}{Style.RESET_ALL}"
        )
