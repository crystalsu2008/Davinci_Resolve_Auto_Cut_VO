import os
import DaVinciResolveScript as dvr_script
from refineTimestamps import get_average_volume_per_frame, refine_timestamps
from script import script_match_sub
from utils import clear_screen, frames_to_dav_timecode, srt_timecode_to_dav_timecode, srt_timecode_to_frames


def get_material_file(proj_dir, prefix):
    # 获取指定目录下的所有文件和文件夹名称
    file_names = os.listdir(proj_dir)
    # 筛选出以特定前缀开头的文件名称
    file = [name for name in file_names if name.startswith(prefix)]
    file = [os.path.join(proj_dir, name) for name in file]
    file = [path for path in file if os.path.isfile(path)]

    return file


def create_proj(resolve, projectManager, proj_dir, pname):
    # Create a Project
    project = projectManager.CreateProject(pname)

    # Object of Mediapool is gotten from project.
    mediaPool = project.GetMediaPool()
    rootFolder = mediaPool.GetRootFolder()
    material_bin = mediaPool.AddSubFolder(rootFolder, "material")

    # Media Storage
    mediaStorage = resolve.GetMediaStorage()
    bi_file = get_material_file(proj_dir, 'bibibi')
    vo_file = get_material_file(proj_dir, 'voiceover')

    # Add bibibi Clips
    mediaPool.SetCurrentFolder(material_bin)
    bi_clip = mediaStorage.AddItemListToMediaPool(bi_file)

    # Add vo Clips
    vo_clip = mediaStorage.AddItemListToMediaPool(vo_file)

    # Timeline from clips
    mediaPool.SetCurrentFolder(rootFolder)
    mediaPool.CreateEmptyTimeline('noise_sample')
    subtitletimeline = mediaPool.CreateTimelineFromClips('SubtitleTimeline', vo_clip)

    return project


def setup_proj(proj_dir):
    # Assign Resolve
    resolve = dvr_script.scriptapp("Resolve")

    if not resolve:
        return(resolve, resolve, resolve)
    # Get a Project Manager
    projectManager = resolve.GetProjectManager()

    # Get Current Project
    project = projectManager.GetCurrentProject()
    if (project.GetName()=='Untitled Project'):
        # Setup a Project
        print('\033[31m没有打开的项目, 将创建新的项目或打开已存在项目...\033[0m')
        print('创建新的项目前请先确保\033[32mPreferences\033[0m -> '
              '\033[32mUser\033[0m -> \033[32mEditing\033[0m -> '
              '\033[32mStart timecode\033[0m设置为00:00:00:00')
        pname = input('\033[33mInsert the name for this project: \033[0m')
        project = projectManager.LoadProject(pname)
        if not project:
            project = create_proj(resolve, projectManager, proj_dir, pname)

        # Try to get a current timeline
        timeline = project.GetCurrentTimeline()

        # If not, then try to get the first timeline and set it to current
        if not timeline:
            if project.GetTimelineCount() > 0:
                timeline = project.GetTimelineByIndex(1)
                project.SetCurrentTimeline(timeline)

    return(resolve, projectManager, project)


def get_material_clip(mediaPool, prefix, bin_name='material'):
    # 获取根文件夹中的子文件夹
    folders = mediaPool.GetRootFolder().GetSubFolderList()
    # 获取名为‘material’的素材箱
    material_bin = [folder for folder in folders if folder.GetName()==bin_name][0]
    # 获取名为‘material’的素材箱中的素材
    clips = material_bin.GetClipList()
    clips = [clip for clip in clips if clip.GetName().startswith(prefix)]
    return clips


def get_timeline(project, prefix):
    timeline = project.GetCurrentTimeline()
    result = timeline
    if not timeline.GetName().startswith(prefix):
        result =  None
        for id in range(0, project.GetTimelineCount()):
            timeline = project.GetTimelineByIndex(id+1)
            if timeline.GetName().startswith(prefix):
                result = timeline
                break
    return result


def get_threshold(project, fps=24, timeline_name='noise_sample'):
    while True:
        ns_timeline = get_timeline(project, timeline_name)
        if not ns_timeline:
            message = (f"未找到'{timeline_name}' 时间线, 无法确定静音判断阈值。\n"
                       f"进行时间点精确定位, 可创建'{timeline_name}' 时间线, 并插入从'voiceover'素材中截取的静音底噪样本。\n"
                       f"回车重新采样'{timeline_name}' 时间线, 或手动输入阈值(整型, 如: 125):")
            threshold = input(f'\033[33m{message}\033[0m')
            if isinstance(threshold, int) and threshold > 0:
                break
        else:
            project.SetCurrentTimeline(ns_timeline)
            tracks = ns_timeline.GetTrackCount('audio')
            # 获取时间线上全部items
            items = []
            for i in range(1, tracks + 1):
                track_items = ns_timeline.GetItemsInTrack('audio', i)
                for item in track_items.values():
                    items.append(item)

            if len(items) == 0:
                message = (f"未在'{timeline_name}' 时间线上找到静音底噪片段, 无法确定静音判断阈值。\n"
                       f"进行时间点精确定位, 可在'{timeline_name}' 时间线插入从'voiceover'素材中截取的静音底噪样本。\n"
                       f"回车重新采样'{timeline_name}' 时间线, 或手动输入阈值(整型, 如: 125):")
                threshold = input(f'\033[33m{message}\033[0m')
                if isinstance(threshold, int) and threshold > 0:
                    break
            else:
                # 获取第一个item在素材上的入点和出点
                in_point = items[0].GetLeftOffset()
                out_point = items[0].GetRightOffset()

                # 获取item对应的素材clip
                media_pool_item = items[0].GetMediaPoolItem()
                # 获取第一个item素材在硬盘上的文件路径
                wav_file = media_pool_item.GetClipProperty()["File Path"]

                volumes = get_average_volume_per_frame(wav_file, fps)[in_point: out_point]

                threshold = max(volumes)*1.25
                break

    return threshold


def cut_vo(proj_dir, subtitle, resolve, projectManager, project, accurate=False):
    
    frameRate = project.GetSetting('timelineFrameRate')

    # 通过对比文稿的每一行在字幕中的位置, 获取需要切割 vo 的每一行的信息数据
    script_file = get_material_file(proj_dir, 'script')
    cut_lines, sub_dict = script_match_sub(script_file, subtitle, accurate)
    if cut_lines == 'quit':
        return
    else:
        frame_points=[]
        for line in cut_lines:
            frame_points.extend([srt_timecode_to_frames(line['start_timecodes_srt']), srt_timecode_to_frames(line['end_timecodes_srt'])])

        vo_file = get_material_file(proj_dir, 'voiceover')[0]
        threshold = get_threshold(project, frameRate)
       
        new_frame_points=refine_timestamps(vo_file, frame_points, threshold, 10, 3, frameRate)
        print(frame_points)
        print(new_frame_points)

        # 获取 Media Pool 对象
        mediaPool = project.GetMediaPool()
        bi_clip = get_material_clip(mediaPool, 'bibibi')[0]
        vo_clip = get_material_clip(mediaPool, 'voiceover')[0]

#'raw_text', 'match_text', 'alignment1', 'alignment2', 'start_pos', 'end_pos',
#'letter_start_pos', 'letter_end_pos', 'start_timecodes_srt', 'end_timecodes_srt', 'score'
        for index, line in enumerate(cut_lines):
            words = line['raw_text'].split()
            name = str(index+1)+'_'+'_'.join(words[0:3])

            start_tc_dav = srt_timecode_to_dav_timecode(line['start_timecodes_srt'])
            end_tc_dav = srt_timecode_to_dav_timecode(line['end_timecodes_srt'])
            sf = new_frame_points[index*2]
            ef = new_frame_points[index*2+1]# + 0.5*frameRate
            new_start_tc_dav = frames_to_dav_timecode(sf)
            new_end_tc_dav = frames_to_dav_timecode(ef)

            mediaPool.CreateTimelineFromClips(name, bi_clip)
            mediaPool.AppendToTimeline([{"mediaPoolItem":vo_clip, "startFrame": sf, "endFrame": ef, "mediaType": 2}])

            print(index, start_tc_dav, end_tc_dav, new_start_tc_dav, new_end_tc_dav, name)