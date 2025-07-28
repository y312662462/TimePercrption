import torch
import torch.nn as nn

class EEGFeatureExtractor(nn.Module):
    def __init__(self, eeg_input_size, dropout=0.5):
        super(EEGFeatureExtractor, self).__init__()
        self.conv1 = nn.Conv1d(eeg_input_size, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(64, 128, kernel_size=3, padding=1)

        self.pool = nn.MaxPool1d(2)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)

    
    def forward(self, x):

        x = self.conv1(x)
        x = self.relu(x)
        x = self.pool(x)
        x = self.conv2(x)
        x = self.relu(x)
        x = self.pool(x)
        x = self.dropout(x)
        return x

class PPGFeatureExtractor(nn.Module):
    def __init__(self, ppg_input_size, dropout=0.5):
        super(PPGFeatureExtractor, self).__init__()
        self.conv1 = nn.Conv1d(ppg_input_size, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(64, 128, kernel_size=3, padding=1)
        self.pool = nn.MaxPool1d(2)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        x = self.conv1(x)
        x = self.relu(x)
        x = self.pool(x)
        x = self.conv2(x)
        x = self.relu(x)
        x = self.pool(x)
        x = self.dropout(x)
        return x
    
class Extractor(nn.Module):
    def __init__(self, eeg_input_size, dropout=0.5):
        super(Extractor, self).__init__()
        self.conv1 = nn.Conv1d(eeg_input_size, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(64, 128, kernel_size=3, padding=1)
        self.pool = nn.MaxPool1d(2)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)

    
    def forward(self, x):
        x = self.conv1(x)
        x = self.relu(x)
        x = self.pool(x)
        x = self.conv2(x)
        x = self.relu(x)
        x = self.pool(x)
        x = self.dropout(x)
        return x
    
class ZeiExtractor(nn.Module):
    def __init__(self):
        super(ZeiExtractor, self).__init__()
        self.num_colors = 3
        self.num_music = 3
        self.num_task = 2
        self.embed_dim = 4


        self.color_embed = nn.Embedding(self.num_colors, self.embed_dim)  
        self.music_embed = nn.Embedding(self.num_music, self.embed_dim)  
        self.task_embed = nn.Embedding(self.num_task, self.embed_dim)  
    
    def forward(self, color, music, task):

        color_embed = self.color_embed(color.long()) 
        music_embed = self.music_embed(music.long()) 
        task_embed = self.task_embed(task.long())     

        color_embed = color_embed.permute(0, 2, 1) 
        music_embed = music_embed.permute(0, 2, 1) 
        task_embed = task_embed.permute(0, 2, 1)   


        x = torch.cat([color_embed, music_embed, task_embed], dim=1) 

        return x


class TransformerClassifier(nn.Module):
    def __init__(self, eeg_input_size, ppg_input_size, num_classes=3, d_model=128, nhead=4, num_layers=2, dropout=0.5):
        super(TransformerClassifier, self).__init__()

        self.eeg_extractor = EEGFeatureExtractor(eeg_input_size, dropout)
        self.ppg_extractor = PPGFeatureExtractor(ppg_input_size, dropout)
        self.extractor = Extractor(eeg_input_size + ppg_input_size, dropout)

        self.transformer_encoder = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, dropout=dropout),
            num_layers=num_layers
        )

        self.fc = nn.Linear(d_model, num_classes)

        self.hidden_layer = nn.Linear(d_model, 64)
        self.output_layer = nn.Linear(64, num_classes)

        self.cnn = Extractor(d_model, dropout)


        self.lstm = nn.LSTM(input_size=d_model, hidden_size=d_model, num_layers=2, batch_first=True, dropout=dropout)


        self.bilstm = nn.LSTM(
            input_size=d_model, 
            hidden_size=d_model, 
            num_layers=2, 
            batch_first=True, 
            dropout=dropout,
            bidirectional=True 
        )

        self.bifc = nn.Linear(d_model * 2, num_classes)  

        self.zei_emb = ZeiExtractor()



    def forward_transformer(self, eeg_data, ppg_data):

        ppg_channels = torch.unbind(ppg_data, dim=1)  
        hr = ppg_channels[0]
        combined_zei = self.zei_emb(ppg_channels[1], ppg_channels[2], ppg_channels[3])
        

        combined_features = self.extractor(torch.cat((eeg_data, hr.unsqueeze(1), combined_zei), dim = 1)).transpose(1, 2)

        transformer_output = self.transformer_encoder(combined_features)

        transformer_output = transformer_output.mean(dim=1)

        output = self.hidden_layer(transformer_output)
        output = self.output_layer(output)
        return output


    def forward_cnn(self, eeg_data, ppg_data):
        ppg_channels = torch.unbind(ppg_data, dim=1)  
        hr = ppg_channels[0]
        combined_zei = self.zei_emb(ppg_channels[1], ppg_channels[2], ppg_channels[3])
        combined_features = self.extractor(torch.cat((eeg_data, hr.unsqueeze(1), combined_zei), dim = 1))

        combined_features = self.cnn(combined_features)
        output = self.hidden_layer(combined_features.mean(dim=2))
        output = self.output_layer(output)
        return output
    

    def forward_lstm(self, eeg_data, ppg_data):
        combined_features = self.extractor(torch.cat((eeg_data, ppg_data), dim=1)).transpose(1, 2)
        lstm_output, (hn, cn) = self.lstm(combined_features)
        lstm_output = lstm_output[:, -1, :]
        output = self.fc(lstm_output)
        return output

    def biforward_lstm(self, eeg_data, ppg_data):
        ppg_channels = torch.unbind(ppg_data, dim=1)  
        hr = ppg_channels[0]
        combined_zei = self.zei_emb(ppg_channels[1], ppg_channels[2], ppg_channels[3])
        combined_features = self.extractor(torch.cat((eeg_data, hr.unsqueeze(1), combined_zei), dim = 1)).transpose(1, 2)

        lstm_output, (hn, cn) = self.bilstm(combined_features)

        lstm_output = torch.cat((hn[-2], hn[-1]), dim=1) 

        output = self.bifc(lstm_output)
        return output
    
    def forward(self, eeg_data, ppg_data, mode='bilstm'):
        if mode == 'transformer':
            return self.forward_transformer(eeg_data, ppg_data)
        elif mode == 'lstm':
            return self.forward_lstm(eeg_data, ppg_data)
        elif mode == 'bilstm':
            return self.biforward_lstm(eeg_data, ppg_data)
        else:  # 默认使用 CNN
            return self.forward_cnn(eeg_data, ppg_data)


