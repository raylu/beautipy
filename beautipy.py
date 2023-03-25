#!/usr/bin/env python3

import difflib
import keyword
import token
import tokenize
import typing

from config import config
import line_manager
import token_tree

def main() -> None:
	for path in config.filepaths:
		if config.diff:
			with path.open('r') as f:
				orig_lines = f.readlines()
			with path.open('rb') as f:
				formatted = '\n'.join(beautify(f, config.line_nos))
				formatted_lines = [line + '\n' for line in formatted.split('\n')]
			print(''.join(difflib.unified_diff(orig_lines, formatted_lines)))
		else:
			with path.open('rb') as f:
				print('\n'.join(beautify(f, config.line_nos)))

def beautify(f: typing.BinaryIO, line_nos: typing.Optional[tuple[int, int]]) -> typing.Iterable[str]:
	tokens = tokenize.tokenize(f.readline)
	encoding = next(tokens)
	assert encoding.type == token.ENCODING

	line_tokens: list[tokenize.TokenInfo] = []
	indentation = 0
	for tok in tokens:
		if tok.type == token.NEWLINE:
			if line_nos is None:
				yield _format_line(line_tokens, indentation)
			else:
				format_start, format_end = line_nos
				line_start = line_tokens[0].start[0]
				line_end = line_tokens[-1].end[0]
				if format_start <= line_end and line_start <= format_end:
					yield _format_line(line_tokens, indentation)
				else:
					# reproduce the line exactly
					print_next = True
					for tok in line_tokens:
						if print_next:
							yield tok.line.rstrip('\n')
						print_next = tok.type == token.NL
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
	lines = line_manager.Lines(indentation, indented=depth != 0)

	prev_token_was_comma = False
	for tok in node.children:
		if isinstance(tok, token_tree.TokenTreeNode):
			if tok.formatted is None or depth + 1 <= split_depth:
				_format_node(tok, lines.indentation, depth + 1, split_depth)
				assert tok.formatted
			lines.write(tok.formatted[0])
			for sub_line in tok.formatted[1:]:
				lines.new_line(sub_line)
			prev_token_was_comma = False
		else:
			if tok.type == token.NL:
				continue
			_format_token(tok, depth, split_depth, node.context, lines, prev_token_was_comma)
			prev_token_was_comma = tok.exact_type == token.COMMA

	node.formatted = lines.get_values()

def _format_token(tok: tokenize.TokenInfo, depth: int, split_depth: int, context: typing.Optional[int],
		  lines: line_manager.Lines, prev_token_was_comma: bool):
	# prefix
	if tok.type == token.OP:
		if tok.exact_type in (token.RPAR, token.RSQB, token.RBRACE):
			if depth <= split_depth:
				lines.indentation -= 1
				if not prev_token_was_comma:
					lines.write(',')
					lines.new_line()
		elif tok.exact_type == token.EQUAL and context != token.LPAR:
			lines.write(' ')

	lines.write(tok.string)

	# suffix
	if tok.type == token.NAME:
		if keyword.iskeyword(tok.string) and tok.string not in ('True', 'False', 'None'):
			lines.write(' ')
	elif tok.type == token.OP:
		if tok.exact_type in (token.LPAR, token.LSQB, token.LBRACE):
			if depth <= split_depth:
				lines.indentation += 1
				lines.new_line()
		elif tok.exact_type == token.COMMA:
			if depth <= split_depth:
				lines.new_line()
			else:
				lines.write(' ')
		elif tok.exact_type == token.EQUAL and context != token.LPAR:
			lines.write(' ')
		elif tok.exact_type == token.COLON and context == token.LBRACE:
			lines.write(' ')

def _debug(children: list[tokenize.TokenInfo | token_tree.TokenTreeNode]):
	for tok in children:
		if isinstance(tok, token_tree.TokenTreeNode):
			print(tok.formatted)
		else:
			print(tok)

if __name__ == '__main__':
	main()
