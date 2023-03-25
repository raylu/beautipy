import argparse
import dataclasses
import pathlib
import typing

@dataclasses.dataclass
class Config:
	filepaths: list[pathlib.Path]
	diff: bool
	line_nos: typing.Optional[tuple[int, int]]

def _parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('-d', '--diff', action='store_true', default=False,
			help='output a unified diff instead of formatted code')
	parser.add_argument('-l', '--lines',
			help='range of lines to format', metavar='START-END')
	parser.add_argument('filepaths', nargs='+', type=pathlib.Path,
			help='files to format')
	return parser.parse_intermixed_args()

def _make_config():
	options = _parse_args()
	line_nos = None
	if options.lines is not None:
		line_nos = tuple(map(int, options.lines.split('-', 1)))
	return Config(options.filepaths, options.diff, line_nos)

config = _make_config()
