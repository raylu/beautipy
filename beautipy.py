#!/usr/bin/env python3

import keyword
import sys
import token
import tokenize
import typing

import line_manager
import token_tree

def main() -> None:
	for path in sys.argv[1:]:
		with open(path, 'rb') as f:
			print('\n'.join(beautify(f)))

def beautify(f: typing.BinaryIO) -> typing.Iterable[str]:
	tokens = tokenize.tokenize(f.readline)
	encoding = next(tokens)
	assert encoding.type == token.ENCODING

	line_tokens: list[tokenize.TokenInfo] = []
	indentation = 0
	for tok in tokens:
		if tok.type == token.NEWLINE:
			yield _format_line(line_tokens, indentation)
			line_tokens.clear()
		elif tok.type == token.INDENT:
			indentation += 1
		elif tok.type == token.DEDENT:
			indentation -= 1
		else:
			line_tokens.append(tok)

	assert tok.type == token.ENDMARKER

def _format_line(line_tokens: list[tokenize.TokenInfo], indentation: int) -> str:
	tree = token_tree.TokenTree()
	for tok in line_tokens:
		if tok.type == token.OP and tok.exact_type in (token.LPAR, token.LSQB, token.LBRACE):
			tree.push(tok.exact_type)

		tree.append(tok)

		if tok.type == token.OP and tok.exact_type in (token.RPAR, token.RSQB, token.RBRACE):
			tree.pop(tok.exact_type)
	assert len(tree.stack) == 1

	split_depth = 0
	_format_node(tree.root, indentation, 0, split_depth)
	assert tree.root.formatted
	while max(len(l.replace('\t', '    ')) for l in tree.root.formatted) > 120 and split_depth < 5:
		split_depth += 1
		_format_node(tree.root, indentation, 0, split_depth)
	return '\n'.join(tree.root.formatted)

def _format_node(node: token_tree.TokenTreeNode, indentation: int, depth: int, split_depth: int):
	lines = line_manager.Lines(indentation)
	if depth == 0:
		lines.write('\t' * indentation)

	prev_token_was_comma = False
	for tok in node.children:
		if isinstance(tok, token_tree.TokenTreeNode):
			if tok.formatted is None or depth + 1 == split_depth:
				_format_node(tok, indentation, depth + 1, split_depth)
				assert tok.formatted
			lines.write(tok.formatted[0])
			for sub_line in tok.formatted[1:]:
				lines.new_line()
				lines.write(sub_line)
			continue

		if tok.type == token.NL:
			continue

		# prefix
		if tok.type == token.OP:
			if tok.exact_type in (token.RPAR, token.RSQB, token.RBRACE):
				if depth <= split_depth and not prev_token_was_comma:
					lines.write(',')
					lines.new_line()
			elif tok.exact_type == token.EQUAL and node.context != token.LPAR:
				lines.write(' ')
		elif depth <= split_depth and prev_token_was_comma:
			lines.write('\t')

		lines.write(tok.string)

		# suffix
		if tok.type == token.NAME:
			if keyword.iskeyword(tok.string) and tok.string not in ('True', 'False', 'None'):
				lines.write(' ')
		elif tok.type == token.OP:
			if tok.exact_type in (token.LPAR, token.LSQB, token.LBRACE):
				if depth <= split_depth:
					lines.new_line()
					lines.write('\t')
			elif tok.exact_type == token.COMMA:
				if depth <= split_depth:
					lines.new_line()
				else:
					lines.write(' ')
			elif tok.exact_type == token.EQUAL and node.context != token.LPAR:
				lines.write(' ')
			elif tok.exact_type == token.COLON and node.context == token.LBRACE:
				lines.write(' ')

		prev_token_was_comma = tok.exact_type == token.COMMA

	node.formatted = lines.get_values()

if __name__ == '__main__':
	main()
