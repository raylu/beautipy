import io

class Lines:
	def __init__(self, indentation: int):
		self.current = io.StringIO()
		self.lines = [self.current]
		self.indentation = indentation

	def write(self, s: str):
		self.current.write(s)

	def new_line(self):
		self.current = io.StringIO('\t' * self.indentation)
		self.lines.append(self.current)

	def get_values(self) -> list[str]:
		return [sio.getvalue() for sio in self.lines]
