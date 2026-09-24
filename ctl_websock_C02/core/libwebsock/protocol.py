#from multiprocessing import Queue
from queue import Queue
from collections import deque
import logging
import websockets
import asyncio
from queue import Empty as qEmpty #import queue
import re #for splitting
import time
import signal
import sys # for general exception handling
import ssl
import pathlib
from concurrent.futures import CancelledError

from .parser import Parse, ParseReq

import traceback

class Protocol():
	__connected = set()
	clientConnected = False
	__writePrompt = None
	__send_queue = Queue()
	__command_queue = Queue()
	__answer_queue = deque(maxlen = 20)
	__event_queue = deque(maxlen = 20)
	__pending_request_queue = Queue()
	__hooks = list()
	__tasks = set()
	#is_stop = False
	event_loop = None
	lastCommandAnswered = False
	exec_obj = None

	def __init__(self, writePrompt = lambda x: None, plugins = []):
		self.__writePrompt = writePrompt
		for plugin in plugins:
			res_type, resource, hook = plugin.get_hook()
			print('plugin loaded:', plugin.__module__, 'type:', res_type, 'resource(s):', ', '.join(resource))
			#self.hooks[resource] = hook
			self.__hooks.append({'type' : res_type, 'resource' : resource, 'hook' : hook})
		#print('plugins loaded: ' + plugins.__repr__())

	async def __run_commands_from_queue(self):
		while True:
			try:
				command = self.__command_queue.get_nowait()
			except qEmpty:
				await asyncio.sleep(0.01)
			else:
				self.__shellPrintDebug('Executing command: ' + command.__str__())
				#command()
				getattr(self, command)()

	async def __consumer(self, message):
		# workaround with '\n\n' ...
		#if '\n\n' in message:
			for mess in message.split('\n\n'):
				if len(mess) != 0:
					result = Parse(mess, self.__hooks, self.__pending_request_get)
					if result['data'] != None:
						if result['answer']:
							self.__answer_queue.append(result)
							self.lastAnswer = result
							self.lastCommandAnswered = True
						else:
							self.__event_queue.append(result)
					self.__shellPrint(result['describe_str'])
			return

		# normal logic
		#result = Parse(message, self.__hooks, self.__pending_request_get)
		#if result['data'] != None:
		#	self.__answer_queue.append(result)
		#	self.lastAnswer = result
		#	self.lastCommandAnswered = True
		#self.__shellPrint(result['describe_str'])

	async def __producer(self):
		self.__shellPrintDebug('Trying to get. size: ' + str(self.__send_queue.qsize()))
		while True:
			try:
				command = self.__send_queue.get_nowait()
			except qEmpty:
				await asyncio.sleep(0.01)
			else:
				break
		self.__shellPrintDebug('Getting: ' + command)
		self.__shellPrint('Sending command: ' + ParseReq(command, self.__hooks))
		return command

	async def __sendreceive(self, websocket):
		listener_task = asyncio.ensure_future(websocket.recv())
		producer_task = asyncio.ensure_future(self.__producer())
		self.__tasks.add(listener_task)
		self.__tasks.add(producer_task)
		done, pending = await asyncio.wait(
			[listener_task, producer_task],
			return_when=asyncio.FIRST_COMPLETED)
		if listener_task in done:
			self.__tasks.remove(listener_task)
			message = listener_task.result()
			self.__shellPrintDebug('< ' + message)
			await self.__consumer(message)
		else:
			self.__shellPrintDebug('Listener cancel')
			listener_task.cancel()
			self.__tasks.remove(listener_task)
		if producer_task in done:
			self.__tasks.remove(producer_task)
			message = producer_task.result()
			self.__shellPrintDebug('> ' + message)
			await websocket.send(message)
			self.__pending_request_queue.put(message)
		else:
			self.__shellPrintDebug('Producer cancel')
			producer_task.cancel()
			self.__tasks.remove(producer_task)

	async def __handlerServer(self, websocket):
		self.__shellPrint('try connected...')
		self.__clear_send_queue()
		self.__connected.add(websocket)
		#print(self.exec_obj.websockets)
		#print(self.exec_obj.server.sockets)
		self.__shellPrint("+ " + websocket.remote_address.__repr__())
		try:
			while True:
				#if is_stop:
				#	print('break!')
				#	break
				await self.__sendreceive(websocket)
		except websockets.exceptions.ConnectionClosed:
			pass
		finally:
			self.__connected.remove(websocket)
			self.__shellPrint('- ' + websocket.remote_address.__repr__())

	async def __handlerClient(self, address, origin):
		#try:
			self.__clear_send_queue()
			self.sendCommandRaw('{"set":"verify_acl","verify_acl":[{}]}')
			try:
				async with websockets.connect(address, origin = origin, proxy = None) as websocket:
					self.clientConnected = True
					self.exec_obj = websocket
					self.__shellPrint('<connected>')
					while True:
						#if is_stop:
						#	break
						await self.__sendreceive(websocket)
			except websockets.exceptions.ConnectionClosed:
				self.__shellPrint('ERROR: Connection closed!')
			except websockets.exceptions.InvalidHandshake:
				self.__shellPrint('ERROR: Can\'t connect!')
			except Exception as e:
				# This will catch ANY other error and print the exact line causing it
				self.__shellPrint(f'UNEXPECTED ERROR: {e}')
				traceback.print_exc()
			finally:
				self.clientConnected = False
				self.exec_obj = None
				self.__shellPrint('<disconnected>')

	def sendCommandRaw(self, command):
		'Thread-safe'
		self.lastCommandAnswered = False
		self.__send_queue.put(command)
		self.__shellPrintDebug('Added. size: ' + str(self.__send_queue.qsize()))

	def executeTask(self, task):
		'Thread-safe, task should be an object with __call__ method, which will be executed in the Protocol process'
		self.__command_queue.put(task)
		#print(logging.getLogger().getEffectiveLevel())

	def startServer(self, arg):  # Ex: start 8080     start 12345 secure
		'Main procedure for starting the server'
		isSecure = False
		port = 80
		ip = '0.0.0.0'
		args = arg.split()
		self.__shellPrint('Args:' + str(args))
		if len(args) > 0 and 's' in args[0]:
			port = 443
			isSecure = True
			args.pop(0)  # Fixed: changed from popleft() to pop(0)
		if len(args) > 0 and args[0] != '':
			port = int(args[0])
		if len(args) > 1 and 's' in args[1]:
			isSecure = True

		self.event_loop = asyncio.new_event_loop()
		asyncio.set_event_loop(self.event_loop)

		ssl_context = None
		if isSecure:
			self.__shellPrint('Starting secure server at ' + ip + ':' + str(port))
			self.__shellPrint('   with key ' + str(pathlib.Path(__file__).with_name("localhost.pem")))
			ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
			localhost_pem = pathlib.Path(__file__).with_name("localhost.pem")
			localhost_key = pathlib.Path(__file__).with_name("localhost.key")
			ssl_context.load_cert_chain(localhost_pem, localhost_key)
		else:
			self.__shellPrint('Starting server at ' + ip + ':' + str(port))

		async def initialize_app():
			server = await websockets.serve(self.__handlerServer, ip, port, ssl=ssl_context)
			queue_task = asyncio.ensure_future(self.__run_commands_from_queue())
			self.__tasks.add(queue_task)
			return server, queue_task

		try:
			# Initialize components
			self.exec_obj, queue_task = self.event_loop.run_until_complete(initialize_app())

			self.event_loop.run_until_complete(queue_task)

		except (KeyboardInterrupt, asyncio.CancelledError):
			self.__shellPrint('\n[Shutdown Triggered] Shutting down thread loop...')
		except Exception as e:
			self.__shellPrintDebug(': %s' % e)
		finally:
			self.__shellPrintDebug('Cleaning up running tasks inside thread...')

			# 1. Close the WebSocket server safely
			if self.exec_obj:
				self.exec_obj.close()
				self.event_loop.run_until_complete(self.exec_obj.wait_closed())

			# 2. Cancel all pending async background tasks (like the command queue)
			pending = asyncio.all_tasks(self.event_loop)
			for task in pending:
				task.cancel()
  
			# Let the tasks finish their cancellation lifecycle
			if pending:
				self.event_loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

			self.__shellPrintDebug('Ending of the event loop...')
			self.event_loop.close()

	def startClient(self, arg):
		'Main procedure for starting the client'
		port = 80
		ip = '127.0.0.1'
		if arg != '':
			ip = arg
		address = 'ws://' + ip + ':' + str(port) + '/tcp'
		self.__shellPrint('Connecting to ' + address)
		self.event_loop = asyncio.new_event_loop()
		asyncio.set_event_loop(self.event_loop)
		#asyncio.set_event_loop(asyncio.new_event_loop())
		queue_task = asyncio.ensure_future(self.__run_commands_from_queue())
		#self.__tasks.add(queue_task)
		#print('run_until_complete')
		#asyncio.get_event_loop().run_until_complete(self.__handlerClient(address, ip))
		client_task = asyncio.ensure_future(self.__handlerClient(address, ip))
		self.__tasks.add(queue_task)
		self.__tasks.add(client_task)
		#print('run_forever')
		#asyncio.get_event_loop().run_forever()
		try:
			#asyncio.get_event_loop().run_until_complete(asyncio.wait(self.__tasks, return_when=asyncio.ALL_COMPLETED))
			asyncio.get_event_loop().run_until_complete(client_task)
		except:
			e = sys.exc_info()[0]
			self.__shellPrintDebug('Error: %s' % e)
		self.__shellPrintDebug('Ending of the event loop...')

	def stop(self):
		print('cancelling task')
		self.exec_obj.close()
		#asyncio.ensure_future(self.exec_obj.wait_closed())
		#asyncio.get_event_loop().run_until_complete(self.exec_obj.wait_closed())
		#asyncio.get_event_loop().ensure_future(self.exec_obj.close())
		for task in self.__tasks:
			task.cancel()
		#print('waiting for task is done')
		#for task in self.__tasks:
		#	while not task.done():
		#		pass
		#print('stopping event loop')
		#self.event_loop.stop()
		#self.clientConnected = False # FIXME: should not be there, will be fixed after nicely close all asyncio tasks
		#is_stop = True
		#print('Stop!')

	def getAnswer(self):
		return self.__answer_queue.popleft()

	def getEvent(self):
		return self.__event_queue.popleft()

	def getEventLast(self):
		return self.__event_queue.pop()

	def __shellPrint(self, arg):
		#if logging.getLogger().getEffectiveLevel() <= logging.INFO:
			logging.info('\r' + arg)
			self.__writePrompt(logging.INFO)

	def __shellPrintDebug(self, arg):
		#if logging.getLogger().getEffectiveLevel() <= logging.DEBUG:
			logging.debug('\r' + arg)
			self.__writePrompt(logging.DEBUG)

	def __chunkstring(self, string, length):
		return (string[0 + i : length + i] for i in range(0, len(string), length))

	def __pending_request_get(self):
		try:
			request = self.__pending_request_queue.get_nowait()
		except qEmpty:
			self.__shellPrint('ERROR: Unexpected answer!')
			return ''
		else:
			#print('GET req: {}'.format(request))
			return request

	def __clear_send_queue(self):
		while not self.__send_queue.empty():
			self.__send_queue.get_nowait()
