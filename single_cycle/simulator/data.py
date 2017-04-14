class Data(object):
	def __init__(self, binStr):
		super(Data, self).__init__()
		self.binStr = binStr
		self.byteList = []
		self.devideToByte()

	def devideToByte(self):
		i = 0
		while i < len(self.binStr):
			self.byteList.append(self.binStr[i:i+2])
			i += 2

	def printData(self):
		for byte in self.byteList:
			print(byte, end = ' ')
		print('\n')