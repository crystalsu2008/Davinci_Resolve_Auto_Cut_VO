import re
from transcribe import sub_process
from utils import clear_screen


def script_process(script_file):
    with open(script_file[0], 'r', encoding='utf-8') as file:
        vo_lines = file.readlines()

    script_list = []

    for vo_line in vo_lines:
        line = vo_line.replace('(', ' or ').replace('（', ' or ')
        line = re.sub(r'[^\w\s]', ' ', line).lower().strip()
        line = re.sub(r'\s{2,}', ' ', line)
        if not len(line):
            continue

        script_list.append({'raw_text': vo_line.strip(), 'match_text': line})

    return  script_list


def smith_waterman(seq1, seq2, start_point=0, match_score=2, mismatch_score=-1, gap_score=-1):
    m = len(seq1)
    n = len(seq2)
    score_matrix = [[0 for j in range(n+1)] for i in range(m+1)]
    max_score = 0
    max_pos = (0, 0)
    for i in range(start_point+1, m+1):
        for j in range(1, n+1):
            match = score_matrix[i-1][j-1] + (match_score if seq1[i-1] == seq2[j-1] else mismatch_score)
            delete = score_matrix[i-1][j] + gap_score
            insert = score_matrix[i][j-1] + gap_score
            score_matrix[i][j] = max(0, match, delete, insert)
            if score_matrix[i][j] > max_score:
                max_score = score_matrix[i][j]
                max_pos = (i, j)
    align1 = ""
    align2 = ""
    i, j = max_pos
    end_pos = i
    while i > 0 and j > 0:
        score_current = score_matrix[i][j]
        score_diag = score_matrix[i-1][j-1]
        score_up = score_matrix[i][j-1]
        score_left = score_matrix[i-1][j]
        if score_current == 0:
            break
        elif score_current == score_diag + (match_score if seq1[i-1] == seq2[j-1] else mismatch_score):
            align1 += seq1[i-1]
            align2 += seq2[j-1]
            i -= 1
            j -= 1
        elif score_current == score_left + gap_score:
            align1 += seq1[i-1]
            align2 += "-"
            i -= 1
        elif score_current == score_up + gap_score:
            align1 += "-"
            align2 += seq2[j-1]
            j -= 1
    start_pos = i + 1
    return (align1[::-1], align2[::-1], start_pos-1, end_pos-1, max_score)


def smith_waterman_match(sub_words, line_words, accurate, start_point=0):
    letter_start_pos = 0
    letter_end_pos = 0
    if not accurate:
        sub_words = [' ' +  word[::-1] for word in sub_words]
        line_words = [' ' + word[::-1] for word in line_words]
        alignment1, alignment2, start_pos, end_pos, score = smith_waterman(sub_words, line_words)
        score = round(score*5000/len(line_words))/100
    else:
        sub_letters=[]
        sub_letter_pos=[]
        line_letters=[]
        id = 0;
        for word in sub_words:
            for letter in word:
                sub_letters.append(letter)
                sub_letter_pos.append(id)
            sub_letters.append(' ')
            sub_letter_pos.append(id)
            id+=1

        for word in line_words:
            for letter in word:
                line_letters.append(letter)
            line_letters.append(' ')

        alignment1, alignment2, start_pos, end_pos, score = smith_waterman(sub_letters, line_letters, start_point)
        score = round(score*5000/len(line_letters))/100
        letter_start_pos = start_pos
        letter_end_pos = end_pos
        start_pos = sub_letter_pos[start_pos]
        end_pos = sub_letter_pos[end_pos]

    return alignment1, alignment2, start_pos, end_pos, letter_start_pos, letter_end_pos, score


def colored_alignment(align1, align2, reset='\033[90m'):
    red = '\033[31m'
    align1cd, align2cd = reset, reset
    for c1, c2 in zip(align1, align2):
        if c1 == c2:
            align1cd += c1
            align2cd += c2
        else:
            align1cd += red + c1 + reset
            align2cd += red + c2 + reset
    align1cd += "\033[0m"
    align2cd += "\033[0m"
    return align1cd, align2cd


def print_match_data(match_dat, sub_dict, index=-1):
    cf = (f'\033[0m')
    if index==-1:
        for line in match_dat:
            raw_text, match_text, alignment1, alignment2, start_pos, end_pos, lsp, lep, st, et, score = line.values()
            sub_text = ' '.join(sub_dict['word'][start_pos:end_pos+1])
            message = ''
            if score == 100:
                cf = (f'\033[32m')
                align1, align2 = colored_alignment(alignment1, alignment2, cf)
                message = f'\033[90mScript:\033[0m\t{cf}<{raw_text}>\033[0m *Perfect!*\n'
            else:
                if (lsp==0 & lep==0):
                    if score > 90:
                        cf = (f'\033[32m')
                    elif 60 <= score <= 90:
                        cf = (f'\033[33m')
                    else:
                        cf = (f'\033[31m')
                    align1, align2 = colored_alignment(alignment1, alignment2, cf)
                    message = (f'\033[90mScript:\t{cf}<{raw_text}>\033[0m\n'
                               f'\033[90mTransc:\t{cf}<{sub_text}>\033[0m\n')
                else:
                    if score > 99:
                        cf = (f'\033[32m')
                    elif 60 <= score <= 99:
                        cf = (f'\033[33m')
                    else:
                        cf = (f'\033[31m')
                    align1, align2 = colored_alignment(alignment1, alignment2, cf)
                    if score >= 60:
                        message = (f'\033[90mScript:\t{cf}<{align2}{cf}>\033[0m\n'
                                   f'\033[90mTransc:\t{cf}<{align1}{cf}>\033[0m\n')
                    else:
                        message = (f'\033[90mScript:\t{cf}<{raw_text}{cf}>\033[0m\n'
                                   f'\033[90mTransc:\t{cf}<{align1}{cf}>\033[0m\n')

            message += (f'\033[90mScore:\t{cf}{score}%\033[0m\t'
                f'\033[90mIndex:\t\033[34m{start_pos}:{end_pos}\033[0m\t'
                f'\033[90mTime:\t\033[36m{st}-{et}\033[0m')
            print(message)


def script_match_sub(script_file, subtitle, accurate):
    sub_check, sub_dict = sub_process(subtitle)
    sub_words = sub_dict['word']
    sub_st = sub_dict['start_timecodes_srt']
    sub_et = sub_dict['end_timecodes_srt']

    unqualified = True
    quit = False
    while unqualified:
        unqualified = False
        clear_screen()

        script_list = script_process(script_file)
        start_point = 0
        for line in script_list:
            line_words = line['match_text'].split()
            alignment1, alignment2, start_pos, end_pos, lsp, lep, score = smith_waterman_match(sub_words, line_words, accurate, start_point)
            start_point = lep
            line['alignment1'] = alignment1
            line['alignment2'] = alignment2
            line['start_pos'] = start_pos
            line['end_pos'] = end_pos
            line['letter_start_pos'] = lsp
            line['letter_end_pos'] = lep
            line['start_timecodes_srt'] = sub_st[start_pos]
            line['end_timecodes_srt'] = sub_et[end_pos]
            line['score'] = score
            if score < 60:
                unqualified = True
                start_point = 0

        print_match_data(script_list, sub_dict)

        if unqualified:
            print('发现匹配度过低的句子，您可以选择以下选项：')
            print('1) 修改匹配VO脚本的文本文件，然后再次查验匹配度。')
            print('2) 忽略低配配度的句子，执行其他句子的VO切分。')
            print('3) 退出程序。')

        while unqualified:
            choice = input('请输入选项（1-3）：')
            if choice == '1':
                input('请修改VO脚本的文本文件，然后按“回车”键继续...')
                break
            elif choice == '2':
                script_list[:] = [item for item in script_list if item['score'] >= 60]
                unqualified = False
                continue
            elif choice == '3':
                print('退出程序')
                unqualified = False
                quit = True
                break
            else:
                print('没有此选项，请重新选择')
                continue
    if quit:
        return('quit')

    return (script_list, sub_dict)