import dataclasses
import token
import tokenize
import typing

@dataclasses.dataclass(eq=False)
class TokenTreeNode:
	context: typing.Optional[int]
	formatted: typing.Optional[str] = None
	children: list[typing.Union[tokenize.TokenInfo, 'TokenTreeNode']] = dataclasses.field(default_factory=list)

class TokenTree:
	def __init__(self) -> None:
		self.root = TokenTreeNode(context=None)
		self.current = self.root
		self.stack = [self.current]

	def push(self, tok_exact: int) -> None:
		new = TokenTreeNode(context=tok_exact)
		self.current.children.append(new)
		self.stack.append(new)
		self.current = new

	def pop(self, tok_exact: int) -> None:
		top = self.stack.pop()
		self.current = self.stack[-1]
		if tok_exact == token.RPAR:
			assert top.context == token.LPAR
		elif tok_exact == token.RSQB:
			assert top.context == token.LSQB
		if tok_exact == token.RBRACE:
			assert top.context == token.LBRACE

	def append(self, tok: tokenize.TokenInfo) -> None:
		self.current.children.append(tok)
