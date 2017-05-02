global cycleCnt

def setCycle(cnt):
	global cycleCnt
	cycleCnt = cnt

def getCycle():
	global cycleCnt
	return cycleCnt

global errorRpt

def setErrorRpt(rpt):
	global errorRpt
	errorRpt = rpt

def addErrorRpt(rpt):
	global errorRpt
	errorRpt += rpt

def getErrorRpt():
	global errorRpt
	return errorRpt