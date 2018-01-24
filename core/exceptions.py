class InvalidOptions(Exception):
    pass

class WindowsError(Exception):

	"""Dummy class for non-Windows systems"""

	def __str__(self):
		return 'this is a dummy class for non-Windows systems'