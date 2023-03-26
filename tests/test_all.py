import pathlib
import unittest

import beautipy

class Test(unittest.TestCase):
	def tests(self):
		for case in pathlib.Path(__file__).parent.glob('case*'):
			if str(case).endswith('_expected'):
				continue
			with self.subTest(case):
				self.run_testcase(case)
	
	def run_testcase(self, case: pathlib.Path):
		with case.open('rb') as f:
			result = '\n'.join(beautipy.beautify(f, None)) + '\n'
		with case.with_name(case.name + '_expected').open('r') as f:
			assert result == f.read()
