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


global ins_bin8_with_VA_bin32

def set_ins_with_VA(ins):
	global ins_bin8_with_VA_bin32
	ins_bin8_with_VA_bin32 = ins

def get_ins_with_VA():
	global ins_bin8_with_VA_bin32
	return ins_bin8_with_VA_bin32


global data_bin8_with_VA_bin32

def set_data_with_VA(data):
	global data_bin8_with_VA_bin32
	data_bin8_with_VA_bin32 = data

def get_data_with_VA():
	global data_bin8_with_VA_bin32
	return data_bin8_with_VA_bin32

global args_dict

def set_args_dict(args):
	global args_dict
	args_dict = args

def get_args_dict():
	global args_dict
	return args_dict


global VA_init_bin32_ins_data

def set_VA_init_bin32_ins_data(ins, data):
	global VA_init_bin32_ins_data
	VA_init_bin32_ins_data = [ins, data]
	VA_init_bin32_ins_data[1] = '0'*32

def get_VA_init_bin32_ins_data():
	global VA_init_bin32_ins_data
	return VA_init_bin32_ins_data


# global CMP_IVA

# def set_CMP_IVA(IVA):
# 	global CMP_IVA
# 	CMP_IVA = IVA

# def get_CMP_IVA():
# 	global CMP_IVA
# 	return CMP_IVA


# global CMP_DVA

# def set_CMP_DVA(DVA):
# 	global CMP_DVA
# 	CMP_DVA = DVA

# def get_CMP_DVA():
# 	global CMP_DVA
# 	return CMP_DVA
