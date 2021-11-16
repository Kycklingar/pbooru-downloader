import time
import requests
from filenamer import lex
from filename_parser import FilenameParser

def main():
	#interactive()
	# Read args

	# Read config

	url = "http://192.168.1.101"
	proxies = None

	search = Search({"tags":"renamon"}, url, proxies)

	parser = FilenameParser()

	lex(":~:creator:~: :?[2](:character=krystal|species=renamon=gatomon:)::[:5] :Sha256::", parser.tokenStream)

	c = 1
	for post in search:
		print("[%d/%d] %d %s" % (c, search.total, post["ID"], post["Hash"]))
		kvs = []
		for tag in post["Tags"]:
			kvs.append({tag["Namespace"]:tag["Tag"]})
		kvs.append({"Hash":post["Hash"]})
		kvs.append({"Sha256":post["Sha256"]})
		kvs.append({"Md5":post["Md5"]})
		kvs.append({"ID":post["ID"]})
		print(parser.compile(kvs))
		c += 1


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
			return self.posts.pop()

		sleepTimer = 10
		while True:
			try:
				self.fetchNextPage()
				break
			except ConnectionError as e:
				print("An error ocurred: %s" % e)
				print(f"Retrying in %d seconds" % sleepTimer)
				time.sleep(sleepTimer)
				sleepTimer += math.floor(sleepTimer / 2)

		if len(self.posts) > 0:
			return self.posts.pop()
		else:
			raise StopIteration



	def fetchNextPage(self):
		params = dict(self.options)
		params["offset"] = self.page

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


class Storage:
	def __init__(self, id, path):
		#self.id = id
		#self.path = path
		self.cacheFilePath = os.path.join(self.path, ".%s.config" % self.id)
		self.dataDir = os.path.join(self.path, self.id)
		
		self.initCache()

	def initCache(self):
		self.cahce = set()
		with open(self.cacheFilePath) as f:
			self.cache.add(f.readline())

	def write(self, hash, filename, data):
		with open(os.path.join(self.dataDir, filename), "wb") as f:
			f.write(data)
			self.writeCache(hash)



if __name__ == "__main__":
	main()
