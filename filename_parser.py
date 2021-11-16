from tokens import Token
from filenamer import lex

class CompileError(Exception):
	pass

class FilenameParser:
	def __init__(self, string):
		self.parseToken = self.tokenText
		self.prints = []
		self.con = None
		self.matchers = []
		lex(string, self.tokenStream)

	def __str__(self):
		ret = ""
		for p in self.prints:
			ret += str(p)
		return ret

	def compile(self, kvs):
		ret = ""
		for p in self.prints:
			(s, suc) = p.compile(kvs)
			if not suc:
				raise CompileError("Required condition failed %s" % p)
			ret += s

		return ret
		
	def tokenStream(self, token):
		print(token)
		self.parseToken(token)

	def tokenText(self, token):
		if token[0] == Token.START:
			self.parseToken = self.newMatcher
		elif token[0] == Token.TEXT:
			self.prints.append(String(token[1]))

	def newMatcher(self, token):
		if self.con is None:
			self.con = Match()

		(tt, text) = token

		if tt == Token.OPTIONAL:
			self.con.optional = True
		elif tt == Token.MAXINST:
			self.con.maxInstances = int(text)
		elif tt == Token.MAXLENGTH:
			self.con.maxLength = int(text)
		elif tt == Token.PREPEND:
			self.con.prepend = text
		elif tt == Token.POSTPEND:
			self.con.postpend = text
		elif tt == Token.NAMESPACE:
			self.con.newCondVal(text)
		elif tt == Token.COND:
			self.con.getCondVal().setCond(text == "=")
		elif tt == Token.CONDARG:
			self.con.getCondVal().addVal(text)
		elif tt == Token.TEXT or tt == Token.START or tt == Token.END:
			self.prints.append(self.con)
			self.matchers.append(self.con)
			self.con = None
			self.parseToken = self.tokenText

class String:
	def __init__(self, string):
		self.string = string
	
	def __str__(self):
		return self.string
	
	def compile(self, kvs):
		return (self.string, True)

class Match:
	def __init__(self):
		#self.matchers = []
		self.matchers = {}
		#self.values = []
		self.maxInstances = 0
		self.maxLength = 0
		self.prepend = ""
		self.postpend = ""
		self.optional = False
		self.lastCondVals = None
	
	def __str__(self):
		return self.prepend
	
	def compile(self, kvs):
		#ret = self.prepend
		ret = ""
		success = True
		n = 0
		strings = []
		for kv in kvs:
			if self.maxInstances > 0 and n > self.maxInstances:
				break

			for key, val in kv.items():
				if key in self.matchers:
					if self.matchers[key].match(val):
						n += 1
						strings.append(val)
						break

		ret = " ".join(strings)
		if not self.optional and len(strings) <= 0:
			success = False

		if len(strings) > 0: 
			if self.maxLength > 0:
				ret = ret[:self.maxLength]
			ret = self.prepend + ret + self.postpend


		return (ret, success)


	def newCondVal(self, key):
		self.matchers[key] = CondVals()
		self.lastCondVals = self.matchers[key]

	def getCondVal(self):
		return self.lastCondVals

class CondVals:
	def __init__(self):
		self.values = []
		self.cond = None

	def setCond(self, cond):
		self.cond = cond

	def addVal(self, val):
		self.values.append(val)

	def match(self, val):
		return self.isMatch(val)
	
	def isMatch(self, val):
		if self.cond is None:
			return True
		elif self.cond is True:
			# Val must match conditionals
			return val in self.values
		else:
			# Val must not match conditionals
			return not val in self.values
