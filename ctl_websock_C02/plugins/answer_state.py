from core.iplugin import IPlugin
import json
import sys

mode_str = {'work mode':'рабочий (дежурный) режим', 'test mode':'режим тестирования прибора', 'memformat mode':'форматирование памяти прибора'}
hard_fail_str = {True:'прибор неисправен', False:'прибор исправен'}
state_suply_12V_str = {True:'питание в норме', False:'выход за диапазон'}
cover_on_str = {True:'корпус прибора открыт', False:'корпус прибора закрыт'}
ip_mode_str = {'on':'перемычка установлена', 'off':'перемычка снята'}
ip_default_str = ip_mode_str
physical_state = {'normal':'дверь закрыта / PASS нормализован', 'active':'дверь открыта / PASS активизирован'}
unlock_state = {'lock':'ИУ заблокировано', 'unlock':'ИУ разблокировано', 'break':'ИУ взломано'}
access_mode = {'open':'ОТКРЫТО', 'control':'КОНТРОЛЬ'}

class AnswerStatePlugin(IPlugin):
	def func(message, resource):
		try:
			json_message = json.loads(message)
		except json.decoder.JSONDecodeError:
			return 'json.decoder.JSONDecodeError!\n' + message

		try:
			res = json_message[resource]

			string = 'Режим прибора: ' + mode_str[res['mode']] + '\n'
			string += 'Аппаратная неисправность: ' + hard_fail_str[res['hard_fail']] + '\n'
			string += 'Исправность источника питания: ' + state_suply_12V_str[res['state_suply_12V']] + '\n' 
			string += 'Вскрытие корпуса прибора: ' + cover_on_str[res['cover_on']] + '\n'
			string += 'Состояние перемычки IP MODE: ' + ip_mode_str[res['ip_mode']] + '\n'
			string += 'Состояние перемычки IP DEFAULT: ' + ip_default_str[res['ip_default']] + '\n'
			string += 'Значение напряжения питания, мВ: ' + str(res['value_suply_12V']) + '\n'

			exdevs = res['exdev']
			for exdev in exdevs:
				string += '\n'
				string += 'ИУ. Физическое состояние: ' + physical_state[exdev['physical_state']] + '\n'
				string += 'ИУ. Состояние разблокировки: ' + unlock_state[exdev['unlock_state']] + '\n'
				modes = exdev['access_mode']
				acc_modes = ''
				for mode in modes:
					acc_modes += access_mode[mode] + ' '
				string += 'ИУ. Режим контроля доступа РКД: ' + acc_modes + '\n'
		except:
			return 'some exception occured: ' + str(sys.exc_info()[0]) + '!\n' + message

		return string

	def get_hook():
		return 'answer', ('state',), AnswerStatePlugin.func