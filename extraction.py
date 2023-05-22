
import os
import sys
import argparse
import datetime
import time
import ctypes

def search_deleted_files(folder_path):
    if folder_path is None:
        folder_path = r"C:\\"
    if os.path.isdir(folder_path):
        drive_type = ctypes.windll.kernel32.GetDriveTypeW(folder_path)
        if drive_type == 3 or drive_type == 2:  # 3 fixed disk drive / 2 removable storage device
            print("Path is a disk")
        else:
            print("Path is not a fixed or removable disk")
    else:
        print("Path is not a directory")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Tool for recovering recently deleted files on NTFS")
    parser.add_argument("-p", "--path", action="store", help="Path to the disk or folder image, default C:\\")
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
    search_deleted_files(arg.path)
