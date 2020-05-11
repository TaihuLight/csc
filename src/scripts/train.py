import os
import sys
sys.path.insert(0, os.path.abspath('../../.'))
from tqdm import tqdm
import torch
from src.model.SparseNet import SparseNet
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from src.model.ImageDataset import NatPatchDataset
from src.utils.cmd_line import parse_args
from src.scripts.plotting import plot_rf


# save to tensorboard
arg = parse_args()
board = SummaryWriter(f"../../runs/{arg.session_name}")
# if use cuda
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# create net
sparse_net = SparseNet(arg.n_neuron, arg.kernel_size, arg.stride_size, R_lr=arg.r_learning_rate, lmda=arg.reg, device=device)
# load data
dataloader = DataLoader(NatPatchDataset(2000, arg.img_size, arg.img_size), batch_size=arg.batch_size)
# train
optim = torch.optim.SGD([{'params': sparse_net.U.weight, "lr": arg.learning_rate}])
for e in tqdm(range(arg.epoch), desc="Epoch", total=arg.epoch):
    running_loss = 0
    c = 0
    for img_batch in tqdm(dataloader, desc='training', total=len(dataloader)):
        img_batch = img_batch.reshape(img_batch.shape[0], 1, arg.img_size, arg.img_size).to(device)
        # update
        pred = sparse_net(img_batch)
        loss = ((img_batch - pred) ** 2).sum()
        running_loss += loss.item()
        loss.backward()
        # update U
        optim.step()
        # zero grad
        sparse_net.zero_grad()
        # norm
        sparse_net.normalize_weights()
        c += 1
    board.add_scalar('Loss', running_loss / c, e * len(dataloader) + c)
    if e % 5 == 4:
        # plotting
        fig = plot_rf(sparse_net.U.weight.reshape(arg.n_neuron, arg.kernel_size, arg.kernel_size).cpu().data.numpy(), arg.n_neuron, arg.kernel_size)
        board.add_figure('RF', fig, global_step=e * len(dataloader) + c)
    if e % 10 == 9:
        # save checkpoint
        torch.save(sparse_net, f"../../trained_models/ckpt-{e+1}.pth")
torch.save(sparse_net, f"../../trained_models/ckpt-{e+1}.pth")
