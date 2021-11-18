import time
import requests
from filename_compiler import FilenameCompiler, CompileError
from os import path, makedirs
from mimetypes import guess_extension
from argparse import ArgumentParser

def main():
	#interactive()
	# Read args

	#args = parseFlags()
	#print(args)
	#return

	# Read config

	url = "http://192.168.1.101"
	proxies = None

	search = Search({"tags":"gatomon"}, url, proxies)

	compiler = FCompilers()
	compiler.add("::ID:::? ~:creator:::?[3] :character|species=renamon=gatomon:::? (:gender:):::Ext::")
	compiler.add("::Cid::::Ext::")

	gateway = Gateway("http://localhost:8080")
	storage = Storage("gatomon")

	prog = ProgressBar(0)

	c = 1
	for post in search:
		prog.setMax(search.total)
		prog.inc()
		prog.display()

		cid = post["Hash"]
		#print("[%d/%d] %d %s" % (c, search.total, post["ID"], cid)) 

		if cid not in storage:
			kvs = postToDictList(post)
			filename = compiler.compile(kvs)
			prog.print("%s -> %s" %(cid, filename))
			storage.write(cid, filename, gateway.get(cid))
		c += 1

def parseFlags():
	parser = ArgumentParser(description="The Permanent Booru Downloader")
	parser.add_argument("path", help="data directory")
	parser.add_argument("--overwrite", metavar="", help="overwrite config file")

	searchGroup = parser.add_argument_group(title="search options")
	searchGroup.add_argument("-a", "--and", metavar="", help="tags to download (AND)")
	searchGroup.add_argument("-o", "--or", metavar="", help="tags to download (OR)")
	searchGroup.add_argument("-f", "--filter", metavar="", help="tags to filter")
	searchGroup.add_argument("-u", "--unless", metavar="", help="filter only if none of these are present")
	searchGroup.add_argument("--mime", metavar="", help="mimetype")

	return parser.parse_args()


def postToDictList(post):
	kvs = []
	for tag in post["Tags"]:
		kvs.append({tag["Namespace"]:tag["Tag"]})
	kvs.append({"Cid":post["Hash"]})
	kvs.append({"Sha256":post["Sha256"]})
	kvs.append({"Md5":post["Md5"]})
	kvs.append({"ID":str(post["ID"])})

	ext = guess_extension(post["Mime"])
	if ext is None:
		ext = ".bin"

	kvs.append({"Ext":ext})
	

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
	def __init__(self):
		self.compilers = []

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
	def __init__(self, options, url, proxies):
		self.options = options
		self.posts = []
		self.url = url
		self.proxies = proxies
		self.sleep = 0
		self.total = 0
	
	def __iter__(self):
		self.page = 0
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
	def __init__(self, url, proxies=None):
		self.proxies = proxies
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
