from enum import Enum

class Token(Enum):
	START     = 0
	OPTIONAL  = 1
	MAXINST   = 2
	MAXLENGTH = 3
	NAMESPACE = 4
	COND      = 5
	CONDARG   = 6
	PREPEND   = 7
	TEXT      = 8
	END       = 9
	POSTPEND  = 10
	SEPARATOR = 11

