import numpy as np
from torch.utils.data import Dataset
import torch
import pandas as pd
import ast

def safe_literal_eval(data):
    try:
       
        if isinstance(data, list):
            return data
        return ast.literal_eval(data)
    except ValueError as e:
        print(f"Error parsing data: {data}")
        raise e  

def load_dataset(dataset_csv_path):
    print("loading data...")
    dataset_df = pd.read_csv(dataset_csv_path)
    dataset_dic = dataset_df.to_dict(orient='list')
    eeg_data_list = []
    ppg_data_list = []
    task_data_list = []
    color_data_list = []
    music_data_list = []
    label_list = []
    debug_list = []
    dataset_size = len(dataset_df)
    for i in range(0, dataset_size):

        eeg_data_list.append(pd.read_csv(dataset_dic["eeg"][i]).to_dict(orient='list'))
        ppg_data_list.append(pd.read_csv(dataset_dic["ppg"][i]).to_dict(orient='list'))
        if len(pd.read_csv(dataset_dic["eeg"][i]).to_dict(orient='list')['meditation']) < 100:
            print(len(pd.read_csv(dataset_dic["eeg"][i]).to_dict(orient='list')['meditation']))
        task_data_list.append(dataset_dic["task"][i])
        color_data_list.append(dataset_dic['color'][i])
        music_data_list.append(dataset_dic['music'][i])
        label_list.append(dataset_dic["class"][i])
        debug_list.append(dataset_dic["name"][i])
    print(f"dataset size: {dataset_size}")

    return eeg_data_list, ppg_data_list, task_data_list, color_data_list, music_data_list, label_list, debug_list


class TripletDataloader(Dataset):
    def __init__(self, dataset_csv_path):
        self.dataset_csv_path = dataset_csv_path
        self.eeg_data_list, self.ppg_data_list, self.task_data_list, self.color_data_list, self.music_data_list, self.label_list, self.debug_list = load_dataset(self.dataset_csv_path)

    def get_eeg_data(self, item):
        eeg_data_dict = self.eeg_data_list[item]

        eeg_data_dict['data'] = [safe_literal_eval(x) for x in eeg_data_dict['data']]

  
        features = [eeg_data_dict[key] for key in ['meditation', 'stress', 'drowsiness', 'awareness', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']]

        raw_data = eeg_data_dict['data']  
        time_values = eeg_data_dict['time']  

        features_tensor = torch.tensor(features, dtype=torch.float32)
        features_permuted = features_tensor.permute(1, 0)
        time_tensor = torch.tensor(time_values, dtype=torch.float32).unsqueeze(1)


        raw_data_tensor = torch.tensor(raw_data, dtype=torch.float32)


        features_norm = self.norm(features_permuted)
        raw_data_norm = self.norm(raw_data_tensor)
        time_norm = self.norm(time_tensor)

        combined_tensor = torch.cat((features_norm, raw_data_norm), dim=1)


        return combined_tensor
    
    def get_ppg_data(self, item):
        ppg_data_dict = self.ppg_data_list[item]
        condition = self.task_data_list[item]
        color = self.color_data_list[item]
        music = self.music_data_list[item]

        hr_values = ppg_data_dict['hr']
        time_values = ppg_data_dict['time'] 
        condition_values = np.full_like(hr_values, condition)
        color_values = np.full_like(hr_values, color)
        music_values = np.full_like(hr_values, music)

        hr_tensor = torch.tensor(hr_values, dtype=torch.float32).unsqueeze(1)
        time_tensor = torch.tensor(time_values, dtype=torch.float32).unsqueeze(1)
        condition_tensor = torch.tensor(condition_values, dtype=torch.float32).unsqueeze(1)
        color_tensor = torch.tensor(color_values, dtype=torch.float32).unsqueeze(1)
        music_tensor = torch.tensor(music_values, dtype=torch.float32).unsqueeze(1)


        hr_norm = self.norm(hr_tensor)
        time_norm = self.norm(time_tensor)

        combined_tensor = torch.cat((hr_norm, color_tensor, music_tensor, condition_tensor), dim=1)

        return combined_tensor
    
    def get_label(self, item):
        label = self.label_list[item]
        label_tensor = torch.tensor(label)
        return label_tensor
    
    def z_score_norm(self, data):
        mean = torch.mean(data, dim=0, keepdim=True)
        std = torch.std(data, dim=0, keepdim=True)
        data_normalized = (data - mean) / std
        return data_normalized

    def norm(self, data):
        min_val = torch.min(data, dim=0, keepdim=True).values
        max_val = torch.max(data, dim=0, keepdim=True).values
        data_normalized = (data - min_val) / (max_val - min_val)
        return data_normalized
    
    def debug(self, item):
        print(self.debug_list[item])

    def __getitem__(self, item):

        eeg_feature = self.get_eeg_data(item)
        ppg_feature = self.get_ppg_data(item)
        label = self.get_label(item)

        return eeg_feature, ppg_feature, label

    def __len__(self):
        return len(self.eeg_data_list)

