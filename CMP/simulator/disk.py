from math import *
from global_declare import *
from side_func import *

class Disk(object):
	"""docstring for Disk"""
	def __init__(self, page_size):
		super(Disk, self).__init__()
		self.page_size = page_size
		self.page_offset_bit_num = int(log(self.page_size, 2))

	def get_page_by_VA(self, VA):
		# Cut the page offset and get the page number but not the address
		
		# VPN = VA[:-self.page_offset_bit_num]
		# VA_start = VPN + '0'*self.page_offset_bit_num
		# VA_list = [ unsignBin32(int(VA_start, 2)+i) for i in range(self.page_size) ]
		# page_data = ''.join([ get_ins_with_VA()[i] for i in VA_list])

		# return page_data
		return 'placehold'

		