#!/usr/bin/env python3
# coding=utf-8
from math import *
from register import *
from global_declare import *
from data import *
from instruction import *
from data import *
from CMP import *
# import CMP as c

def simulate(r, i, d, ins_bin8_with_PA_bin32, data_bin8_with_PA_bin32):
	# cycleCnt = 0
	setCycle(0)
	# Get the initial value of pc and sp, is a 'bin str' format
	pcInit = i[0]
	spInit = d[0]
	# iNum adn dNum is transformed into 'int'
	iNum = int(i[1], 2)
	dNum = int(d[1], 2)
	r.set('PC', pcInit)
	r.set(29, spInit)
	# We print all the register first time, so first assume all is changed
	r.changeRgst(r.rgstDict.keys(), isInt = True)
	# Initial the rptStr and cycleCnt
	rptStr = ''
	# Creat first rptStr
	rptStr += 'cycle {}\n'.format(getCycle())
	# cycleCnt += 1
	setCycle(getCycle()+1)
	rptStr += r.getRegisterRptStr()
	# writeSnapshot(rptStr)
	# rptStr = ''
	# creat a blank error_dump.rpt
	# Initial the errorRpt
	global errorRpt
	setErrorRpt('')

	# Initial the CMP
	CMP = CMP_class(get_args_dict())

	# Get the main body of instruction and data
	instruction = i[2:iNum+3]
	data = d[2:dNum+3] + [Data('0'*32) for i in range(1022)]
	# Deal with every instruction
	iCnt = 0

	# Pass a bin32 PC into CMP
	curr_PC = unsignBin32(int(instruction[iCnt].PC, 2) - 4) # Bin 32
	# Insert for byte of one instruction into CMP
	# for i in range(4):
	# 	CMP.IVA_in(unsignBin32(int(curr_PC, 2)+i))
	CMP.IVA_in(curr_PC, instruction[iCnt].getInsName())
	
	# while instruction[iCnt].getInsName() != 'halt':
	while True:
		i = instruction[iCnt]
		ins = i.getInsName()
		
		# print(getCycle())
		# print(instruction[iCnt].getInsName())
		# print(instruction[iCnt].PC)
		# print('-'*10)

# lw, lh, lhu, lb, lbu
		if ins in ['lw', 'lh', 'lhu', 'lb', 'lbu']:
			rgstIdx = int(i.rt, 2)
			c = signInt(i.immediate, 2)
			loadLoc = r.getSignDecByBin(i.rs) + c
			# print('testtest', ins,getCycle(), loadLoc)
			# assign align
			if ins == 'lw':
				align = 4
			elif ins in ['lh', 'lhu']:
				align = 2
			elif ins in ['lb', 'lbu']:
				align = 1
			# error detection
			if not r.errorDetection(idx = rgstIdx,
									isCANO = True, AN = signBin(loadLoc),
									dataLoc = loadLoc,
									align = align, offset = loadLoc)[0]:
				break
			# find putInData
			if ins in ['lw', 'lh', 'lb']:
				putInData = signZfill(''.join(data[loadLoc//4].binStr[(loadLoc%4)*8: (loadLoc%4)*8+8*align]), 32)
			elif ins in ['lhu', 'lbu']:
				putInData = (''.join(data[loadLoc//4].binStr[(loadLoc%4)*8: (loadLoc%4)*8+8*align])).zfill(32)
			# check if changed regester
			if putInData == r.getBinByBin(i.rt).zfill(8):
				r.changeRgst([])
			else:
				r.changeRgst([rgstIdx])
		 	# set value 
			r.set(rgstIdx, putInData)

			# print('-'*10)
			# print(instruction[iCnt].getInsName())
			# print('loc')
			# print(loadLoc)
			# CMP.DVA_in(unsignBin32(int(spInit, 2) + (loadLoc//4)*4), instruction[iCnt].getInsName(), save_loc = loadLoc)
			CMP.DVA_in(unsignBin32((loadLoc//4)*4), instruction[iCnt].getInsName(), save_loc = loadLoc)

# sw, sh, sb
		elif ins in ['sw', 'sh', 'sb']:
			c = signInt(i.immediate, 2)
			saveLoc = r.getUnsignDecByBin(i.rs) + c
			# assign align and compute save data
			if ins == 'sw':
				align = 4
				saveData = r.getBinByBin(i.rt)
			elif ins == 'sh':
				align = 2
				saveData = bin(r.getUnsignDecByBin(i.rt) & int('0x0000FFFF', 16))[2:].zfill(16)[-16:]
			elif ins == 'sb':
				align = 1
				saveData = bin(r.getUnsignDecByBin(i.rt) & int('0x000000FF', 16))[2:].zfill(8)[-8:]
			# error detection
			if not r.errorDetection(isCANO = True, AN = signBin(saveLoc),
									dataLoc = saveLoc,
									align = align, offset = saveLoc)[0]:
				break
			# do save data 
			save_data_origin = data[saveLoc//4].binStr
			data[saveLoc//4] = Data(data[saveLoc//4].binStr[:(saveLoc%4)*8]
										+ saveData 
										+ data[saveLoc//4].binStr[(saveLoc%4)*8+align*8:])
			# save data change no regester
			r.changeRgst([])

			# print('-'*10)
			# print(instruction[iCnt].getInsName())
			# print('loc')
			# print(saveLoc)
			if data[saveLoc//4].binStr == save_data_origin:
				save_change = False
			else:
				save_change = True
			# CMP.DVA_in(unsignBin32(int(spInit, 2) + (saveLoc//4)*4), instruction[iCnt].getInsName(), save_change, saveLoc)
			CMP.DVA_in(unsignBin32((saveLoc//4)*4), instruction[iCnt].getInsName(), save_loc = saveLoc)

# slt, slti
		elif ins in ['slt', 'slti']:
			firstOp = signInt(r.getBinByBin(i.rs), 2)
			# assign the second operator
			if ins == 'slt':
				rgstIdx = int(i.rd, 2)
				secondOp = signInt(r.getBinByBin(i.rt), 2)
			elif ins == 'slti':
				rgstIdx = int(i.rt, 2)
				secondOp = signInt(i.immediate, 2)
			# assign the putInData for different situation
			if firstOp < secondOp:
				putInData = '0'*31 + '1'
			else:
				putInData = '0'*32
			# error detection, only 'write to zero' can be occured
			r.errorDetection(idx = rgstIdx)
			# change register
			if r.getBin(rgstIdx) != putInData:
				r.changeRgst([rgstIdx])
			else:
				r.changeRgst([])
			# set the register
			r.set(rgstIdx, putInData)

# sll, srl, sra
		elif ins in ['sll', 'srl', 'sra']:
			rgstIdx = int(i.rd, 2)
			# assign putInData
			if ins == 'sll':
				putInData = bin(int(r.getBinByBin(i.rt), 2) << int(i.shamt, 2))[2:][-32:].zfill(32)
			elif ins == 'srl':
				putInData = bin(int(r.getBinByBin(i.rt), 2) >> int(i.shamt, 2))[2:][-32:].zfill(32)
			elif ins == 'sra':
				sm = int(i.shamt, 2)
				putInData = signZfill(bin(int(r.getBinByBin(i.rt), 2) >> sm)[2:].zfill(32-sm), 32)
			# error detection
			# if putInData == '0'*32 and ins == 'sll':
			# print(getCycle(), i.binStr)
			if ins == 'sll' and i.rt == '0'*5 and i.rd == '0'*5 and i.shamt == '0'*5:
				r.errorDetection(rgstIdx, isNop = True)
			else:
				r.errorDetection(rgstIdx)
			# change register
			if putInData == r.getBin(rgstIdx):
				r.changeRgst([])
			else:
				r.changeRgst([rgstIdx])
			# set 
			r.set(rgstIdx, putInData)

# and, nand, or, xor, ori, nori 
		elif ins in ['and', 'nand', 'andi', 'or', 'xor', 'nor', 'ori', 'nori']:
			# assign rgstIdx
			if ins[-1] != 'i':
				rgstIdx = int(i.rd, 2)
			else:
				rgstIdx = int(i.rt, 2)
			# compute putInData
			if ins == 'and':
				putInData = bin(r.getUnsignDecByBin(i.rs) & r.getUnsignDecByBin(i.rt))[2:].zfill(32)
			elif ins == 'nand':
				putInDataReverse = r.getUnsignDecByBin(i.rs) & r.getUnsignDecByBin(i.rt)
				putInData = bin(putInDataReverse ^ int('1'*32, 2))[2:].zfill(32)
			elif ins == 'andi':
				putInData = bin(r.getUnsignDecByBin(i.rs) & int(i.immediate, 2))[2:].zfill(32)
			elif ins == 'or':
				putInData = bin(r.getUnsignDecByBin(i.rs) | r.getUnsignDecByBin(i.rt))[2:].zfill(32)
			elif ins == 'xor':
				putInData = bin(r.getUnsignDecByBin(i.rs) ^ r.getUnsignDecByBin(i.rt))[2:].zfill(32)
			elif ins == 'nor':
				putInDataReverse = r.getUnsignDecByBin(i.rs) | r.getUnsignDecByBin(i.rt)
				putInData = bin(putInDataReverse ^ int('1'*32, 2))[2:].zfill(32)
			elif ins == 'ori':
				putInData = bin(r.getUnsignDecByBin(i.rs) | int(i.immediate, 2))[2:].zfill(32)
			elif ins == 'nori':
				putInDataReverse = r.getUnsignDecByBin(i.rs) | int(i.immediate, 2)
				putInData = bin(putInDataReverse ^ int('1'*32, 2))[2:].zfill(32)
			# error detection
			r.errorDetection(idx = rgstIdx)
			if putInData != r.getBin(rgstIdx):
				r.changeRgst([rgstIdx])
			else:
				r.changeRgst([])
			r.set(rgstIdx, putInData)

# sub, add, addu, addi, addiu:
		elif ins in ['sub', 'add', 'addu', 'addi', 'addiu']:
			# assign the register idx
			if ins in ['addi', 'addiu']:
				rgstIdx = int(i.rt, 2)
			else:
				rgstIdx = int(i.rd, 2)
			# compute the putInData
			if ins == 'sub':
				rtRevese = signInt(signBin(-r.getSignDecByBin(i.rt))[-32:], 2)
				putInData = signBin(r.getSignDecByBin(i.rs) + rtRevese, 32)	
				# print(getCycle())
				# print(r.getSignDecByBin(i.rt))
				# print(rtRevese)
				# print(r.getSignDecByBin(i.rs))
				# print(putInData)
				# print('\n')		
			elif ins == 'add':
				putInData = signBin(r.getSignDecByBin(i.rs) + r.getSignDecByBin(i.rt), 32)
			elif ins == 'addu':
				putInData = bin((r.getUnsignDecByBin(i.rs) + r.getUnsignDecByBin(i.rt)))[2:].zfill(32)
			elif ins == 'addi':
				putInData = signBin(r.getSignDecByBin(i.rs) + signInt(signZfill(i.immediate, 32), 2), 32)
			elif ins == 'addiu':
				putInData = bin(r.getUnsignDecByBin(i.rs) + int(signZfill(i.immediate, 32), 2))[2:].zfill(32)
			if ins[-1] != 'u':
				r.errorDetection(idx = rgstIdx, value = putInData, 
									isCNO = True)
			else:
				r.errorDetection(idx = rgstIdx, value = putInData)
			# fear for the overflow of putInData, so get the [-32:]
			if putInData[-32:] == r.getBin(rgstIdx):
				r.changeRgst([])
			else:
				r.changeRgst([rgstIdx])
			r.set(rgstIdx, putInData)

# mult, multu
		elif ins in ['mult', 'multu']:
			# compute putInData
			if ins == 'mult':
				putInData = signBin(r.getSignDecByBin(i.rs) * r.getSignDecByBin(i.rt), num = 64)
			elif ins == 'multu':
				putInData = bin(r.getUnsignDecByBin(i.rs) * r.getUnsignDecByBin(i.rt))[2:].zfill(64)
			# error dection
			errorCode = r.errorDetection(mulSet = True)
			# change register and set
			changeList = []
			# if not(3 in errorCode): 
			if putInData[0:32] != r.getBin('HI').zfill(32):
				changeList.append('HI')
			r.set('HI', putInData[0:32])

			if putInData[32:] != r.getBin('LO').zfill(32):
				changeList.append('LO')
			r.set('LO', putInData[32:])
			r.changeRgst(changeList)


# mfhi, mflo
		elif ins in ['mfhi', 'mflo']:
			rgstIdx = int(i.rd, 2)
			# errorCode = r.errorDetection(idx = rgstIdx, mulGet = True)
			# print('test in mfhi')
			# print(getCycle())
			# print(errorCode)
			# print('-'*10)
			# if 3 in errorCode:
			# 	continue
			if r.getBin(rgstIdx) == r.getBin(ins[-2:].upper()):
				r.changeRgst([])
			else:
				r.changeRgst([rgstIdx])
			r.set(rgstIdx, r.getBin(ins[-2:].upper()))
# lui	 
		elif i.getInsName() == 'lui':
			rgstIdx = int(i.rt, 2)
			putInData = i.immediate + '0'*16
			r.errorDetection(idx = rgstIdx)
			if putInData == r.getBin(rgstIdx):
				r.changeRgst([])
			else:
				r.changeRgst([rgstIdx])
			r.set(rgstIdx, putInData)

# bne, beq, bgtz
		elif ins in ['bne', 'beq', 'bgtz']:
			# compute the going-to pc
			jump = signInt(signZfill(i.immediate, 32), 2)
			toPC = int(i.PC, 2) + 4 + 4*jump
			# assign jumpFlag
			if ins == 'bne':
				jumpFlag = (r.getSignDecByBin(i.rs) != r.getSignDecByBin(i.rt))
			elif ins == 'beq':
				jumpFlag = (r.getSignDecByBin(i.rs) == r.getSignDecByBin(i.rt))
			elif ins == 'bgtz':
				jumpFlag = (r.getSignDecByBin(i.rs) > 0)
			# judge and jump
			if jumpFlag:
				iCnt += jump
			# special situation for jump to pos that less than zore
			if iCnt < 0:
				pcNOP = '0x' + hex(int(i.PC, 2) + 4*(jump))[2:].zfill(8).upper()
				# print(pcNOP)
				while pcNOP != '0x' + (hex(int(pcInit, 2)+4)[2:].zfill(8)).upper():
					
					# For CMP in
					CMP.IVA_in(unsignBin32(int(pcNOP, 16) ), 'NOP')

					rptStr += 'cycle {}\n'.format(getCycle())
					# cycleCnt += 1
					setCycle(getCycle()+1)
					rptStr += 'PC: ' + pcNOP + '\n\n\n'
					# print(rptStr)
					# writeSnapshot(rptStr)
					# rptStr = ''
					pcNOP = '0x' + (hex(int(pcNOP, 16) + 4)[2:].zfill(8)).upper()
				# restart from the first instruction
				iCnt = 0
				# continue to execute the first instruction 
				continue
			# no change
			r.changeRgst([])

# j, jal, jr
		elif ins in ['j', 'jal', 'jr']:
			# computer toPC and the value of jump
			if ins == 'jr':
				toPC = r.getBinByBin(i.rs).zfill(32)
			else:
				toPC = (i.PC).zfill(32)[:4] + (i.address).zfill(26) + '00'
			jump = int((int(toPC, 2) - int(instruction[iCnt].PC, 2)) / 4)
			# jump
			iCnt += jump
			if iCnt < 0:
				pcNOP = '0x' + hex(int(i.PC, 2) + 4*(jump))[2:].zfill(8).upper()
				# print(pcNOP)
				while pcNOP != '0x' + (hex(int(pcInit, 2)+4)[2:].zfill(8)).upper():
					
					# For CMP in
					CMP.IVA_in(unsignBin32(int(pcNOP, 16) ), 'NOP')
					
					rptStr += 'cycle {}\n'.format(getCycle())
					setCycle(getCycle()+1)
					rptStr += 'PC: ' + pcNOP + '\n\n\n'
					# print('this is in loop!!')
					# print(rptStr)
					# writeSnapshot(rptStr)
					# rptStr = ''
					pcNOP = '0x' + (hex(int(pcNOP, 16) + 4)[2:].zfill(8)).upper()
				# restart from the first instruction
				iCnt = 0
				# continue to execute the first instruction 
				continue
			# change register
			if ins == 'jal':
				if r.getBin(31) == i.PC.zfill(32):
					r.changeRgst([])
				else:
					r.changeRgst([31])
				r.set(31, i.PC)
			else:
				r.changeRgst([])

# halt
		elif i.getInsName() == 'halt':
			break


		# Set register same with the fixed pc in instruction
		r.set('PC', instruction[iCnt].PC)
		# Add iCnt means the program is executing
		iCnt += 1


		# Pass a bin32 PC into CMP
		curr_PC = unsignBin32(int(instruction[iCnt-1].PC, 2)) # Bin 32
		# Insert for byte of one instruction into CMP
		# for i in range(4):
		# 	CMP.IVA_in(unsignBin32(int(curr_PC, 2)+i))
		CMP.IVA_in(curr_PC, instruction[iCnt].getInsName())

		# We add the cycleCnt with 1 and print it
		rptStr += 'cycle {}\n'.format(getCycle())
		setCycle(getCycle()+1)
		rptStr += r.getRegisterRptStr()
		# print(rptStr)
		# writeSnapshot(rptStr)
		# rptStr = ''
	writeSnapshot(rptStr)

	CMP.writeReport()
	# CMP.writeTrace()
	# writeErrorDump(getErrorRpt())
