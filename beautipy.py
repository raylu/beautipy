#!/usr/bin/env python3

import difflib
import token
import tokenize
import typing

import libcst as cst
import libcst.metadata

import configuration

def main() -> None:
	config = configuration.make_config()
	for path in config.filepaths:
		if config.diff:
			with path.open('r') as f:
				orig_lines = f.readlines()
			with path.open('rb') as f:
				formatted = beautify(f, config.line_nos).decode()
				formatted_lines = [line + '\n' for line in formatted.split('\n')]
			print(''.join(difflib.unified_diff(orig_lines, formatted_lines)))
		else:
			with path.open('rb') as f:
				print(beautify(f, config.line_nos).decode(), end='')

def beautify(f: typing.BinaryIO, line_nos: typing.Optional[tuple[int, int]]) -> bytes:
	tree = cst.MetadataWrapper(cst.parse_module(f.read()))
	return tree.visit(TreeBeautifier()).bytes

class TreeBeautifier(cst.CSTTransformer):
	METADATA_DEPENDENCIES = (libcst.metadata.ParentNodeProvider,)
	SPACE = cst.SimpleWhitespace(' ')
	NO_SPACE = cst.SimpleWhitespace('')
	NEWLINE = cst.TrailingWhitespace(newline=cst.Newline())

	def visit_Module_body(self, node: cst.Module) -> None:
		#print(node.body)
		pass

	def leave_IndentedBlock(self, orig, node: cst.IndentedBlock) -> cst.IndentedBlock:
		return node.with_changes(indent='\t')

	def leave_Comma(self, orig, node: cst.Comma) -> cst.Comma:
		parent = self.get_metadata(libcst.metadata.ParentNodeProvider, orig)
		if isinstance(parent, cst.DictElement):
			return node.with_changes(whitespace_before=self.NO_SPACE, whitespace_after=self.NEWLINE)
		return self._space(node, before=False, after=True)
	
	def leave_AssignEqual(self, orig, node: cst.AssignEqual) -> cst.AssignEqual:
		return self._space(node, before=False, after=False)

	def leave_LeftCurlyBrace(self, orig, node: cst.LeftCurlyBrace) -> cst.LeftCurlyBrace:
		return self._space(node, after=False)

	def leave_RightCurlyBrace(self, orig, node: cst.RightCurlyBrace) -> cst.RightCurlyBrace:
		return self._space(node, before=False)

	def leave_DictElement(self, orig, node: cst.DictElement) -> cst.DictElement:
		return self._space(node, 'colon', before=False, after=True)

	def leave_If(self, orig, node: cst.If) -> cst.If:
		return self._space(node, 'test', after=False)
	
	@classmethod
	def _space(cls, node: cst.CSTNodeT, suffix = '', before: typing.Optional[bool] = None,
			after: typing.Optional[bool] = None) -> cst.CSTNodeT:
		changes = {}
		if before is True:
			changes['whitespace_before'] = cls.SPACE
		elif before is False:
			changes['whitespace_before'] = cls.NO_SPACE
		if after is True:
			changes['whitespace_after'] = cls.SPACE
		elif after is False:
			changes['whitespace_after'] = cls.NO_SPACE

		if suffix:
			changes = {f'{k}_{suffix}': v for k, v in changes.items()}
		return node.with_changes(**changes)

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
	while _width(tree.root.formatted) > 120 and split_depth < 5:
		split_depth += 1
		_format_node(tree.root, indentation, 0, split_depth)
	return '\n'.join(tree.root.formatted)

def _width(formatted: list[str]) -> int:
	max_width = 0
	for line in formatted:
		width = 0
		for i, ch in enumerate(line):
			if ch == '\t':
				width += 4
			else:
				width += len(line) - i
				break
		if width > max_width:
			max_width = width
	return max_width

if __name__ == '__main__':
	main()
