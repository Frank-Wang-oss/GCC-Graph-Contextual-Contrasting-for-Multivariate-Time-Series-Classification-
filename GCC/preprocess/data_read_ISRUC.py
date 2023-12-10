import numpy as np
import scipy.io as scio
from os import path
from scipy import signal
import torch
import os


path_Extracted = './data/ISRUC_S3/ExtractedChannels/'
path_RawData   = './data/ISRUC_S3/RawData/'
path_output    = './data/ISRUC_S3/'
channels = ['C3_A2', 'C4_A1', 'F3_A2', 'F4_A1', 'O1_A2', 'O2_A1',
            'LOC_A2', 'ROC_A1','X1', 'X2']


def read_psg(path_Extracted, sub_id, channels, resample=3000):
    psg = scio.loadmat(path.join(path_Extracted, 'subject%d.mat' % (sub_id)))
    psg_use = []
    for c in channels:
        psg_use.append(
            np.expand_dims(signal.resample(psg[c], resample, axis=-1), 1))
    psg_use = np.concatenate(psg_use, axis=1)
    return psg_use


def read_label(path_RawData, sub_id, ignore=30):
    label = []
    with open(path.join(path_RawData, '%d/%d_1.txt' % (sub_id, sub_id))) as f:
        s = f.readline()
        while True:
            a = s.replace('\n', '')
            label.append(int(a))
            s = f.readline()
            if s == '' or s == '\n':
                break
    return np.array(label[:-ignore])


'''
output:
    save to $path_output/ISRUC_S3.npz:
        Fold_data:  [k-fold] list, each element is [N,V,T]
        Fold_label: [k-fold] list, each element is [N,C]
        Fold_len:   [k-fold] list
'''

fold_label = []
fold_psg = []
fold_len = []

for sub in range(1, 11):
    print('Read subject', sub)
    label = read_label(path_RawData, sub)
    psg = read_psg(path_Extracted, sub, channels)
    print('Subject', sub, ':', label.shape, psg.shape)
    assert len(label) == len(psg)

    # in ISRUC, 0-Wake, 1-N1, 2-N2, 3-N3, 5-REM
    label[label==5] = 4  # make 4 correspond to REM
    fold_label.append(np.eye(5)[label])
    fold_psg.append(psg)
    fold_len.append(len(label))
print('Preprocess over.')



data = np.concatenate(fold_psg, 0)
label = np.concatenate(fold_label, 0)
label = np.argmax(label,-1)
# print(data)
print(list(label))
data_idx = np.arange(data.shape[0])

np.random.shuffle(data_idx)

data = data[data_idx]
label = label[data_idx]
# print(data.shape)
num_train = int(0.8*data.shape[0])

data = torch.from_numpy(data).float()
label = torch.from_numpy(label).long()

data_train = data[:num_train]
label_train = label[:num_train]

data_test = data[num_train:]
label_test = label[num_train:]



torch.save({'samples':data_train, 'labels':label_train}, os.path.join('ISRUC', 'train.pt'))
torch.save({'samples':data_test, 'labels':label_test}, os.path.join('ISRUC', 'test.pt'))
