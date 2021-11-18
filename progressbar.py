from sys import stdout
from shutil import get_terminal_size

class ProgressBar:
	def __init__(self, max, disable_bar=False):
		self.max = max
		self.i = 0
		self.lineWidth = 0
		self.print = self.printWithBar
		if disable_bar:
			self.print = self.printWithoutBar
			self.display = self.nothing
	
	def setMax(self, max):
		self.max = max

	def inc(self, n=1):
		self.i += n
	
	def nothing(self):
		pass

	def printWithoutBar(self, text):
		print("[%d/%d] %s" % (self.i, self.max, text))

	# Print to stdout witout disturbing the progress bar
	def printWithBar(self, text):
		self.clear()
		stdout.write(text + "\n")
		self.printbar()

	def display(self):
		self.clear()
		self.printbar()

	def printbar(self):
		(termWidth, _) = get_terminal_size()

		percent = (self.i / self.max)
		percentStr = "%3d%%" % int(percent * 100)
		counter = "%d/%d" % (self.i, self.max)

		barWidth = termWidth - len(percentStr) - len(counter)
		mwidth = barWidth - 4

		bars = "#" * min(int(mwidth * percent), mwidth)
		spacing = " " * int(mwidth - len(bars))
		bar = ""
		if barWidth >= 8:
			bar = " [%s] " % (bars + spacing)


		string = percentStr + bar + counter
		self.lineWidth = len(string)
		stdout.write(string)
		stdout.flush()

	def clear(self):
		stdout.write("\r%s\r" % (" " * self.lineWidth))
