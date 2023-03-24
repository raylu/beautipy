import io

class Lines:
	def __init__(self, indentation: int, indented: bool):
		self.current = io.StringIO()
		self.lines = [self.current]
		self.indentation = indentation
		self.indented = indented

	def write(self, s: str):
		if not self.indented:
			self.current.write('\t' * self.indentation)
			self.indented = True
		self.current.write(s)

	def new_line(self, content=None):
		self.current = io.StringIO()
		if content is None:
			self.indented = False
		else:
			self.current.write(content)
			self.indented = True
		self.lines.append(self.current)

	def get_values(self) -> list[str]:
		return [sio.getvalue() for sio in self.lines]
