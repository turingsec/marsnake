from core.db import Kdatabase

def run(payload, socket):
	detail = payload["args"]["detail"]
	
	#need to check
	if detail:
		Kdatabase().set_obj("strategy", detail)
