from math import *

class PTE(object):
	'''
	Attributes:
		page_size:  The size of one page
		etr_num:    The entry number of this PTE 
		valid_bit:  The valid bit list just like the ALU_record, by int
		PTE_list:	The PTE entity like the [ ['0', '1'], ['0', '1'], ...]
					index 0 is the VPN, index 1 is the PPN, is the page number but not the page address
	'''
	def __init__(self, page_size, VA_init_bin32):
		super(PTE, self).__init__()
		self.page_size = page_size
		self.page_offset_bit_num = int(log(self.page_size, 2))
		self.VA_init_bin32 = VA_init_bin32 # Used for computing the index of a VA
		self.build_PTE()

	def build_PTE(self):
		self.etr_num = int(2**10 / self.page_size)
		self.valid_bit = [0]*self.etr_num
		self.PTE_list = [ [bin(int(self.VA_init_bin32[:-self.page_offset_bit_num], 2) + i)[2:].zfill(32-self.page_offset_bit_num), '1'] 
										for i in range(self.etr_num) ] 

	def get_idx(self, VA):
		'''Get the index of the PTE_list by the VPN
        Args:
			The virtual page number
		Returns:
			The index of the entry of this VPN
		'''
		init_VPN = self.VA_init_bin32[:-self.page_offset_bit_num]
		VPN = VA[:-self.page_offset_bit_num]
		idx = int(VPN, 2) - int(init_VPN, 2)
		
		# offset = int(VA, 2) - int(self.VA_init_bin32, 2)
		# idx = offset // (self.page_size)

		return idx
		
	def find(self, VA_bin32):
		VPN = VA_bin32[: -self.page_offset_bit_num]
		offset = VA_bin32[-self.page_offset_bit_num:]
		idx = self.get_idx(VA_bin32)

		
		# print(idx)


		if self.valid_bit[idx] == 1:
			return [True, self.PTE_list[idx][1]] # Back to TLB
		else:
			return [False, VA_bin32] # To disk
		
	def insert(self, VA_bin32, PPN):
		VPN = VA_bin32[:-self.page_offset_bit_num]
		idx = self.get_idx(VA_bin32)

		self.PTE_list[idx][1] = PPN
		self.valid_bit[idx] = 1

	def invalid_by_PPN(self, PPN):
		for idx, page in enumerate(self.PTE_list):
			if page[1] == PPN:
				self.valid_bit[idx] = 0

