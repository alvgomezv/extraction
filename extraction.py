
# https://github.com/dkovar/analyzeMFT
# "Record Number","Good","Active","Record type","Sequence Number","Parent File Rec. #","Parent File Rec. Seq. #","Filename #1","Std Info Creation date","Std Info Modification date","Std Info Access date","Std Info Entry date","FN Info Creation date","FN Info Modification date","FN Info Access date","FN Info Entry date","Object ID","Birth Volume ID","Birth Object ID","Birth Domain ID","Filename #2","FN Info Creation date","FN Info Modify date","FN Info Access date","FN Info Entry date","Filename #3","FN Info Creation date","FN Info Modify date","FN Info Access date","FN Info Entry date","Filename #4","FN Info Creation date","FN Info Modify date","FN Info Access date","FN Info Entry date","Standard Information","Attribute List","Filename","Object ID","Volume Name","Volume Info","Data","Index Root","Index Allocation","Bitmap","Reparse Point","EA Information","EA","Property Set","Logged Utility Stream","Log/Notes","STF FN Shift","uSec Zero","ADS","Possible Copy","Possible Volume Move"
import os
import sys
import argparse
import datetime
import time
import ctypes
import pytsk3
from tabulate import tabulate
import psutil
from tqdm import tqdm
import csv
import pandas as pd
import subprocess
import re
import curses

magics = {
    "jpg" : [b"\xff\xd8\xff\xe0\x00\x10\x4a\x46", b"\xff\xd9"],
    "png" : [b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a", b"\x49\x45\x4e\x44\xae\x42\x60\x82"],
    "pdf" : [b"\x25\x50\x44\x46", b"\x25\x25\x45\x4f\x46"],
    "gif" : [b"\x47\x49\x46\x38", b"\x00\x3b"],
    "xml" : [b"\x50\x4b\x03\x04\x14\x00\x06\x00", b"\x50\x4b\x05\x06"],
}

good_recovered_files = []
recoverable = {}
selected_files = {}

'''path to analyzeMFT module'''
analyzeMFT_path = "./analyzeMFT/analyzeMFT.py"

'''path to MFT file'''
mft_file_path = "./analyzeMFT/mft_tmp"

'''path to MFT parsed file'''
mft_parse_file_path = "./analyzeMFT/mft_tmp.txt"
#mft_parse_file_path_csv = "./analyzeMFT/mft2.csv"
#mft_parse_file_path_tl = "./analyzeMFT/mft2.tl.txt"

'''path to image file'''
#image_path = "./analyzeMFT/image2.dd"

def ft_read_disk(disk):
    '''Read disk'''
    # Open the image file and create an image object
    image = pytsk3.Img_Info(disk)
    # Open the partition table and print the partitions
    try:
        partitionTable = pytsk3.Volume_Info(image)
    except Exception as error:
        print(error)
        exit(1)
    # Open the file system and retrieve the root directory
    try:
        fileSystemObject = pytsk3.FS_Info(image, offset=partitionTable[0].start*512)
    except Exception as error:
        print(error)
        exit(1)
    return fileSystemObject

def ft_parse_MFT(mft_file_path):
    # analyzeMFT_path = "./analyzeMFT-master/analyzeMFT.py"
    # mft_file_path = "./analyzeMFT-master/mft"
    # mft_parse_file_path = "./analyzeMFT-master/mft.txt"

    # Comando a ejecutar
    command = ["python3", analyzeMFT_path, "-f", mft_file_path,  "-o", mft_parse_file_path]
    #command = ["python3", analyzeMFT_path, "-f", mft_file_path,  "-c", mft_parse_file_path_csv]
    #command = ["python3", analyzeMFT_path, "-f", mft_file_path,  "-b", mft_parse_file_path_tl]

    # Ejecutar el comando
    subprocess.run(command)

def ft_check_MFT(mft_parse_file_path):
    # Leer el archivo parseado
    df = pd.read_csv(mft_parse_file_path, encoding="latin-1")

    for index, row in df.iterrows():
        good_value = row['Good']
        record_type = row['Record type']
        filename = row['Filename']
        modif_date = row['Std Info Modification date']
        filename1 = row['Filename #1']
        active_value = row['Active']
        if good_value == 'Good' and record_type == 'File' and active_value == "Inactive":
            if "Zone.Identifier" not in filename1:
                good_recovered_files.append(filename1)
            # record_number = row['Record Number']
            sequence_number = row['Sequence Number']
            parent_file_rec = row['Parent File Rec. #']
            # Haz algo con los valores de cada línea, por ejemplo, imprimirlos
            #print(f"Good: {good_value}, Active: {active_value}, filename1: {filename1}, filename: {filename}, modif_date: {modif_date}, Record type: {record_type}, Sequence Number: {sequence_number}, Parent File Rec. #: {parent_file_rec}")

#Open the usb as raw bytes
#with open(r"\\.\\D:", "rb") as f:
#    image = f.read(512)

def create_image_from_disk(folder_path, image_path):
    #drive_type = ctypes.windll.kernel32.GetDriveTypeW(folder_path)
    #if drive_type == 3 or drive_type == 2:  # 3 fixed disk drive / 2 removable storage device
    #   print("Path is a disk")
    img_info = pytsk3.Img_Info(folder_path)
    # Open the output file in write-binary mode
    with open(image_path, "wb") as output_file:
        # Read and write the contents of the disk to the output file
        offset = 0
        chunk_size = 1024 * 1024  # 1MB chunk size (adjust as needed)
        while offset < img_info.get_size():
            data = img_info.read(offset, chunk_size)
            output_file.write(data)
            offset += chunk_size

    print(f"Image {image_path} created successfully")

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

def ft_extract_MFT(file):
    #for entry in file
    content = file.read_random(0, file.info.meta.size)
    with open(mft_file_path, 'wb') as output:
        output.write(content)

def search_deleted_files(image):
    img_info = pytsk3.Img_Info(image)
    fs_info = pytsk3.FS_Info(img_info)
    #root_dir = fs_info.open_dir(path="/")
    mft_file = fs_info.open("/$MFT")
    #print_directory_table(root_dir)
    ft_extract_MFT(mft_file)
    ft_parse_MFT(mft_file_path)
    ft_check_MFT(mft_parse_file_path)

#def go_through_disk(disk_path):
#    total = None
#    for disk in psutil.disk_partitions():
#        if disk_path in disk.device or disk_path in disk.mountpoint:
#            total = psutil.disk_usage(disk.mountpoint).total
#    if total is None:
#        print("Error: Disk not found")
#        sys.exit()
#    size = 512
#    blocks = total/size
#    count = 0
#    offset = 0
#    with tqdm(total=blocks, unit='block') as progress_bar:
#        try:
#            d = open(f"\\.\\{disk_path}", "rb")
#        except:
#            print("Disk cannot be read, format must be: \\\\.\\\\D:")
#            sys.exit()
#        else:
#            bytes = d.read(size)
#            progress_bar.update(1)
#            try:
#                while bytes:
#                    for key, value in magics.items():
#                        # HACER: afinar busqueda por nombre de archivo a recuperar
#                        found = bytes.find(value[0])
#                        if found >= 0:
#                            drec = True
#                            #print(f"Found {key} at location: {str(hex(found+(size*offset)))}")
#                            # File name option for the folder
#                            if not os.path.exists("C:\\Users\\Usuario\\extraction\\Recovered"):
#                                os.makedirs("C:\\Users\\Usuario\\extraction\\Recovered")     
#                            with open(f"C:\\Users\\Usuario\\extraction\\Recovered\\{str(count)}.{key}", "wb") as f:
#                                f.write(bytes[found:])
#                                while drec is True:
#                                    bytes = d.read(size)
#                                    progress_bar.update(1)
#                                    found = bytes.find(value[1])
#                                    if found >= 0:
#                                        f.write(bytes[:found+2])
#                                        d.seek((offset+1)*size)
#                                        #print(f"Wrote {key} to location: {str(count)}.{key}\n")
#                                        drec = False
#                                        count += 1
#                                    else:
#                                        f.write(bytes)
#                    bytes = d.read(size)
#                    progress_bar.update(1)
#                    offset += 1
#                d.close()
#            except KeyboardInterrupt:
#                progress_bar.close()
#                print("Program stopped!")
#                sys.exit()

def go_through_disk(disk_path, selected_files):
    total = None
    for disk in psutil.disk_partitions():
        if disk_path in disk.device or disk_path in disk.mountpoint:
            total = psutil.disk_usage(disk.mountpoint).total
    if total is None:
        print("Error: Disk not found")
        sys.exit()
    if not os.path.exists(".\\Recovered"):
            os.makedirs(".\\\Recovered")
    for key, value in selected_files.items():
        with open(rf"\\.\\{disk_path}", "rb") as d:
            bytes = d.read(value["offset"] + value["file_size"])
            with open(f".\\Recovered\\{key}", "wb") as f:
                f.write(bytes[value["offset"]:])


def get_file_attributes(disk_path):
    img_info = pytsk3.Img_Info(disk_path)
    fs_info = pytsk3.FS_Info(img_info)
    # Iterate through the files to recover from the entries of the MFT
    for file in good_recovered_files:
        mft_file = fs_info.open(file)
        # Iterate through the attributes of the entries
        for attribute in mft_file:
            if attribute.info.type == pytsk3.TSK_FS_ATTR_TYPE_NTFS_DATA and attribute.info.name != b'Zone.Identifier':
                # Iterate through the data runs of the $DATA attribute of each entry
                for run in attribute:
                    cluster_start = run.addr * fs_info.info.block_size  # Offset in bytes
                    cluster_length = run.len * fs_info.info.block_size  # Length in bytes
                    #print(f"Cluster start: {cluster_start}, Cluster length: {cluster_length}")
                    recoverable[file.lstrip('/')] = {
                        "offset" : cluster_start, 
                        "file_size" : attribute.info.size, 
                        "cluster_size" : cluster_length}
                    
def select_options(stdscr):
    # Clear the screen
    stdscr.clear()

    selected_options = set()
    current_option = 0

    while True:
        # Clear the screen
        stdscr.clear()
        # Introductory message
        intro_message = "Select files to recover:"
        stdscr.addstr(0, 0, intro_message, curses.A_BOLD)

        # Display the options
        for i, (name, data) in enumerate(recoverable.items()):
            if i == current_option:
                # Display the current option with a highlight
                stdscr.addstr(i+1, 0, "> " + f"{name:50s}" + " <" + f" - size: {float(data['file_size']/1024):.2f}KB", curses.A_REVERSE)
            elif i in selected_options:
                # Display a tick after the selected options
                stdscr.addstr(i+1, 0,"* " + f"{name:50s}" + 2*" "+ f" - size: {float(data['file_size']/1024):.2f}KB")
            else:
                stdscr.addstr(i+1, 0, f"{name:50s}" + 4*" " + f" - size: {float(data['file_size']/1024):.2f}KB")

        # Display the "Start" option in bold letters without the asterisk
        start_option = "Start"
        if current_option == len(recoverable):
            stdscr.addstr(len(recoverable)+1, 0, "> " + start_option + " <", curses.A_REVERSE)
        else:
            stdscr.addstr(len(recoverable)+1, 0, start_option)

        # Refresh the screen
        stdscr.refresh()

        # Wait for user input
        try:
            key = stdscr.getch()
        except KeyboardInterrupt:
            print("Program stopped!")
            sys.exit()

        # Handle arrow key input
        if key == curses.KEY_UP:
            current_option = (current_option - 1) % (len(recoverable) + 1)
        elif key == curses.KEY_DOWN:
            current_option = (current_option + 1) % (len(recoverable) + 1)
        elif key == ord('\n'):  # Handle Enter key press
            if current_option == len(recoverable):
                break  # Break the loop if "Start" option is selected
            else:
                # Toggle the selection of the current option
                if current_option in selected_options:
                    selected_options.remove(current_option)
                else:
                    selected_options.add(current_option)

    if len(selected_options) > 0:
        # Print the selected options after the loop
        print("Recovered files:")
        for option_idx in selected_options:
            option_name = list(recoverable.keys())[option_idx]
            print(option_name)
        remove = []
        for i in range(len(recoverable)):
            if i not in selected_options:
                remove.append(i)
        items = list(recoverable.items())
        filtered_items = [item for i, item in enumerate(items, start=0) if i not in remove]
        selected_files = dict(filtered_items)
        go_through_disk("D:", selected_files)

    #print("Do you want to do a deep search though the whole disk?[Y/N]")
    #key = input()
    #if key == "Y":
    #    stdscr.clear()
    #    while True:
    #        # Clear the screen
    #        stdscr.clear()


def parse_arguments():
    parser = argparse.ArgumentParser(description="Tool for recovering recently deleted files on NTFS")
    parser.add_argument("-d", "--disk", action="store", help="Path to the disk")
    parser.add_argument("-i", "--image", action="store", help="Create an image from a disk file")
    parser.add_argument("-t", "--timelaps", action="store", help="Time range in hours, default 24h" )
    arg = parser.parse_args()
    date_format = "%d-%m-%Y"
    if arg.disk is None:
        print("A disk must be provided")
        sys.exit()
    if re.match(r'^[A-Z]:$', arg.disk) is None:
        print("Disk format must be uppercase letter followed by a colon (ex: 'D:')")
        sys.exit()
    if arg.image and not arg.disk:
        print("You need to specify a disk to create an image from with the '-i' flag")
        sys.exit()
    try:
        if arg.timelaps is not None:
            arg.timelaps = datetime.datetime.strptime(arg.timelaps, date_format).timestamp()
        else:
            arg.timelaps = time.time() - (24 * 60 * 60)
        return arg
    except Exception as e:
        print(f"Error: {e}")
        sys.exit()



if __name__ == "__main__":
    #create_image_from_disk(r"\\.\\d:")

    search_deleted_files(r"\\.\\d:")
    get_file_attributes(r"\\.\\d:")
    curses.wrapper(select_options)
    sys.exit(0)
    arg = parse_arguments()
    if arg.disk:
        if arg.image:
            create_image_from_disk(arg.disk, arg.image)
        else:
            #search_deleted_files(arg.disk)
            go_through_disk(arg.disk)
            # imput disk like this (r"D:")