from math import *
import numpy as np

class TLB(object):
	'''
	Attributes:
		page_size:  The size of page, for computing the etr_num
		etr_num:    The number of the entry
		LRU_record: The list for recording the LRU bits
		TLB_list:   The entity of the TLB, from VPN to PPN, like [ ['0', '1'], ['0', '1'], ... ... ]
					index 0 means the VPN, index 1 means the PPN, remember is the number not the address
	'''
	def __init__(self, page_size):
		super(TLB, self).__init__()
		self.page_size = page_size
		self.build_TLB()

	def build_TLB(self):
		self.etr_num = int((2**10 / self.page_size) / 4)
		self.LRU_record = [0]*self.etr_num
		self.valid_bit = [0]*self.etr_num
		# self.TLB_list = np.zeros((self.etr_num, 2)) 
		self.TLB_list = [['0' for i in range(2)] for j in range(self.etr_num)]

		self.page_offset_bit_num = int(log(self.page_size, 2))

	def get_PPN(self, VPN):
		for e in self.TLB_list:
			if e[0] == VPN:
				return e[1]

	def get_replace_idx(self):
		# If exists non_valid bit indx
		try:
			idx = self.valid_bit.index(0)
			return idx
		# If all valid, use LRU
		except ValueError:
			idx = self.LRU_record.index(max(self.LRU_record))
			return idx
	
	def LRU_by_VA(self, VA_bin32):
		VPN = VA_bin32[: -self.page_offset_bit_num]

		for idx, tag in enumerate([p[0] for p in self.TLB_list]):
			if tag == VPN and self.valid_bit[idx] == 1:
				self.LRU_add(idx)

	def LRU_add(self, idx):
		self.LRU_record[idx] = 0
		self.LRU_record = [self.LRU_record[i]+1 if i != idx else self.LRU_record[i] for i in range(self.etr_num)]
	
	def find(self, VA_bin32):
		'''Find if there exists the VPN of this VA
		Args:
			The VA_bin32 from CPU
		Returns:
			If exist, return the PA and next step to cache,
			if not, return the VA and go to PTE
		'''
		# Strip the offset to get the virtual page number 
		VPN = VA_bin32[: -self.page_offset_bit_num]
		# print('VPN:', VPN)
		offset = VA_bin32[-self.page_offset_bit_num:]

		for idx, tag in enumerate([p[0] for p in self.TLB_list]):
			if tag == VPN and self.valid_bit[idx] == 1:
				# return [True, self.get_PPN(VPN) + offset]
				return [True, self.get_PPN(VPN)]
		return [False, VA_bin32]

	def insert(self, VA_bin32, PPN):
		VPN = VA_bin32[:-self.page_offset_bit_num]
		replace_idx = self.get_replace_idx()

		self.TLB_list[replace_idx][0] = VPN
		self.TLB_list[replace_idx][1] = PPN

		# Turn on the valid bits		
		self.valid_bit[replace_idx] = 1


	def invalid_by_PPN(self, PPN):
		# print(self.TLB_list)
		for idx, page in enumerate(self.TLB_list):
			if page[1] == PPN:
				self.valid_bit[idx] = 0 
		# print(self.TLB_list)
		# print('\n\n')


		