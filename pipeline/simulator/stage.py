from instruction import *

class Stage(object):
	def __init__(self):
		super(Stage, self).__init__()
		self.ins = Instruction('0'*32)
		self.insName = 'NOP'
		self.PC_bin32 = '0'*32	



class IFstage(Stage):
	def __init__(self):
		Stage.__init__(self)
		self.insHexStr_hex8 = 'F'*8
		self.insBinStr_bin32 = '0'*32
		# self.PC_bin32 = '0'*32

class IDstage(Stage):
	def __init__(self):
		Stage.__init__(self)
		self.readData1_bin32 = '0'*32
		self.readData2_bin32 = '0'*32
		self.imdt_bin32 = '0'*32
		self.rt_bin5 = '0'*5
		self.rd_bin5 = '0'*5

class EXstage(Stage):
	def __init__(self):
		Stage.__init__(self)
		self.jumpPC_bin32 = '0'*32
		self.jumpControl = 0
		self.ALURst_bin32 = '0'*32
		self.ALURst_bin64 = '0'*64 # Special for mult instruction
		self.writeData_bin32 = '0'*32
		self.writeRgst_bin5 = '0'*5
		
class DMstage(Stage):
	def __init__(self):
		Stage.__init__(self)
		self.readDataFromMem_bin32 = '0'*32
		self.readDataFromALU_bin32 = '0'*32
		self.readDataFromALU_bin64 = '0'*64
		self.writeRgst_bin5 = '0'*5

class WBstage(Stage):
	def __init__(self):
		Stage.__init__(self)
		self.writeRgst_bin5 = '0'*5
		self.writeData_bin32 = '0'*32
		self.writeData_bin64 = '0'*64
		

		