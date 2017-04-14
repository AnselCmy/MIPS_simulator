from math import *
def readBinFile(fileName):
	file = open(fileName, 'rb')
	content = file.read()
	strcontent = content.hex()
	listcontent = [strcontent[i:i+8] for i in range(len(strcontent)) if i%8==0]
	# print(listcontent)	
	return listcontent

def hexToBin(hexList):
	return list(map(lambda h: bin(int(h, 16))[2:].zfill(32), hexList))

def signInt(binStr, figure):
	if figure == 2:
		if binStr[0] == '1':
			# '1' means negative
			if binStr[1:]:
				return -2**(len(binStr)-1) + int(binStr[1:], 2)
			else:
				return -2**(len(binStr)-1)
		elif binStr[0] == '0':
			return int(binStr, 2)

def signBin(integer, num = 32):
	if integer >= 0:
		return ('0'+bin(integer)[2:]).zfill(num)
	elif integer == -1:
		return ('1'*num)
	else:
		length = ceil(log(-integer, 2))+1
		positive = bin(2**(length-1) + integer)[2:]
		return signZfill(('1'+positive.zfill(length-1)), num)

def signZfill(binStr, length):
	binLen = len(binStr)
	compliment = length - binLen
	symbol = binStr[0]
	return symbol*compliment + binStr

def writeSnapshot(content):
	file = open('snapshot.rpt', 'w')
	file.writelines(content)
	file.close()

def writeErrorDump(content):
	file = open('error_dump.rpt', 'w')
	file.writelines(content)
	file.close()