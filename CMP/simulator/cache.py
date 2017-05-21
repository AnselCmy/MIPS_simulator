from math import *
from global_declare import *
import numpy as np

class Cache(object):
	'''
	Attribute:
		total_size: 		The total size of the cache, by byte
		block_size: 		The size of one block, any data stored in cache must be one integral block
		asc:        		The associate of this cache
		block_num:  		The total number of the block
		set_num:    		The total number of the set in this cache
		cache_list: 		The entity of this cache, like [ [['0', '1'] , ['0', '1']], [['0', '1'], ['0', '1']], ... ...]
							idx 0 is the tag which is a part of the PA, idx 1 is the real data
		bit_pseudo_record:  The record of the bit pseudo, like [ [0, 0, ...], [0, 0, ...], ... ...]
		valid_bit:			The valid bit list just like bit_pseudo_record, by int 
		offset_bit_num:		The number of the bit present the offset in one block in the PA
		index_bit_num:		The number of the bit present the index in the PA
	'''
	def __init__(self, total_size, block_size, asc):
		super(Cache, self).__init__()
		self.total_size = total_size
		self.block_size = block_size
		self.asc = asc
		self.build_cache()
		
	def build_cache(self):
		# The number of the block
		self.block_num = int(self.total_size / self.block_size)
		# The number of the set if not one-way associative
		self.set_num = int(self.block_num / self.asc)
		
		# self.cache_list = [[['0', '1']]*self.asc]*self.set_num
		# self.cache_list = np.zeros((self.set_num, self.asc, 2))
		self.cache_list = [[['0', '0'] for i in range(self.asc)] for j in range(self.set_num)]
		# self.bit_pseudo_record = [[0]*self.asc]*self.set_num
		self.bit_pseudo_record = [[0 for i in range(self.asc)] for j in range(self.set_num)]
		self.valid_bit = [[0 for i in range(self.asc)] for j in range(self.set_num)]
		self.dirty_bit = [[0 for i in range(self.asc)] for j in range(self.set_num)]

		# The number of offset bit
		self.offset_bit_num = int(log(self.block_size, 2))
		# The number of index bit 
		self.index_bit_num = int(log(self.set_num, 2))

	def locate(self, PA_bin):
		'''Locate the PA_bin location in the cache
		Args:
			PA_bin: The physical address which is 32 bits bin string format
					and the length of PA also controled by page_size and mem_size which is signed by programming
		Returns:
			The index of the set which can used by self.cache_list[set_idx] to get the set
		'''
		
		# block_address = int(floor(int(PA_bin, 2) / self.block_size))
		# set_idx = block_address % self.set_num
		
		offset = self.offset_bit_num
		idx = self.index_bit_num
		if idx != 0:
			set_idx = int(PA_bin[-(offset+idx): -offset], 2)
		else:
			set_idx = 0
		# print('set_idx', set_idx)
		return set_idx

	def bit_pseudo_add(self, set_idx, idx):
		self.bit_pseudo_record[set_idx][idx] = 1
		self.bit_pseudo_record[set_idx] = self.bit_pseudo_reverse_check(self.bit_pseudo_record[set_idx], idx)

	def bit_pseudo_by_PA(self, PA_bin):
		set_idx = self.locate(PA_bin)
		tag_bit_num = len(PA_bin) - self.offset_bit_num - self.index_bit_num
		for i, b in enumerate(self.cache_list[set_idx]):
			if b[0] == PA_bin[:tag_bit_num] and self.valid_bit[set_idx][i] == 1:
				self.bit_pseudo_add(set_idx, i)

	def find(self, PA_bin):
		'''Find if there exist the PA_bin block in this cache 
		Args:
			PA_bin: The physical address
		Returns:
			If exist, return true means hit, 
			while false and return the PA_bin for grabing data from mem(next stage if fault)
		'''
		# Locate the index of the set first
		set_idx = self.locate(PA_bin)
		# Compute the number of bit present tag
		tag_bit_num = len(PA_bin) - self.offset_bit_num - self.index_bit_num
		# Search in one set, fully search
		for i, b in enumerate(self.cache_list[set_idx]):
			if b[0] == PA_bin[:tag_bit_num] and self.valid_bit[set_idx][i] == 1: 
				return [True, PA_bin]
		return [False, PA_bin]

	def bit_pseudo_reverse_check(self, bit_list, idx):
		if (not 0 in bit_list):
			bit_list = [0]*len(bit_list)
			bit_list[idx] = 1
		return bit_list

	def get_replace_idx(self, set_idx):
		if self.asc == 1:
			return 0
		else:
			try:
				idx = self.valid_bit[set_idx].index(0)
				return idx
			except ValueError:
				# print(self.bit_pseudo_record)
				idx = self.bit_pseudo_record[set_idx].index(0)
				# bit_pseudo_reverse_check(self.bit_pseudo_record[set_idx], idx)
				return idx

	# We discard the index 1 in cache_list, cause the data is no need to use 
	def insert(self, PA_bin):
		set_idx = self.locate(PA_bin)
		# Fully search
		replace_idx = self.get_replace_idx(set_idx)
		tag_bit_num = len(PA_bin) - self.offset_bit_num - self.index_bit_num
		# print('offset', self.offset_bit_num)

		self.cache_list[set_idx][replace_idx][0] = PA_bin[:tag_bit_num] # Insert the tag 
		self.cache_list[set_idx][replace_idx][1] = 'placehold'

		# Turn to valid
		self.valid_bit[set_idx][replace_idx] = 1
		

	def invalid_page_fault(self, PPN, PA_bin):
		# assert block_offset_num < page_offset_num
		PA_len = len(PA_bin)
		PPN_len = len(PPN)
		block_offset_num = self.offset_bit_num
		add_bit_num = PA_len - PPN_len - block_offset_num
		fack_PA = []
		if add_bit_num == 0:
			fack_PA.append(PPN + '0'*block_offset_num)
		else:
			for i in range(2**add_bit_num):
				fack_PA.append(PPN + bin(i)[2:].zfill(add_bit_num) + '0'*block_offset_num)

		for a in fack_PA:
			set_idx = self.locate(a)
			tag_bit_num = len(a) - self.offset_bit_num - self.index_bit_num
			# Fully search 
			for i, b in enumerate(self.cache_list[set_idx]):
				if b[0] == a[:tag_bit_num] and self.valid_bit[set_idx][i] == 1: 
					self.valid_bit[set_idx][i] = 0

	def set_dirty_by_PA(self, PA):
		set_idx = self.locate(PA)
		tag_bit_num = len(PA) - self.offset_bit_num - self.index_bit_num
		# Fully search 
		for i, b in enumerate(self.cache_list[set_idx]):
			if b[0] == PA[:tag_bit_num] and self.valid_bit[set_idx][i] == 1: 
					self.dirty_bit[set_idx][i] = 1

	def is_dirty(self, PA):
		set_idx = self.locate(PA)
		tag_bit_num = len(PA) - self.offset_bit_num - self.index_bit_num
		# Fully search 
		for i, b in enumerate(self.cache_list[set_idx]):
			if b[0] == PA[:tag_bit_num] and self.valid_bit[set_idx][i] and self.dirty_bit[set_idx][i]: 
				return True
		