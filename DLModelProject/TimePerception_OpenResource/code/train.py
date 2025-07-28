from model import TransformerClassifier
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, random_split, Subset
from dataloader import TripletDataloader
import os
from torch.nn.utils.rnn import pad_sequence, pack_padded_sequence
from sklearn.model_selection import KFold
import numpy as np
from datetime import datetime 
from sklearn.metrics import f1_score, recall_score
from focal_loss import FocalLoss

def custom_collate_fn(batch):

    eeg_features = [item[0] for item in batch]
    ppg_features = [item[1] for item in batch]
    labels = [item[2] for item in batch]

    eeg_lengths = [eeg.size(0) for eeg in eeg_features]
    ppg_lengths = [ppg.size(0) for ppg in ppg_features]


    max_seq_len = max(max(eeg_lengths), max(ppg_lengths))

    padded_eeg_features = [F.pad(eeg, (0, 0, 0, max_seq_len - eeg.size(0))) for eeg in eeg_features]
    padded_ppg_features = [F.pad(ppg, (0, 0, 0, max_seq_len - ppg.size(0))) for ppg in ppg_features]


    padded_eeg_features = torch.stack(padded_eeg_features)
    padded_ppg_features = torch.stack(padded_ppg_features)


    
    padded_eeg_features = padded_eeg_features.transpose(1, 2)
    padded_ppg_features = padded_ppg_features.transpose(1, 2)

    labels_tensor = torch.tensor(labels)


    return padded_eeg_features, padded_ppg_features, labels_tensor

def interploate_collate_fn(batch):

    eeg_features = [item[0] for item in batch]
    ppg_features = [item[1] for item in batch]
    labels = [item[2] for item in batch]


    target_seq_len = 512

    interpolated_eeg_features = [F.interpolate(eeg.unsqueeze(0).transpose(1, 2), size=target_seq_len, mode='linear', align_corners=False).squeeze(0).transpose(0, 1) for eeg in eeg_features]
    
    interpolated_ppg_features = [F.interpolate(ppg.unsqueeze(0).transpose(1, 2), size=target_seq_len, mode='linear', align_corners=False).squeeze(0).transpose(0, 1) for ppg in ppg_features]

    interpolated_eeg_features = torch.stack(interpolated_eeg_features)
    interpolated_ppg_features = torch.stack(interpolated_ppg_features)

    interpolated_eeg_features = interpolated_eeg_features.transpose(1, 2)
    interpolated_ppg_features = interpolated_ppg_features.transpose(1, 2)

    labels_tensor = torch.tensor(labels)

    return interpolated_eeg_features, interpolated_ppg_features, labels_tensor

os.chdir(os.path.dirname(os.path.abspath(__file__)))


torch.manual_seed(777)

eeg_input_size = 39  
ppg_input_size = 13  
num_epochs = 300
train_batch_size = 24
val_batch_size = 24
learning_rate = 0.00005
patience = 40 

dataset = TripletDataloader("/TimeP/code/Dataset/train_dataset.csv")


best_val_loss = float('inf')
best_model_state = None
early_stop_counter = 0  


train_size = int(0.8 * len(dataset))
val_size = len(dataset) - train_size
train_dataset, val_dataset = random_split(dataset, [train_size, val_size])


train_dataloader = DataLoader(train_dataset, batch_size=train_batch_size, shuffle=True, collate_fn=custom_collate_fn)
val_dataloader = DataLoader(val_dataset, batch_size=val_batch_size, shuffle=False, collate_fn=custom_collate_fn)


device = torch.device("cuda:1" if torch.cuda.is_available() else "cpu")
model = TransformerClassifier(eeg_input_size, ppg_input_size).to(device)


criterion = nn.CrossEntropyLoss()

optimizer = optim.Adam(model.parameters(), lr=learning_rate, weight_decay=5e-4)


for epoch in range(num_epochs):
    model.train() 
    for eeg_feature, ppg_feature, label in train_dataloader:
        optimizer.zero_grad()

        eeg_feature = eeg_feature.to(device)
        ppg_feature = ppg_feature.to(device)
        label = label.to(device)

        outputs = model(eeg_feature, ppg_feature)
        loss = criterion(outputs, label)

        loss.backward()
        optimizer.step()

        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')
    

    model.eval()
    val_loss = 0
    correct = 0
    total = 0
    all_labels = []
    all_predictions = []
    with torch.no_grad(): 
        for eeg_feature, ppg_feature, label in val_dataloader:

            eeg_feature = eeg_feature.to(device)
            ppg_feature = ppg_feature.to(device)
            label = label.to(device)

            outputs = model(eeg_feature, ppg_feature)
            loss = criterion(outputs, label)
            val_loss += loss.item()

            _, predicted = torch.max(outputs, 1)

            all_labels.extend(label.cpu().numpy())
            all_predictions.extend(predicted.cpu().numpy())

            total += label.size(0)
            correct += (predicted == label).sum().item()

    avg_val_loss = val_loss / len(val_dataloader)
    accuracy = 100 * correct / total
    print(f'Epoch [{epoch+1}/{num_epochs}], Validation Loss: {avg_val_loss:.4f}, Validation Accuracy: {accuracy:.2f}%')

    macro_f1 = f1_score(all_labels, all_predictions, average='macro')
    uac = recall_score(all_labels, all_predictions, average='macro')
    print(f'Macro F1 Score: {macro_f1:.4f}')
    print(f'UAC (Macro Recall): {uac:.4f}')

    if avg_val_loss < best_val_loss:
        best_val_loss = avg_val_loss
        best_model_state = model.state_dict()  
        early_stop_counter = 0 
        get_best_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        model_filename = f"../best_model/{best_val_loss:.4f}_{get_best_time}.pkl"
    else:
        early_stop_counter += 1
        print(f"Early stopping counter: {early_stop_counter}/{patience}")

    if early_stop_counter >= patience:
        print(f"Early stopping at epoch {epoch+1}")
        break

if best_model_state is not None:
    torch.save(best_model_state, model_filename)
    print(f"Best model saved with validation loss: {best_val_loss:.4f}")


