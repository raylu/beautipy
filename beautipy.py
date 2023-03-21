#!/usr/bin/env python3

import keyword
import sys
import token
import tokenize
import typing

def main() -> None:
	for path in sys.argv[1:]:
		with open(path, 'rb') as f:
			print('\n'.join(beautify(f)))

def beautify(f: typing.BinaryIO) -> typing.Iterable[str]:
	tokens = tokenize.tokenize(f.readline)
	encoding = next(tokens)
	assert encoding.type == token.ENCODING

	indentation = 0
	stack = Stack()
	line = ''
	for tok in tokens:
		print(token.tok_name[tok.exact_type], tok, file=sys.stderr)
		if tok.type == token.NEWLINE:
			yield '\t' * indentation + line
			line = ''
		elif tok.type == token.INDENT:
			indentation += 1
		elif tok.type == token.DEDENT:
			indentation -= 1
		else:
			# prefix
			if tok.type == token.OP:
				if tok.exact_type == token.EQUAL and stack.top() != token.LPAR:
					line += ' '

			line += tok.string

			# suffix
			if tok.type == token.NAME:
				if keyword.iskeyword(tok.string) and tok.string not in ('True', 'False', 'None'):
					line += ' '
			elif tok.type == token.OP:
				if tok.exact_type == token.COMMA:
					line += ' '
				elif tok.exact_type == token.EQUAL and stack.top() != token.LPAR:
					line += ' '
				elif tok.exact_type == token.COLON and stack.top() == token.LBRACE:
					line += ' '

			# modify stack
			if tok.type == token.OP:
				if tok.exact_type in (token.LPAR, token.LSQB, token.LBRACE):
					stack.push(tok.exact_type)
				elif tok.exact_type in (token.RPAR, token.RSQB, token.RBRACE):
					stack.pop(tok.exact_type)

class Stack:
	def __init__(self):
		self.stack: list[int] = []

	def push(self, tok: int) -> None:
		self.stack.append(tok)

	def pop(self, tok: int) -> int:
		top = self.stack.pop()
		if tok == token.RPAR:
			assert top == token.LPAR
		elif tok == token.RSQB:
			assert top == token.LSQB
		if tok == token.RBRACE:
			assert top == token.LBRACE
		return top

	def top(self) -> typing.Optional[int]:
		if len(self.stack) > 0:
			return self.stack[-1]

if __name__ == '__main__':
	main()
