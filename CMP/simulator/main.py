#!/usr/bin/env python3
# coding=utf-8
from math import *
from side_func import *
from register import *
from global_declare import *
from data import *
from instruction import *
from data import *
from single_cycle import *
import sys

def main():
	# clean the environment
	# os.system('rm snapshot.rpt')
	# os.system('rm error_dump.rpt')
	iHexList, IDiskContent_hex2 = readBinFile('iimage.bin')
	dHexList, DDiskContent_hex2 = readBinFile('dimage.bin')
	iBinList = hexToBin(iHexList)
	dBinList = hexToBin(dHexList)
	allInsList = []
	allDataList = []

	for cnt, i in enumerate(iBinList[2:]):
		allInsList.append(Instruction(i))
		# Push the PC value into evey instruction, it's fixed, also bin string format
		allInsList[-1].PC = bin(int(iBinList[0], 2)+4*(cnt+1))[2:].zfill(32)
		# Print for debug
		# allInsList[-1].printInstruction()
	allInsList = iBinList[:2] + allInsList
	for d in dBinList[2:]:
		allDataList.append(Data(d))
		# allDataList[-1].printData()
	allDataList = dBinList[:2] + allDataList
	
	# Init a ins and data dict with PA align in byte 
	global ins_bin8_with_PA_bin32
	global data_bin8_with_PA_bin32
	global VA_init_bin32_ins_data
	IDiskContent_bin8 = hexToBin(IDiskContent_hex2[8:], length = 8)
	DDiskContent_bin8 = hexToBin(DDiskContent_hex2[8:], length = 8)
	IDiskVA_bin32 = [unsignBin32(int(iBinList[0], 2)+i) for i in range(int(iBinList[1], 2)*4)]
	DDiskVA_bin32 = [unsignBin32(int(dBinList[0], 2)+i) for i in range(int(dBinList[1], 2)*4)]
	set_ins_with_VA(dict(zip(IDiskVA_bin32, IDiskContent_bin8)))
	set_data_with_VA(dict(zip(DDiskVA_bin32, IDiskContent_bin8)))
	set_VA_init_bin32_ins_data(iBinList[0], dBinList[0])

	# Get the args and assign
	args = [int(p) for p in sys.argv[1:]]
	default_args = [64, 32, 8, 16, 16, 4, 4, 16, 4, 1]
	args = args + default_args[len(args):]
	args_names = ['IMem_size', 'DMem_size', 'IPage_size', 'DPage_size', 
				'ICache_size', 'ICache_block_size', 'ICache_asc', 
				'DCache_size', 'DCache_block_size', 'DCache_asc']
	global args_dict
	set_args_dict(dict(zip(args_names, args)))

	rgst = Register()
	simulate(rgst, allInsList, allDataList, get_ins_with_VA(), get_data_with_VA())

	
if __name__ == '__main__':
	main()