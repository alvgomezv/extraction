
import os
import argparse
import datetime
import time
import ctypes
import pytsk3
from tabulate import tabulate
import psutil
from tqdm import tqdm

jpg_start = b"\xff\xd8\xff\xe0\x00\x10\x4a\x46"
jpg_end = b"\xff\xd9"

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
        elif entry.info.meta.type == pytsk3.TSK_FS_META_NAME_DELETED:
            # Display recovered file information
            print(f"Recovered File: {entry.info.name.name.decode()}")

def print_directory_table(directory):
    table = [["Name", "Type", "Size", "Create Date", "Modify Date"]]
    for f in directory:
        name = f.info.name.name
        if f.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
            f_type = "DIR"
        else:
            f_type = "FILE"
        size = f.info.meta.size
        create = f.info.meta.crtime
        modify = f.info.meta.mtime
        table.append([name, f_type, size, create, modify])
    print(tabulate(table, headers="firstrow"))


def search_deleted_files(image):
    img_info = pytsk3.Img_Info(image)
    fs_info = pytsk3.FS_Info(img_info)
    root_dir = fs_info.open_dir(path="/")
    #traverse_directory(root_dir)
    print_directory_table(root_dir)

def go_through_disk(disk):
    # suponemos que es el disco D
    disk_mounted = psutil.disk_partitions()[1]
    total = psutil.disk_usage(disk_mounted.mountpoint).total
    size = 512
    blocks = total/size
    count = 0
    offset = 0
    with tqdm(total=blocks, unit='block') as progress_bar:
        try:
            d = open(disk, "rb")
        except:
            print("Disk cannot be read, format must be: \\\\.\\\\D:")
            exit()
        else:
            bytes = d.read(size)
            progress_bar.update(1)
            try:
                while bytes:
                    found = bytes.find(jpg_start)
                    if found >= 0:
                        drec = True
                        print(f"Found JPG at location: {str(hex(found+(size*offset)))}")
                        if count == 0:
                            os.makedirs("C:\\Users\\Usuario\Desktop\\Recovered")     
                        with open(f"C:\\Users\\Usuario\Desktop\\Recovered\\{str(count)}.jpg", "wb") as f:
                            f.write(bytes[found:])
                            while drec is True:
                                bytes = d.read(size)
                                progress_bar.update(1)
                                found = bytes.find(jpg_end)
                                if found >= 0:
                                    f.write(bytes[:found+2])
                                    d.seek((offset+1)*size)
                                    print(f"Wrote JPG to location: {str(count)}.jpg\n")
                                    drec = False
                                    count += 1
                                else:
                                    f.write(bytes)
                    bytes = d.read(size)
                    progress_bar.update(1)
                    offset += 1
                d.close()
            except KeyboardInterrupt:
                progress_bar.close()
                print("Program stopped!")
                exit()


def parse_arguments():
    parser = argparse.ArgumentParser(description="Tool for recovering recently deleted files on NTFS")
    parser.add_argument("-d", "--disk", action="store", help="Path to the disk")
    parser.add_argument("-c", "--create", action="store_true", help="Create an image from a disk file")
    parser.add_argument("-i", "--image", action="store", help="Path to the image file")
    parser.add_argument("-t", "--timelaps", action="store", help="Time range in hours, default 24h" )
    arg = parser.parse_args()
    date_format = "%d-%m-%Y"
    if arg.image and arg.disk:
        print("Provide either a disk or an image path")
        exit()
    if arg.create is True:
        if not arg.disk:
            print("You need to specify a disk to create an image from with the '-d' flag")
            exit()
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
    if arg.image:
        search_deleted_files(arg.image) 
    if arg.disk:
        if arg.create is True:
            image = create_image_from_disk(arg.disk)
        else:
            go_through_disk(arg.disk)
        # imput disk like this (r"\\.\\D:")
    
