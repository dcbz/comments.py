#!/usr/bin/env python

import sys
import re
import os
import lldb
import shlex
import sqlite3
import tempfile

class bcolors:
    HEADER = '\033[95m'
    OKRED = "\033[.31m" 
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''

globals()['DATABASE'] = 0
globals()["ARCH"] = 8

def load_comment_db(debugger,command,result,dict):
	args = shlex.split(command)
	if(len(args) != 1):
		print "usage: load_comment_db <filename.db>"
		return
	if(globals()['DATABASE']):
		globals()['DATABASE'].close()
		
	globals()["DATABASE"] = sqlite3.connect(os.path.expanduser(args[0]))

def save_comment_db(debugger,command,result,dict):
	args = shlex.split(command)
	if(len(args) != 1):
		print "usage: save_comment_db <filename.db>"
		return
	#if(globals()['DATABASE']):
	#	globals()['DATABASE'].close()
	filename = os.path.expanduser(args[0])
	try:
		os.unlink(filename)
	except:
		pass
	tmpconn	= sqlite3.connect(filename)
	c = tmpconn.cursor()
	script = "".join(globals()['DATABASE'].iterdump())
	c.executescript(script)
	tmpconn.commit()
	globals()['DATABASE'].close()
	globals()['DATABASE'] = tmpconn # now we use the file instead

def add_comment(debugger,command,result,dict):
	# Insert a row of data
	#c.execute("INSERT INTO stocks VALUES ('2006-01-05','BUY','RHAT',100,35.14)")
	# We can also close the connection if we are done with it.
	# Just be sure any changes have been committed or they will be lost.
	#conn.close()
	args = shlex.split(command)
	target = debugger.GetSelectedTarget()
	process = target.GetProcess()
	thread = process.GetSelectedThread()
	frame = thread.GetSelectedFrame()
	args = shlex.split(command)
	if(len(args) != 2):
		print "usage: add_comment <address> <comment>"
		return
	addobj = target.ResolveLoadAddress(int(args[0],0))
        offset = addobj.GetOffset()
        #print dir(addobj)
	sectionname = addobj.GetSection().__str__().split(" ")[1]
	sectionname = re.sub("[.]__[A-Z0-9]+[.]__",".__",sectionname) # hack for ida -> osx compat
        insts =  addobj.GetSymbol().GetInstructions(target)
	c = globals()['DATABASE'].cursor()
	c.execute("INSERT INTO comments VALUES ('%s',%u, '%s')" % (sectionname,offset,args[1]))
	globals()['DATABASE'].commit()

def cdis(debugger, command, result, dict):
	print ""
	args = shlex.split(command)
	target = debugger.GetSelectedTarget()
	process = target.GetProcess()
	thread = process.GetSelectedThread()
	frame = thread.GetSelectedFrame()
	error = lldb.SBError()
	
	lldb.debugger.SetAsync (False)
	addobj = 0
	
	if(len(args) > 0) :
		variable = target.FindSymbols(args[0])
		if len(variable) > 0:
			sym = variable[0].symbol
			addobj = sym.addr
		else:
			try:
				address = int(args[0], 0)
			except:
				print "The argument is not a valid address or variable in the frame"
				return
		if(not addobj):
			addobj = target.ResolveLoadAddress(address) 

	if(len(args) == 0):
		insts = target.ReadInstructions(target.ResolveLoadAddress(frame.pc),5);
	elif(len(args) == 1):
		insts =  addobj.GetSymbol().GetInstructions(target)
	elif(len(args) == 2):
		insts = target.ReadInstructions(addobj,int(args[1],0));
	else:
		print "usage: cdis <address> [number of instructions]"
		return

	

	c = globals()['DATABASE'].cursor()
	for inst in insts:
		operand = inst.GetOperands(target)
	#	operand = re.sub("(0x[0-9a-zA-Z]+)", bcolors.HEADER + "\1" + bcolors.ENDC, operand)
#		operand = re.sub("(%[a-z0-9]+)", bcolors.OKRED + "%s\1" + bcolors.ENDC, operand)
		operand = re.sub("(0x[0-9a-zA-Z]+)", r'\033[95m\1\033[0m', operand)
		operand = re.sub("(%[a-z0-9]+)", r'\033[.31m\1\033[0m', operand)
		#bcolors.HEADER + inst.GetOperands(target) + bcolors.ENDC 	inst.GetOperands(target)
		line = ("%s" % bcolors.WARNING) + ("0x%016lx" % inst.GetAddress().GetLoadAddress(target)) + "\t" + bcolors.ENDC + bcolors.OKGREEN + inst.GetMnemonic(target) + bcolors.ENDC + "\t" + operand + "\t"
	 	instaddr = inst.GetAddress()
		comment = inst.GetComment(target)
		if(comment):
			line += (bcolors.OKBLUE + "// %s" + bcolors.ENDC) % comment

		offset = instaddr.GetOffset()
		#print dir(addobj)
		sectionname = instaddr.GetSection().__str__().split(" ")[1]
		sectionname = re.sub("[.]__[A-Z0-9]+[.]__",".__",sectionname) # hack for ida -> osx compat
		#print "looking up: %s:%u" % (sectionname,offset)

		c.execute("SELECT comment FROM comments WHERE sectionname='%s' AND offset=%u" % (sectionname,offset)) 
		mycomment = c.fetchone()
		if(mycomment):
			line += " //" + mycomment[0]

		print line
	lldb.debugger.SetAsync (True)
	

def __lldb_init_module (debugger, dict):
	debugger.HandleCommand('command script add -f comments.cdis cdis')
	debugger.HandleCommand('command script add -f comments.add_comment add_comment')
	debugger.HandleCommand('command script add -f comments.save_comment_db save_comment_db')
	debugger.HandleCommand('command script add -f comments.load_comment_db load_comment_db')
	print bcolors.WARNING
	print "--------------------------------------"
	print " Commented Disassembly lldb Module"
	print " nemo 2014"
	print "--------------------------------------"
	print ""
	print bcolors.ENDC
	globals()["DATABASE"] = sqlite3.connect(':memory:')
	c = globals()["DATABASE"].cursor()
	lldb.debugger.HandleCommand("settings set stop-disassembly-count 0")  # remove disassembly from stop
	lldb.debugger.HandleCommand("target stop-hook add --one-liner cdis")  # add our own.

	# Create table
	c.execute('''CREATE TABLE comments
		     (sectionname text, offset integer, comment text)''')

	tgt =  lldb.debugger.GetSelectedTarget()
	globals()["ARCH"] = tgt.GetAddressByteSize()

	# Save (commit) the changes
	globals()["DATABASE"].commit()

