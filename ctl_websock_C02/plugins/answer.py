from core.iplugin import IPlugin
import json

class AnswerPlugin(IPlugin):
	def func(message, resource):
		try:
			json_message = json.loads(message)
		except json.decoder.JSONDecodeError:
			return 'json.decoder.JSONDecodeError!'

		try:
			pad = json_message[resource]

			#string = 'Номер: ' + str(pad['number']) + '\n' + 'Функция: ' + str(pad['function'])
			string = json.dumps(pad, indent = 4)
			#string = pad.__str__()
		except:
			return message

		return string

	def get_hook():
		return 'answer', ('net', 'reader', 'pad', 'exdev', 'cref'), AnswerPlugin.func