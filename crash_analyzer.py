# -*- coding: utf-8 -*
#!/usr/bin/python

import datetime
import dateutil.parser
import json

#日志扫描器，生成ResolvedInfo
class LogScanner:
	def scan(self, logFilePath, lineParser):
		with open(logFilePath) as f:
			linesArr = f.read().splitlines()

			for lnStr in linesArr:
				lnData = lineParser.parse(lnStr)
				print("parsed:" + json.dumps(lnData))

#解析一行日志里的tab隔开的字符串
class StringReader:
	def read(self, lnStr, start):
		lenOfStr = len(lnStr)
		if (start >= lenOfStr):
			return None

		idx = start

		# print("start char:"+lnStr[start])

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
					continue
			else:
				if (lnStr[idx] == ' '):
					# print("start, stop:" + str(startIdx) + "," + str(idx))
					result = lnStr[startIdx:idx]
					break

			idx = idx + 1

		if (result == None and hasBegin):
			result = lnStr[startIdx : idx]

		return result


class LineParser:
	def __init__(self):
		strRdr = StringReader()
		formatter = [("Date", strRdr),
					("Time", strRdr),
					("PID", strRdr),
					("IGNORE", strRdr),
					("Level", strRdr),
					("Message", strRdr)
					]
		self.formatter = formatter

	def parse(self, lineStr):

		lnData = {}

		cursor = 0
		for name, rdr in self.formatter:
			val = rdr.read(lineStr, cursor)

			if (val != None):
				lnData[name] = val
				# print(val)
				cursor = cursor + len(val) + 1
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

	# for test
	logFilePath = "examples/test.log"

	scanner = LogScanner()
	lineParser = LineParser()

	scanner.scan(logFilePath, lineParser)


	