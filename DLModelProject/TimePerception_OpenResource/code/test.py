import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from model import TransformerClassifier
from dataloader import TripletDataloader
from torch.nn.utils.rnn import pad_sequence, pack_padded_sequence
import torch.nn.functional as F
import os
from sklearn.metrics import f1_score, recall_score

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


device = torch.device("cuda:1" if torch.cuda.is_available() else "cpu")
test_dataset = TripletDataloader("/code/Dataset/test_dataset.csv")

torch.manual_seed(777)



test_batch_size = 24
test_dataloader = DataLoader(test_dataset, batch_size=test_batch_size, shuffle=False, collate_fn=custom_collate_fn)

eeg_input_size = 39  
ppg_input_size = 13   
model = TransformerClassifier(eeg_input_size, ppg_input_size).to(device)

model_filename = "/TimeP/best_model/"
model.load_state_dict(torch.load(model_filename))
model.eval()  


criterion = nn.CrossEntropyLoss()


test_loss = 0
correct = 0
total = 0
all_labels = []
all_predictions = []
with torch.no_grad():
    for eeg_feature, ppg_feature, label in test_dataloader:
        eeg_feature = eeg_feature.to(device)
        ppg_feature = ppg_feature.to(device)
        label = label.to(device)

        outputs = model(eeg_feature, ppg_feature)
        loss = criterion(outputs, label)
        test_loss += loss.item()

        _, predicted = torch.max(outputs, 1)


        all_labels.extend(label.cpu().numpy())
        all_predictions.extend(predicted.cpu().numpy())

        total += label.size(0)
        correct += (predicted == label).sum().item()

avg_test_loss = test_loss / len(test_dataloader)
accuracy = 100 * correct / total
print(f'Test Loss: {avg_test_loss:.4f}, Accuracy: {accuracy:.2f}%')
macro_f1 = f1_score(all_labels, all_predictions, average='macro')
uac = recall_score(all_labels, all_predictions, average='macro')
print(f'Macro F1 Score: {macro_f1:.4f}')
print(f'UAC (Macro Recall): {uac:.4f}')
