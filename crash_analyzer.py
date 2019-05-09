# -*- coding: utf-8 -*
#!/usr/bin/python

import json

#日志扫描器，生成ResolvedInfo
class LogScanner:
	def scan(self, logFilePath, lineParser):
		ctx = LogContext()

		with open(logFilePath) as f:

			linesArr = f.read().splitlines()

			print("total lines:" + str(len(linesArr)))

			lnDataList = []

			lnNum = 0
			for lnStr in linesArr:
				lnNum = lnNum + 1
				#print("start parse:" + lnStr)
				lnData = lineParser.parse(lnStr)
				lnData["Line"] = lnNum
				#self.printLineData(lnData)
				lnDataList.append(lnData)

			ctx.setLines(lnDataList)

		return ctx



	def printLineData(self, lnData):
		if ("Message" in lnData):
			print(lnData["Message"])

#解析一行日志里的tab隔开的字符串
class ReadToEndReader:
	def read(self, lnStr, start):
		lenOfStr = len(lnStr)
		if (start >= lenOfStr):
			return None, 0

		toIdx = lenOfStr
		return lnStr[start:toIdx], toIdx

class StringReader:
	def read(self, lnStr, start):

		lenOfStr = len(lnStr)
		if (start >= lenOfStr):
			return None, 0

		idx = start

		hasBegin = False
		startIdx = -1

		result = None
		while (idx < lenOfStr):

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
	def setLines(self, lines):
		self.lines = lines

class BaseKnowledge:
	def apply(self, logContext):
		pass

class Tip:
	def __init__(self, msg):
		self.msg = msg
		self.lines = []
		self.infos = []

	def addInfo(self, infoMsg):
		self.infos.append(infoMsg)

	def addRelatedLog(self, line):
		self.lines.append(line)

class Reporter:
	def report_to(path):
		pass


# knowledge impl #
class BaseInfoKnowledge(BaseKnowledge):
	def apply(self, logContext):
		totalLines = len(logContext.lines)
		foundCrash = False
		tip = Tip("基础信息")
		tip.addInfo("日志总行数：" + str(totalLines))

		for ln in logContext.lines:
			if ("Message" in ln):
				msg = ln["Message"]
				if (msg.find("exited due to signal") >= 0 or
					msg.find("app died") >= 0):
					foundCrash = True
					tip.addRelatedLog(ln)



		if (foundCrash):
			tip.addInfo("发现crash")

		return tip

class TooManyFileOpenKnowledge(BaseKnowledge):
	def apply(self, logContext):

		tip = None
		for ln in logContext.lines:
			if ("Message" in ln):
				#print(ln["Message"])
				if (ln["Message"].find("java.io.IOException: Too many open files") >= 0):
					if (tip == None):
						tip = Tip("文件句柄耗尽导致crash")

					tip.addRelatedLog(ln)

		return tip


#end impl

def showTip(index, tip):
	print(str(index) + ". " + tip.msg)

	if (tip.infos):
		for info in tip.infos:
			print(info)

	if (tip.lines):
		print ""
		print "相关日志："

		logLines = len(tip.lines)
		showLines = logLines
		hasMoreLog = False
		if (logLines > 10):
			showLines = 10
			hasMoreLog = True

		for lnNum in range(0, showLines):
			ln = tip.lines[lnNum]
			print("Line " + str(ln["Line"]) + ",\t" + ln["Message"])

		if (hasMoreLog):
			print("... has more " + str(logLines - 10) + " logs")

		print ""


if __name__=="__main__":
	print("===== crash analyze tool =====")

	#for test
	#logFilePath = "examples/crash-yafei.log"
	logFilePath = "examples/test.log"

	scanner = LogScanner()
	lineParser = LineParser()

	ctx = scanner.scan(logFilePath, lineParser)


	#knowledge database
	knowledgeDb = [
		BaseInfoKnowledge(),
		TooManyFileOpenKnowledge()
	]

	#tips container
	tips = []

	print "start analyze..."
	for kn in knowledgeDb:
		t = kn.apply(ctx)
		if (t):
			tips.append(t)

	print "analyze finished."
	print("===== report =====")	
	if (len(tips) > 0):
		index = 0
		for tip in tips:
			index = index + 1
			showTip(index, tip)

	else:
		print "没有找到线索"

