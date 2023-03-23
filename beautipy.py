#!/usr/bin/env python3

import keyword
import sys
import token
import tokenize
import typing

import token_tree

def main() -> None:
	for path in sys.argv[1:]:
		with open(path, 'rb') as f:
			print('\n'.join(beautify(f)))

def beautify(f: typing.BinaryIO) -> typing.Iterable[str]:
	tokens = tokenize.tokenize(f.readline)
	encoding = next(tokens)
	assert encoding.type == token.ENCODING

	indentation = 0
	line_tokens: list[tokenize.TokenInfo] = []
	for tok in tokens:
		if tok.type == token.NEWLINE:
			yield '\t' * indentation + _format_line(line_tokens)
			line_tokens.clear()
		elif tok.type == token.INDENT:
			indentation += 1
		elif tok.type == token.DEDENT:
			indentation -= 1
		else:
			line_tokens.append(tok)

	assert tok.type == token.ENDMARKER

def _format_line(line_tokens: list[tokenize.TokenInfo]) -> str:
	tree = token_tree.TokenTree()
	for tok in line_tokens:
		if tok.type == token.OP and tok.exact_type in (token.LPAR, token.LSQB, token.LBRACE):
			tree.push(tok.exact_type)

		tree.append(tok)

		if tok.type == token.OP and tok.exact_type in (token.RPAR, token.RSQB, token.RBRACE):
			tree.pop(tok.exact_type)

	assert len(tree.stack) == 1
	return _format_node(tree.root)

def _format_node(node: token_tree.TokenTreeNode):
	line = ''
	for tok in node.children:
		if isinstance(tok, token_tree.TokenTreeNode):
			line += _format_node(tok)
			continue

		if tok.type == token.NL:
			continue

		# prefix
		if tok.type == token.OP:
			if tok.exact_type == token.EQUAL and node.context != token.LPAR:
				line += ' '

		line += tok.string

		# suffix
		if tok.type == token.NAME:
			if keyword.iskeyword(tok.string) and tok.string not in ('True', 'False', 'None'):
				line += ' '
		elif tok.type == token.OP:
			if tok.exact_type == token.COMMA:
				line += ' '
			elif tok.exact_type == token.EQUAL and node.context != token.LPAR:
				line += ' '
			elif tok.exact_type == token.COLON and node.context == token.LBRACE:
				line += ' '

	node.formatted = line
	return line

if __name__ == '__main__':
	main()
