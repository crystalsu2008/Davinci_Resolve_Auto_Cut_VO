import os
import textwrap
from project import cut_vo, get_material_file, setup_proj
from transcribe import create_subtitle
from utils import clear_screen


# Get Project Path
proj_dir = os.path.dirname(os.path.abspath(__file__))


def prepare_guide(proj_dir):
    clear_screen()
    intro = ("This is a script program based on Davinci Resolve "
             "that can split a voice file into individual sentences "
             "according to a script. With this program, you can quickly "
             "split a voice file into multiple parts for easy editing and processing.")
    intro = textwrap.fill(intro, width=60)
    print(f'\033[36m{intro}\033[0m\n')

    guide = ("请先准备需要的素材：\n"
            "1) 请准备'哔哔哔'声音的音频文件, 名称以'bibibi'开头。\n"
            "2) 请准备旁白的音频文件, 名称以'voiceover'开头。\n"
            "3) 请准备需要剪切的每句话的文稿文件, 确保每一句一行, 名称以'script'开头。\n"
            "4) 将以上文件copy到同一个目录下。\n")
    print(f'\033[32m{guide}\033[0m')

    guide = ("输入素材所在目录的绝对路径(默认路径为当前位置), 或者输入'quit'退出当前程序。")

    print(f'\033[33m{guide}\033[0m')
    action = input()
    
    while action != 'quit':
        action = action.rstrip()
        if os.path.exists(action) and os.path.isdir(action):
            proj_dir = action

        bi_file = get_material_file(proj_dir, 'bibibi')
        vo_file = get_material_file(proj_dir, 'voiceover')
        script_file = get_material_file(proj_dir, 'script')

        if not bi_file:
            print(f"\033[31m'bibibi'素材没找到, 请检查素材名称和目录是否正确。\033[0m")
            print(f"\033[33mPress Enter key to continue 或者输入'quit'退出当前程序。\033[0m")
            action = input()
            if action == "quit":
                break
        elif not vo_file:
            print(f"\033[31m'voiceover'素材没找到, 请检查素材名称和目录是否正确。\033[0m")
            print(f"\033[33mPress Enter key to continue 或者输入'quit'退出当前程序。\033[0m")
            action = input()
            if action == "quit":
                break
        elif not script_file:
            print(f"\033[31m'script'素材没找到, 请检查素材名称和目录是否正确。\033[0m")
            print(f"\033[33mPress Enter key to continue 或者输入'quit'退出当前程序。\033[0m")
            action = input()
            if action == "quit":
                break
        else:
            break
    return action


# 准备工作
action = prepare_guide(proj_dir)
if action == 'quit':
    print("退出程序")

else:
    # Setup a Davinci Resolce Project
    if os.path.exists(action) and os.path.isdir(action):
            proj_dir = action
    resolve, projectManager, project = setup_proj(proj_dir)
    if not resolve:
        print("\033[31m没有找到DaVinci Resolve Project Manager, 请确保Resolve已经打开, 然后再执行此程序。\033[0m")

    else:
        # Create .srt Subtitle
        clear_screen()
        subtitle = create_subtitle(proj_dir)
        if subtitle == 'quit':
            print("退出程序")

        else:
            # Cut Voice Over
            cut_vo(proj_dir, subtitle, resolve, projectManager, project)