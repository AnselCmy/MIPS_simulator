from instruction import *

class StageBuffer(object):
	def __init__(self):
		super(StageBuffer, self).__init__()
		self.bufferDict = {'ins': Instruction('0'*32), 'insName': 'NOP', 'insBinStr_bin32': '0'*32, 'insHexStr_hex8': '0'*8}
		self.controlBuffer = {'EX': {'ALUSrc': -1, 'ALUOp': -1, 'RegDst': -1}, 
								'DM': {'MemWrite': -1, 'MemRead': -1, 'BrcOp': -1}, 
								'WB': {'RegWrite': -1, 'MemtoReg': -1}}

	def bufferIn(self, dict):
		self.bufferDict.update(dict)

	def getBuffer(self, key):
		return self.bufferDict[key]

	def clearBuffer(self):
		self.bufferDict = {}



