#!/usr/bin/env python3
from pipeline import *
from side_func import *

iBinList, dBinList =  handleFile()
p = Pipeline()
p.parseInsAndData(iBinList, dBinList)
p.pipelineWork()

writeSnapshot(p.snapshotStr)
writeErrorDump(p.errordumpStr)
