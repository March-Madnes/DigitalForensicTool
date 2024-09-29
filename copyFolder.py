import os
import hashlib
import click
from tqdm import tqdm
from colorama import Fore, Style

def list_folders(directory=None):
    """List available folders in the current directory."""
    folders = []
    if not directory:
        folders = [f for f in os.listdir() if os.path.isdir(f)]
    folders = [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]
    for idx, folder in enumerate(folders):
        print(Fore.WHITE + f"[{idx}] Folder: {folder}")
    return folders

@click.command()
@click.option('--output', required=True, help='Path to the output destination image file (.img or .iso)')
@click.option('--block-size', default=4096, help='Block size in bytes (default is 4096)')
@click.option('--hash', default='sha256', help='Hash algorithm to use (default is sha256)')
def create_image(output, block_size, hash):
    """Creates a bit-by-bit image of a folder in .img or .iso format."""
    
    # Check if the output path is a directory instead of a file
    if os.path.isdir(output):
        print(Fore.RED + f"Error: {output} is a directory, not a file. Please specify a valid file path." + Style.RESET_ALL)
        return
    
    print(Fore.YELLOW + "Please enter the input directory:")
    input_directory = input(Fore.CYAN + "Directory: ")
    
    # Check if the directory exists
    if not os.path.isdir(input_directory):
        print(Fore.RED + "Error: The directory does not exist.")
        return
    
    # List all folders in the current directory
    folders = list_folders(input_directory)

    # Ask the user to select a folder by index
    selected_folder = click.prompt("Select a folder by index", type=int)
    
    if selected_folder >= len(folders) or selected_folder < 0:
        print(Fore.RED + "Invalid selection. Please try again." + Style.RESET_ALL)
        return
    
    input_folder = folders[selected_folder]
    
    # Display confirmation
    print(Fore.GREEN + f"\nSelected folder: {input_folder}" + Style.RESET_ALL)
    confirmation = click.prompt(f"Are you sure you want to create an image of this folder as {output}? (y/n)", type=str)
    
    if confirmation.lower() != 'y':
        print(Fore.YELLOW + "Operation cancelled by user." + Style.RESET_ALL)
        return

    total_bytes = calculate_total_size(input_folder)
    
    print(f"\nStarting folder imaging from {input_folder} to {output}...\n")
    copied_bytes = 0

    try:
        # Ensure the output directory exists
        output_dir = os.path.dirname(output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output, 'wb') as img_file:
            with tqdm(total=total_bytes, unit='B', unit_scale=True, desc="Creating Image Progress") as progress_bar:
                for root, dirs, files in os.walk(input_folder):
                    for file in files:
                        src_file = os.path.join(root, file)
                        copied_bytes += write_to_image(src_file, img_file, block_size, progress_bar)
                    
        print(Fore.GREEN + "\nFolder imaging completed." + Style.RESET_ALL)

        hash_value = generate_hash(output, hash)
        print(f"{hash.upper()} hash of the image file: {Fore.CYAN}{hash_value}{Style.RESET_ALL}")

    except Exception as e:
        print(Fore.RED + f"Error during folder imaging: {str(e)}" + Style.RESET_ALL)

def write_to_image(src, img_file, block_size, progress_bar):
    """Copy a file byte-by-byte to the image file."""
    bytes_written = 0
    with open(src, 'rb') as fsrc:
        while True:
            data = fsrc.read(block_size)
            if not data:
                break
            img_file.write(data)
            bytes_written += len(data)
            progress_bar.update(len(data))
    return bytes_written

def calculate_total_size(folder):
    """Calculate total size of all files in a folder."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def generate_hash(image_file, algorithm='sha256'):
    """Generate a cryptographic hash of the image file."""
    print(f"Calculating {algorithm.upper()} hash for image file {image_file}...")
    hasher = hashlib.new(algorithm)
    with open(image_file, 'rb') as f:
        while chunk := f.read(4096):
            hasher.update(chunk)
    return hasher.hexdigest()

if __name__ == '__main__':
    create_image()
