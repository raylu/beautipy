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

def beautify(f) -> typing.Iterable[str]:
	tokens = tokenize.tokenize(f.readline)
	encoding = next(tokens)
	assert encoding.type == token.ENCODING

	indentation = 0
	stack: list[int] = []
	line = ''
	for tok in tokens:
		print(token.tok_name[tok.exact_type], tok)
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
				if tok.exact_type == token.EQUAL:
					line += ' '

			line += tok.string

			# suffix
			if tok.type == token.NAME:
				if keyword.iskeyword(tok.string) and tok.string not in ('True', 'False', 'None'):
					line += ' '
			elif tok.type == token.OP:
				if tok.exact_type == token.EQUAL:
					line += ' '

			# modify stack
			if tok.type == token.OP:
				if tok.exact_type in (token.LPAR, token.LSQB, token.LBRACE):
					stack.append(tok.exact_type)
				elif tok.exact_type in (token.RPAR, token.RSQB, token.RBRACE):
					stack.pop()

if __name__ == '__main__':
	main()
