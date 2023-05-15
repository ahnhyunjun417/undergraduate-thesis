import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import torchvision
import torchvision.transforms as transforms
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
sys.path.append('../models')
import ResNet as resnet
import DenseNet as densenet
import EfficientNet as efficientnet
import MobileNetV2 as mobilenet
import ViT as vit

os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "2, 3"

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

##########################################
######### Configure Metric Setting ####### 
##########################################
batch_size = 1
weight_path = './weights/ResNet'
model = torch.load(weight_path)
criterion = nn.CrossEntropyLoss()
member_path = '/media/data1/hyunjun/cifar-10/train/'
nonmember_path = '/media/data1/hyunjun/cifar-10/test/'
data = 'ImageNet'
##########################################
##########################################

mean, std = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225) 
if data == 'STL-10':
    mean, std = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)
elif data == 'Cifar-10':
    mean, std = (0.491, 0.482, 0.447), (0.247, 0.243, 0.262)
elif data == 'CelebA':
    mean, std = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)

trans = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean, std),
    transforms.Resize((224, 224)),
])

nonmember_set = torchvision.datasets.ImageFolder(root=nonmember_path, transform=trans)
nonmember_loader = DataLoader(nonmember_set, batch_size=batch_size, shuffle=True, drop_last=False,)
member_set = torchvision.datasets.ImageFolder(root=member_path, transform=trans)
member_loader = DataLoader(member_set, batch_size=batch_size, shuffle=True, drop_last=False,)

classes = nonmember_set.classes

model.to(device)
model.eval()

def softmax_entropy(pred):
    score = pred
    score = np.exp(score) / np.sum(np.exp(score))
    sum = 0.0
    for i in range(len(score)):
        if score[i] != 0:
            sum -= score[i] * np.log2(score[i])
    return sum

def confidence_measure_loop(dataloader):
    model.eval()
    
    conf_entropy = []
    
    with torch.no_grad():
        for X, y in dataloader:
            pred = model(X.to(device))
            pred = torch.argmax(pred, dim=1)
            pred = pred.cpu().numpy()
            for i in range(len(pred)):
                conf_entropy.append(softmax_entropy(pred[i]))
            
    return np.array(conf_entropy)

print("#################################")
print("## Non-member Label resistance ##")
print("#################################")
non_member = confidence_measure_loop(nonmember_loader)

print("#################################")
print("#### member Label resistance ####")
print("#################################")
member = confidence_measure_loop(member_loader)

print(np.mean(non_member), np.var(non_member))
uniques, count = np.unique(non_member, return_counts=True)
count = count / np.sum(count)
plt.hist(non_member, alpha=0.5, density=True)

print(np.mean(member), np.var(member))
uniques, count = np.unique(member, return_counts=True)
count = count / np.sum(count)
plt.hist(member, alpha=0.5, density=True)

plt.show()