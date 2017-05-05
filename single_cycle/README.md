## Project Report
***

### Program Flow Chart
1. Get Data and Instruction

	&emsp;&emsp;In the function of```main()```, firstly, I transform the the content in the .bin file from hexadecimal into binary, then I get two list ```instruction``` and ```data``` which will be passed into the function ```simulator()```, furthermore another argument is ```registor``` -- a object of ```Registor``` class
<div style="text-align: center">
<img src="1.jpg"/>
2. Simulator

	&emsp;&emsp;The simulator is normally wraped by a ***while*** loop, the loop control the ```cycleCnt``` and ```iCnt```(instruction counter), beacause of the class ```Instruction``` which will be reported later, we can easily get the info of every instruction we are handling currently, so we can branch every instruction into the proper branch and do the proper computation, error detection, etc.  
	
	&emsp;&emsp;The cycleCnt will be added by 1 in every cycle, normally, iCnt also will be added by 1. But this circumstance will be breaked when we meet the branch condition.  
	
	&emsp;&emsp;Furthermore, the iCnt is the index of the instruction in the intruction list, while the pc is the fixed number of an instruction. 
</div>
<div style="text-align: center">
<img src="2.jpg"/>
</div>


### Detailed Description
1. Classes in My Project(OOP)
 + 	Instruction
 
	&emsp;&emsp;All the instruction will be transformed into the object of this class, I can easily get every specific part by the the symbol ```.```.
 
	 ```python
	 binStr: 
	 	the binary string format of this instruction, 32 bits
	 insType: 
	 	the type, can be 'r', 'i', 'j' and 's'
	 parse(): 
	 	the function can parse the fundamental part, like 'rt', 'rs', etc.
	 ```  
 + Data

 	&emsp;&emsp;Just like the Instruction class, the Data class makes it easy to get the binary format of the data. It's just like the parser of the data.
 
	 ```python
	 binStr: 
	 	I can easily get the binary strings which are store in a list
	 ```
 + Register
 
 	&emsp;&emsp;This class is just like a simulator registor in this project, it has 32 registers and LO, HI, PC as its attributes. The condition of each cycle is also stored in here. Here are some main methords

	```python
	getSignDecByBin(self, idx): 
		get the decimal format in the register, and the rsgister index is in binary format
	set(self, idx, value): 
		set the value into the register with idx
	errorDetection(self, idx = -1, value = -1, isNop = False, isCNO = False, isCANO = False, AN = 0, mulSet = False, mulGet = False, dataLoc = 0, align = 	0, offset = 0): 
		the error dectection part is implemented in register class
	changeRgst(self, idxList , isInt = False): 
		store the changed registor in here, for print the snapshot
	
	```
	
2. Error Detection
	
	&emsp;&emsp;I insert the error dectection module into the Register class, I will psss the value as the arguments which are necessary for the dectection.  
	
	&emsp;&emsp;For example, for load instruction, I need to detect four kinds of error, ***Write to register $0***, ***Number overflow***, ***Memory address overflow***, ***Data misaligned***, so I need to implement the part of error dectec in load instruction branch like this:
	
	```
	if not r.errorDetection(idx = rgstIdx,
								isCANO = True, AN = signBin(loadLoc),
								dataLoc = loadLoc,
								align = align, offset = loadLoc):
				break
	```
	+ ```idx = rgstIdx```   
		This is for detect the ***Write to register $0***.
	+ ```isCANO = True, AN = signBin(loadLoc)```  
	 	Turn the check add numberflow(CANO) into true， and pass the add number(AN), here for distinguishing the ***Number overflow*** of load/save from add/sub..., I use CANO and CNO.  
	+ ```dataLoc = loadLoc```  
		Passing the loadLoc which is a signed decimal to detect the ***Memory address overflow***
	+ ```align = align, offset = loadLoc```  
	   For detecting the ***Data misaligned***

3. Side Functions  
	
	```python
	readBinFile(fileName):
		read the .bin file and get the hex string in a list
	hexToBin(hexList):
		transform the hex list into bin list
	signInt(binStr, figure):
		transform a signed bin-string into int 
	signBin(integer, num = 32):
		transform a int into a signed bin-string
	signZfill(binStr, length):
		sign extension on a bin-string
	writeSnapshot(content):
		write the sanpshot into the file
	writeErrorDump(content):
		write the error_dump into the file
	```

### Test Case Design

&emsp;&emsp;The most import part in my test case is a jump to the front of the initial pc, as the behaviours of the gloden simulator, in this case, the pc will jump back with the instruction of NOP to the initial pc and start again.		
&emsp;&emsp;Here is the details.  
		

			lw	  $0, 0($0)  	# "write to $0"
			lw    $1, 16($0) 	# $1 = 7fffffff
			addi  $2, $1, 4  	# $2 = $1 + 4, "Number Overflow", $2 = 80000003
			bne   $3, $4, flag  # ($3 = $4 = 0) if $3 != $4, jump to flag
			xor   $1, $2, $3 	# $3 = $2 xor $1, $3 = fffffffc, next bne will jump to flag
			j 	  0x0000002c 	# for test jumping to the front of init pc
	flag: 	addi  $2, $1, 5  	# $2 = $1 + 5, "Number Overflow", $2 = 80000004

 
