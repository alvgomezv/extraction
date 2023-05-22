
import os
import argparse
import datetime
import time
import ctypes
import pytsk3

#Open the usb as raw bytes
#with open(r"\\.\\D:", "rb") as f:
#    image = f.read(512)

def create_image_from_disk(folder_path):
    #drive_type = ctypes.windll.kernel32.GetDriveTypeW(folder_path)
    #if drive_type == 3 or drive_type == 2:  # 3 fixed disk drive / 2 removable storage device
    #   print("Path is a disk")
    
    destination_image = r'C:\Users\Usuario\image2.dd'
    img_info = pytsk3.Img_Info(folder_path)
    # Open the output file in write-binary mode
    with open(destination_image, "wb") as output_file:
        # Read and write the contents of the disk to the output file
        offset = 0
        chunk_size = 1024 * 1024  # 1MB chunk size (adjust as needed)
        while offset < img_info.get_size():
            data = img_info.read(offset, chunk_size)
            output_file.write(data)
            offset += chunk_size

    print(f"Image {destination_image} created successfully")



def traverse_directory(directory):
    # Iterate over each entry in the directory
    for entry in directory:
        if entry.info.name.name.decode() == "." or entry.info.name.name.decode() == "..":
            continue
        # Check if the entry is a directory
        if entry.info.name.type == pytsk3.TSK_FS_NAME_TYPE_DIR:
            sub_directory = entry.as_directory()
            traverse_directory(sub_directory)  # Recursively traverse the sub-directory
        # Check if the entry is a file
        elif entry.info.name.type == pytsk3.TSK_FS_NAME_TYPE_REG and entry.info.meta.type in [pytsk3.TSK_FS_META_TYPE_REG, pytsk3.TSK_FS_META_TYPE_DIR]:
            # Display recovered file information
            print(f"Recovered File: {entry.info.name.name.decode()}")


def search_deleted_files(image):
    img_info = pytsk3.Img_Info(image)
    fs_info = pytsk3.FS_Info(img_info)
    root_dir = fs_info.open_dir(path="/")
    traverse_directory(root_dir)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Tool for recovering recently deleted files on NTFS")
    parser.add_argument("-d", "--disk", action="store", help="Path to the disk")
    parser.add_argument("-i", "--image", action="store", help="Path to the image file")
    parser.add_argument("-t", "--timelaps", action="store", help="Time range in hours, default 24h" )
    arg = parser.parse_args()
    date_format = "%d-%m-%Y"
    try:
        if arg.timelaps is not None:
            arg.timelaps = datetime.datetime.strptime(arg.timelaps, date_format).timestamp()
        else:
            arg.timelaps = time.time() - (24 * 60 * 60)
        return arg
    except Exception as e:
        print(f"Error: {e}")
        exit()

if __name__ == "__main__":
    arg = parse_arguments()
    if arg.image and arg.disk:
        print("Provide either a disk or an image path")
    if arg.image:
        search_deleted_files(arg.image) 
    if arg.disk:
        # imput disk like this (r"\\.\\D:")
        image = create_image_from_disk(arg.disk)
    
