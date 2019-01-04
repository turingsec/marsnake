from core.security import Ksecurity
from core.computer_score import KScore
from core.information import KInformation
from core.profile_reader import KProfile
import base64

def run(payload, socket):
	encrypt_aes = base64.b64decode(payload["args"]["aes"])
	Ksecurity().set_aes_iv(Ksecurity().rsa_long_decrypt(encrypt_aes), 'This is an IV456')
	
	warning, score = KScore().get_status()

	response = KInformation().get_info()
	response["password"] = KProfile().read_key("password")
	response["cmd_id"] = payload["cmd_id"]
	response["score"] = score
	response["warning"] = warning

	socket.response(response)
