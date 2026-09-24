from core.iplugin import IPlugin
import json
import sys

class ResultAccessPlugin(IPlugin):
	def func(message, resource):
		try:
			json_message = json.loads(message)
		except json.decoder.JSONDecodeError:
			return 'ERROR: json.decoder.JSONDecodeError!\n' + message

		try:
			res = json_message[resource]

			string = 'Номер ИУ: ' + str(res['number']) + '\n'
			string += 'Номер направления ИУ: ' + str(res['direction']) + '\n'
		except:
			return 'ERROR: some exception occured: ' + str(sys.exc_info()[0]) + '!\n' + message

		return string

	def get_hook():
		return 'result', ('access',), ResultAccessPlugin.func