from datetime import datetime
import os


def clear_screen():
    if os.name == 'nt':  # Windows 系统
        os.system('cls')
    else:  # macOS 或 Linux 系统
        os.system('clear')


def timecode_to_frame_number(timecode: str, frame_rate: int) -> int:
    # split the timecode into its components
    hours, minutes, seconds = timecode.split(':')
    seconds, milliseconds = seconds.split(',')

    # calculate the total number of seconds
    total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000

    # calculate the frame number
    frame_number = round(total_seconds * frame_rate)

    return frame_number


def srt_timecode_to_frames(timecode, frame_rate=24):
    time_parts = timecode.split(':')
    hours = int(time_parts[0])
    minutes = int(time_parts[1])
    seconds = int(time_parts[2].split(',')[0])
    milliseconds = int(time_parts[2].split(',')[1])
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
    return int(total_seconds * frame_rate)


def srt_timecode_to_seconds(timestamp: str) -> float:
    dt = datetime.strptime(timestamp, '%H:%M:%S,%f')
    return dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1e6


def srt_timecode_to_dav_timecode(timecode, frame_rate=24):
    time_parts = timecode.split(':')
    hours = int(time_parts[0])
    minutes = int(time_parts[1])
    seconds = int(time_parts[2].split(',')[0])
    milliseconds = int(time_parts[2].split(',')[1])
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
    frames = int((total_seconds - int(total_seconds)) * frame_rate)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"


def s_2_tc(seconds, frame_rate=24):
    frames = int((seconds - int(seconds)) * frame_rate)
    return f"{int(seconds)}:{frames}"


def frames_to_dav_timecode(frames, frame_rate=24):
    total_seconds = frames / frame_rate
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    remaining_frames = int((total_seconds - int(total_seconds)) * frame_rate)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{remaining_frames:02d}"


def f_2_tc(frames, frame_rate=24):
    seconds = frames // frame_rate
    remaining_frames = frames % frame_rate
    return f"{seconds}:{remaining_frames}"


def seconds_to_dav_timecode(seconds, frame_rate=24):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    remaining_frames = int((seconds - int(seconds)) * frame_rate)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{remaining_frames:02d}"


def seconds_to_frames(seconds, frame_rate):
    frames = int(seconds * frame_rate)
    return frames


