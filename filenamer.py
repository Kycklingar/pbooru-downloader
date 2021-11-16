from tokens import Token

def printConsumer(token):
	print(token)

class SyntaxError(Exception):
	pass

NUMERIC = "1234567890"


def lex(text, consumer=None):
	l = lexer(text, consumer)

	return l.lex()

# Defines a syntax for filenames based on what namespaced tags exists in a post
# Defenition as follows:
#	prepend with o
#		optionally set max number of instances and max length of instance
#		[maxInstance:maxLengthPerInstance]
#	prepend text
#	begin with :
#	namespace
#	optional =/!=
#		must be equal or not equal
#	optional |
#	exit with :
# Example:
#	r artist:creator:-o[1]:species=renamon=gatomon|character!=krystal:
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


	def lexText(self):
		start = self.index
		nextState = None
		for c in self:
			if c == ":":
				nextState = self.lexNewDef
				break

		self.emitIfAny(Token.TEXT, self.indexed(start))
		return nextState

	def lexNewDef(self):
		self.emit(Token.START, ":")
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
			self.emit(Token.MAXINST, self.any(NUMERIC))

		if self.peek() == ":":
			self.next()
			self.emit(Token.MAXLENGTH, self.any(NUMERIC))

		if self.next() != "]":
			raise SyntaxError("Expected ] got %s in position %d" % (self.text[self.index], self.index))

		return self.lexPrepend

	def lexPrepend(self):
		start = self.index
		for c in self:
			if c == ":":
				self.emitIfAny(Token.PREPEND, self.indexed(start))
				return self.lexNamespace

		raise SyntaxError("Sequence end in prepend state; unmatched :")

	def lexPostpend(self):
		start = self.index
		for c in self:
			if c == ":":
				self.emitIfAny(Token.POSTPEND, self.indexed(start))
				self.emit(Token.END, ":")
				return self.lexText
		raise SyntaxError("Sequence end in postpend state; unmatched :")

	def lexNamespace(self):
		start = self.index
		for c in self:
			if c == ":":
				self.emit(Token.NAMESPACE, self.indexed(start))
				return self.lexPostpend
			if c == "=" or c == "!":
				self.emit(Token.NAMESPACE, self.indexed(start))
				self.emit(Token.COND, c)
				return self.lexCond 
			if c == "|":
				self.emit(Token.NAMESPACE, self.indexed(start))
				return self.lexNamespace
		raise SyntaxError("Sequence end in namespace state; unmatched :")


	def lexCond(self):
		start = self.index
		nextState = None
		for c in self:
			if c == ":":
				self.emit(Token.CONDARG, self.indexed(start))
				return self.lexPostpend
			elif c == "|":
				nextState = self.lexNamespace
				break
			elif c == "=":
				nextState = self.lexCond
				break
			
		if nextState == None:
			raise SyntaxError("Sequence end in cond state; unmatched :")

		if len(self.indexed(start)) == 0:
			raise SyntaxError("Expected CONDARG but got nothing in position %d" % self.index)

		self.emit(Token.CONDARG, self.indexed(start))
		return nextState
