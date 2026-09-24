import json
#import str

def Parse(message, hooks, pending_request_get):
	'parse incoming message'
	#str = hooks['ex'](message)

	describe_str = ''

	try:
		json_message = json.loads(message)
	except json.decoder.JSONDecodeError:
		return {'status' : False, 'describe_str' : 'Parser: json.decoder.JSONDecodeError: """' + message + '"""', 'data' : None, 'answer' : False}

	resultkey = None
	messagekeys = json_message.keys()
	if 'answer' in messagekeys:
		resultkey = 'answer'
	else:
		if 'result' in messagekeys:
			resultkey = 'result'
		else:
			if 'event' in messagekeys:
				resultkey = 'event'
			else:
				if 'verify' in messagekeys:
					resultkey = 'verify'
				else:
					return {'status': False, 'describe_str': 'Parser: unknown JSON message: """' + message + '"""', 'data': None, 'answer': False}

	result = json_message[resultkey]

	strkey = ''
	if isinstance(result, str):
		strkey = result
		status_str = 'ok'
	else:
		for key in result.keys():
			strkey = key
			break
		status_str = result[strkey]

	#describe_str = '{}: {} {}'.format(resultkey, strkey, status_str).upper()
	describe_str += 'RECEIVE:'

	answer = False
	if resultkey in ('answer', 'result'):
		answer = True
		req = pending_request_get()
		status = Check(req, message)
	else:
		status = True

	if status_str != 'ok':
		describe_str += '\n' + message
		return {'status' : False, 'describe_str' : describe_str, 'data' : json_message, 'answer' : answer}

	execute_hook = None
	#try:
	#	execute_hook = hooks[strkey]
	#except:
	#	describe_str += message
	#else:
	#	describe_str += execute_hook(message)
	for hook in hooks:
		if hook['type'] == resultkey:
			if strkey in hook['resource']:
				execute_hook = hook['hook']
				break

	if execute_hook != None:
		describe_str += '\n' + execute_hook(message, strkey)
	else:
		describe_str += '\n' + message

	return {'status' : status, 'describe_str' : describe_str, 'data' : json_message, 'answer' : answer}

def Check(request, answer):
	'check if `answer` is an answer at our request'
	try:
		json_request = json.loads(request)
	except json.decoder.JSONDecodeError:
		return False

	try:
		json_answer = json.loads(answer)
	except json.decoder.JSONDecodeError:
		return False

	request_keys = json_request.keys()
	if 'id' not in request_keys:
		return True # can't really say anything

	try:
		id = json_answer['id']
	except:
		return False

	if json_request['id'] != id:
		return False

	return True

def ParseReq(message, hooks):
	try:
		json_message = json.loads(message)
	except json.decoder.JSONDecodeError:
		return 'Parser: json.decoder.JSONDecodeError: """' + message + '"""'

	return json.dumps(json_message)
