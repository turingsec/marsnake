from core.profile_reader import KProfile

def run(payload, socket):
	detail = payload["args"]["detail"]

	KProfile().set_web_strategy(detail)
