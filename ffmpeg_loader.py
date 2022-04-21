from os import system
from time import sleep
from pathlib import is_file
import movenet
from math import sqrt

FRAMERATE = 12
TEMPORARY_BMP_PREFIX = "output"

def log_path_error(path_name=""):
    print("The requested path is not a valid path name!")

def normalize(float_coordinate):
    return int(float_coordinate*500)

def get_pose(path):
    coordinates = movenet.read_frame(path)
    coordinates = [(normalize(x), normalize(y)) for x, y in coordinates]
    return coordinates

def read_video(input_path, start, end, rest=0.0):

    frame_poses = []

    if is_file(input_path):
        system(f"ffmpeg -loglevel quiet -i {input_path} -ss {start} -t {end-start} -r {FRAMERATE} {TEMPORARY_BMP_PREFIX}-%01d.bmp")
        for i in range(1, (end - start) * 12):
            current_pose = get_pose(f'{TEMPORARY_BMP_PREFIX}-{i}.bmp')
            frame_poses.append(current_pose)
            system(f'rm {TEMPORARY_BMP_PREFIX}-{i}.bmp')
            if rest != 0:
                sleep(rest)
    
    elif not is_file(input_path):
        log_path_error()

    return frame_poses