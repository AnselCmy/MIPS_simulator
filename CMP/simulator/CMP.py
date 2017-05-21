import os, sys
from math import *
from register import *
from global_declare import *
from data import *
from instruction import *
from data import *
from single_cycle import *
from cache import *
from TLB import *
from PTE import *
from mem import *
from disk import *
from global_declare import *

class CMP_class(object):
	"""docstring for CMP"""
	def __init__(self, args_dict):
		super(CMP_class, self).__init__()
		self.args_dict = args_dict
		self.ICache = Cache(args_dict['ICache_size'], args_dict['ICache_block_size'], args_dict['ICache_asc'])
		self.DCache = Cache(args_dict['DCache_size'], args_dict['DCache_block_size'], args_dict['DCache_asc'])
		self.ITLB = TLB(args_dict['IPage_size'])
		self.DTLB = TLB(args_dict['DPage_size'])
		self.IPageTable = PTE(args_dict['IPage_size'], get_VA_init_bin32_ins_data()[0])
		self.DPageTable = PTE(args_dict['DPage_size'], get_VA_init_bin32_ins_data()[1])
		self.IMem = Mem(args_dict['IMem_size'], args_dict['IPage_size'], args_dict['ICache_block_size'])
		self.DMem = Mem(args_dict['DMem_size'], args_dict['DPage_size'], args_dict['DCache_block_size'])
		self.IDisk = Disk(args_dict['IPage_size'])
		self.DDisk = Disk(args_dict['DPage_size'])

		self.I_offset_num = int(log(args_dict['IPage_size'], 2))
		self.D_offset_num = int(log(args_dict['DPage_size'], 2))

		self.IStatus = 'MMM'
		self.DStatus = 'MMM'

		self.ICache_HoM = [0, 0]
		self.ITLB_HoM = [0, 0]
		self.IPageTable_HoM = [0, 0]
		
		self.DCache_HoM = [0, 0]
		self.DTLB_HoM = [0, 0]
		self.DPageTable_HoM = [0, 0]

		self.traceStr = ''


	def IVA_in(self, IVA, insName):
		# TLB miss
		if self.ITLB.find(IVA)[0] == False: 
			# Page Fault
			if self.IPageTable.find(IVA)[0] == False:
				# Assign the state
				self.IStatus = 'MMM' # Miss, Miss, Miss
				
				# Use IVA to grab page_data from disk
				page_data = self.IDisk.get_page_by_VA(IVA)
				assert self.IMem.find_by_VA(IVA) == False, "ERROR in MMM in {} {}".format(getCycle(), insName)

				# Insert the page into mem and assign a PPN, swap
				PPN = self.IMem.insert(page_data, IVA) 
				PA = PPN + IVA[-self.I_offset_num:]

				# Invalid the block_date in cache and page_data in PTE TLB 
				# cause maybe the PPN in mem is replaced
				self.ICache.invalid_page_fault(PPN, PA)
				self.IPageTable.invalid_by_PPN(PPN)
				self.ITLB.invalid_by_PPN(PPN)
				
				assert self.ICache.find(PA)[0] == False, 'ERROR in MMM in {} {}'.format(getCycle(), insName)
				assert self.IMem.find(PPN)[0] == True, "ERROR in MMM in {} {}".format(getCycle(), insName)
				
				# Update the PTE, TLB
				self.IPageTable.insert(IVA, PPN)
				self.ITLB.insert(IVA, PPN)
				self.ICache.insert(PA)
			
			# Page table hit 
			else:
				PPN = self.IPageTable.find(IVA)[1]
				PA = PPN + IVA[-self.I_offset_num:]

				assert self.IMem.find(PPN)[0] == True, "ERROR in HHM in {} {}".format(getCycle(), insName)
				
				# Cache miss
				if self.ICache.find(PA)[0] == False:
					self.IStatus = 'MHM'
					
					self.ITLB.insert(IVA, PPN)
					self.ICache.insert(PA)
				# Cache hit
				else:
					self.IStatus = 'MHH'
					
					self.ITLB.insert(IVA, PPN)
		# TLB hit
		else:
			PPN = self.ITLB.find(IVA)[1]
			PA = PPN + IVA[-self.I_offset_num:]

			assert self.IPageTable.find(IVA)[0] == True, "ERROR in HH in {} {}".format(getCycle(), insName)

			# Cache miss
			if self.ICache.find(PA)[0] == False:				
	
				assert self.IMem.find(PPN)[0] == True, "ERROR in HHM in {} {}".format(getCycle(), insName)
				
				self.IStatus = 'HHM'
				self.ICache.insert(PA)
			else:
				self.IStatus = 'HHH'

		# Bit_pseudo or LRU
		self.ICache.bit_pseudo_by_PA(PA)
		self.ITLB.LRU_by_VA(IVA)
		if self.IStatus[1] == 'M':
			self.IMem.LRU_by_PPN(PPN)

		stage_name = ['ITLB', 'IPageTable', 'ICache']
		stage = [self.ITLB_HoM, self.IPageTable_HoM, self.ICache_HoM]
		for i, HoM in enumerate(self.IStatus):
			if HoM == 'H':
				stage[i][0] += 1
			else:
				stage[i][1] += 1

		if self.IStatus in ['HHM', 'HHH'] :
			self.IPageTable_HoM[0] -= 1

		# Write the trace report
		self.traceStr += insName + '\t' + self.IStatus + '\n'


	def DVA_in(self, DVA, insName, save_change = False, save_loc = -1):
		# print('-'*20)
		# print('cycle:')
		# print(getCycle())
		# print(save_loc)
		# TLB miss
		if self.DTLB.find(DVA)[0] == False: 
			# Page Fault
			if self.DPageTable.find(DVA)[0] == False:
				# Assign the state
				self.DStatus = 'MMM' # Miss, Miss, Miss
				
				# Use IVA to grab page_data from disk
				page_data = self.DDisk.get_page_by_VA(DVA)
				assert self.DMem.find_by_VA(DVA) == False, "ERROR in MMM in {} {}".format(getCycle(), insName)

				# Insert the page into mem and assign a PPN, swap
				PPN = self.DMem.insert(page_data, DVA) 
				PA = PPN + DVA[-self.D_offset_num:]

				# Invalid the block_date in cache and page_data in PTE TLB 
				# cause maybe the PPN in mem is replaced
				self.DCache.invalid_page_fault(PPN, PA)
				self.DPageTable.invalid_by_PPN(PPN)
				self.DTLB.invalid_by_PPN(PPN)
				
				assert self.DCache.find(PA)[0] == False, 'ERROR in MMM in {} {}'.format(getCycle(), insName)
				assert self.DMem.find(PPN)[0] == True, "ERROR in MMM in {} {}".format(getCycle(), insName)
				
				# Update the PTE, TLB
				self.DPageTable.insert(DVA, PPN)
				self.DTLB.insert(DVA, PPN)
				self.DCache.insert(PA)
			
			# Page table hit 
			else:
				PPN = self.DPageTable.find(DVA)[1]
				PA = PPN + DVA[-self.D_offset_num:]

				assert self.DMem.find(PPN)[0] == True, "ERROR in HHM in {} {}".format(getCycle(), insName)
				
				# Cache miss
				if self.DCache.find(PA)[0] == False:
					self.DStatus = 'MHM'
					
					self.DTLB.insert(DVA, PPN)
					self.DCache.insert(PA)
				# Cache hit
				else:
					self.DStatus = 'MHH'
					
					self.DTLB.insert(DVA, PPN)
		# TLB hit
		else:
			PPN = self.DTLB.find(DVA)[1]
			PA = PPN + DVA[-self.D_offset_num:]

			assert self.DPageTable.find(DVA)[0] == True, "ERROR in HH in {} {}".format(getCycle(), insName)

			# Cache miss
			if self.DCache.find(PA)[0] == False:				
	
				assert self.DMem.find(PPN)[0] == True, "ERROR in HHM in {} {}".format(getCycle(), insName)
				
				self.DStatus = 'HHM'
				self.DCache.insert(PA)
			else:
				self.DStatus = 'HHH'

		# Bit_pseudo or LRU
		self.DCache.bit_pseudo_by_PA(PA)
		self.DTLB.LRU_by_VA(DVA)
		if self.DStatus[1] == 'M':
			self.DMem.LRU_by_PPN(PPN)

		stage_name = ['DTLB', 'DPageTable', 'DCache']
		stage = [self.DTLB_HoM, self.DPageTable_HoM, self.DCache_HoM]
		for i, HoM in enumerate(self.DStatus):
			if HoM == 'H':
				stage[i][0] += 1
			else:
				stage[i][1] += 1

		if self.DStatus in ['HHM', 'HHH'] :
			self.DPageTable_HoM[0] -= 1

		self.traceStr = self.traceStr.strip()
		self.traceStr += '\t' + ';' + '\t' + self.DStatus + '\n'

		# print('-'*20)

	def writeReport(self):
		f = open('report.rpt', 'w')
		stage_name = ['ICache', 'DCache', 'ITLB', 'DTLB', 'IPageTable', 'DPageTable']
		stage = [self.ICache_HoM, self.DCache_HoM, self.ITLB_HoM, self.DTLB_HoM, self.IPageTable_HoM, self.DPageTable_HoM]
		reportStr = ''
		for i in range(6):
			reportStr +=  "{} :\n# hits: {}\n# misses: {}\n\n".format(stage_name[i], stage[i][0], stage[i][1])
		f.writelines(reportStr)
		f.close()

	def writeTrace(self):
		f = open('trace_std.rpt', 'w')
		f.writelines(self.traceStr)
		f.close()
