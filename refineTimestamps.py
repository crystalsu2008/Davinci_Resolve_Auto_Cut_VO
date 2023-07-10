# numpy需要提示安装
import numpy as np
import wave


def volume_analyze(volume_list, threshold, sample_point, sample_width, type, mode, percent=0.7):
    l = len(volume_list)-1
    a = min(l, max(0, sample_point))
    b = min(l, sample_point+sample_width)
    if type == 'mute':
        if mode == 'all':
            result = all(x < threshold for x in volume_list[a:b])
        elif  mode == 'any':
            result = any(x < threshold for x in volume_list[a:b])
        elif  mode == 'count':
            count = len([x for x in volume_list[a:b] if x < threshold])
            result = (count/(b-a))>=percent
        elif  mode == 'center_count':
            if volume_list[a] < threshold and volume_list[b-1] < threshold:
                count = len([x for x in volume_list[a+1:b-1] if x < threshold])
            else:
                count = 0
            result = (count/(b-a))>=percent
        else:
            result = None
    elif type == 'sound':
        if mode == 'all':
            result = all(x >= threshold for x in volume_list[a:b])
        elif  mode == 'any':
            result = any(x >= threshold for x in volume_list[a:b])
        elif  mode == 'count':
            count = len([x for x in volume_list[a:b] if x >= threshold])
            result = (count/(b-a))>=percent
        elif  mode == 'center_count':
            if volume_list[a] < threshold and volume_list[b-1] >= threshold:
                count = len([x for x in volume_list[a+1:b-1] if x >= threshold])
            else:
                count = 0
            result = (count/(b-a))>=percent
        else:
            result = None
    else:
        result = None

    return result


def get_average_volume_per_frame(filename, frame_rate=24):
    # 打开音频文件
    with wave.open(filename, 'rb') as wav_file:
        # 获取采样率和采样宽度
        sample_rate = wav_file.getframerate()
        sample_width = wav_file.getsampwidth()

        dtype=np.int8
        if sample_width == 2:
            dtype=np.int16
        elif sample_width == 3:
            dtype=np.int24
        elif sample_width == 4:
            dtype=np.int32

        # 初始化结果列表和误差累积器
        volume_per_frame = []
        error_accumulator = 0.0
        # 计算每一帧的理论采样数
        samples_per_frame = sample_rate / frame_rate
        # 读取音频数据并计算每一帧的平均音量
        while True:
            # 计算当前帧的实际采样数
            current_samples_per_frame = int(round(samples_per_frame + error_accumulator))
            # 更新误差累积器
            error_accumulator += samples_per_frame - current_samples_per_frame
            # 读取一帧的音频数据
            frames = wav_file.readframes(current_samples_per_frame)
            if not frames:
                break
            # 将音频数据转换为numpy数组
            samples = np.frombuffer(frames, dtype)
            # 计算当前帧的平均音量并添加到结果列表中
            volume_per_frame.append(np.mean(np.abs(samples)))
    return volume_per_frame


def refine_start_frame(volumes, frame, threshold, front_range, back_range, min_f, max_f):
    # 搜索距离此时间点最近的符合条件的时间点
    result = frame
    left = frame
    right = frame+1
    #min_f = max(min_f, front_range)
    #max_f = min(max_f, len(volumes)-1-back_range)
    while left >= min_f or right <= max_f:
        # 在左侧区间中搜寻
        # 判断时间点的 front_range 内是否“没有”声音
        if left >= min_f and volume_analyze(volumes, threshold, left-front_range, front_range, 'mute', 'all'):
            # 判断时间点的 back_range 内是否“有”声音
            if volume_analyze(volumes, threshold, left, back_range, 'sound', 'all'):
                result = left
                break
        # 在右侧区间中搜寻
        # 判断时间点的 front_range 内是否“没有”声音
        if right <= max_f and volume_analyze(volumes, threshold, right-front_range, front_range, 'mute', 'all'):
            # 判断时间点的 back_range 个区间内是否“有”声音
            if volume_analyze(volumes, threshold, right, back_range, 'sound', 'all'):
                result = right
                break
        left -= 1
        right += 1

    return result


def refine_end_frame(volumes, frame, threshold, front_range, back_range, min_f, max_f):
    # 搜索距离此时间点最近的符合条件的时间点
    result = frame
    left = frame
    right = frame+1
    #min_f = max(min_f, front_range)
    #max_f = min(max_f, len(volumes)-1-back_range)
    while left >= min_f or right <= max_f:
        # 在左侧区间中搜寻
        # 判断时间点的 front_range 内是否“有”声音
        if left >= min_f and volume_analyze(volumes, threshold, left-front_range, front_range, 'sound', 'all'):
            # 判断时间点的 back_range 内是否“没有”声音
            if volume_analyze(volumes, threshold, left, back_range, 'mute', 'center_count'):
                result = left
                break
        # 在右侧区间中搜寻
        # 判断时间点的 front_range 个区间内是否“有”声音
        if right <= max_f and volume_analyze(volumes, threshold, right-front_range, front_range, 'sound', 'all'):
            # 判断后 back_range 个区间内是否“没有”声音
            if volume_analyze(volumes, threshold, right, back_range, 'mute', 'center_count'):
                result = right
                break
        left -= 1
        right += 1

    return result


def refine_timestamps(wav_file, frame_points, threshold, mutehwidth, viocewidth, fps=24):
    # 获取每一帧的音量
    volumes = get_average_volume_per_frame(wav_file, fps)

    # 初始化结果列表
    result = []

    # 精确第一个时间点
    volumes_count = len(volumes)-1
    sf = frame_points[0]
    min_f = max(0, mutehwidth)
    max_f = min(frame_points[1], volumes_count-viocewidth)

    result.append( refine_start_frame(volumes, sf, threshold, mutehwidth, viocewidth, min_f, max_f) )

    # 遍历时间点
    for i in range(1, len(frame_points)-1, 2):
        # 精确起始时间点
        sf = frame_points[i+1]
        min_f = max(result[-1], mutehwidth)
        max_f = min(frame_points[i+2], volumes_count-viocewidth)
        sf = refine_start_frame(volumes, sf, threshold, mutehwidth, viocewidth, min_f, max_f)

        # 精确结束时间点
        ef = frame_points[i]
        min_f = max(result[-1], viocewidth)
        max_f = min(sf, volumes_count-mutehwidth)
        ef = refine_end_frame(volumes, ef, threshold, viocewidth, mutehwidth, min_f, max_f)

        result.append(ef)
        result.append(sf)

    # 精确最后一个时间点
    ef = frame_points[-1]
    min_f = max(result[-1], viocewidth)
    max_f = min(volumes_count, volumes_count-mutehwidth)
    result.append( refine_end_frame(volumes, ef, threshold, viocewidth, mutehwidth, min_f, max_f) )

    return result