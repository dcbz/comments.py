#!/usr/bin/env python

import idc
import sqlite3
import os

# prompt for filename
filename = idc.AskFile(1,"*.db","Enter name for output file:")

try:
	os.remove(filename)
except:
	pass # remove file if it exists..

# make database
dbconn = sqlite3.connect(filename)
c = dbconn.cursor()
c.execute('''CREATE TABLE comments
	     (sectionname text, offset integer, comment text)''')

dbconn.commit()


ea = idaapi.cvar.inf.minEA
modulename = idaapi.get_root_filename()

# Brute-force find all comments
while ea != BADADDR and ea <= idaapi.cvar.inf.maxEA:
	comment = ""
	cmt = GetCommentEx(ea,0)
	rep = GetCommentEx(ea,1)
	if(cmt):
		comment += cmt
	if(rep):
		comment += ("\n" + rep)
	if(comment != ""):
		print comment
		seg = idaapi.getseg(ea)
		if seg:
			offset = ea - seg.startEA
			name = modulename + "." + idc.SegName(seg.startEA)	
			print "[+] Inserting %s + %u: %s" % (name,offset,comment)
			c.execute("INSERT INTO comments VALUES ('%s',%u, '%s')" % (name,offset,comment))
			dbconn.commit()
			
	ea = idaapi.next_head(ea, idaapi.cvar.inf.maxEA)


dbconn.close()
print "[+] DONE"

