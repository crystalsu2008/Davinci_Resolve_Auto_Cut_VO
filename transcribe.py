import os
import re
import string


def create_subtitle(proj_dir):
    guide= ("\033[31mIn order to get the subtitle file, do the following:\033[0m"
            "\033[31mStep 1:\033[0m\nClick '\033[32mCreate Subtitles from Audio...'\033[0m in the '\033[32mTimeline'\033[0m "
            "menu to transcribes speech to text automatically into a subtitle track on the timeline.\n"
            "\033[31mStep 2:\033[0m\nIn the '\033[32mCreate Subtitles'\033[0m dialog box, "
            "make sure the '\033[32mMax Characters per Line'\033[0m is set to '\033[32m1'\033[0m. "
            "Then click the '\033[32mCreate'\033[0m button.\n"
            "\033[31mStep 3:\033[0m\nWhen the subtitle is created, right-click the subtitle track "
            "and click the '\033[32mExport Subtitle...'\033[0m button.\n"
            "\033[31mStep 4:\033[0m\nIn the pop-up '\033[32mExport Subtitle'\033[0m dialog box, "
            "save the subtitle file as .srt type.\n"
            "\033[33mInsert the name of the subtitle file output by the above steps, \033[0m")
    print(f'{guide}')
    subtitle = input("\033[33m或者直接回车, 将自动搜索项目目录下已存在的'.srt'文件（输入'quit'可退出程序）: \033[0m")
    subtitlepath = 'quit'

    while subtitle != 'quit':
        if subtitle=='':
            # 获取指定目录下的所有文件和文件夹名称
            file_names = os.listdir(proj_dir)
            # 筛选出以 .srt 为扩展名的文件名称
            srt_files = [name for name in file_names if name.endswith('.srt')]
            # 为每个文件名添加完整路径
            full_paths = [os.path.join(proj_dir, name) for name in srt_files]
            # 删除不是文件的元素
            result = [path for path in full_paths if os.path.isfile(path)]
            subtitlepath = result[0]
        else:
            subtitlepath = os.path.join(proj_dir, subtitle)
        if os.path.isfile(subtitlepath):
            break
        else:
            print(f"\033[31m'{subtitle}'文件不存在在项目目录或者不是一个文件！请重新输入字幕文件名称。\033[0m")
            print(f"\033[31m或者输入'quit'退出当前程序。\033[0m")
            subtitle = input('\033[33mInsert the name of the subtitle file output by the above steps: \033[0m')
            if subtitle == 'quit':
                subtitlepath = 'quit'
                break

    return(subtitlepath)


def sub_process(subtitle):
    sub_check  = subtitle+'.txt'

    start_timecodes_srt = []
    end_timecodes_srt = []
    texts = []
    translator = str.maketrans('', '', string.punctuation)

    with open(subtitle, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if '-->' in line:
                times = line.split('-->')
                start_timecodes_srt.append(times[0].strip())
                end_timecodes_srt.append(times[1].strip())
            elif line.strip().isdigit():
                continue
            elif line.strip() == '':
                continue
            else:
                text = re.sub('<b>', '', line.strip())
                text = re.sub('</b>', '', text)
                text = re.sub(r'[^\w\s]', ' ', text).lower().strip()
                words = text.split()
                for i in range(len(words)-1):
                    start_timecodes_srt.append(start_timecodes_srt[-1])
                    end_timecodes_srt.append(end_timecodes_srt[-1])
                texts.extend(words)

    all_text = ' '.join(texts)
    with open(sub_check, 'w') as f:
        f.write(all_text)

    sub_dict = {'word': texts, 'start_timecodes_srt': start_timecodes_srt, 'end_timecodes_srt': end_timecodes_srt}
    return(sub_check, sub_dict)