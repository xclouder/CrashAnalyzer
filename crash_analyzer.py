# -*- coding: utf-8 -*
#!/usr/bin/python

import json

#日志扫描器，生成ResolvedInfo
class LogScanner:
	def scan(self, logFilePath, lineParser):
		with open(logFilePath) as f:
			linesArr = f.read().splitlines()

			print("total lines:" + str(len(linesArr)))

			for lnStr in linesArr:
				#print("start parse:" + lnStr)
				lnData = lineParser.parse(lnStr)
				self.printLineData(lnData)
	def printLineData(self, lnData):
		if ("Message" in lnData):
			print(lnData["Message"])

#解析一行日志里的tab隔开的字符串
class ReadToEndReader:
	def read(self, lnStr, start):
		lenOfStr = len(lnStr)
		if (start >= lenOfStr):
			return None, 0

		toIdx = lenOfStr - 1
		return lnStr[start:toIdx], toIdx

class StringReader:
	def read(self, lnStr, start):

		lenOfStr = len(lnStr)
		if (start >= lenOfStr):
			return None, 0

		idx = start

		#("start char:"+lnStr[start])

		hasBegin = False
		startIdx = -1

		result = None
		while (idx < lenOfStr):
			#print("idx:" + str(idx))

			if (not hasBegin):
				if (lnStr[idx] != ' '):
					hasBegin = True
					startIdx = idx
			else:
				if (lnStr[idx] == ' '):
					#print("start, stop:" + str(startIdx) + "," + str(idx))
					result = lnStr[startIdx:idx]
					break

			idx = idx + 1

		if (result == None and hasBegin):
			result = lnStr[startIdx : idx]

		return result, idx


class LineParser:
	def __init__(self):
		strRdr = StringReader()
		read2EndRdr = ReadToEndReader()
		formatter = [("Date", strRdr),
					("Time", strRdr),
					("PID", strRdr),
					("IGNORE", strRdr),
					("Level", strRdr),
					("Message", read2EndRdr)
					]
		self.formatter = formatter

	def parse(self, lineStr):

		lnData = {}

		cursor = 0
		for name, rdr in self.formatter:
			val, toIndex = rdr.read(lineStr, cursor)

			if (val != None):
				#print("name:" + name + ", val:" + val)
				lnData[name] = val
				cursor = toIndex + 1
			else:
				break

		return lnData


# 解析后的crash信息
class LogContext:
	def test():
		pass

class Rule:
	def get():
		pass

class Reporter:
	def report_to(path):
		pass

if __name__=="__main__":
	print("===== crash analyze tool =====")


	# test = "05-01 00:15:48.162   625   646 E NetlinkEvent: NetlinkEvent::FindParam(): Parameter 'TIME_NS' not found"
	# rdr = StringReader()
	# data, idx = rdr.read(test, 25)
	# print("data:" + data)



	#for test
	logFilePath = "examples/test.log"

	scanner = LogScanner()
	lineParser = LineParser()

	scanner.scan(logFilePath, lineParser)


	