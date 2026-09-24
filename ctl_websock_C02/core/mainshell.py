import cmd
try:
	import readline
except ImportError:
	# Fallback for Windows
	from pyreadline3 import Readline
	readline = Readline()
#from multiprocessing import Process
from threading import Thread
import logging
import os
import time
import signal
import sys

from .iplugin import IPluginRegistry, discover_plugins
from .libwebsock.protocol import Protocol

clear_flag = False
def exit_gracefully(signum, frame):
	global clear_flag
	clear_flag = True

# Register signals based on the Operating System
signal.signal(signal.SIGINT, exit_gracefully)
if sys.platform != "win32":
    # On Linux/macOS, register SIGTSTP (triggered by Ctrl+Z)
    signal.signal(signal.SIGTSTP, exit_gracefully)

class MainShell(cmd.Cmd):
	intro = 'Welcome to the main shell.\nType help or ? to list commands.\n'
	prompt = 'main$ '
	proc = None
	prot = None
	file = None

	def __init__(self):
		#super(MainShell, self).__init__()
		logging.basicConfig(level=logging.INFO, format='%(message)s')
		cmd.Cmd.__init__(self)
		plugins = discover_plugins(('plugins',))
		self.prot = Protocol(self.writePrompt, plugins)
		try:
			readline.read_history_file('websock_history')
		except:
			pass

	def do_start(self, arg):
		'Start web sockets server: start [port]'
		if self.proc is not None and self.proc.is_alive():
			print('Server or client is already started')
			return
		#self.proc = Process(name = 'ProtocolProcess', target = self.prot.startServer, args=(arg,))
		self.proc = Thread(name = 'ProtocolProcess', target = self.prot.startServer, args=(arg,))
		self.proc.start()

	def do_connect(self, arg):
		'Connect to the web sockets server: connect [ip]'
		if self.proc is not None and self.proc.is_alive():
			print('Server or client is already started')
			return
		#self.proc = Process(name = 'ProtocolProcess', target = self.prot.startClient, args=(arg,))
		self.proc = Thread(name = 'ProtocolProcess', target = self.prot.startClient, args=(arg,))
		self.proc.start()

	def do_run(self, arg):
		'Execute json file with protocol commands: run <file.json>'
		print('RUN', arg)
		file = open('commands/' + arg, 'r')
		commands = file.read()
		for part in commands.split('\n\n'): # workaround with '\n\n' ...
			self.__run(part+'\n\n')

	def __run(self, part):
		self.prot.sendCommandRaw(part)
		self.do_check(None)
		answer = None
		try:
			answer = self.prot.getAnswer()
		except IndexError:
			pass
		#print(answer['describe_str'])

	def complete_run(self, text, line, begidx, endidx):
		#print('text:' + text + '\n')
		str_list = []
		#if text == '':
		for filename in os.listdir('commands'):
			if filename.startswith(text):
				str_list.append(filename)
		return str_list

	def do_list(self, arg):
		'List of available arguments for command "run": list'
		str = ''
		for filename in os.listdir('commands'):
			str += filename + '\n'
		print(str)
		return

	def do_debug(self, arg):
		'Set DEBUG level'
		logging.getLogger().setLevel(level=logging.DEBUG)
		#self.prot.setDebug()

	def do_exit(self, arg):
		'Stop/disconnect from server and exit'
		self.do_disconnect('')
		self.close()
		try:
			readline.write_history_file('websock_history')
		except:
			print('error while writing history file')
		return True

	def do_disconnect(self, arg):
		'Stop/disconnect from server: disconnect'
		if self.proc is not None and self.proc.is_alive():
			#self.proc.terminate()
			self.prot.stop()
			self.proc.join()

	def do_check(self, arg):
		'Check if there was an answer to the last command'
		start_time = time.perf_counter()
		while not self.prot.lastCommandAnswered:
			if (time.perf_counter() - start_time > 0.1):
				print('Didn\'t receive answer!')
				return
			time.sleep(0.01)
		#print('Receive answer!')

	def do_yes(self, arg):
		'Verification permit'
		verif = str(self.prot.getEventLast()['data']).replace('\'', '"')
		self.__run('{"control":"verify",' + verif[1 : len(verif) - 2] + ',"reply":"permit"}}')

	def do_no(self, arg):
		'Verification prohibit'
		verif = str(self.prot.getEventLast()['data']).replace('\'', '"')
		self.__run('{"control":"verify",' + verif[1 : len(verif) - 2] + ',"reply":"prohibit"}}')

	def do_EOF(self, arg):
		'same as exit: Stop/disconnect from server and exit'
		return self.do_bye(arg)

	def do_eof(self, arg):
		'same as exit: Stop/disconnect from server and exit'
		return self.do_bye(arg)

	def do_bye(self, arg):
		'same as exit: Stop/disconnect from server and exit'
		return self.do_exit(arg)

	def emptyline(self):
		return

	def writePrompt(self, level):
		if logging.getLogger().getEffectiveLevel() <= level:
			#self.stdout.write('\n')
			self.stdout.write(self.prompt)
			self.stdout.flush()

# ----- record and playback -----
	def do_record(self, arg):
		'Save future commands to filename: record <test.cmd>'
		self.file = open(arg, 'w')
	def do_playback(self, arg):
		'Playback commands from a file: playback <test.cmd> <timeout in ms> <retries to try>'
		global clear_flag
		clear_flag = False
		self.close()
		args = arg.split()
		for i in range(int(args[2])):
			with open(args[0]) as f:
				for cmd in f.read().splitlines():
					#print('executing: {}'.format(cmd))
					self.cmdqueue.extend([cmd])
					#self.pause(int(args[1]))
					#self.cmdqueue.extend(['check'])
					self.cmdqueue.extend(['pause {}'.format(int(args[1]))])
	def precmd(self, line):
		global clear_flag
		if clear_flag:
			print('stopping!')
			clear_flag = False
			self.cmdqueue[:] = []
		#line = line.lower()
		if self.file and 'playback' not in line:
			print(line, file=self.file)
		return line
	def close(self):
		if self.file:
			self.file.close()
			self.file = None
	def do_pause(self, ms):
		time.sleep(int(ms)/1000)
