from core.iplugin import IPlugin

class ExPlugin(IPlugin):
	def func(json, resource):
		return json

	def get_hook():
		return 'ex_type', ('ex_res1', 'ex_res2'), ExPlugin.func