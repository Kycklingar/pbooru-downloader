import time
import requests
from filename_compiler import FilenameCompiler, CompileError
from os import path, makedirs
from mimetypes import guess_extension
from argparse import ArgumentParser
from progressbar import ProgressBar
from math import floor, ceil
from signal import signal, SIGINT

def main():
	#interactive()
	# Read args

	args = parseFlags()
	sopts = searchKvs(args)

	# Read config

	startPage = int(floor((args.start_from / 50)))

	search = Search(sopts, args.url, args.proxy, startPage)

	compiler = FCompilers(args.filenamer)

	gateway = Gateway(args.gateway, proxy=args.gateway_proxy)
	storage = Storage(args.path)

	prog = ProgressBar(0, args.disable_progressbar)
	prog.inc(startPage * 50)

	for post in search:
		prog.setMax(search.total)
		prog.inc()
		prog.display()

		cid = post["Hash"]

		if cid not in storage:
			kvs = postToDictList(post)
			filename = compiler.compile(kvs)
			prog.print("...%s -> %s" %(cid[-6:], filename))
			storage.write(cid, filename, gateway.get(cid))

	print()

def ketchup(signum, frame):
	exit(1)
signal(SIGINT, ketchup)

def parseFlags():
	defaultBooru = "http://owmvhpxyisu6fgd7r2fcswgavs7jly4znldaey33utadwmgbbp4pysad.onion"
	defaultGateway = "http://localhost:8080"

	parser = ArgumentParser(description="The Permanent Booru Downloader")
	parser.add_argument("path", help="data directory")
	parser.add_argument("--overwrite", metavar="", help="overwrite config file")
	parser.add_argument("--url", default=defaultBooru, help="default: %s" % defaultBooru)
	parser.add_argument("--proxy", default="socks5h://localhost:9050", help="default: socks5h://localhost:9050 use socks5h://localhost:9150 for tor browser")
	parser.add_argument("--filenamer", help="filename compiler defenitions file")
	parser.add_argument("--start-from", type=int, default="0", help="offset the starting post")
	parser.add_argument("--disable-progressbar", action="store_true", help="disables the progress bar")

	searchGroup = parser.add_argument_group(title="search options")
	searchGroup.add_argument("-a", "--and", metavar="", help="tags to download (AND)", dest="tand")
	searchGroup.add_argument("-o", "--or", metavar="", help="tags to download (OR)", dest="tor")
	searchGroup.add_argument("-f", "--filter", metavar="", help="tags to filter")
	searchGroup.add_argument("-u", "--unless", metavar="", help="filter only if none of these are present")
	searchGroup.add_argument("--mime", metavar="", help="mimetype")

	gate = parser.add_argument_group(title="gateway options")
	gate.add_argument("--gateway", default=defaultGateway, help="IPFS gateway. Default %s" % defaultGateway)
	gate.add_argument("--gateway-proxy", help="proxy for the gateway")

	return parser.parse_args()

def searchKvs(args):
	opts = {}
	if args.tand:
		opts["tags"] = args.tand
	if args.tor:
		opts["or"] = args.tor
	if args.filter:
		opts["filter"] = args.filter
	if args.unless:
		opts["unless"] = args.unless
	if args.mime:
		opts["mime-type"] = []
		for mime in args.mime.split():
			opts["mime-type"].append(mime.strip())

	return opts


def postToDictList(post):
	kvs = []
	for tag in post["Tags"]:
		kvs.append((tag["Namespace"], tag["Tag"]))
	kvs.append(("Cid", post["Hash"]))
	kvs.append(("Sha256", post["Sha256"]))
	kvs.append(("Md5", post["Md5"]))
	kvs.append(("ID", str(post["ID"])))

	ext = guess_extension(post["Mime"])
	if ext is None:
		ext = ".bin"

	kvs.append(("Ext", ext))
	

	return kvs


def interactive():
	main = Menu("Welcome common pleb.\nWhat is it you request?")
	main.display()

def downloadOptions():
	action = Action("Setup download arguments.")

	#action.installAction("And")


class Menu:
	def __init__(self, message):
		self.message = message
		self.actions = []
		pass

	def installAction(self, description, callback):
		self.actions.append((description, callback))
	
	def display(self):
		cont = True
		while cont:
			print(self.message)
			i = 1
			for action in self.actions:
				print("[%d] %s" % (i, action[0]))
				i += 1
			print("Select option: ", end="")
			
			cont = self.waitForSelection()
		return True
	
	def waitForSelection(self):
		x = int(input()) - 1

		if x >= len(self.actions) or x < 0:
			print("Invalid option. Try again!")
			return True

		return self.actions[x][1]()



def loadConfig(path):
	if not exists(path):
		Path(path).touch()
	with open(path, "r") as f:
		return json.load(f)
	

def saveConfig(path, conf):
	with open(path, "w") as f:
		json.dump(conf, f)


class FCompilers:
	def __init__(self, compFile):
		self.compilers = []
		if compFile:
			with open(compFile, "r") as f:
				for line in f:
					line = line.strip()
					if len(line) <= 0:
						continue
					if line[0] == "#":
						continue
					self.add(line)
		else:
			self.add("<::Cid:><::Ext:>")

	def add(self, string):
		self.compilers.append(FilenameCompiler(string))

	def compile(self, kvs):
		errors = []
		for comp in self.compilers:
			try:
				filename = comp.compile(kvs)
				return filename
			except CompileError as e:
				errors.append(e)

		raise Exception(errors)


class ServerError(Exception):
	pass

class Search:
	def __init__(self, options, url, proxy, start):
		self.options = options
		self.posts = []
		self.url = url
		self.proxies = None
		if proxy:
			self.proxies = {"http": proxy}

		self.sleep = 0
		self.total = 0
		self.page = start
	
	def __iter__(self):
		return self

	# Returns a post and fetches the next page if necessary
	def __next__(self):
		if len(self.posts) > 0:
			return self.posts.pop(0)

		sleepTimer = 10
		while True:
			try:
				self.fetchNextPage()
				break
			except ConnectionError as e:
				print("An error ocurred: %s" % e)
				print("Retrying in %d seconds" % sleepTimer)
				time.sleep(sleepTimer)
				sleepTimer += math.floor(sleepTimer / 2)

		if len(self.posts) > 0:
			return self.posts.pop(0)
		else:
			raise StopIteration



	def fetchNextPage(self):
		if self.total > 0:
			if self.page >= int(ceil(self.total / 50)):
				return

		params = dict(self.options)
		params["offset"] = self.page
		params["order"] = "asc"

		# Sleep between requests
		time.sleep(max(0, self.sleep - time.time() + 5))

		resp = requests.get(self.url + "/api/v1/posts", proxies=self.proxies, params=params)
		self.sleep = time.time()
		resp.raise_for_status()

		j = resp.json()
		if "Error" in j:
			raise ServerError(j["Error"])

		self.total = j["TotalPosts"]

		for post in j["Posts"]:
			self.posts.append(post)

		self.page += 1

class Gateway:
	def __init__(self, url, proxy=None):
		self.proxies = None
		if proxy:
			self.proxies = {"http":proxy}
		self.url = url

	def get(self, cid):
		resp = requests.get(self.url + "/ipfs/%s" % cid, proxies=self.proxies)
		resp.raise_for_status()

		return resp.content

class Storage:
	def __init__(self, dataDir):
		self.dataDir = dataDir
		self.cacheFilePath = path.join(self.dataDir, ".cache")

		makedirs(self.dataDir, exist_ok=True)
		
		self.initCache()
	
	def __contains__(self, item):
		return item in self.cache

	def initCache(self):
		self.cache = set()
		if not path.exists(self.cacheFilePath):
			with open(self.cacheFilePath, "w"):
				pass

		with open(self.cacheFilePath) as f:
			for line in f:
				s = line.split(" ", 1)
				if len(s) > 0:
					cid = s[0].strip()
					if len(cid) > 0:
						self.cache.add(cid)

	def write(self, cid, filename, data):
		with open(path.join(self.dataDir, filename), "wb") as f:
			f.write(data)
			self.writeCache(cid, filename)
	
	def writeCache(self, cid, filename):
		with open(self.cacheFilePath, "a") as f:
			f.write("%s %s\n" % (cid, filename))




if __name__ == "__main__":
	main()
