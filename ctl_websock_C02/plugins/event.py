from core.iplugin import IPlugin
import json
import sys

remove_card = {True:'карта изъята', False:'карта не изъята'}
command_source = {'server':'сервер', 'remote_control':'ПДУ', 'sensor_fault':'неисправность датчика прохода контроллера'}
unlock = {True:'ИУ разблокировано', False:'ИУ заблокировано'}
on = {True:'активизирован', False:'нормализован'}

class EventPlugin(IPlugin):
	def func(message, resource):
		try:
			json_message = json.loads(message)
		except json.decoder.JSONDecodeError:
			return 'ERROR: json.decoder.JSONDecodeError!\n' + message

		try:
			res = json_message[resource]

			string = ''

			if resource == 'card':
				string += 'Предъявлена карта\n'
				string += 'Номер ИУ: ' + str(res['number']) + '\n'
				string += 'Номер направления ИУ: ' + str(res['direction']) + '\n'
				string += 'ID: ' + res['id'] + '\n'
			elif resource == 'pass_personal':
				string += 'Проход по карте\n'
				string += 'Номер ИУ: ' + str(res['number']) + '\n'
				string += 'Номер направления ИУ: ' + str(res['direction']) + '\n'
				string += 'ID: ' + res['id'] + '\n'
				string += remove_card[res['remove_card']] + '\n'
			elif resource == 'pass_impersonal':
				string += 'Проход по команде ПДУ (софта)\n'
				string += 'Номер ИУ: ' + str(res['number']) + '\n'
				string += 'Номер направления ИУ: ' + str(res['direction']) + '\n'
				string += 'Источник команды разблокировки ИУ: ' + command_source[res['command_source']] + '\n'
			elif resource == 'refusal_personal':
				string += 'Отказ от прохода по карте\n'
				string += 'Номер ИУ: ' + str(res['number']) + '\n'
				string += 'Номер направления ИУ: ' + str(res['direction']) + '\n'
				string += 'ID: ' + res['id'] + '\n'
				string += remove_card[res['remove_card']] + '\n'
			elif resource == 'refusal_impersonal':
				string += 'Отказ от прохода по команде ПДУ (софта)\n'
				string += 'Номер ИУ: ' + str(res['number']) + '\n'
				string += 'Номер направления ИУ: ' + str(res['direction']) + '\n'
				string += 'Источник команды разблокировки ИУ: ' + command_source[res['command_source']] + '\n'
			elif resource == 'pass_ban_personal':
				string += 'Запрет прохода по карте\n'
				string += 'Номер ИУ: ' + str(res['number']) + '\n'
				string += 'Номер направления ИУ: ' + str(res['direction']) + '\n'
				string += 'Источник команды запрета: ' + command_source[res['command_source']] + '\n'
				string += 'ID: ' + res['id'] + '\n'
				string += remove_card[res['remove_card']] + '\n'
			elif resource == 'pass_ban_impersonal':
				string += 'Запрет прохода по команде ПДУ (софта)\n'
				string += 'Номер ИУ: ' + str(res['number']) + '\n'
				string += 'Номер направления ИУ: ' + str(res['direction']) + '\n'
				string += 'Источник команды запрета: ' + command_source[res['command_source']] + '\n'
			elif resource == 'break':
				string += 'Взлом ИУ\n'
				string += 'Номер ИУ: ' + str(res['number']) + '\n'
				string += 'Номер направления ИУ: ' + str(res['direction']) + '\n'
			elif resource == 'exdev_long_open':
				string += 'Не закрыта дверь после прохода\n'
				string += 'Номер ИУ: ' + str(res['number']) + '\n'
				string += 'Номер направления ИУ: ' + str(res['direction']) + '\n'
			elif resource == 'exdev_unlock':
				string += 'Изменение состояния ИУ\n'
				string += 'Номер ИУ: ' + str(res['number']) + '\n'
				string += 'Номер направления ИУ: ' + str(res['direction']) + '\n'
				string += unlock[res['unlock']] + '\n'
			elif resource == 'input':
				string += 'Изменение состояния входа\n'
				string += 'Функция входа: ' + json_message['function'] + '\n'
				string += 'Номер входа: ' + str(res['number']) + '\n'
				string += 'Вход: ' + on[res['on']] + '\n'
			elif resource == 'output':
				string += 'Изменение состояния выхода\n'
				string += 'Номер выхода: ' + str(res['number']) + '\n'
				string += 'Выход: ' + on[res['on']] + '\n'
			else:
				string += 'Неизвестное событие'
		except:
			return 'ERROR: some exception occured: ' + str(sys.exc_info()[0]) + '!\n' + res.__str__() + '\n' + message

		return string

	def get_hook():
		return 'event', ('card', 'pass_personal', 'pass_impersonal', 'refusal_personal', 'refusal_impersonal', 'pass_ban_personal', 'pass_ban_impersonal', 'break', 'exdev_long_open', 'exdev_unlock', 'input', 'output'), EventPlugin.func
