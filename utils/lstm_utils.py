## EEG classification utilities for LSTM
# Author: B. Himmetoglu
# 7/26/2017

import numpy as np
from scipy.io import loadmat

## Construct LSTM seuqnces from one segment
def lstm_sequence(input_segment, target, sampling_freq, window, stride, block_s = 60):
	""" Function for generating blocks of LSTM input tensors 
        input_segment : The EEG segment
        target        : 1/0 (preictal/interictial)
        sampling_freq : Samplig frequency
        window        : Window size for 1d convolutions on each block
        stride        : Stride size of the 1d convolution
        block_s       :ize of the block in seconds (default = 60)
	"""

	# Dimensions
	n_channels, T_segment = input_segment.shape

	# Determine block dimensions
	block_len = sampling_freq * block_s   # Length of each block 
	n_blocks = (T_segment-1) // block_len # Number of blocks
	blocks = [block for block in range(0,(n_blocks+1)*block_len,block_len)]

	# Determine the sequence length for LSTM
	div = (block_len - window)%stride
	if (div != 0):
		pad = stride - div # Size of padding neded
	else:
		pad = 0

	seq_len = (block_len + pad - window) // stride

	# Initiate tensor
	X = np.zeros((n_blocks, seq_len, n_channels))

	# Loop over blocks and fill X
	for ib in range(n_blocks):
		# Get block
		data_block = input_segment[:, blocks[ib]:blocks[ib+1]]

		# Pad if necessary
		if (pad !=0):
			data_block = np.concatenate((data_block, np.zeros((n_channels, pad))), axis=1)

		# 1d convolution by mean
		index = 0
		for j in range(seq_len):
			X[ib, j, :] = np.mean(data_block[:, (index+j):(index+j+seq_len)], axis = 1)

	# Fill in the target
	if (target == 1):
		Y = np.ones(n_blocks)
	else:
		Y = np.zeros(n_blocks)

	# Return
	return X, Y

## Collect all the segments to build a tesnsor input for LSTM. Uses the function lstm_sequence1971
def lstm_build_input(clips, target, window, stride, n_channels = 16, block_s = 60):
	""" Collect all the data and build sequences for LSTM
	.......
	"""

	# Number of clips
	n_clips = len(clips)

	# Loop over all clips and store data
	iclip = 0
	for fil in clips:
		clip = loadmat(fil)
		segment_name = list(clip.keys())[3] # Get segment name
		input_segment = clip[segment_name][0][0][0] # Get electrode data
		sampling_freq = np.squeeze(clip[segment_name][0][0][1]) # Sampling frequency

		if (clip[segment_name][0][0][0].shape[0] != n_channels):
			raise ValueError('Wrong number of channels!')

		# Get tensor input and targets from blocks
		X, Y = lstm_sequence(input_segment, target, sampling_freq, window, stride, block_s)

		# Concatenate the tensor and target vector
		if (iclip == 0):
			X_train = X
			Y_train = Y[:,None]
		else:
			X_train = np.vstack((X_train,X))
			Y_train = np.vstack((Y_train,Y[:,None]))

		iclip +=1

	# Return
	return X_train, Y_train
