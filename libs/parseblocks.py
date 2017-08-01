import re

class Blocks:
	
	def __init__(self):
		self.error = None
		self.blocks = {} # block format: { blockname : [blocktype,blockcontent] }
		self.cblock = '' # current block name
		self.order = [] # keep the blockname indexes of self.blocks in order processed here
	
	# return True if open tag found, False otherwise
	def __parseOpen(self,line):
		m = re.split('{%',line,1)
		if len(m) > 1:
			# found open tag, grab btype & bname, send the rest to parseClose
			tm = re.split(':',m[1],1)
			if len(tm) > 1:
				btype = tm[0]
				nm = re.split('\s',tm[1],1)
				if len(nm) > 1:
					bname = nm[0]
					self.cblock = nm[0]
					self.__createBlock(bname,btype)
					if len(nm[1]) > 0:
						return not self.__parseClose(nm[1])
					else:
						return True
				else:
					self.error = {'incomplete open tag on line ' + str(self.lncnt):'the entire open tag must be on one line like, {%btype:bname'}
					return False
			else:
				self.error = {'incomplete open tag on line ' + str(self.lncnt):'the entire open tag must be on one line like, {%btype:bname'}
				return False
		else:
			# ignore everything between %} {%
			return False
	
	# return True if close tag found, False otherwise
	def __parseClose(self,line):
		m = re.split(r'%}',line,1)
		if len(m) > 1:
			# found end tag, add line to block content, send the rest to parseOpen
			self.__addToBlock(m[0])
			return not self.__parseOpen(m[1])
		else:
			# did not find end tag, just add line to block content
			self.__addToBlock(line)
			return False
		
	def __createBlock(self,bname,btype):
		self.blocks[bname] = [btype,'']
		self.order.append(bname)
	
	def __addToBlock(self,line):
		self.blocks[self.cblock][1] += line
	
	# if there is an error in the open tag formatting,
	# the entire block is just discarded,
	# other well formatted blocks will be kept
	def parseFile(self,file,step=0):
		with open(file) as f:
			lines = f.read().split('@@@@')[step].splitlines(True)
		
		bsearch = True
		self.lncnt = 0
		for line in lines:
			self.lncnt += 1
			if bsearch:
				bsearch = not self.__parseOpen(line)
			else:
				bsearch = self.__parseClose(line)
		self.lncnt = 0

