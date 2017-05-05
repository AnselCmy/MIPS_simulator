class Instruction(object):
	"""A class to parse instruction and describe every instruction's feature

	Attributes:
		binStr: The bin string of a raw instruction, 32 bits
		intType: Store the type of a instruction
		insDict: Store every codes' name(key) and them value, by bin string
		PC: The PC value of instruction, a bin string format
	"""
	rIdx = ['opcode', 'rs', 'rt', 'rd', 'shamt', 'funct']
	rLen = [6, 5, 5, 5, 5, 6]
	iIdx = ['opcode', 'rs', 'rt', 'immediate']
	iLen = [6, 5, 5, 16]
	jIdx = ['opcode', 'address']
	jLen = [6, 26]
	sIdx = ['opcode', 'address']
	sLen = [6, 26]
	nameDict = {'r':rIdx, 'i':iIdx, 'j':jIdx, 's':sIdx}
	lenDict = {'r':rLen, 'i':iLen, 'j':jLen, 's':sLen}

	def __init__(self, binStr):
		super(Instruction, self).__init__()
		self.binStr = binStr
		self.hexStr = hex(int(binStr, 2))[2:].zfill(8)
		self.insType = 'f'
		self.insDict = {}
		self.PC = -1
		self.parse()

	def parse(self):
		self.parseType()
		self.parseFormat()
		self.opcode = self.insDict.get('opcode', '0'*6)
		self.rs = self.insDict.get('rs', '0'*5)
		self.rt = self.insDict.get('rt', '0'*5)
		self.rd = self.insDict.get('rd', '0'*5)
		self.shamt = self.insDict.get('shamt', '0'*5)
		self.funct = self.insDict.get('funct', '0'*6)
		self.immediate = self.insDict.get('immediate', '0'*16)
		self.address = self.insDict.get('address', '0'*26)

	def parseType(self):
		opcode = '0x' + hex(int(self.binStr[0:6], 2))[2:].zfill(2)
		if opcode == '0x00':
			self.insType = 'r'
		elif opcode == '0x3f':
			self.insType = 's'
		elif opcode == '0x02' or opcode == '0x03':
			self.insType = 'j'
		else:
			self.insType = 'i'

	def parseFormat(self):
		for cnt in range(len(self.nameDict[self.insType])):
			self.insDict[self.nameDict[self.insType][cnt]] = \
						self.binStr[sum(self.lenDict[self.insType][:cnt]): sum(self.lenDict[self.insType][:cnt+1])]

	def getInsName(self):
		iTypeOpcodeDict = {'0x08':'addi', '0x09':'addiu', '0x23':'lw', '0x21':'lh', '0x25':'lhu', '0x20':'lb', 
							'0x24':'lbu', '0x2b':'sw', '0x29':'sh', '0x28':'sb', '0x0f':'lui', '0x0c':'andi',
							'0x0d':'ori', '0x0e':'nori', '0x0a':'slti', '0x04':'beq', '0x05':'bne', '0x07':'bgtz'}
		jTypeOpcodeDict = {'0x02':'j', '0x03':'jal'}
		sTypeOpcodeDict = {'0x3f':'halt'}
		rTypeFunctDict = {'0x20':'add', '0x21':'addu', '0x22':'sub', '0x24':'and', '0x25':'or', '0x26':'xor',
							'0x27':'nor', '0x28':'nand', '0x2a':'slt', '0x00':'sll', '0x02':'srl', '0x03':'sra',
							'0x08':'jr', '0x18':'mult', '0x19':'multu', '0x10':'mfhi', '0x12':'mflo'}
		
		opcode = '0x' + hex(int(self.binStr[0:6], 2))[2:].zfill(2)
		funct = '0x' + hex(int(self.binStr[-6:], 2))[2:].zfill(2)
		if self.binStr == '0'*32:
			return 'NOP'
		if  self.opcode == '0'*6 and self.funct == '0'*6 \
			and self.rt == '0'*5 and self.rd == '0'*5 and self.shamt == '0'*5:
			return 'NOP'
		elif self.insType == 'r':
			return rTypeFunctDict[funct]
		elif self.insType == 'i':
			return iTypeOpcodeDict[opcode]
		elif self.insType == 'j':
			return jTypeOpcodeDict[opcode]
		elif self.insType == 's':
			return sTypeOpcodeDict[opcode]

	def printInstruction(self):
		print(self.getInsName())
		print('0x'+hex(int(self.PC, 2))[2:].zfill(8).upper())
		for cnt in self.nameDict[self.insType]:
			print(self.insDict[cnt], end = ' ')
		print('\n')
