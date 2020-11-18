import torch.nn as nn
import torch
import math

class PositionalEncoding(nn.Module):

    def __init__(self, d_model, dropout=0.1, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        # print(div_term.shape)
        # print(pe[:, 1::2].shape[1])
        pe[:, 1::2] = torch.cos(position * div_term[:pe[:, 1::2].shape[1]])
        pe = pe.unsqueeze(0).transpose(0, 1)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)

class TransformerModel(nn.Module):

    def __init__(self, ninp, nhead, nhid, nlayers, dropout=0.5, hidden_size=64):
        super(TransformerModel, self).__init__()
        from torch.nn import TransformerEncoder, TransformerEncoderLayer
        self.model_type = 'Transformer'
        self.linear = nn.Linear(ninp, hidden_size)
        self.src_mask = None
        # self.pos_encoder = PositionalEncoding(ninp, dropout)
        self.pos_encoder = PositionalEncoding(hidden_size, dropout)
        # encoder_layers = TransformerEncoderLayer(ninp, nhead, nhid, dropout)
        encoder_layers = TransformerEncoderLayer(hidden_size, nhead, nhid, dropout)
        self.transformer_encoder = TransformerEncoder(encoder_layers, nlayers)
        # self.decoder = nn.Linear(ninp, 1)
        self.decoder = nn.Linear(hidden_size, 1)



        self.init_weights()

    def _generate_square_subsequent_mask(self, sz):
        mask = (torch.triu(torch.ones(sz, sz)) == 1).transpose(0, 1)
        mask = mask.float().masked_fill(mask == 0, float('-inf')).masked_fill(mask == 1, float(0.0))
        return mask

    def init_weights(self):
        initrange = 0.1
        # self.encoder.weight.data.uniform_(-initrange, initrange)
        self.decoder.bias.data.zero_()
        self.decoder.weight.data.uniform_(-initrange, initrange)

    def forward(self, src):
        src = self.linear(src)
        # src = torch.relu(src)

        if self.src_mask is None or self.src_mask.size(0) != src.size(0):
            device = src.device
            mask = self._generate_square_subsequent_mask(src.size(0)).to(device)
            self.src_mask = mask

        # src = self.encoder(src) * math.sqrt(self.ninp)
        src = src
        src = self.pos_encoder(src)
        output = self.transformer_encoder(src, self.src_mask)
        output = self.decoder(output)
        output = torch.sigmoid(output)
        return output