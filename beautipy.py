#!/usr/bin/env python3

import dataclasses
import difflib
import typing

import libcst as cst
import libcst.metadata
import libcst._nodes.expression

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
	return cst.MetadataWrapper(module).visit(TreeBeautifier(line_nos)).bytes

SPACE = cst.SimpleWhitespace(' ')
NO_SPACE = cst.SimpleWhitespace('')

def _indented_newline(indent_level: int) -> cst.ParenthesizedWhitespace:
	return cst.ParenthesizedWhitespace(cst.TrailingWhitespace(newline=cst.Newline()), indent=True,
		last_line=cst.SimpleWhitespace('\t' * indent_level))

class TreeBeautifier(cst.CSTTransformer):
	METADATA_DEPENDENCIES = (libcst.metadata.PositionProvider, libcst.metadata.ExperimentalReentrantCodegenProvider)

	def __init__(self, line_nos: typing.Optional[tuple[int, int]]) -> None:
		self.indent_level = 0
		self.line_nos = line_nos

	def leave_SimpleStatementLine(self, orig, node: cst.SimpleStatementLine) -> cst.SimpleStatementLine:
		if not self._should_format(orig):
			return node
		codegen = self.get_metadata(libcst.metadata.ExperimentalReentrantCodegenProvider, orig)
		context = FormatContext(depth=0, split_depth=0, indent_level=self.indent_level)
		while context.split_depth < 5 and _width(codegen.get_modified_statement_code(node)) > 120:
			context = dataclasses.replace(context, split_depth=context.split_depth + 1)
			node = node.with_changes(body=[_format_node(child, context) for child in node.body])
		return node

	def visit_IndentedBlock(self, node: cst.IndentedBlock) -> None:
		self.indent_level += 1

	def leave_IndentedBlock(self, orig, node: cst.IndentedBlock) -> cst.IndentedBlock:
		self.indent_level -= 1
		if not self._should_format(orig):
			return node
		return node.with_changes(indent='\t')

	def leave_Comma(self, orig, node: cst.Comma) -> cst.Comma:
		if not self._should_format(orig):
			return node
		return self._space(node, before=False, after=True)
	
	def leave_AssignEqual(self, orig, node: cst.AssignEqual) -> cst.AssignEqual:
		if not self._should_format(orig):
			return node
		return self._space(node, before=False, after=False)

	def leave_LeftCurlyBrace(self, orig, node: cst.LeftCurlyBrace) -> cst.LeftCurlyBrace:
		if not self._should_format(orig):
			return node
		return self._space(node, after=False)

	def leave_RightCurlyBrace(self, orig, node: cst.RightCurlyBrace) -> cst.RightCurlyBrace:
		if not self._should_format(orig):
			return node
		return self._space(node, before=False)

	def leave_DictElement(self, orig, node: cst.DictElement) -> cst.DictElement:
		if not self._should_format(orig):
			return node
		return self._space(node, 'colon', before=False, after=True)

	def leave_If(self, orig, node: cst.If) -> cst.If:
		if not self._should_format(orig):
			return node
		return self._space(node, 'test', after=False)
	
	def _should_format(self, orig: cst.CSTNode) -> bool:
		if self.line_nos is None:
			return True
		pos = self.get_metadata(libcst.metadata.PositionProvider, orig)
		format_start, format_end = self.line_nos
		return format_start <= pos.end.line and pos.start.line <= format_end

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

@dataclasses.dataclass(eq=False, frozen=True)
class FormatContext:
	depth: int
	split_depth: int
	indent_level: int

	def incr_depth(self) -> 'FormatContext':
		return dataclasses.replace(self, depth=self.depth + 1)

	def incr_split_depth(self) -> 'FormatContext':
		return dataclasses.replace(self, split_depth=self.split_depth + 1)

def _format_node(node: cst.CSTNode, context: FormatContext) -> cst.CSTNode:
	if isinstance(node, cst.Dict):
		context = context.incr_depth()
		if context.depth == context.split_depth and len(node.elements) > 0:
			newline = _indented_newline(context.indent_level + context.depth)
			return node.with_changes(elements=_split_elements(node.elements, newline),
			    lbrace=cst.LeftCurlyBrace(whitespace_after=newline),
				rbrace=cst.RightCurlyBrace(whitespace_before=_indented_newline(context.indent_level + context.depth - 1)))
		else:
			return node.with_changes(elements=[_format_node(element, context) for element in node.elements])
	elif isinstance(node, cst.List):
		context = context.incr_depth()
		if context.depth == context.split_depth and len(node.elements) > 0:
			newline = _indented_newline(context.indent_level + context.depth)
			return node.with_changes(elements=_split_elements(node.elements, newline),
			    lbracket=cst.LeftSquareBracket(whitespace_after=newline),
				rbracket=cst.RightSquareBracket(whitespace_before=_indented_newline(context.indent_level + context.depth - 1)))
		else:
			return node.with_changes(elements=[_format_node(element, context) for element in node.elements])
	elif isinstance(node, (cst.Element, cst.DictElement)):
		return node.with_changes(value=_format_node(node.value, context))
	elif isinstance(node, cst.BaseCompoundStatement):
		return node.with_changes(body=_format_node(node.body, context))
	elif isinstance(node, cst.BaseSuite):
		return node.with_changes(body=[_format_node(stmt, context) for stmt in node.body])
	elif isinstance(node, cst.Assign):
		return node.with_changes(value=_format_node(node.value, context))
	else:
		return node

Elements = typing.Sequence[libcst._nodes.expression._BaseElementImpl]
def _split_elements(elements: Elements, newline: cst.ParenthesizedWhitespace) -> Elements:
	comma_newline = cst.Comma(whitespace_after=newline)
	new_elements = [element.with_changes(comma=comma_newline) for element in elements[:-1]]
	new_elements.append(elements[-1].with_changes(comma=cst.Comma()))
	return new_elements

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
