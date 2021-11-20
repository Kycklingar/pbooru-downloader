from tokens import Token

def lex(text, consumer=None):
	l = lexer(text, consumer)

	return l.lex()

def printConsumer(token):
	print(token)

class SyntaxError(Exception):
	pass

NUMERIC = "1234567890"

# Defines a syntax for filenames based on what namespaced tags exists in a post
# Defenition as follows:
#	start match with :
#		optionally set optional flag with ?
#		optionally set max number of instances and max length of instance
#			[maxInstances:maxLength]
#		prepend text
#		start namespace constraint with :
#			namespace
#			optional =/!
#				must be equal or not equal
#			optional | followed by new namespace
#		end with :
#		postpone text
#	end with :
#
# Explained examples:
#	Basic namespace match:
#		"::namespace::"
#		This will match the namespace and compilation will fail if no match is found
#	Basic optional namespace with max instaces:
#		":?[2]:namespace::
#		This will match none or at most two of 'namespace'
#	With multiple namespace and conditionals:
#		":?[2:10]:character=foo|species!bar::"
#		This will match at most 2 of either character where
#		character is foo or species where species is not bar
#		and truncating the length to 10
#
# Example:
#	":artist:creator::-:?[1]:species=renamon=gatomon|character!krystal::"
#	":artist:creator:-::character: :?[1:10]spec:species=renamon=gatomon:"
class lexer:
	def lex(self):
		state = self.lexText
		while state is not None:
			state = state()

	def __init__(self, text, consumer=None):
		self.text = text
		self.index = 0
		self.consumer = consumer
		if consumer is None:
			self.consumer = printConsumer


	def __iter__(self):
		return self

	def __next__(self):
		self.index += 1
		if self.index > len(self.text):
			raise StopIteration

		return self.text[self.index-1]

	def next(self):
		return self.__next__()
	
	def peek(self):
		c = self.next()
		self.index -= 1
		return c

	def any(self, characters):
		start = self.index
		for char in self:
			if char not in characters:
				self.index -= 1
				return self.text[start:self.index]

	def emit(self, ttype, token):
		self.consumer((ttype, token))

	def emitIfAny(self, ttype, token):
		if len(token) > 0:
			self.emit(ttype, token)

	def indexed(self, start):
		return self.text[start:self.index-1]

	def indexedR(self, start):
		return self.removeEscapeChar(self.indexed(start))

	def removeEscapeChar(self, string):
		retu = ""
		skip = False
		for c in string:
			if not skip and c == "\\":
				skip = True
				continue

			skip = False
			retu += c
		return retu

	def lexText(self):
		start = self.index
		nextState = None
		for c in self:
			if c == "\\":
				self.next()
			elif c == "<":
				nextState = self.lexNewDef
				break

		self.emitIfAny(Token.TEXT, self.indexedR(start))
		return nextState

	def lexNewDef(self):
		self.emit(Token.START, "<")
		#self.any(" ")

		# optional or requriement
		c = self.peek()
		if c == "?":
			self.emit(Token.OPTIONAL, c)
			self.next()
			c = self.peek()
		if c == "[":
			return self.lexLimits

		return self.lexPrepend

	def lexLimits(self):
		if self.peek() != "[":
			return self.lexPrepend

		self.next()

		if self.peek() != ":":
			nums = self.any(NUMERIC)
			if len(nums) <= 0:
				raise SyntaxError("Expected numeric value but got %s in position %d" %(self.peek(), self.index))
			self.emit(Token.MAXINST, nums)

		if self.peek() == ":":
			self.next()
			neg = ""
			if self.peek() == "-":
				neg = self.next()
			nums = self.any(NUMERIC)
			if len(nums) <= 0:
				raise SyntaxError("Expected numeric value but got %s in position %d" %(self.peek(), self.index))
			self.emit(Token.MAXLENGTH, neg + nums)

		if self.next() != "]":
			raise SyntaxError("Expected ] got %s in position %d" % (self.text[self.index], self.index))

		return self.lexPrepend

	def lexPrepend(self):
		start = self.index
		for c in self:
			if c == "\\":
				self.next()
			elif c == ":":
				self.emitIfAny(Token.PREPEND, self.indexedR(start))
				return self.lexSep

		raise SyntaxError("Sequence end in prepend state:\n %s" % self.text[:start])

	def lexSep(self):
		start = self.index
		for c in self:
			if c == "\\":
				self.next()
			elif c == ":":
				self.emitIfAny(Token.SEPARATOR, self.indexedR(start))
				return self.lexNamespace

		raise SyntaxError("Sequence end in separator state:\n %s" % self.text[:start])

	def lexPostpend(self):
		start = self.index
		for c in self:
			if c == "\\":
				self.next()
			elif c == ">":
				self.emitIfAny(Token.POSTPEND, self.indexedR(start))
				self.emit(Token.END, c)
				return self.lexText
		raise SyntaxError("Sequence end in postpend state:\n %s" % self.text[:start])

	def lexNamespace(self):
		start = self.index
		for c in self:
			if c == "\\":
				self.next()
			elif c == ":":
				self.emit(Token.NAMESPACE, self.indexedR(start))
				return self.lexPostpend
			elif c == "=" or c == "!":
				self.emit(Token.NAMESPACE, self.indexedR(start))
				self.emit(Token.COND, c)
				return self.lexCond 
			elif c == "|":
				self.emit(Token.NAMESPACE, self.indexedR(start))
				return self.lexNamespace
		raise SyntaxError("Sequence end in namespace state:\n %s" % self.text[:start])


	def lexCond(self):
		start = self.index
		nextState = None
		for c in self:
			if c == "\\":
				self.next()
			elif c == ":":
				self.emit(Token.CONDARG, self.indexedR(start))
				return self.lexPostpend
			elif c == "|":
				nextState = self.lexNamespace
				break
			elif c == "=":
				nextState = self.lexCond
				break
			
		if nextState == None:
			raise SyntaxError("Sequence end in cond state:\n %s" % self.text[:start])

		if len(self.indexed(start)) == 0:
			raise SyntaxError("Expected CONDARG but got nothing in position %d" % self.index)

		self.emit(Token.CONDARG, self.indexed(start))
		return nextState
