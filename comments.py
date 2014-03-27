#!/usr/bin/env python

import sys
import os
import lldb
import shlex
import sqlite3
import tempfile

globals()['DATABASE'] = 0



#target stop-hook add --one-liner "frame variable argc argv"
#globals()["ARCH"] = 32
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
        insts =  addobj.GetSymbol().GetInstructions(target)
	c = globals()['DATABASE'].cursor()
	c.execute("INSERT INTO comments VALUES ('%s',%u, '%s')" % (sectionname,offset,args[1]))
	globals()['DATABASE'].commit()

def cdis(debugger, command, result, dict):
	args = shlex.split(command)
	target = debugger.GetSelectedTarget()
	process = target.GetProcess()
	thread = process.GetSelectedThread()
	frame = thread.GetSelectedFrame()
	error = lldb.SBError()
	
	lldb.debugger.SetAsync (False)
	
	if(len(args) > 0) :
		variable = frame.FindVariable(args[0])
		if variable.IsValid():
			address = variable.GetValueAsSigned()
		else:
			try:
				address = int(args[0], 0)
			except:
				print "The argument is not a valid address or variable in the frame"
				return
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
		line = ("0x%016lx" % inst.GetAddress().GetLoadAddress(target)) + "\t" + inst.GetMnemonic(target) + "\t" + inst.GetOperands(target) + "\t"
	 	instaddr = inst.GetAddress()
		comment = inst.GetComment(target)
		if(comment):
			line += "// %s" % comment

		offset = instaddr.GetOffset()
		#print dir(addobj)
		sectionname = instaddr.GetSection().__str__().split(" ")[1]
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
	print "--------------------------------------"
	print " Commented Disassembly lldb Module"
	print " nemo 2014"
	print "--------------------------------------"
	print ""
	globals()["DATABASE"] = sqlite3.connect(':memory:')
	c = globals()["DATABASE"].cursor()

	# Create table
	c.execute('''CREATE TABLE comments
		     (sectionname text, offset integer, comment text)''')

	# Save (commit) the changes
	globals()["DATABASE"].commit()

