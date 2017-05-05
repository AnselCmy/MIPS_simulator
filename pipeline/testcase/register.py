from side_func import *

class Register(object):
	"""A register class for describe a MIPS register

	Attributes:
		rgstDict: Get the integer in 0~31, str of 'HI', 'LO', 'PC as index, store the value of each register.
	"""
	mulLocked = False
	def __init__(self):
		super(Register, self).__init__()
		self.rgstDict = dict(zip([i for i in range(32)], ['0x00000000' for i in range(32)]))
		self.rgstDict['HI'] = '0x00000000'
		self.rgstDict['LO'] = '0x00000000'
		self.rgstDict['PC'] = '0x00000000'
		self.rgstChangeList = []
		self.lastStateDict = {}

	def getRaw(self, idx):
		"""
		Args:
			idx: The decimal index of the register

		Returns:
			Return a raw string like '0x00000000' 
		"""
		return self.rgstDict[idx]

	def getHex(self, idx):
		"""
		Args:
			idx: The decimal index of the register

		Returns:
			Return a hex string format position like '0ff0f000' 
		"""
		return self.getRaw(idx)[2:]


	def getSignDec(self, idx):
		"""
		Args:
			idx: The decimal index of the register

		Returns:
			Return A integer of the value of the indexed register
		"""
		binStr = bin(int(self.rgstDict[idx], 16))[2:].zfill(32)
		return signInt(binStr, 2)

	def getUnsignDec(self, idx):
		return int(self.rgstDict[idx], 16)

	def getBin(self, idx):
		"""
		Args:
			idx: The decimal index of the register

		Returns:
			Return A bin string format of the value with length of 32
		"""
		return bin(self.getUnsignDec(idx))[2:].zfill(32)
			
	def getBinByBin(self, idx):
		"""
		Args:
			idx: The binary index of the register

		Returns:
			Return A bin string format of the value of the indexed register
		"""
		return self.getBin(int(idx, 2))

	def getSignDecByBin(self, idx):
		return self.getSignDec(int(idx, 2))

	def getUnsignDecByBin(self, idx):
		return self.getUnsignDec(int(idx, 2))

	def getHexByBin(self, idx):
		return self.getHex(int(idx, 2))
	
	def set(self, idx, value):
		'''
		Args:
			idx: The index of the register
			value: A bin string format, attention, a bin string
		'''
		# fear for oveflow and cut into 32 bits
		value = value[-32:]
		# fear for set to $0
		if idx == 0:
			return 
		value = '0x' + hex(int(value, 2))[2:].zfill(8).upper()
		self.rgstDict[idx] = value

	def errorDetection(self, idx = -1, value = -1, isNop = False,
						isCNO = False, isCANO = False, AN = 0, 
						mulSet = False, mulGet = False,
						dataLoc = 0,
						align = 0, offset = 0):
		"""
		Args:
			idx: the index of operation register
			value: a 'bin str' format, the value into idx register
			isNop: if is a no operation
			isCNO: if check number overflow
			isCANO: if check add number overflow, for load & save instruction
			AN: add number, do check with isCANO
			mulSet: mul operation set value
			mulGet: mul operation get value
			dataLoc: a 'int' fromat, the data location for check address overflow
			align: the alignment of the load or save instruction
			offset: the offset of instruction, for alignment checking
		""" 
		noError = True
		# 1,write to register $0
		if idx == 0 and (not isNop):
			if 0 in self.rgstChangeList:
				self.rgstChangeList.pop(self.rgstChangeList.index(0))
			errorRpt = 'In cycle {}: Write $0 Error\n'.format(getCycle())
			addErrorRpt(errorRpt)
			# writeErrorDump(errorRpt)	
		# 2,number flow
		# Check Number Overflow
		if isCNO: 
			value = self.checkNumberOverflow(value)
		# Check Add Number Overflow
		if isCANO:
			self.checkNumberOverflow(AN)
		# 3,overwrite HI-LO
		if mulSet:
			if self.mulLocked:
				errorStr = 'In cycle {}: Overwrite HI-LO registers\n'.format(getCycle())
				addErrorRpt(errorStr)
				# writeErrorDump(errorRpt)	
			else:
				self.mulLocked = True
		if mulGet:
			self.mulLocked = False	
		# 4,address overflow 
		if dataLoc  > 1024-align or dataLoc < 0:
			errorStr = 'In cycle {}: Address Overflow\n'.format(getCycle())
			addErrorRpt(errorStr)
			# writeErrorDump(errorRpt)	
			noError = False
		# 5,data misaligned
		if align != 0: # means need to check alignment
			if offset % align != 0:
				errorStr = 'In cycle {}: Misalignment Error\n'.format(getCycle())
				addErrorRpt(errorStr)
				# writeErrorDump(errorRpt)	
				noError = False # need to break out and halt the simulation
		return noError


	def checkNumberOverflow(self, putInData):
		if (signInt(putInData, 2) > (2**31)-1) or (signInt(putInData, 2) < -(2**31)):
			errorStr = 'In cycle {}: Number Overflow\n'.format(getCycle())
			addErrorRpt(errorStr)
			# writeErrorDump('In cycle {}: Number Overflow\n'.format(getCycle()))
			# only need the last 32 bits, if longer, cut it 
			putInData = putInData[-32:]
		return putInData

	def changeRgst(self, idxList , isInt = False):
		"""Set the rgstChangeList by input the list of changed register"""
		# fear for the error dectection is in front of the changeRgst
		if not isInt:
			if 0 in idxList:
				idxList.pop(idxList.index(0))
		self.rgstChangeList = idxList

	def getRegisterRptStr(self, cycle = 1):
		"""Return the Register condition as str"""
		rptStr = ''
		# print('test in rgststr')
		# print(cycle)
		for idx in range(32):
			# if idx == 2:
			# 	print('test in get rpt str')
			# 	print(self.rgstDict[idx])
			# 	print(self.lastStateDict.get(idx, 'NULL'))
			if self.rgstDict[idx] != self.lastStateDict.get(idx, 'NULL') or cycle == 0:
				rptStr += '${0}: {1}\n'.format(str(idx).zfill(2), self.rgstDict[idx])
		
		if self.rgstDict['HI'] != self.lastStateDict.get('HI', 'NULL') or cycle == 0:
			rptStr += '$HI: {}\n'.format(self.rgstDict['HI'])
		if self.rgstDict['LO'] != self.lastStateDict.get('LO', 'NULL') or cycle == 0:
			rptStr += '$LO: {}\n'.format(self.rgstDict['LO'])
		
		# The PC must be changed and print
		# rptStr += 'PC: {}\n'.format(self.rgstDict['PC'])
		# Store the current state for the comperation of next cycle
		self.lastStateDict = self.rgstDict.copy()
		return rptStr

	def printRegister(self):
		"""Print the register condition into bash"""
		for idx, val in self.rgstDict.items():
			if type(idx) == int:
				print('${0}: {1}'.format(str(idx).zfill(2), val))
		print('$HI: {}'.format(self.rgstDict['HI']))
		print('$LO: {}'.format(self.rgstDict['LO']))
		print('PC: {}'.format(self.rgstDict['PC']))
		

