import torch
import torch.nn as nn
import torch.nn.functional as F
from utils import conv_layer, get_param_size

from collections import OrderedDict



class draft(nn.Module):
	def __init__(self, skipable_layers, out_classes,random = True):
		super(draft,self).__init__()

		self.len_ = skipable_layers
		self.random = random

		self.layerb1_1 = conv_layer(3, 16, kernel_size=3, stride = (1,1), padding=1, max_pool = True)
		self.layerb1_2 = conv_layer(16, 3, kernel_size=1, stride = (1,1), padding=0)
		self.layerb1_3 = conv_layer(3, 32, kernel_size=3, stride = (1,1), padding=1,max_pool = True)
		self.drop_layer1 = nn.Dropout(0.25)
		
		self.layerb3_1 = conv_layer(32, 64, kernel_size=3, stride = (1,1), padding=1)
		self.drop_layer3 = nn.Dropout(0.25)

		self.layerb4_1 = conv_layer(64, 32, kernel_size=1, stride = (1,1), padding=0)
		self.layerb4_2 = conv_layer(32, 256, kernel_size=3, stride = (1,1), padding=1)
		self.drop_layer4 = nn.Dropout(0.25)

		
		skip = []

		for i in range(0,self.len_):
			skip.append((str(i),nn.Sequential(conv_layer(256, 256, kernel_size = 3, stride = (1,1), padding = 1)
				,nn.Dropout(0.5))))

		self.skip = nn.Sequential(OrderedDict(skip))
 		
		self.after_skip = nn.Sequential(conv_layer(256, 512, kernel_size=3, stride = (2,2), padding=1, max_pool = True)
						  ,nn.Dropout(0.1)
						  ,conv_layer(512, 512, kernel_size=3, stride = (2,2), padding=1, max_pool = True)
						  ,nn.Dropout(0.1)
						  ,conv_layer(512, 1024, kernel_size=3, stride = (1,1), padding=1)
						  ,nn.Dropout(0.1))


		# self.fc1 = nn.Sequential(nn.Linear(1024, 1024),
		# 						 nn.ReLU6(True))
		# self.fc1_drop = nn.Dropout(0.5)
		self.fc2 = nn.Linear(1024, out_classes)
		
	def forward(self, input, device_ = "cpu", baseline = True, temp_ = 0, brain = None):
		x = self.layerb1_1(input)
		x = self.layerb1_2(x)
		x = self.layerb1_3(x)
		x = self.drop_layer1(x)

		x = self.layerb3_1(x)
		x = self.drop_layer3(x)

		x = self.layerb4_1(x)
		x = self.layerb4_2(x)
		x = self.drop_layer4(x)

		# y = torch.cat((x_1.clone().detach(),x.clone().detach()),1)
		out_ = []
			

		if baseline == True:

			for cnn in self.skip:
				x = cnn(x)

		elif self.random == True:
			for i, cnn in enumerate(self.skip, 1):
				if i <= temp_ :
					x = cnn(x)
				else: break
		elif self.random == False:
			# input_ shape is [batch_size, 3, 224,224]
			input_ = F.max_pool2d(input.clone().detach(),(2,2))
			# input_ shape is [batch_size, 3, 112,112]
			input_ = input_.to(device)

			print("using brain")
			for i, cnn in enumerate(self.skip):
				if i%2 == 0:
					x_ = x.clone().detach()
					x_ = x_.to(device_)
					# x_ shape is [batch_size, 256, 112, 112]
					surety = brain(input_, x_)
					out_.append(surety)
					# print(surety.item())
					if surety.item()  <= 0.5:
						x = cnn(x)
					else: break
			# exit()
		x = self.after_skip(x)
		
		m =  nn.AvgPool2d((x.size()[2],x.size()[3]),stride = 1)
		x = m(x)
		x = x.view(-1, self.num_flat_features(x))

		# x = self.fc1(x)
		# x = self.fc1_drop(x)
		x = self.fc2(x)

		return x, out_

	def num_flat_features(self, x):
		size = x.size()[1:]  # all dimensions except the batch dimension
		num_features = 1
		for s in size:
		    num_features *= s
		return num_features


