# from prettytable import PrettyTable
from register import *
from side_func import *
from data import *
from instruction import *
from stagebuffer import *
from stage import *

class Pipeline(object):
	def __init__(self):
		super(Pipeline, self).__init__()
		# Declare the object register
		self.r = Register()
		# Declare four stage_buffers
		self.IF_ID = StageBuffer()
		self.ID_EX = StageBuffer()
		self.EX_DM = StageBuffer()
		self.DM_WB = StageBuffer()
		self.stageBufferDict = {'IF_ID': self.IF_ID, 'ID_EX': self.ID_EX, 'EX_DM': self.EX_DM, 'DM_WB': self.DM_WB}
		# Declare five stages
		self.IF = IFstage()
		self.ID = IDstage()
		self.EX = EXstage()
		self.DM = DMstage()
		self.WB = WBstage()
		# self.IF.insName = self.ID.insName = self.EX.insName = self.DM.insName = self.WB.insName = 'NOP'
		self.stageDict = {'IF': self.IF, 'ID': self.ID, 'EX': self.EX, 'DM': self.DM, 'WB': self.WB}
		# Essential info from indtruction and data
		self.PCInit_bin32 = '0'*32
		self.spInit_bin32 = '0'*32
		self.iNum_dec = 0
		self.dNum_dec = 0
		self.instruction = []
		self.instructionWithPC_bin32 = []
		self.data = []
		self.PC_bin32 = 0
		# Declare the component list of the instruction
		self.insComponent = ['opcode', 'rs', 'rt', 'rd', 'shamt', 'funct', 'immediate', 'address']
		# Initial iCnt, the idx of the fetched instruction currently
		self.iCnt_dec = 0
		# Initial the cycleCnt_dec
		self.cycleCnt_dec = 0
		# Initial the snapshot and errordump
		self.snapshotStr = ''
		self.errordumpStr = ''
		# Initial the control
		self.controlEX = {'ALUSrc': -1, 'ALUOp': -1, 'RegDst': -1, 'DoMult':-1}
		self.controlDM = {'MemWrite': -1, 'MemRead': -1, 'BrcOp': -1}
		self.controlWB = {'RegWrite': -1, 'MemtoReg': -1} 
		# self.control = {'EX': self.controlEX, 'DM': self.controlDM, 'WB': self.controlWB}
		self.defaultControl = {'EX': {'ALUSrc': -1, 'ALUOp': -1, 'RegDst': -1, 'DoMult': -1}, 
								'DM': {'MemWrite': -1, 'MemRead': -1, 'BrcOp': -1}, 
								'WB': {'RegWrite': -1, 'MemtoReg': -1}}
		# Initial the unit signal
		self.forwardSignal = {'ALUOpMux0': 0, 'ALUOpMux1': 0} # The default input of mux
		self.forwardType = '00'

		self.hazardSignal = {'PCWrite': 1, 'IF_IDWrite': 1, 'controlWrite': 1} # 1 means can be wrote, 0 means be stalled
		self.IDLock = False
		# self.IDLock2 = False
		
		self.branchSignal = {'PCSel': 1, 'EquRst': -1, 'IFFlush': 0} # PCSel, 1 means normal; EquRst = 1 means rs==rt, 0 for rs!=rt
		self.IFFlushThisCycle = False
		self.branchHazardSignal = {'PCWrite': 1, 'IF_IDWrite': 1, 'controlWrite': 1}
		self.branchPC_bin32 = '0'*32 # The rst of the branch adder
		self.branchForwardType = '00'
		# Initial the snapshot and errordump
		self.rgstStrReserve = ''
		self.snapshotStr = ''
		self.errordumpStr = ''

		# Use mulLock to detect the over write of HI-LO
		self.mulLock = False

		# Flag for error detection 
		self.mulError = False
		self.numberOverflowError = False
		self.addressOverflowError = False
		self.misalignedError = False

	def parseInsAndData(self, i, d):
		# Get the binStr of the initial value of PC_bin32 and sp
		if len(i) > 0:
			self.PCInit_bin32 = i[0]
			self.iNum_dec = int(i[1], 2)
		if len(d) > 0:
			self.spInit_bin32 = d[0]
			self.dNum_dec = int(d[1], 2)
		# Get the real part instruction and data, with format of binStr
		self.instruction = i[2:self.iNum_dec+3]
		PCList = [unsignBin32(int(self.PCInit_bin32, 2)+step*4) for step in range(self.iNum_dec)]
		self.instructionWithPC_bin32 = dict(zip(PCList, self.instruction))
		# If the data is out of the range, skip it
		self.data = d[2:self.dNum_dec+2] + ['0'*32 for i in range(1022)]
		# for key,value in self.instructionWithPC_bin32.items():
		# 	print(hex(int(key, 2))[2:].zfill(8), ':', Instruction(value).getInsName())

	def setControl(self, ALUSrc = -1, ALUOp = -1, RegDst = -1, DoMult = -1, 
							MemWrite = -1, MemRead = -1, BrcOp = -1, 
							RegWrite = -1, MemtoReg = -1):
		# ALUSrc, ALUOp, RegDst, MemWrite, MemRead, BrcOp, RegWrite, MemtoReg
		self.controlEX['ALUSrc']   = ALUSrc
		self.controlEX['ALUOp']    = ALUOp
		self.controlEX['RegDst']   = RegDst
		self.controlEX['DoMult']   = DoMult
		self.controlDM['MemWrite'] = MemWrite
		self.controlDM['MemRead']  = MemRead
		self.controlDM['BrcOp']    = BrcOp
		self.controlWB['RegWrite'] = RegWrite
		self.controlWB['MemtoReg'] = MemtoReg

	def resetControl(self):
		for c in [self.controlEX, self.controlDM, self.controlWB]:
			for s in c:
				c[s] = -1

	def pipelineWork(self):
		# Do the first IF
		self.PC_bin32 = self.PCInit_bin32
		self.r.set('PC', self.PC_bin32)
		self.r.set(29, self.spInit_bin32)
		self.doIF()

		# print('After Do: ')
		# self.printPipeline()
		# self.printControlBuffer()
		# print('\n\n')
		
		# DM->DM_WB
		self.bufferDM()
		# EX->EX_DM
		self.bufferEX()
		# ID->ID_EX
		self.bufferID()
		# IF->IF_ID
		self.bufferIF()
		
		# print('test in work')
		# print('PCSel: ', self.branchSignal['PCSel'])
		
		# print('After Buffer: ')
		# self.printPipeline()
		# self.printControlBuffer()
		# print('\n\n')

		currentSnapshot = self.getSnapshotStr(cycle = 0)
		self.snapshotStr += currentSnapshot
		# print(currentSnapshot)
		self.cycleCnt_dec += 1
		while True:
			PCMuxOp0_bin32 = self.branchPC_bin32
			PCMuxOp1_bin32 = self.PCAdder(self.PC_bin32, unsignBin32(1)) # Normal add 1 for PC
			nextPC_bin32 = self.mux(self.branchSignal['PCSel'], PCMuxOp0_bin32, PCMuxOp1_bin32)
			self.PC_bin32 = self.mux(self.hazardSignal['PCWrite'], self.PC_bin32, nextPC_bin32)
			self.r.set('PC', self.PC_bin32)
			
			if not self.pushStage():
				break

			if self.WB.insName == 'HALT':
				break

	def pushStage(self):
		self.forwardDetec()
		self.doWB()
		self.finalSet()
		self.doDM()
		self.doEX()
		self.doID()
		self.hazardDetec()
		self.branchForwardDetec()
		self.branchDetec()
		self.doIF()


		currentSnapshot = self.getSnapshotStr()
		self.snapshotStr += currentSnapshot
		# print(currentSnapshot)

		if self.errorDetect():
			return False # Stop the pushSatge

		# print('After Do: ')
		# self.printPipeline()
		# self.printControlBuffer()
		# print(self.ID_EX.controlBuffer)
		# print(self.forwardSignal)
		# print(self.hazardSignal)
		# print(self.branchSignal)
		# print('\n\n')


		# Put info into stageBuffer		
		self.bufferDM()
		self.bufferEX()
		self.bufferID()
		self.bufferIF()

		# print('After Buffer: ')
		# self.printPipeline()
		# self.printControlBuffer()
		# print(self.forwardSignal)
		# print(self.hazardSignal)
		# print(self.branchSignal)
		# print('\n\n')
				
		# Add the iCnt normally
		self.cycleCnt_dec += 1
		return True # Can do next step without break

	def doIF(self):
		# If the branch pc is not in the pc list, we use 0x00000000 instead
		if self.IFFlushThisCycle == True and self.branchSignal['IFFlush'] == 1 \
				and not(self.PC_bin32 in list(self.instructionWithPC_bin32.keys())):
			self.IF.insHexStr_hex8 = '0'*8
			self.IF.insBinStr_bin32 = '0'*32
			self.IF.PC_bin32 = self.PC_bin32
			return
		# If branch or jump out of the PC range
		if not(self.PC_bin32 in list(self.instructionWithPC_bin32.keys())):
			self.IF.insHexStr_hex8 = '0'*8
			self.IF.insBinStr_bin32 = '0'*32
			self.IF.PC_bin32 = self.PC_bin32
			return 

		self.IF.insHexStr_hex8 = hex(int(self.instructionWithPC_bin32[self.PC_bin32], 2))[2:].zfill(8)
		self.IF.insBinStr_bin32 = self.instructionWithPC_bin32[self.PC_bin32]
		self.IF.PC_bin32 = unsignBin32(int(self.PC_bin32, 2) + 4) # Add 4 and store in buffer

	def bufferIF(self):
		if self.IFFlushThisCycle == True and self.branchSignal['IFFlush'] == 1:
			self.IF_ID.bufferDict = ({'insHexStr_hex8': '0'*8, 'insBinStr_bin32': '0'*32,
										'PC_bin32': self.IF.PC_bin32})
			return

		if self.IDLock:
			# Use the content in ID to implement the IF_ID stage
			ins = self.ID.ins
			PC_bin32 = self.ID.PC_bin32
			self.IF_ID.bufferDict = ({'insHexStr_hex8': ins.hexStr, 'insBinStr_bin32': ins.binStr,
										'PC_bin32': PC_bin32})
			return 
	
		self.IF_ID.bufferDict = ({'insHexStr_hex8': self.IF.insHexStr_hex8, 'insBinStr_bin32': self.IF.insBinStr_bin32, 
										'PC_bin32': self.IF.PC_bin32})

	def branchDetec(self):
		EquRst = -1
		sig = self.branchSignal
		bType = self.branchForwardType
		# Because the writeData is not in WB only in DE_WB currently, so we do the mux in WB ahead
		WBMuxOp0_bin32 = self.DM_WB.bufferDict['readDataFromALU_bin32']
		WBMuxOp1_bin32 = self.DM_WB.bufferDict['readDataFromMem_bin32']
		WBMuxSig = self.DM_WB.controlBuffer.get('WB', self.controlWB)['MemtoReg']
		WBWriteData_bin32 = self.mux(WBMuxSig, WBMuxOp0_bin32, WBMuxOp1_bin32)
		# Do target address adder	
		if self.ID.insName in ['BEQ', 'BNE', 'BGTZ']:
			self.branchPC_bin32 = self.PCAdder(self.ID.PC_bin32, self.ID.imdt_bin32) # We do this func after doID()
		elif self.ID.insName == 'JR':
			# Here JR also need the fwd
			self.branchPC_bin32 = self.mux(int(bType[0]), self.ID.readData1_bin32, WBWriteData_bin32, self.EX_DM.bufferDict['ALURst_bin32'])

		elif self.ID.insName in ['J', 'JAL']:
			self.branchPC_bin32 = self.PC_bin32[:4] + (self.ID.ins.address).zfill(26) + '00'


		# Part for forwarding 
		# rs
		# using the [-32:] solving the problem of overflow
		equOp0 = self.mux(int(bType[0]), self.ID.readData1_bin32, WBWriteData_bin32[-32:], self.EX_DM.bufferDict['ALURst_bin32'][-32:])
		# rt
		equOp1 = self.mux(int(bType[1]), self.ID.readData2_bin32, WBWriteData_bin32[-32:], self.EX_DM.bufferDict['ALURst_bin32'][-32:])
		# Do comparator
		if equOp0 == equOp1:
			EquRst = 1
		else:
			EquRst = 0
		# Change the PCSel for next PC choosing 
		# Here we also need to consider the if stall now, if stall, we do the flush next cycle
		if self.hazardSignal['IF_IDWrite'] == 1:
			if self.ID.insName == 'BEQ' and EquRst == 1:
				sig['PCSel'] = 0 # DO branch add
				# At first, I want to use IFFlishThisCycle and branchSignal['IFFlush'] to control the 
				# flush in this or next cycle like the stall, but no need do it now
				self.IFFlushThisCycle = True
				sig['IFFlush'] = 1
			elif self.ID.insName == 'BNE' and EquRst == 0:
				sig['PCSel'] = 0 # Do branch add
				self.IFFlushThisCycle = True
				sig['IFFlush'] = 1
			elif self.ID.insName == 'BGTZ' and (signInt(equOp0, 2) > 0):
				sig['PCSel'] = 0 # Do branch add
				self.IFFlushThisCycle = True
				sig['IFFlush'] = 1
			elif self.ID.insName in ['J', 'JR', 'JAL']:
				sig['PCSel'] = 0
				self.IFFlushThisCycle = True
				sig['IFFlush'] = 1
			else:
				sig['PCSel'] = 1
				self.IFFlushThisCycle = False
				sig['IFFlush'] = 0

	def branchForwardDetec(self):
		# Foewarding for branch
		EX_DM_RegWrite = self.EX_DM.controlBuffer['WB']['RegWrite']
		DM_WB_RegWrite = self.DM_WB.controlBuffer['WB']['RegWrite']
		EX_DM_Rd = self.EX_DM.bufferDict.get('writeRgst_bin5', 'wr') 
		DM_WB_Rd = self.DM_WB.bufferDict.get('writeRgst_bin5', 'wr') 
		ID_Rs = self.ID.ins.rs
		ID_Rt = self.ID.ins.rt
		branch_20 = ( EX_DM_RegWrite and (EX_DM_Rd != '0'*5) and (EX_DM_Rd == ID_Rs) )
		branch_02 = ( EX_DM_RegWrite and (EX_DM_Rd != '0'*5) and (EX_DM_Rd == ID_Rt) )
		branch_10 = ( DM_WB_RegWrite and (DM_WB_Rd != '0'*5) and (not branch_20) and DM_WB_Rd == ID_Rs )
		branch_01 = ( DM_WB_RegWrite and (DM_WB_Rd != '0'*5) and (not branch_02) and DM_WB_Rd == ID_Rt )
		# print('branch_10', branch_10)
		if self.ID.insName in ['BEQ', 'BNE']:
			if branch_02 and branch_20:
				self.branchForwardType = '22'
			# elif branch_01 and branch_10:
			# 	self.branchForwardType = '11'
			# elif branch_02 and branch_10:
			# 	self.branchForwardType = '12'
			# elif branch_20 and branch_01:
			# 	self.branchForwardType = '21'
			elif branch_20:
				self.branchForwardType = '20'
			elif branch_02:
				self.branchForwardType = '02'
			# elif branch_10:
			# 	self.branchForwardType = '10'
			# elif branch_01:
			# 	self.branchForwardType = '01'
			else:
				self.branchForwardType = '00'
		elif self.ID.insName in ['BGTZ', 'JR']:
			if branch_20:
				self.branchForwardType = '20'
			# elif branch_10:
			# 	self.branchForwardType = '10'
			else:
				self.branchForwardType = '00'
		else:
			self.branchForwardType = '00'
		# print('-'*10)
		# print('test in branch fwd')
		# print('cycle', self.cycleCnt_dec)
		# print('fwdtype',self.branchForwardType)
		# print(self.r.getBinByBin())


	def hazardAdd(self):
		for key, value in self.hazardSignal.items():
			self.hazardSignal[key] = value - 1

	def hazardSub(self): 
		for key, value in self.hazardSignal.items():
			self.hazardSignal[key] = value + 1

	def hazardMaintain():
		pass

	def hazardDetec(self):
		ID_EX_Rt_bin5 = self.ID_EX.bufferDict['rt_bin5']
		ID_EX_Rd_bin5 = self.ID_EX.bufferDict['rd_bin5']
		ID_EX_WrtReg_bin5 = self.mux(self.ID_EX.controlBuffer['EX']['RegDst'], ID_EX_Rt_bin5, ID_EX_Rd_bin5)
		ID_EX_RegWrite = self.ID_EX.controlBuffer['WB']['RegWrite']
		ID_EX_MemRead = self.ID_EX.controlBuffer['DM']['MemRead']
		EX_DM_WrtReg_bin5 = self.EX_DM.bufferDict['writeRgst_bin5']
		EX_DM_RegWrite = self.EX_DM.controlBuffer['WB']['RegWrite']
		EX_DM_MemRead = self.EX_DM.controlBuffer['DM']['MemRead']
		IF_ID_Rt_bin5 = Instruction(self.IF_ID.bufferDict['insBinStr_bin32']).rt
		IF_ID_Rs_bin5 = Instruction(self.IF_ID.bufferDict['insBinStr_bin32']).rs
		IF_ID_insName = Instruction(self.IF_ID.bufferDict['insBinStr_bin32']).getInsName().upper()
		ID_Rt_bin5 = self.ID.ins.rt
		ID_Rs_bin5 = self.ID.ins.rs	
		# Done ID just now, the control signal is in self but not in buffer
		ID_ALUSrc = self.controlEX['ALUSrc']
		# Load-stall
		if (ID_EX_MemRead > 0) and (ID_EX_Rt_bin5 != '0'*5) and (IF_ID_insName != 'NOP') and \
				( (ID_EX_Rt_bin5 == IF_ID_Rs_bin5 and not IF_ID_insName in ['LUI', 'SRL', 'SLL', 'SRA'])
				or ( ID_ALUSrc != 1 and ID_EX_Rt_bin5 == IF_ID_Rt_bin5 and not (IF_ID_insName in ['SW', 'SH', 'SB']+['BGTZ']+['MFHI', 'MFLO']) )
				or ( (IF_ID_insName in ['SW', 'SH', 'SB']) and ID_EX_Rt_bin5 == IF_ID_Rt_bin5 ) ):  
				# If here use ID_ALUSrc == 0, the BNE etc. will not in
				# (ID_EX_Rt_bin5 == IF_ID_Rs_bin5 or ID_EX_Rt_bin5 == IF_ID_Rt_bin5):
				# (not IF_ID_insName in ['BNE', 'BEQ', 'BGTZ']):
			# print('-'*10)
			# print('test in hazard detect')
			# print('cycle', self.cycleCnt_dec)
			# print('IF_ID_insName', IF_ID_insName)
			# print('ID_EX_Rt_bin5', ID_EX_Rt_bin5)
			# print('IF_ID_Rs_bin5', IF_ID_Rs_bin5)
			self.hazardSignal['PCWrite'] = 0
			self.hazardSignal['IF_IDWrite'] = 0
			self.hazardSignal['controlWrite'] = 0
			# self.hazardAdd()
			self.IDLock = True
			return True
		# Branch-stall, stall one cycle
		# No need for hazard for data witten into 0
		elif (not ID_EX_MemRead) and \
			( ( ((ID_EX_WrtReg_bin5 == IF_ID_Rt_bin5 and ID_EX_WrtReg_bin5 != '0'*5) or (ID_EX_WrtReg_bin5 == IF_ID_Rs_bin5 and ID_EX_WrtReg_bin5 != '0'*5)) and ID_EX_RegWrite and (IF_ID_insName in ['BNE', 'BEQ']) )
			or (ID_EX_WrtReg_bin5 == IF_ID_Rs_bin5 and ID_EX_RegWrite and ID_EX_WrtReg_bin5 != '0'*5 and IF_ID_insName in ['BGTZ', 'JR']) ):

			 # and (IF_ID_Rt_bin5 != IF_ID_Rs_bin5)

			# print('-'*20)
			# print('test in hazard')
			# print('cycle', self.cycleCnt_dec)
			# print(IF_ID_insName)
			# print('IF_ID_Rt_bin5', IF_ID_Rt_bin5)
			# print('IF_ID_Rs_bin5', IF_ID_Rs_bin5)
			# print('ID_EX_WrtReg_bin5', ID_EX_WrtReg_bin5)
			self.hazardSignal['PCWrite'] = 0
			self.hazardSignal['IF_IDWrite'] = 0
			self.hazardSignal['controlWrite'] = 0
			# self.hazardAdd()
			self.IDLock = True
			return True
		# Branch-Load-stall, stall two cycles
		elif (EX_DM_MemRead > 0) and \
			( (( (EX_DM_WrtReg_bin5 == IF_ID_Rt_bin5 and EX_DM_WrtReg_bin5 != '0'*5) or (EX_DM_WrtReg_bin5 == IF_ID_Rs_bin5 and EX_DM_WrtReg_bin5 != '0'*5)) and (IF_ID_insName in ['BNE', 'BEQ']))
			or (EX_DM_WrtReg_bin5 == IF_ID_Rs_bin5 and EX_DM_WrtReg_bin5 and IF_ID_insName in ['BGTZ', 'JR']) ):
			# print('test', 3)
			self.hazardSignal['PCWrite'] = 0
			self.hazardSignal['IF_IDWrite'] = 0
			self.hazardSignal['controlWrite'] = 0
			self.IDLock = True
			return True

		self.hazardSignal['PCWrite'] = 1
		self.hazardSignal['IF_IDWrite'] = 1
		self.hazardSignal['controlWrite'] = 1
		# self.hazardMaintain()
		return False

	def doID(self):
		# if ((self.IDLock == True and self.hazardSignal['IF_IDWrite'] == 1)):
		if (self.IDLock == True):
		     # or (self.IDLock2 == True and self.hazardSignal['IF_IDWrite'] == 0)):
			self.IDLock = False # Do nothing in ID and Unlock the ID stage. 

		# Using the Instruction class to parse the row binStr
		self.ID.ins = Instruction(self.IF_ID.bufferDict['insBinStr_bin32'])
		# Get the insName and the component after creating the object
		self.ID.insName = self.ID.ins.getInsName().upper()
		insName = self.ID.insName	
		readRgst1_bin5 = self.ID.ins.rs
		readRgst2_bin5 = self.ID.ins.rt
		

		imdt_bin16 = self.ID.ins.binStr[-16:] # The length of immediate, but not always immediate
		self.ID.PC_bin32 = self.IF_ID.bufferDict['PC_bin32']
		self.ID.readData1_bin32 = self.r.getBinByBin(readRgst1_bin5)
		self.ID.readData2_bin32 = self.r.getBinByBin(readRgst2_bin5)
		self.ID.imdt_bin32 = signZfill(imdt_bin16, 32) # Do sign extend from 16 to 32
		self.ID.rt_bin5 = self.ID.ins.rt
		self.ID.rd_bin5 = self.ID.ins.rd	
		# Control unit
		'''
		ALUSrc:   The Op1 of ALU is rt(0) or imdt(1)
		ALUOp:    No use currently
		RegDst:   The dst of the reg need to be wrote, rt(0) or rd(1)
		MemWrite: Only save instruction can do write mem, also presents the offset
		MemRead:  Only load instruction can do read mem, also presents the offset
		BrcOp:    The string of the name of branch instruction
		RegWrite: Mainly use for forward detection  
		MemtoReg: Need to put data into reg using ALURst(0) or mem data(1), or not(-1)
		'''
		if insName in ['LW', 'LH', 'LHU', 'LB', 'LBU']:
			if insName == 'LW':
				offset = 4
			elif insName == 'LH':
				offset = 2
			elif insName == 'LHU':
				offset = 20
			elif insName == 'LB':
				offset = 1
			elif insName == 'LBU':
				offset = 10
			self.setControl(ALUSrc = 1, ALUOp = -1, RegDst = 0, 
							MemWrite = 0, MemRead = offset, BrcOp = -1, 
							RegWrite = 1, MemtoReg = 1)
		elif insName in ['SW', 'SH', 'SB']:
			if insName == 'SW':
				offset = 4
			elif insName == 'SH':
				offset = 2
			elif insName == 'SB':
				offset = 1
			self.setControl(ALUSrc = 1, ALUOp = -1, RegDst = 0, DoMult = 0,
							MemWrite = offset, MemRead = 0, BrcOp = -1,
							RegWrite = 0, MemtoReg = -1)
		elif insName in ['AND', 'OR', 'XOR', 'NOR', 'NAND'] + ['SLT'] \
							+ ['SLL', 'SRL', 'SRA']: # But do sll, srl, sra special in doEX
			self.setControl(ALUSrc = 0, ALUOp = -1, RegDst = 1, DoMult = 0, 
							MemWrite = 0, MemRead = 0, BrcOp = -1, 
							RegWrite = 1, MemtoReg = 0)
		elif insName in ['ANDI', 'ORI', 'NORI'] + ['SLTI'] + ['LUI']:
			self.setControl(ALUSrc = 1, ALUOp = -1, RegDst = 0, DoMult = 0, 
							MemWrite = 0, MemRead = 0, BrcOp = -1,
							RegWrite = 1, MemtoReg = 0)
		elif insName in ['SUB', 'ADD', 'ADDU']:
			self.setControl(ALUSrc = 0, ALUOp = -1, RegDst = 1, DoMult = 0,
							MemWrite = 0, MemRead = 0, BrcOp = -1,
							RegWrite = 1, MemtoReg = 0)
		elif insName in ['ADDI', 'ADDIU']:
			self.setControl(ALUSrc = 1, ALUOp = -1, RegDst = 0, DoMult = 0,
							MemWrite = 0, MemRead = 0, BrcOp = -1,
							RegWrite = 1, MemtoReg = 0)
		elif insName in ['BEQ', 'BNE', 'BGTZ']:
			self.setControl(ALUSrc = -1, ALUOp = -1, RegDst = -1, DoMult = 0,
							MemWrite = 0, MemRead = 0, BrcOp = insName, 
							RegWrite = 0, MemtoReg = 0)
		elif insName in ['J', 'JR']:
			self.setControl(ALUSrc = -1, ALUOp = -1, RegDst = -1, DoMult = 0,
							MemWrite = 0, MemRead = 0, BrcOp = insName,
							RegWrite = 0, MemtoReg = -1)
		elif insName in ['JAL']:
			self.setControl(ALUSrc = -1, ALUOp = -1, RegDst = -1, DoMult = 0,
							MemWrite = 0, MemRead = 0, BrcOp = insName,
							RegWrite = 1, MemtoReg = -1)
		elif insName in ['MULT', 'MULTU']:
			if insName == 'MULT':
				multOp = 1
			else:
				multOp = 2
			self.setControl(ALUSrc = 0, ALUOp = -1, RegDst = -1, DoMult = multOp,
							MemWrite = 0, MemRead = 0, BrcOp = -1, 
							RegWrite = 1, MemtoReg = -1) # Do write reg in the EX
		elif insName in ['MFHI', 'MFLO']:
			self.setControl(ALUSrc = -1, ALUOp = -1, RegDst = 1, DoMult = 0,
							MemWrite = 0, MemRead = 0, BrcOp = -1,
							RegWrite = 1, MemtoReg = 0)
		else:
			self.setControl(ALUSrc = -1, ALUOp = -1, RegDst = -1, 
						MemWrite = -1,  MemRead = -1, BrcOp = -1, 
						RegWrite = -1, MemtoReg = -1)

	def bufferID(self):
		if self.hazardSignal['IF_IDWrite']:
			self.ID_EX.controlBuffer = {'EX': self.controlEX.copy(), 'DM': self.controlDM.copy(), 'WB': self.controlWB.copy()}
			# Reset the control for the use of next instruction
			self.resetControl()
			self.ID_EX.bufferDict = {'ins': self.ID.ins, 'insName': self.ID.insName, 
										'PC_bin32': self.ID.PC_bin32,
										'readData1_bin32': self.ID.readData1_bin32, 'readData2_bin32': self.ID.readData2_bin32,
										'imdt_bin32': self.ID.imdt_bin32, 'rt_bin5': self.ID.rt_bin5, 'rd_bin5': self.ID.rd_bin5}
		else:
			# Insert a NOP by changing the way of buffering the ID
			self.ID_EX.controlBuffer = self.defaultControl
			self.ID_EX.bufferDict = {'ins': Instruction('0'*32), 'insName': 'NOP', 
										'PC_bin32': self.ID.PC_bin32,
										'readData1_bin32': self.ID.readData1_bin32, 'readData2_bin32': self.ID.readData2_bin32,
										'imdt_bin32': self.ID.imdt_bin32, 'rt_bin5': self.ID.rt_bin5, 'rd_bin5': self.ID.rd_bin5}

	def doEX(self):
		# Basic operation for each stage
		self.EX.ins = self.ID_EX.getBuffer('ins')
		self.EX.insName = self.ID_EX.getBuffer('insName')
		self.EX.PC_bin32 = self.ID_EX.getBuffer('PC_bin32')
		# Get the nickname
		insName = self.EX.insName
		control = self.ID_EX.controlBuffer['EX']
		buf = self.ID_EX.bufferDict
		
		PC_bin32 = buf['PC_bin32']
		readData1_bin32 = buf['readData1_bin32']
		readData2_bin32 = buf['readData2_bin32']
		imdt_bin32 = buf['imdt_bin32']
		rt_bin5 = buf['rt_bin5']
		rd_bin5 = buf['rd_bin5']
		WBWriteData_bin32 = self.WB.writeData_bin32

		readData1_bin32 = self.mux(self.forwardSignal['ALUOpMux0'], readData1_bin32, WBWriteData_bin32[-32:], self.EX_DM.bufferDict['ALURst_bin32'][-32:])
		ALUOp0_bin32 = readData1_bin32
		readData2_bin32 = self.mux(self.forwardSignal['ALUOpMux1'], readData2_bin32, WBWriteData_bin32[-32:], self.EX_DM.bufferDict['ALURst_bin32'][-32:])
		# print('-'*10)
		# print('cycle:', self.cycleCnt_dec)
		# print('ALUSrc', control['ALUSrc'])
		# print('ALUOpMux1', self.forwardSignal['ALUOpMux1'])
		# print('readData2_bin32', readData2_bin32)
		ALUOp1_bin32 = self.mux(control['ALUSrc'], readData2_bin32, imdt_bin32)

		ALUcontrol = insName

		if insName == 'MULT':
			self.EX.ALURst_bin64 = signBin(signInt(ALUOp0_bin32, 2) * signInt(ALUOp1_bin32, 2), num = 64)
		elif insName == 'MULTU':
			self.EX.ALURst_bin64 = bin(int(ALUOp0_bin32, 2) * int(ALUOp1_bin32, 2))[2:].zfill(64)
		else:
			self.EX.ALURst_bin32 = self.ALU(ALUcontrol, ALUOp0_bin32, ALUOp1_bin32)
		self.EX.writeData_bin32 = readData2_bin32 # The data wrote into mem is rt data
		
		# Special for JAL
		if insName == 'JAL':
			self.EX.writeRgst_bin5 = bin(31)[2:].zfill(5)
		else:
			self.EX.writeRgst_bin5 = self.mux(control['RegDst'], rt_bin5, rd_bin5)

		# Do it here
		if insName in ['MULT', 'MULTU']:
			self.r.set('HI', self.EX.ALURst_bin64[:32])
			self.r.set('LO', self.EX.ALURst_bin64[32:])
			if self.mulLock == True:
				self.mulError = True # Get the error
			self.mulLock = True
			
	def bufferEX(self):
		# Because of the pass of controlBuffer, we need to do buffer from back
		self.EX_DM.controlBuffer = {'EX': self.ID_EX.controlBuffer['EX'].copy(), 
									'DM': self.ID_EX.controlBuffer['DM'].copy(), 'WB': self.ID_EX.controlBuffer['WB'].copy()}
		self.EX_DM.bufferDict = {'ins': self.EX.ins, 'insName': self.EX.insName, 
									'PC_bin32': self.EX.PC_bin32,
									'jumpPC_bin32': self.EX.jumpPC_bin32, 
									'jumpControl': self.EX.jumpControl,
									# 'ALURst_bin64': self.EX.ALURst_bin64,
									'ALURst_bin32': self.EX.ALURst_bin32,
									'writeData_bin32': self.EX.writeData_bin32,
									'writeRgst_bin5': self.EX.writeRgst_bin5}

	def doDM(self):
		self.DM.ins = self.EX_DM.getBuffer('ins')
		self.DM.insName = self.EX_DM.getBuffer('insName')
		self.DM.PC_bin32 = self.EX_DM.getBuffer('PC_bin32')
		insName = self.DM.insName
		buf = self.EX_DM.bufferDict
		control = self.EX_DM.controlBuffer.get('DM', self.controlDM.copy())

		address_bin32 = buf['ALURst_bin32']
		writeData_bin32 = buf['writeData_bin32']

		# Do write or read in the function dataMemory()
		self.DM.readDataFromMem_bin32 = self.dataMemory(control['MemRead'], control['MemWrite'], address_bin32, writeData_bin32)
		self.DM.readDataFromALU_bin32 = buf['ALURst_bin32']
		self.DM.writeRgst_bin5 = buf['writeRgst_bin5']

	def bufferDM(self):
		self.DM_WB.controlBuffer = {'EX': self.EX_DM.controlBuffer['EX'].copy(), 
									'DM': self.EX_DM.controlBuffer['DM'].copy(), 'WB': self.EX_DM.controlBuffer['WB'].copy()}
		self.DM_WB.bufferDict = {'ins': self.DM.ins, 'insName': self.DM.insName,
									'PC_bin32': self.DM.PC_bin32,
									'readDataFromMem_bin32': self.DM.readDataFromMem_bin32, 
									'readDataFromALU_bin32': self.DM.readDataFromALU_bin32,
									# 'readDataFromALU_bin64': self.DM.readDataFromALU_bin64,
									'writeRgst_bin5': self.DM.writeRgst_bin5}


	def doWB(self):
		self.WB.ins = self.DM_WB.getBuffer('ins')
		self.WB.insName = self.DM_WB.getBuffer('insName')
		self.WB.PC_bin32 = self.DM_WB.getBuffer('PC_bin32')
		insName = self.WB.insName
		buf = self.DM_WB.bufferDict
		control = self.DM_WB.controlBuffer.get('WB', self.controlWB)

		muxOp0_bin32 = buf['readDataFromALU_bin32']
		muxOp1_bin32 = buf['readDataFromMem_bin32']
		self.WB.writeRgst_bin5 = buf['writeRgst_bin5']
		if self.WB.insName in ['JAL']:
			self.WB.writeData_bin32 = self.WB.PC_bin32
		else:
			self.WB.writeData_bin32 = self.mux(control['MemtoReg'], muxOp0_bin32, muxOp1_bin32)

	def errorDetect(self):
		# For write 0 error
		writeRgst_bin5 = self.WB.writeRgst_bin5
		ins = self.WB.ins
		errorFlag = False
		if writeRgst_bin5 == '0'*5 and self.DM_WB.controlBuffer['WB']['RegWrite']\
			and not (self.WB.insName == 'NOP') \
			and not (ins.getInsName() == 'sll' and ins.rt == '0'*5 and ins.rd == '0'*5 and ins.shamt == '0'*5): # For NOP
			# Simplely use the way of plusing one on cycleCnt
			self.errordumpStr += 'In cycle {}: Write $0 Error\n'.format(self.cycleCnt_dec+1)
		# For Address Overflow
		if self.addressOverflowError == True:
			self.errordumpStr += 'In cycle {}: Address Overflow\n'.format(self.cycleCnt_dec+1)
			self.addressOverflowError = False
			errorFlag = True
		# For Misaligned 
		if self.misalignedError == True:
			self.errordumpStr += 'In cycle {}: Misalignment Error\n'.format(self.cycleCnt_dec+1)
			self.misalignedError = False
			errorFlag = True
		# For over write HI-LO
		if self.mulError == True:
			self.errordumpStr += 'In cycle {}: Overwrite HI-LO registers\n'.format(self.cycleCnt_dec+1)
			self.mulError = False
		# For Number Overflow
		if self.numberOverflowError == True:
			self.errordumpStr += 'In cycle {}: Number Overflow\n'.format(self.cycleCnt_dec+1)
			self.numberOverflowError = False

		return errorFlag



	def finalSet(self):
		control = self.DM_WB.controlBuffer.get('WB', self.controlWB)
		MemtoReg = control['MemtoReg']
		writeRgst_bin5 = self.WB.writeRgst_bin5
		writeData_bin32 = self.WB.writeData_bin32
		writeData_bin64 = self.WB.writeData_bin64
		if MemtoReg != -1:
			self.r.set(int(writeRgst_bin5, 2), writeData_bin32)
		
		# print('-'*20)
		# print('test in fianl set')
		# print('cycle', self.cycleCnt_dec)
		# print('wbins', self.WB.insName)
		# print('data', writeData_bin32)
		# print('reg',writeRgst_bin5)

		# Here we need to set the MemtoReg as -1 for skip the 'if' ahead here
		if self.WB.insName == 'JAL':
			self.r.set(31, self.WB.PC_bin32)

	def mux(self, signal, i0, i1, i2=0):
		if signal == 0:
			return i0
		elif signal == 1:
			return i1
		elif signal == 2:
			return i2
		elif signal == -1:
			return '0'

	def ALU(self, opType, op1_bin32, op2_bin32):
		if opType in ['LW', 'LH', 'LHU', 'LB', 'LBU'] + ['SW', 'SH', 'SB']:
			ALURst_bin32 = signBin(signInt(op1_bin32, 2) + signInt(op2_bin32, 2))
			ALURst_bin32 = self.checkNumberOverflow(ALURst_bin32)			
		elif opType in ['OR', 'ORI']:
			# To solve the problem of sign extending of imdt in ID
			if opType == 'ORI':
				op2_bin32 = op2_bin32[-16:]
			ALURst_bin32 = unsignBin32(int(op1_bin32, 2) | int(op2_bin32, 2))
		elif opType == 'XOR':
			ALURst_bin32 = unsignBin32(int(op1_bin32, 2) ^ int(op2_bin32, 2))
		elif opType in ['NOR', 'NORI']:
			if opType == 'NORI':
				op2_bin32 = op2_bin32[-16:]
			rstReverse = int(op1_bin32, 2) | int(op2_bin32, 2)
			ALURst_bin32 = unsignBin32(rstReverse ^ int('1'*32, 2))
		elif opType in ['AND', 'ANDI']:
			if opType == 'ANDI':
				op2_bin32 = op2_bin32[-16:]
			ALURst_bin32 = unsignBin32(int(op1_bin32, 2) & int(op2_bin32, 2))
		elif opType == 'NAND':
			rstReverse = int(op1_bin32, 2) & int(op2_bin32, 2)
			ALURst_bin32 = unsignBin32(rstReverse ^ int('1'*32, 2))
		elif opType in ['SLT', 'SLTI']:
			if signInt(op1_bin32, 2) < signInt(op2_bin32, 2):
				ALURst_bin32 = '0'*31 + '1'
			else:
				ALURst_bin32 = '0'*32
		elif opType == 'LUI':
			ALURst_bin32 = op2_bin32[-16:] + '0'*16
			# print('-'*10)
			# print('test in ALU')
			# print('ALURst', ALURst_bin32)
		elif opType == 'SUB':
			# Use [-32:] to cut it into 32 bits
			op2Reverse = signInt(signBin(-signInt(op2_bin32, 2))[-32:], 2)
			ALURst_bin32 = signBin(signInt(op1_bin32, 2) + op2Reverse)
			# print('-'*10)
			# print('test in SUB ALU')
			# print('cycle' ,self.cycleCnt_dec)
			# print('op2Reverse', op2Reverse)
			# print('-signInt(op2_bin32, 2)', -signInt(op2_bin32, 2))
			# print('signInt(op1_bin32)', signInt(op1_bin32, 2))
			# print('ALURst_bin32', ALURst_bin32)

			ALURst_bin32 = self.checkNumberOverflow(ALURst_bin32)
		elif opType in ['ADD', 'ADDI']:
			ALURst_bin32 = signBin(signInt(op1_bin32, 2) + signInt(op2_bin32, 2))
			ALURst_bin32 = self.checkNumberOverflow(ALURst_bin32)
		elif opType in ['ADDU', 'ADDIU']:
			ALURst_bin32 = unsignBin32(int(op1_bin32, 2) + int(op2_bin32, 2))
		elif opType == 'MFHI':
			ALURst_bin32 = self.r.getBin('HI')
			# Get the value in HI, so unlock the mulLock
			self.mulLock = False
		elif opType == 'MFLO':
			ALURst_bin32 = self.r.getBin('LO')
			self.mulLock = False
		elif opType == 'SLL':
			ALURst_bin32 = unsignBin32(int(op2_bin32, 2) << int(self.EX.ins.shamt, 2))[-32:]
			# print('-'*10)
			# print('test in ALU SLL')
			# print('cycleCnt_dec', self.cycleCnt_dec)
			# print(op2_bin32)
			# print(int(self.EX.ins.shamt, 2))
			# print(ALURst_bin32)
		elif opType == 'SRL':
			ALURst_bin32 = unsignBin32(int(op2_bin32, 2) >> int(self.EX.ins.shamt, 2))
			# print('-'*10)
			# print('test in ALU')
			# print('cycleCnt_dec', self.cycleCnt_dec)
			# print(op2_bin32)
			# print(int(self.EX.ins.shamt, 2))
		elif opType == 'SRA':
			sm = int(self.EX.ins.shamt, 2)
			ALURst_bin32 = signZfill(bin(int(op2_bin32, 2) >> sm)[2:].zfill(32-sm), 32)
			# print('-'*10)
			# print('test in SRA')
			# print('ALURst', ALURst_bin32)
		elif opType == 'JAL':
			ALURst_bin32 = self.EX.PC_bin32
		else:
			ALURst_bin32 = '0'*32
		return ALURst_bin32

	def add(self, op1_bin32, op2_bin32):
		return unsignBin32(int(op1_bin32, 2) + int(op2_bin32, 2))

	def PCAdder(self, PC_bin32, jump_bin32):
		return unsignBin32(int(PC_bin32, 2) + 4*signInt(jump_bin32, 2))

	def dataMemory(self, MemRead, MemWrite, address_bin32, writeData_bin32):
		# address_bin32 = self.checkNumberOverflow(address_bin32)
		address_dec = int(address_bin32, 2)
		if MemWrite > 0:
			if MemWrite == 4:
				align = 4
				writeData_bin32 = writeData_bin32[-32:]
			elif MemWrite == 2:
				align = 2
				writeData_bin32 = bin(int(writeData_bin32, 2) & int('0x0000FFFF', 16))[2:].zfill(16)[-16:]
			elif MemWrite == 1:
				align = 1
				writeData_bin32 = bin(int(writeData_bin32, 2) & int('0x000000FF', 16))[2:].zfill(8)[-8:]
			
			self.checkAddressOverflow(address_dec, align)
			self.checkMisaligned(address_dec, align)
			if not(self.addressOverflowError or self.misalignedError):
				self.data[address_dec//4] = self.data[address_dec//4][:(address_dec%4)*8] \
												+ writeData_bin32 \
												+ self.data[address_dec//4][(address_dec%4)*8+align*8:]
			# Must return a value to placehold the readData,
			# for save ins, the value will be stalled in mux in WB because the signal '-1'
			return '0'*32 

		if MemRead > 0:
			readData_bin32 = '0'*32
			if MemRead == 4:
				align = 4
			elif MemRead in [2, 20]: # Use 2 present lh, 20 for lhu
				align = 2
			elif MemRead in [1, 10]: # Use 1 present lb, 10 for lbu
				align = 1
			
			self.checkAddressOverflow(address_dec, align)
			self.checkMisaligned(address_dec, align)
			if not(self.addressOverflowError or self.misalignedError):
				if MemRead in [4, 2, 1]:
					readData_bin32 = signZfill(''.join(self.data[address_dec//4][(address_dec%4)*8: (address_dec%4)*8+8*align]), 32)
				elif MemRead in [10, 20]:
					readData_bin32 = (''.join(self.data[address_dec//4][(address_dec%4)*8: (address_dec%4)*8+8*align])).zfill(32)
			return readData_bin32

	def forwardDetec(self):
		ALUSrc = self.ID_EX.controlBuffer['EX']['ALUSrc']
		RegDst = self.ID_EX.controlBuffer['EX']['RegDst']
		MemRead = self.ID_EX.controlBuffer['DM']['MemRead']
		MemWrite = self.ID_EX.controlBuffer['DM']['MemWrite']
		EX_DM_RegWrite = self.EX_DM.controlBuffer['WB']['RegWrite']
		DM_WB_RegWrite = self.DM_WB.controlBuffer['WB']['RegWrite'] 
		EX_DM_Rd = self.EX_DM.bufferDict.get('writeRgst_bin5', 'wr') 
		DM_WB_Rd = self.DM_WB.bufferDict.get('writeRgst_bin5', 'wr') 
		ID_EX_Rs = self.ID_EX.bufferDict.get('ins', Instruction('0'*32)).rs
		ID_EX_Rt = self.ID_EX.bufferDict.get('ins', Instruction('0'*32)).rt
		ID_EX_BrcOp = self.ID_EX.controlBuffer['DM']['BrcOp']
		ID_EX_insName = self.ID_EX.bufferDict['insName']
		
		if not(ID_EX_insName in ['SLL', 'SRL', 'SRA', 'MFHI', 'MFLO', 'LUI', 'NOP']):
			flag_20 = ( EX_DM_RegWrite and (EX_DM_Rd != '0'*5) and (EX_DM_Rd == ID_EX_Rs) )
		else:
			flag_20 = False
		# Beacuse in save instruction, the rt is not the ALUSrc		
		if ALUSrc == 0 or (MemWrite and RegDst == 0): # rt 
			flag_02 = ( EX_DM_RegWrite and (EX_DM_Rd != '0'*5) and (EX_DM_Rd == ID_EX_Rt) )
		else:
			flag_02 = False
		if not(ID_EX_insName in ['SLL', 'SRL', 'SRA', 'MFHI', 'MFLO', 'LUI', 'NOP']):	
			flag_10 = ( DM_WB_RegWrite and (DM_WB_Rd != '0'*5) and (not flag_20) and (DM_WB_Rd == ID_EX_Rs) )
		else:
			flag_10 = False
		if ALUSrc == 0 or (MemWrite and RegDst == 0): # rt 
			flag_01 = ( DM_WB_RegWrite and (DM_WB_Rd != '0'*5) and (not flag_02) and (DM_WB_Rd == ID_EX_Rt) )
		else:
			flag_01 = False

		self.forwardType = '00'
		# If not the branch operator
		if ID_EX_BrcOp == -1:
			if flag_10 and flag_02:
				self.forwardType = '12'
			elif flag_20 and flag_01:
				self.forwardType = '21'
			elif flag_10 and flag_01:
				self.forwardType = '11'
			elif flag_20 and flag_02:
				self.forwardType = '22'
			elif flag_20:
				self.forwardType = '20'
			elif flag_02:
				self.forwardType = '02'
			elif flag_10:
				self.forwardType = '10'
			elif flag_01:
				self.forwardType = '01'
		self.forwardSignal = {'ALUOpMux0': int(self.forwardType[0]), 'ALUOpMux1': int(self.forwardType[1])}


	def checkNumberOverflow(self, putInData):
		# print('-'*10)
		# print('test in check')
		# print('cycle', self.cycleCnt_dec)
		# print(putInData)
		# print(signInt(putInData, 2))
		if (signInt(putInData, 2) > (2**31)-1) or (signInt(putInData, 2) < -(2**31)):
			self.numberOverflowError = True
			# print('here error')
			# only need the last 32 bits, if longer, cut it 
			putInData = putInData[-32:]
		return putInData

	def checkAddressOverflow(self, dataLoc, align):
		if dataLoc  > 1024-align or dataLoc < 0:
			self.addressOverflowError = True

	def checkMisaligned(self, dataLoc, align):
		if dataLoc % align != 0:
			self.misalignedError = True 

	def getSnapshotStr(self, cycle = 1):
		# rgstStr = self.r.getRegisterRptStr(cycle)
		if cycle == 0:
			rgstStr = self.r.getRegisterRptStr(cycle = 0)
			self.rgstStrReserve = ''
		else:
			rgstStr = self.rgstStrReserve
			self.rgstStrReserve = self.r.getRegisterRptStr(cycle)
		
		rgstStr += 'PC: {}\n'.format(self.r.rgstDict['PC'])
		stageStr = ''
		stageName = ['IF', 'ID', 'EX', 'DM', 'WB']
		bufferName = ['IF_ID', 'ID_EX', 'EX_DM', 'DM_WB']
		for s in stageName:
			if s == 'IF':
				stageStrApdx = ''
				if not self.hazardSignal['IF_IDWrite']:
					stageStrApdx = ' to_be_stalled'	
				if self.IFFlushThisCycle == True and self.branchSignal['IFFlush'] == 1:
					# self.branchSignal['IFFlush'] = 0
					# self.IFFlush = False
					stageStrApdx = ' to_be_flushed'
				stageStr += s + ': ' + '0x' + self.stageDict[s].insHexStr_hex8.upper() + stageStrApdx + '\n'
			elif s == 'ID':
				stageStrApdx = ''
				# Branch forwarding 
				fwd = self.branchForwardType
				if fwd[0] == '1':
					fwd = '0' + fwd[1]
				elif fwd[1] == '1':
					fwd = fwd[0] + '0'
				if fwd != '00':
					if fwd[0] != '0':
						fwd_rgst = 'rs'
						rgst_num = int(self.ID.ins.rs, 2)
						stageStrApdx += ' fwd_' + 'EX-DM'  + '_' + fwd_rgst + '_' + '$' + str(rgst_num)
					if fwd[1] != '0':
						fwd_rgst = 'rt'
						rgst_num = int(self.ID.ins.rt, 2)
						stageStrApdx += ' fwd_' + 'EX-DM'  + '_' + fwd_rgst + '_' + '$' + str(rgst_num)
				# Stalled
				if not self.hazardSignal['IF_IDWrite']:
					stageStrApdx = ' to_be_stalled'	
				stageStr += s + ': ' + self.stageDict[s].insName + stageStrApdx + '\n'
			elif s == 'EX':
				stageStrApdx = ''
				# Forwarding 
				fwd = self.forwardType
				if fwd != '00':
					fwd_from_list = ['', 'DM-WB', 'EX-DM']
					if fwd[0] != '0':
						fwd_from = fwd_from_list[int(fwd[0])]
						fwd_rgst = 'rs'
						rgst_num = int(self.ID_EX.bufferDict['ins'].rs, 2)
						stageStrApdx += ' fwd_' + fwd_from  + '_' + fwd_rgst + '_' + '$' + str(rgst_num) 
					if fwd[1] != '0':
						fwd_from = fwd_from_list[int(fwd[1])]
						fwd_rgst = 'rt'
						rgst_num = int(self.ID_EX.bufferDict['ins'].rt, 2)
						stageStrApdx += ' fwd_' + fwd_from  + '_' + fwd_rgst + '_' + '$' + str(rgst_num) 
				stageStr += s + ': ' + self.stageDict[s].insName + stageStrApdx + '\n'
			else:
				stageStr += s + ': ' + self.stageDict[s].insName + '\n'
		stageStr += '\n\n'
		cycleStr = 'cycle ' + str(self.cycleCnt_dec) + '\n'
		return cycleStr + rgstStr + stageStr

	# def printPipeline(self):
	# 	tab = PrettyTable()
	# 	filed = ['IF', 'IF_ID', 'ID', 'ID_EX', 'EX', 'EX_DM', 'DM', 'DM_WB', 'WB'] 
	# 	tab.field_names = filed
	# 	rowStr = []
	# 	for f in filed:
	# 		if f == 'IF':
	# 			rowStr.append('0x'+self.IF.insHexStr_hex8.upper())
	# 		elif f == 'IF_ID':
	# 			rowStr.append('0x'+self.IF_ID.bufferDict['insHexStr_hex8'].upper())
	# 		elif len(f) == 2:
	# 			rowStr.append(eval('self.{}.insName'.format(f)))
	# 		else:
	# 			rowStr.append(eval("self.{}.bufferDict['insName']".format(f)))
	# 	tab.add_row(rowStr)
	# 	print(tab)

	# def printControlBuffer(self):
	# 	tab = PrettyTable()
	# 	filed = ['IF_ID', 'ID_EX', 'EX_DM', 'DM_WB']
	# 	tab.field_names = ['buffer', 'insName', 'ALUSrc', 'ALUOp', 'RegDst', 'MemWrite', 'MemRead', 'BrcOp', 'RegWrite', 'MemtoReg']
	# 	signal = {'EX': ['ALUSrc', 'ALUOp', 'RegDst'], 
	# 				'DM': ['MemWrite', 'MemRead', 'BrcOp'], 
	# 				'WB': ['RegWrite', 'MemtoReg']}
	# 	for f in filed:
	# 		rowList = []
	# 		if f == 'IF_ID':
	# 			rowList.append(eval("Instruction(self.IF_ID.bufferDict['insBinStr_bin32']).getInsName().upper()"))
	# 		else:
	# 			rowList.append(eval("self.{}.bufferDict['insName']".format(f)))
	# 		rowList.append(eval("self.{}.controlBuffer['EX']['ALUSrc']".format(f)))
	# 		rowList.append(eval("self.{}.controlBuffer['EX']['ALUOp']".format(f)))
	# 		rowList.append(eval("self.{}.controlBuffer['EX']['RegDst']".format(f)))
	# 		rowList.append(eval("self.{}.controlBuffer['DM']['MemWrite']".format(f)))
	# 		rowList.append(eval("self.{}.controlBuffer['DM']['MemRead']".format(f)))
	# 		rowList.append(eval("self.{}.controlBuffer['DM']['BrcOp']".format(f)))
	# 		rowList.append(eval("self.{}.controlBuffer['WB']['RegWrite']".format(f)))
	# 		rowList.append(eval("self.{}.controlBuffer['WB']['MemtoReg']".format(f)))
	# 		tab.add_row([f]+rowList)
	# 	print(tab)





