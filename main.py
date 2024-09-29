import hashlib

def create_disk_image(input_disk, output_image):
    block_size = 4096  # Block size for reading chunks of data
    
    # Open the source disk and destination file
    with open(input_disk, 'rb') as f_in, open(output_image, 'wb') as f_out:
        while True:
            # Read a block of data from the disk
            data = f_in.read(block_size)
            if not data:
                break
            # Write the block to the output file
            f_out.write(data)

def generate_hash(file_path, hash_algorithm='sha256'):
    hasher = hashlib.new(hash_algorithm)
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(4096)
            if not data:
                break
            hasher.update(data)
    return hasher.hexdigest()

input_disk = '/dev/sdX'  
output_image = 'disk_image.img'  

create_disk_image(input_disk, output_image)
print(f"Image created: {output_image}")

input_hash = generate_hash(input_disk)
output_hash = generate_hash(output_image)

print(f"Input Disk Hash: {input_hash}")
print(f"Output Image Hash: {output_hash}")
