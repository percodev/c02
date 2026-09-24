import os
import importlib.util

class IPluginRegistry(type):
	plugins = []

	def __init__(cls, name, bases, attrs):
		if name != 'IPlugin':
			IPluginRegistry.plugins.append(cls)

class IPlugin(object, metaclass=IPluginRegistry):
	def __init__(self):
		pass

	def get_hook(self):
		return None

def discover_plugins(dirs):
	for dir in dirs:
		for filename in os.listdir(dir):
			modname, ext = os.path.splitext(filename)
			if ext == '.py':
				spec = importlib.util.spec_from_file_location(modname, filename)
				if spec is None:
					raise ImportError(f"Could not load spec for module '{modname}' at: {fname}")
				mod = importlib.util.module_from_spec(spec)
	return IPluginRegistry.plugins