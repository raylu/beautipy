#!/usr/bin/env python3

import difflib
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
	module = cst.parse_module(f.read()).with_changes(default_indent='\t')
	return cst.MetadataWrapper(module).visit(TreeBeautifier()).bytes

SPACE = cst.SimpleWhitespace(' ')
NO_SPACE = cst.SimpleWhitespace('')
NEWLINE = cst.ParenthesizedWhitespace(cst.TrailingWhitespace(newline=cst.Newline()), indent=True,
	last_line=cst.SimpleWhitespace('\t'))
DEDENT_NEWLINE = cst.ParenthesizedWhitespace(cst.TrailingWhitespace(newline=cst.Newline()), indent=True)

class TreeBeautifier(cst.CSTTransformer):
	METADATA_DEPENDENCIES = (libcst.metadata.ExperimentalReentrantCodegenProvider,)

	def leave_SimpleStatementLine(self, orig, node: cst.SimpleStatementLine) -> cst.SimpleStatementLine:
		codegen = self.get_metadata(libcst.metadata.ExperimentalReentrantCodegenProvider, orig)
		split_depth = 1
		while split_depth < 5 and _width(codegen.get_modified_statement_code(node)) > 120:
			node = node.with_changes(body=[_format_node(child, 0, split_depth) for child in node.body])
			split_depth += 1
		return node

	def leave_IndentedBlock(self, orig, node: cst.IndentedBlock) -> cst.IndentedBlock:
		return node.with_changes(indent='\t')

	def leave_Comma(self, orig, node: cst.Comma) -> cst.Comma:
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
			changes['whitespace_before'] = SPACE
		elif before is False:
			changes['whitespace_before'] = NO_SPACE
		if after is True:
			changes['whitespace_after'] = SPACE
		elif after is False:
			changes['whitespace_after'] = NO_SPACE

		if suffix:
			changes = {f'{k}_{suffix}': v for k, v in changes.items()}
		return node.with_changes(**changes)

def _format_node(node: cst.CSTNode, depth: int, split_depth: int) -> cst.CSTNode:
	if isinstance(node, cst.Dict):
		depth += 1
		if depth == split_depth and len(node.elements) > 0:
			comma_newline = cst.Comma(whitespace_after=NEWLINE)
			elements = [element.with_changes(comma=comma_newline) for element in node.elements[:-1]]
			elements.append(node.elements[-1].with_changes(comma=cst.Comma()))
			return node.with_changes(elements=elements,
			    lbrace=cst.LeftCurlyBrace(whitespace_after=NEWLINE),
				rbrace=cst.RightCurlyBrace(whitespace_before=DEDENT_NEWLINE))
		return node
	elif isinstance(node, cst.BaseCompoundStatement):
		return node.with_changes(body=_format_node(node.body, depth, split_depth))
	elif isinstance(node, cst.BaseSuite):
		return node.with_changes(body=[_format_node(stmt, depth, split_depth) for stmt in node.body])
	elif isinstance(node, cst.Assign):
		return node.with_changes(value=_format_node(node.value, depth, split_depth))
	else:
		return node

def _width(formatted: str) -> int:
	max_width = 0
	for line in formatted.split('\n'):
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
