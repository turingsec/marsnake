from utils.singleton import singleton

import random, string

@singleton
class Krandom(object):
    def __init__(self):
        pass

    def uppercase(self, length):
        seq = string.ascii_uppercase
        return ''.join(random.choice(seq) for _ in range(length))

    def lowercase(self, length):
        seq = string.ascii_lowercase
        return ''.join(random.choice(seq) for _ in range(length))

    def purely(self, length):
        seq = string.ascii_uppercase + string.digits + string.ascii_lowercase
        return ''.join(random.choice(seq) for _ in range(length))
