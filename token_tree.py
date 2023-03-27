import dataclasses
import token
import tokenize
import typing

Node = typing.Union[tokenize.TokenInfo, 'TokenTreeNode']

@dataclasses.dataclass(eq=False)
class TokenTreeNode:
	delim_context: typing.Optional[int] # LPAR, LSQB, or LBRACE
	formatted: typing.Optional[list[str]] = None
	children: list[Node] = dataclasses.field(default_factory=list)

class TokenTree:
	def __init__(self) -> None:
		self.root = TokenTreeNode(delim_context=None)
		self.current = self.root
		self.stack = [self.current]

	def push(self, tok_exact: int) -> None:
		new = TokenTreeNode(delim_context=tok_exact)
		self.current.children.append(new)
		self.stack.append(new)
		self.current = new

	def pop(self, tok_exact: int) -> None:
		top = self.stack.pop()
		self.current = self.stack[-1]
		if tok_exact == token.RPAR:
			assert top.delim_context == token.LPAR
		elif tok_exact == token.RSQB:
			assert top.delim_context == token.LSQB
		if tok_exact == token.RBRACE:
			assert top.delim_context == token.LBRACE

	def append(self, tok: tokenize.TokenInfo) -> None:
		self.current.children.append(tok)

@dataclasses.dataclass
class Context:
	delim_context: typing.Optional[int]
	fn_def: bool
	prev_token_was_comma: bool
