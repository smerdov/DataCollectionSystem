import torch
import torch.nn as nn
from config import *


input_size = len(columns_order)


class Predictor(nn.Module):

    def __init__(self, hidden_size=16, n_lstm_layers=2, n_linear_layers=1, batch_size=1):
        super().__init__()
        self.lstm = nn.LSTM(input_size=input_size, hidden_size=hidden_size, num_layers=n_lstm_layers)
        self.linear_0 = nn.Linear(hidden_size, 1)
        self.batch_size = batch_size
        self.hidden_size = hidden_size
        self.n_lstm_layers = n_lstm_layers
        self.n_linear_layers = n_linear_layers

        self._init_linear_layers()


    def forward(self, x):
        # x, (self.hidden, self.cell) = self.lstm(x, (self.hidden, self.cell))
        # lstm_output, (self.hidden, self.cell) = self.lstm(x, (self.hidden, self.cell))
        lstm_output, (self.hidden, self.cell) = self.lstm(x)
        self.hidden = self.hidden.detach()
        self.hidden = self.cell.detach()
        # output = self.linear_0(self.hidden)
        # output = self.linear_0(lstm_output.detach())
        # output = torch.sigmoid(output)
        # output = self._linear_layer_forward(lstm_output.detach())  # Are you ok?
        output = self._linear_layer_forward(lstm_output)

        return output

    def reset_hidden(self):
        self.hidden = torch.zeros((self.n_lstm_layers, self.batch_size, self.hidden_size))
        self.cell = torch.zeros((self.n_lstm_layers, self.batch_size, self.hidden_size))


    def _init_linear_layers(self):
        for n_linear_layer in range(self.n_linear_layers):
            if n_linear_layer < self.n_linear_layers - 1:
                new_layer = nn.Linear(self.hidden_size, self.hidden_size)
            else:
                new_layer = nn.Linear(self.hidden_size, 1)

            setattr(self, f'linear_{n_linear_layer}', new_layer)


    def _linear_layer_forward(self, x):
        for n_linear_layer in range(self.n_linear_layers):
            new_layer = getattr(self, f'linear_{n_linear_layer}')
            x = new_layer(x)

            if n_linear_layer < self.n_linear_layers - 1:
                x = torch.relu(x)
            else:
                x = torch.sigmoid(x)

        return x
