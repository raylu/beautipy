import argparse
import dataclasses
import pathlib

@dataclasses.dataclass
class Config:
	filepaths: list[pathlib.Path]
	diff: bool

def _parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('-d', '--diff', action='store_true', default=False,
			help='output a unified diff instead of formatted code')
	parser.add_argument('filepaths', nargs='+', type=pathlib.Path,
			help='files to format')
	return parser.parse_intermixed_args()

config = Config(**vars(_parse_args()))
