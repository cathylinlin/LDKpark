# src/LDKpark/games100/__init__.py
"""games100 package - lazy import helpers

Avoid importing heavy GUI modules at package import time. Use the
`run_*` helpers to run games (they import modules only when needed).
"""

__all__ = [
	"run_minesweeper",
	"run_dinosaur",
	"get_minesweeper",
	"get_dinosaur",
	"minesweeper",
	"dinosaur",
]


def get_minesweeper():
	"""Return the `minesweeper` module (imported on demand)."""
	from . import minesweeper

	return minesweeper


def run_minesweeper(*args, **kwargs):
	"""Run the minesweeper game. Imports `minesweeper` lazily."""
	mod = get_minesweeper()
	if hasattr(mod, "run"):
		return mod.run(*args, **kwargs)


def get_dinosaur():
	"""Return the `dinosaur` module (imported on demand)."""
	from . import dinosaur

	return dinosaur


def run_dinosaur(*args, **kwargs):
	"""Run the dinosaur game. Imports `dinosaur` lazily."""
	mod = get_dinosaur()
	if hasattr(mod, "run"):
		return mod.run(*args, **kwargs)


# Provide module-like lazy proxies so users can do:
#   from LDKpark.games100 import minesweeper
#   minesweeper.run()
class _ModuleProxy:
	def __init__(self, name):
		self._name = name
		self._mod = None

	def _load(self):
		if self._mod is None:
			# import submodule relative to this package
			self._mod = __import__(f"{__name__}.{self._name}", fromlist=[self._name])

	def __getattr__(self, item):
		self._load()
		return getattr(self._mod, item)

	def run(self, *args, **kwargs):
		self._load()
		if hasattr(self._mod, "run"):
			return self._mod.run(*args, **kwargs)
		raise AttributeError("module has no attribute 'run'")

	def __repr__(self):
		return f"<lazy module proxy {self._name}>"


minesweeper = _ModuleProxy("minesweeper")
dinosaur = _ModuleProxy("dinosaur")

