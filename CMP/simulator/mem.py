from math import *


class Mem(object):
    '''
	Attributes:
        mem_list: The memory entity, index 0 is the physical page number, index 1 is the real data page
	'''

    def __init__(self, mem_size, page_size, block_size):
        super(Mem, self).__init__()
        self.mem_size = mem_size
        self.page_size = page_size
        self.mem_page_num = int(self.mem_size / self.page_size)
        self.block_size = block_size
        self.page_offset_bit = int(log(self.page_size, 2))
        self.build_mem()

    def build_mem(self):
        PPN_bin_num = len(bin(self.mem_page_num - 1)[2:])
        self.mem_list = [[bin(i)[2:].zfill(PPN_bin_num), '1', '2'] for i in range(self.mem_page_num)]
        self.LRU_record = [0] * self.mem_page_num
        self.valid_bit = [0] * self.mem_page_num

    def get_idx(self, PPN):
        return int(PPN, 2)

    def find(self, PPN):
        idx = self.get_idx(PPN)
        if self.valid_bit[idx] == 1:
            return [True, self.mem_list[idx][1]]
        else:
            return [False]

    def find_by_VA(self, VA):
     for page in enumerate(self.mem_list):
     	try:
     		if page[2][: -self.page_offset_bit] == VA[: -self.page_offset_bit]:
     			return True
     	except IndexError:
     		pass
     return False

    def get_replace_idx(self):
        # If exists non_valid bit indx
        try:
            idx = self.valid_bit.index(0)
            return idx
        # If all valid, use LRU
        except ValueError:
            idx = self.LRU_record.index(max(self.LRU_record))
            return idx

    def LRU_by_PPN(self, PPN):
        idx = self.get_idx(PPN)
        self.LRU_add(idx)

    def LRU_add(self, idx):
        self.LRU_record[idx] = 0
        self.LRU_record = [self.LRU_record[i] + 1 if i != idx else self.LRU_record[i] for i in range(self.mem_page_num)]

    def insert(self, page_data, IVA):
        '''Insert the page from disk and assign the PPN and return'''
        replace_idx = self.get_replace_idx()

        # Need only judge strping of the page offset bit 
        # if self.mem_list[replace_idx][2][] == IVA

        # Put the page into mem
        self.mem_list[replace_idx][1] = page_data
        self.mem_list[replace_idx][2] = IVA # Used for judging if valid in cache
        # Turn the valid bit into 1
        self.valid_bit[replace_idx] = 1
        # Return the assigned PPN
        return self.mem_list[replace_idx][0]

    def get_block_by_PA(self, PA):
        block_offset_bit_num = int(log(self.block_size, 2))
        PA_start = self.PA[:-block_offset_bit_num] + '0' * block_offset_bit_num
        block_data = 'palcehold'
        return block_data

    def invalid_by_PPN(self, PPN):
    	idx = self.get_idx(PPN)
    	self.valid_bit[idx] = 0
