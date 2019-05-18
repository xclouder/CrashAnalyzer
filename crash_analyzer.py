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
	def __init__(self):
		self.backtraces = []

	def setLines(self, lines):
		self.lines = lines

	def addBackTrace(self, backtrace):
		self.backtraces.append(backtrace)

class BaseKnowledge:
	def apply(self, logContext):
		pass

class Tip:
	def __init__(self, msg):
		self.msg = msg
		self.lines = []
		self.infos = []
		self.showAllLogs = False
		self.tips = []

	def addInfo(self, infoMsg):
		self.infos.append(infoMsg)

	def addRelatedLog(self, line):
		self.lines.append(line)

	def addTip(self, tipStr):
		self.tips.append(tipStr)

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
			tip.addTip(self.getTips())

		return tip

	def getTips(self):
		return '''signal含义：
		SIGHUP 1 A 终端挂起或者控制进程终止 
		SIGINT 2 A 键盘中断（如break键被按下） 
		SIGQUIT 3 C 键盘的退出键被按下 
		SIGILL 4 C 非法指令 
		SIGABRT 6 C 由abort(3)发出的退出指令 
		SIGFPE 8 C 浮点异常 
		SIGKILL 9 AEF Kill信号 
		SIGSEGV 11 C 无效的内存引用 
		SIGPIPE 13 A 管道破裂: 写一个没有读端口的管道 
		SIGALRM 14 A 由alarm(2)发出的信号 
		SIGTERM 15 A 终止信号 
		SIGUSR1 30,10,16 A 用户自定义信号1 
		SIGUSR2 31,12,17 A 用户自定义信号2 
		SIGCHLD 20,17,18 B 子进程结束信号 
		SIGCONT 19,18,25 进程继续（曾被停止的进程） 
		SIGSTOP 17,19,23 DEF 终止进程 
		SIGTSTP 18,20,24 D 控制终端（tty）上按下停止键 
		SIGTTIN 21,21,26 D 后台进程企图从控制终端读 
		SIGTTOU 22,22,27 D 后台进程企图从控制终端写 
		'''
		


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

class StackLine:
	def __init__(self, typ, addr, content):
		self.type = typ
		self.content = content
		self.address = addr

class BackTrace:
	def __init__(self):
		self.stack = []

	def addStackLine(self, stackLine):
		self.stack.append(stackLine)

class BacktraceExtractKnowledge(BaseKnowledge):

	def __init__(self):
		#stack parse formatter
		strRdr = StringReader()
		read2EndRdr = ReadToEndReader()
		formatter = [("Index", strRdr),
					("Register", strRdr),
					("Address", strRdr),
					("Content", read2EndRdr)
					]
		self.formatter = formatter

	def apply(self, logContext):
		tip = None

		lnNum = 0
		backtraceBegin = False

		currBackTrace = None

		for ln in logContext.lines:
			if ("Message" in ln):
				#print(ln["Message"])
				if (ln["Message"].find("backtrace:") >= 0):
					
					if (tip == None):
						tip = Tip("有堆栈信息")
						tip.showAllLogs = True

					backtraceBegin = True
					currBackTrace = BackTrace()

					tip.addRelatedLog(ln)

					continue

				if backtraceBegin:
					if (ln["Message"].find("#") >= 0):
						tip.addRelatedLog(ln)

						stackLine = self.parseStackLine(ln["Message"])
						currBackTrace.addStackLine(stackLine)

					else:
						logContext.addBackTrace(currBackTrace)
						currBackTrace = None
						backtraceBegin = False

		return tip

	def parseStackLine(self, content):

		index = content.find('#')
		if (index >= 0):
			lineStr = content[index:]

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

			typ = "other"
			content = lnData["Content"]
			if (content.find("libunity.so") >= 0):
				typ = "libunity"
			elif (content.find("il2cpp.so") >= 0):
				typ = "il2cpp"
			elif (content.find("libc.so") >= 0):
				typ = "libc"

			return StackLine(typ, lnData["Address"], content)
		else:
			return None
		

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

		print "show all lines:" + str(tip.showAllLogs)

		if tip.showAllLogs:
			for lnNum in range(0, showLines):
				ln = tip.lines[lnNum]
				print("Line " + str(ln["Line"]) + ",\t" + ln["Message"])

		else:
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

	if (tip.tips):
		print "提示:"
		for t in tip.tips:
			print(t)

def showBackTrace(bt):
	print("this is a backtrace:")
	for ln in bt.stack:
		print("type:" + ln.type + ", addr:" + ln.address + " " + ln.content)

if __name__=="__main__":
	print("===== crash analyze tool =====")

	#for test
	#logFilePath = "examples/R11.log"
	logFilePath = "examples/test4.log"

	scanner = LogScanner()
	lineParser = LineParser()

	ctx = scanner.scan(logFilePath, lineParser)


	#knowledge database
	knowledgeDb = [
		BaseInfoKnowledge(),
		TooManyFileOpenKnowledge(),
		BacktraceExtractKnowledge()
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

		#打印翻译后的堆栈
		if (len(ctx.backtraces) > 0):
			print "resymbol stack:"

			for bt in ctx.backtraces:
				showBackTrace(bt)

	else:
		print "没有找到线索"

