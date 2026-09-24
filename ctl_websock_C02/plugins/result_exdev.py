from core.iplugin import IPlugin
import json
import sys

action = {'open':'разблокировать ИУ', 'close':'заблокировать ИУ'}
open_type = {'open once':'открыть для однократного прохода', 'open oncealways':'открыть для однократного прохода с бесконечным ожиданием (прохода)', 'open once remove card':'открыть для однократного прохода с изъятием карты', 'open always':'открыть для многокрытных проходов (постоянно)'}

class ResultExDevPlugin(IPlugin):
	def func(message, resource):
		try:
			json_message = json.loads(message)
		except json.decoder.JSONDecodeError:
			return 'ERROR: json.decoder.JSONDecodeError!\n' + message

		try:
			res = json_message[resource]

			string = 'Номер ИУ: ' + str(res['number']) + '\n'
			string += 'Номер направления ИУ: ' + str(res['direction']) + '\n'
			string += 'Действие: ' + action[res['action']] + '\n'
			if res['action'] != 'close':
				string += 'Тип разблокировки: ' + open_type[res['open_type']] + '\n'
				string += 'Время разблокировки, мс: ' + str(res['open_time']) + '\n'
		except:
			return 'ERROR: some exception occured: ' + str(sys.exc_info()[0]) + '!\n' + message

		return string

	def get_hook():
		return 'result', ('exdev',), ResultExDevPlugin.func