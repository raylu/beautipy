import pathlib
import typing
import unittest

import beautipy

def _make_test(case: pathlib.Path) -> typing.Callable:
	def test(self: 'Test') -> None:
		with case.open('rb') as f:
			result = beautipy.beautify(f, None).decode()
		with case.with_name(case.name + '_expected').open('r') as f:
			assert result == f.read()

	return test

class Meta(type):
	def __new__(cls, name, bases, attrs):
		for case in pathlib.Path(__file__).parent.glob('case*'):
			if str(case).endswith('_expected'):
				continue
			attrs['test_' + case.name] = _make_test(case)
		return type.__new__(cls, name, bases, attrs)

class Test(unittest.TestCase, metaclass=Meta):
	pass
