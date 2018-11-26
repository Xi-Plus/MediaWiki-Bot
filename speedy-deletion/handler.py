import socket
import json
import subprocess
import os
import time
from config import handler


basepath = os.path.dirname(os.path.realpath(__file__))

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((handler['host'], handler['port']))
sock.settimeout(5)

pool = []
while True:
	try:
		data, address = sock.recvfrom(handler['max_bytes'])
		data = data.decode()
		data = json.loads(data)
		data["time"] = time.time()
		pool.append(data)
		print("recv {}, {} waiting".format(data, len(pool)))
	except socket.timeout:
		pass
	
	while len(pool) > 0 and time.time()-pool[0]["time"] > handler["wait"]:
		data = pool.pop(0)
		print("run {}".format(data))

		if data["csd"] == "R2":
			subprocess.call(["python3.6", basepath+"/R2.py", data["page"]])
		elif data["csd"] == "G15-3":
			subprocess.call(["python3.6", basepath+"/G15-3.py", data["page"]])
		elif data["csd"] == "G15-4":
			subprocess.call(["python3.6", basepath+"/G15-4.py", data["page"]])

		print("{} waiting".format(len(pool)))
