import os
import pandas as pd
import chardet
from sklearn.model_selection import train_test_split

high_bound = 69
low_bound = 51

high_data_cnt = 0
low_data_cnt = 0
std_data_cnt = 0

# 自动检测文件编码的函数
def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        result = chardet.detect(file.read())
    return result['encoding']

def extract_time_differences(file_path, file_name):
    global high_data_cnt, low_data_cnt, std_data_cnt
    print(file_name)
    name = file_name.split('_')[1]
    have_task = 0
    physical_time_diffs = []
    color_class = []
    music_class = []
    with open(file_path, 'r', encoding= detect_encoding(file_path)) as file:
        lines = file.readlines()
        # Find all lines that contain physical time differences
        for line in lines:
            if '物理时间差' in line:
                physical_time_diffs.append(float(line.split('物理时间差')[1].strip()))
            if '实验开始' in line:
                color = line.split('Color: ')[1].strip()
                if color.startswith("White"):
                    color_class.append(0)
                elif color.startswith('Blue'):
                    color_class.append(float(1/3))
                elif color.startswith('Red'):
                    color_class.append(float(2/3))
                else:
                    print('颜色error')

                music = line.split('Music: ')[1].strip()
                if music.startswith('No'):
                    music_class.append(0)
                elif music.startswith('70'):
                    music_class.append(float(1/3))
                elif music.startswith('140'):
                    music_class.append(float(2/3))
                else:
                    print("音乐error")            

        # physical_time_diffs = [float(line.split('物理时间差')[1].strip()) for line in lines if '物理时间差' in line]

        if '认知负荷' in lines[5]:
            have_task = 1
        for i in range(1, 10):
            if_valid_path = f"Dataset/eeg/{name}/{name}_{i}.csv"
            if os.path.exists(if_valid_path):
                name_list.append(f"{name}_{i}")
                time_list.append(physical_time_diffs[i - 1])
                eeg_path.append(if_valid_path)
                ppg_path.append(f"Dataset/ppg/{name}/{name}_{i}.csv")
                if_task_list.append(have_task)
                music_list.append(music_class[i - 1])
                color_list.append(color_class[i - 1])
                if physical_time_diffs[i - 1] > high_bound:
                    flag_list.append(2)
                    high_data_cnt = high_data_cnt + 1
                elif physical_time_diffs[i - 1] < low_bound:
                    flag_list.append(0)
                    low_data_cnt = low_data_cnt + 1
                else:
                    flag_list.append(1)
                    std_data_cnt = std_data_cnt + 1
            else:
                print(f"无{if_valid_path}")

if __name__ == "__main__":
    root_path = "../raw/Data"
    file_list = os.listdir(root_path)
    name_list = []
    time_list = []
    flag_list = []
    eeg_path = []
    ppg_path = []
    if_task_list = []
    color_list = []
    music_list = []
    
    for file in file_list:
        if not file.endswith(".txt"):
            continue
        file_path = os.path.join(root_path, file)
        extract_time_differences(file_path, file)

    df = pd.DataFrame({
        'name': name_list,
        'eeg': eeg_path,
        'ppg': ppg_path,
        'time': time_list,
        'task': if_task_list,
        'music': music_list,
        'color': color_list,
        'class': flag_list
    })
    df.to_csv("Dataset/5169.csv", index=False)
    print(f"生成结束, 标签保存在Dataset/time.csv, 共计{std_data_cnt + high_data_cnt + low_data_cnt}条，其中标准的有{std_data_cnt}条，超过{high_bound}的有{high_data_cnt}条，低于{low_bound}的有{low_data_cnt}条")
    
    df = pd.read_csv('Dataset/5169.csv')
    X = df.drop('class', axis=1)  # 特征数据
    y = df['class']  # 标签数据
    # 设定测试集比例
    test_size = 0.15  # 测试集比例为15%

    # 使用 train_test_split 划分训练集和测试集，并指定 random_state 保证每次划分一致
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, stratify=y, random_state=42)

    # 将训练集和测试集保存为 CSV 文件，方便以后加载
    train_df = pd.concat([X_train, y_train], axis=1)
    test_df = pd.concat([X_test, y_test], axis=1)

    train_df.to_csv('Dataset/train_dataset.csv', index=False)
    test_df.to_csv('Dataset/test_dataset.csv', index=False)

    print("训练集和测试集已永久保存为 CSV 文件。")