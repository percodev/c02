from core.iplugin import IPlugin
import json
import sys

access_mode = {'open':'ОТКРЫТО', 'control':'КОНТРОЛЬ'}

class ResultAcmPlugin(IPlugin):
	def func(message, resource):
		try:
			json_message = json.loads(message)
		except json.decoder.JSONDecodeError:
			return 'ERROR: json.decoder.JSONDecodeError!\n' + message

		try:
			res = json_message[resource]

			string = 'Номер ИУ: ' + str(res['number']) + '\n'
			string += 'Номер направления ИУ: ' + str(res['direction']) + '\n'
			string += 'Режим контроля доступа РКД: ' + str(access_mode[res['access_mode']]) + '\n'
		except:
			return 'ERROR: some exception occured: ' + str(sys.exc_info()[0]) + '!\n' + message

		return string

	def get_hook():
		return 'result', ('acm',), ResultAcmPlugin.func