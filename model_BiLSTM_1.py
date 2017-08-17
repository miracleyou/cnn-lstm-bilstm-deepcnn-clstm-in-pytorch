import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
import numpy as np
import random
import torch.nn.init as init

random.seed(1141)
torch.manual_seed(1233)


class BiLSTM_1(nn.Module):
    def __init__(self, args):
        super(BiLSTM_1, self).__init__()
        self.args = args
        self.hidden_dim = args.lstm_hidden_dim
        self.num_layers = args.lstm_num_layers
        V = args.embed_num
        D = args.embed_dim
        C = args.class_num
        if args.max_norm is not None:
            print("max_norm = {} ".format(args.max_norm))
            self.embed = nn.Embedding(V, D, max_norm=args.max_norm)
        else:
            print("max_norm = {} ".format(args.max_norm))
            self.embed = nn.Embedding(V, D)
        if args.word_Embedding:
            pretrained_weight = np.array(args.pretrained_weight)
            self.embed.weight.data.copy_(torch.from_numpy(pretrained_weight))
        self.bilstm = nn.LSTM(D, self.hidden_dim, num_layers=self.num_layers, dropout=args.dropout, bidirectional=True,
                              bias=True)
        print(self.bilstm)
        if args.init_weight:
            print("Initing W .......")
            init.xavier_normal(self.bilstm.all_weights[0][0], gain=np.sqrt(args.init_weight_value))
            init.xavier_normal(self.bilstm.all_weights[0][1], gain=np.sqrt(args.init_weight_value))
            init.xavier_normal(self.bilstm.all_weights[1][0], gain=np.sqrt(args.init_weight_value))
            init.xavier_normal(self.bilstm.all_weights[1][1], gain=np.sqrt(args.init_weight_value))
            # print("self.bilstm.all_weights {} ".format(self.bilstm.all_weights))
            self.bilstm.all_weights[0][3].data[20:40].fill_(1)
            self.bilstm.all_weights[0][3].data[0:20].fill_(0)
            self.bilstm.all_weights[0][3].data[40:80].fill_(0)
            # self.bilstm.all_weights[0][3].data[40:].fill_(0)
            self.bilstm.all_weights[0][2].data[20:40].fill_(1)
            self.bilstm.all_weights[0][2].data[0:20].fill_(0)
            self.bilstm.all_weights[0][2].data[40:80].fill_(0)
            # self.bilstm.all_weights[0][2].data[40:].fill_(0)
            self.bilstm.all_weights[1][3].data[20:40].fill_(1)
            self.bilstm.all_weights[1][3].data[0:20].fill_(0)
            self.bilstm.all_weights[1][3].data[40:80].fill_(0)
            # self.bilstm.all_weights[1][3].data[40:].fill_(0)
            self.bilstm.all_weights[1][2].data[20:40].fill_(1)
            self.bilstm.all_weights[1][2].data[0:20].fill_(0)
            self.bilstm.all_weights[1][2].data[40:80].fill_(0)
            # self.bilstm.all_weights[1][2].data[40:].fill_(0)

        self.hidden2label1 = nn.Linear(self.hidden_dim * 2, self.hidden_dim)
        self.hidden2label2 = nn.Linear(self.hidden_dim, C)
        self.hidden = self.init_hidden(self.num_layers, args.batch_size)
        self.dropout = nn.Dropout(args.dropout)

    def init_hidden(self, num_layers, batch_size):
        # the first is the hidden h
        # the second is the cell  c
        # return (Variable(torch.zeros(2, batch_size, self.hidden_dim // 2)),
        #          Variable(torch.zeros(2, batch_size, self.hidden_dim // 2)))
        return (Variable(torch.zeros(2 * num_layers, batch_size, self.hidden_dim)),
                Variable(torch.zeros(2 * num_layers, batch_size, self.hidden_dim)))

    def forward(self, x):
        embed = self.embed(x)
        x = self.dropout(embed)
        # x = embed.view(len(x), embed.size(1), -1)
        bilstm_out, self.hidden = self.bilstm(x, self.hidden)

        bilstm_out = torch.transpose(bilstm_out, 0, 1)
        bilstm_out = torch.transpose(bilstm_out, 1, 2)
        bilstm_out = F.max_pool1d(bilstm_out, bilstm_out.size(2)).squeeze(2)
        bilstm_out = self.hidden2label1(F.tanh(bilstm_out))
        logit = self.hidden2label2(F.tanh(bilstm_out))
        return logit