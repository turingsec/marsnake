from utils import net_op
from config import constant
from core.db import Kdatabase
import getpass
import urllib.parse, json

def login(username, password):
	setting_db = Kdatabase().get_obj("setting")
	status, data = net_op.create_http_request(constant.SERVER_URL,
		"POST",
		"/client/login",
		urllib.parse.urlencode({'username': username, 'password': password}),
		{"Content-type": "application/x-www-form-urlencoded", "Accept": "application/json"})
	
	if status == 200 and data:
		data = json.loads(data)

		setting_db["username"] = data["username"]
		setting_db["credential"] = data["credential"]

		Kdatabase().dump("setting")

		return True

	return False

def read_from_user():
	setting_db = Kdatabase().get_obj("setting")

	if not setting_db["username"] or not setting_db["credential"]:
		print("""Visit https://www.marsnake.com to register a cloud account.\nCloud account used to manage your multiple devices via web panel.\n""")

		while True:
			username = input("Please enter your email: ")
			password = getpass.getpass("Please enter your password: ")
			
			if username and password:
				if login(username, password):
					print("Login successful")
					break

			print("Something went wrong, retry login")
	else:
		print("You already logged in with username:{}".format(setting_db["username"]))

if __name__ == "__main__":
	Kdatabase().on_initializing(True)
	
	read_from_user()