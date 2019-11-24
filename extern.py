#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import os
import re
import time
import datetime
from logger import logger


def port_to_pid(port):
	"""
		port to pid useing `netstat`.
	"""
	pid = None
	try:
		result = os.popen(f'netstat -nlp|grep {port} |tr -s " "').readlines()
		flag = f':{port}'
		res = [line.strip() for line in result if flag in line]
		logger.debug(res[0])
		p = res[0].split(' ')
		pp = p[3].split(':')[-1]
		if str(port) == pp:
			pid = p[p.index('LISTEN') + 1].split('/')[0]
	except Exception as err:
		logger.error(err)

	return pid


class DealLogs(object):
	def __init__(self, search, is_io=1):
		self.search = search    # a flag using to find lines in logs
		self.is_io = is_io      # get IO(%) from logs when `search` is not `system`.
		self.total_time = []
		self.io_total_time = []
		self.system = [[], []]      # system cpu, memory
		self.disk_io = [[], [], []]   # disk read, write and util
		self.cpu_and_mem = [[], [], []]     # cpu, memory, jvm

	def get_logs(self, logs, startTime=None, endTime=None):
		"""
			Get logs and rows in logs that contain monitor result.
			logs：all logs，type：list
			startTime：start time, floating point seconds after 1970.
			endTime：end time, floating point seconds after 1970.
		"""
		logs_modify_time = []       # modify time
		logs_create_time = []       # create time
		for log in logs:
			# logs_modify_time.append(os.path.getmtime(log))
			# logs_create_time.append(os.path.getctime(log))
			with open(log, 'r') as f:
				lines = f.readlines()
				logs_modify_time.append(time.mktime(datetime.datetime.strptime(
					self.get_start_end_time(lines, 1), '%Y-%m-%d %H:%M:%S').timetuple()))
				logs_create_time.append(time.mktime(datetime.datetime.strptime(
					self.get_start_end_time(lines, 0), '%Y-%m-%d %H:%M:%S').timetuple()))

		# a tuple that contains modify time, create time and logs.
		data = [(modify_time, log_name, create_time) for modify_time, log_name, create_time in zip(logs_modify_time, logs, logs_create_time)]
		data.sort(reverse=True)     # order by modify time desc.

		flag = 0
		startIndex = -1     # row's start index that contains result
		startLogSort = 0    # log's start index that contains result
		endIndex = -1       # row's end index that contains result
		endLogSort = 0      # log's end index that contains result

		if startTime and endTime:
			for d in data:
				if d[0] <= endTime:     # If modify time is smaller than end time.
					if d[2] <= startTime:   # If create time is smaller than start time.
						# If modify time is larger than start time, to avoid modify time is also smaller than start time.
						if d[0] >= startTime:
							# Start time and end time are both in new log.
							with open(d[1], 'r') as f:
								lines = f.readlines()

							startIndex = self.get_index(lines, 0, len(lines), startTime)     # start index of row
							flag = 2    # get start index of row, and break
						else:
							raise Exception('ERROR: "startTime" is wrong. please input "startTime" again.')
					else:
						startLogSort += 1   # start index of log is add 1.
						continue

				else:    # If modify time is larger than end time.
					if flag != 1:       # If get end index of row, don't get end index of row.
						# If create time is larger than end time, Start time and end time are neither in new log.
						if d[2] > endTime:
							endLogSort += 1     # end index of log is add 1.
							startLogSort += 1   # start index of log is add 1.
							continue
						else:       # If create time is smaller than end time, end time is in new log.
							with open(d[1], 'r') as f:
								lines = f.readlines()

							endIndex = self.get_index(lines, 0, len(lines), endTime)     # end index of row
							flag = 1    # If get end index of row, don't get end index of row.

					if d[2] > startTime:    # If create time is larger than start time.
						startLogSort += 1   # start index of log is add 1.
						continue
					else:       # If create time is smaller than start time.
						if d[0] >= startTime:   # If modify time is larger than start time.
							with open(d[1], 'r') as f:
								lines = f.readlines()

							startIndex = self.get_index(lines, 0, len(lines), startTime)
							flag = 2    # get start index of row, and break.
						else:
							raise Exception('ERROR: "startTime" is wrong. please input "startTime" again.')

				if flag == 2:   # If get index, break
					break

			# If start index of logs is equal to total number of logs, and don't get start index of row,
			# result is in all logs, set start index of row to 0.
			if startLogSort == len(logs) and startIndex == -1:
				startLogSort -= 1   # To avoid index out of bounds.
				startIndex = 0

			return {'startIndex': startIndex, 'startLogSort': startLogSort, 'endIndex': endIndex, 'endLogSort': endLogSort, 'logs': data}

		else:   # If time is None, get result from last start monitor.
			for d in data:      # traverse all logs
				with open(d[1], 'r') as f:
					lines = f.readlines()

				total_lines = len(lines)
				for i in range(total_lines):
					if 'Start monitor' in lines[total_lines - i - 1]:   # Looking backward to find the last start monitor.
						startIndex = total_lines - i - 1
						flag = 1
						break

				if flag == 1:
					break

				startLogSort += 1

			# If start index of logs is equal to total number of logs, and don't get start index of row,
			# result is in all logs, set start index of row to 0.
			if startLogSort == len(logs) and startIndex == -1:
				startLogSort -= 1
				startIndex = 0

			return {'startIndex': startIndex, 'startLogSort': startLogSort, 'endIndex': endIndex, 'endLogSort': endLogSort, 'logs': data}

	def get_start_end_time(self, lines, type):
		"""
			Get first row time and last row time, type=0 is from front to back, type=1 is from back to front.
		"""
		if type == 0:   # get first row time
			for i in range(len(lines)):
				res = self.recompile(lines[i])
				if res:
					return res.group()
				else:
					logger.warning(lines[i])
		if type == 1:   # get last row time
			total_lines = len(lines)
			for i in range(total_lines):
				res = self.recompile(lines[total_lines - i - 1])
				if res:
					return res.group()
				else:
					logger.warning(lines[i])

	def get_index(self, lines, start_index, end_index, search_time):
		"""
			Get index of specified time in log, using dichotomy
			lines: all line of log
			start_index: start index
			end_index: end index
			search_time: specified time, floating point seconds from 1970
		"""
		# To avoid the `search_time` is wrong, or log is blank long-time, it can jump out of loop.
		if end_index - start_index < 2:
			return start_index

		# Use dichotomy to get index
		index = int((start_index + end_index) / 2)
		try:
			t = time.mktime(datetime.datetime.strptime(self.recompile(lines[index]).group(), '%Y-%m-%d %H:%M:%S').timetuple())
			if search_time - t < 0:
				return self.get_index(lines, start_index, index, search_time)
			elif search_time - t > 0:
				return self.get_index(lines, index, end_index, search_time)
			else:
				return index

		except Exception as err:
			logger.warning(err)
			return self.get_index(lines, start_index+1, end_index, search_time)

	def get_values(self, results):
		"""
			Get result from logs.
		"""
		# If start index of row is -1, it means data is wrong, then throw ERROR.
		startIndex = results['startIndex']
		if startIndex == -1:
			raise Exception('ERROR: "startTime" is wrong. please input "startTime" again.')

		startLogSort = results['startLogSort']      # start index of log
		endIndex = results['endIndex']              # end index of row
		endLogSort = results['endLogSort']          # end index of log
		logs = results['logs']                      # log's path, order by modify time desc

		log_list = list(range(startLogSort, endLogSort-1, -1))      # all logs include result

		if len(log_list) == 1:      # If only one log
			with open(logs[log_list[0]][1], 'r') as f:
				lines = f.readlines()

			if endIndex == -1:      # from `startIndex` to end of log
				for j in range(startIndex, len(lines)):
					if self.search == 'system':
						if 'CpuAndMem' in lines[j]:
							self.deal_total_time(lines[j].strip())
							self.system_cpu_mem(lines[j].strip())
						if 'disk_util' in lines[j]:
							self.deal_io_total_time(lines[j].strip())
							self.system_io(lines[j].strip())
					else:
						if 'cpu_and_mem' in lines[j]:
							self.deal_total_time(lines[j].strip())
							self.deal_cpu_and_mem(lines[j].strip())
						if self.is_io:
							if 'disk_util' in lines[j]:
								self.deal_io_for_pid(lines[j].strip())
								self.system_io(lines[j].strip())
			else:       # from `startIndex` to `endIndex`
				for j in range(startIndex, endIndex):
					if self.search == 'system':
						if 'CpuAndMem' in lines[j]:
							self.deal_total_time(lines[j].strip())
							self.system_cpu_mem(lines[j].strip())
						if 'disk_util' in lines[j]:
							self.deal_io_total_time(lines[j].strip())
							self.system_io(lines[j].strip())
					else:
						if 'cpu_and_mem' in lines[j]:
							self.deal_total_time(lines[j].strip())
							self.deal_cpu_and_mem(lines[j].strip())
						if self.is_io:
							if 'disk_util' in lines[j]:
								self.deal_io_for_pid(lines[j].strip())
								self.system_io(lines[j].strip())

		if len(log_list) == 2:      # If only two logs
			with open(logs[log_list[0]][1], 'r') as f:
				lines = f.readlines()

			for j in range(startIndex, len(lines)):     # first log, from `startIndex` to end of log
				if self.search == 'system':
					if 'CpuAndMem' in lines[j]:
						self.deal_total_time(lines[j].strip())
						self.system_cpu_mem(lines[j].strip())
					if 'disk_util' in lines[j]:
						self.deal_io_total_time(lines[j].strip())
						self.system_io(lines[j].strip())
				else:
					if 'cpu_and_mem' in lines[j]:
						self.deal_total_time(lines[j].strip())
						self.deal_cpu_and_mem(lines[j].strip())
					if self.is_io:
						if 'disk_util' in lines[j]:
							self.deal_io_for_pid(lines[j].strip())
							self.system_io(lines[j].strip())

			with open(logs[log_list[1]][1], 'r') as f:
				lines = f.readlines()

			if endIndex == -1:      # second log, from start to end of log
				for j in range(len(lines)):
					if self.search == 'system':
						if 'CpuAndMem' in lines[j]:
							self.deal_total_time(lines[j].strip())
							self.system_cpu_mem(lines[j].strip())
						if 'disk_util' in lines[j]:
							self.deal_io_total_time(lines[j].strip())
							self.system_io(lines[j].strip())
					else:
						if 'cpu_and_mem' in lines[j]:
							self.deal_total_time(lines[j].strip())
							self.deal_cpu_and_mem(lines[j].strip())
						if self.is_io:
							if 'disk_util' in lines[j]:
								self.deal_io_for_pid(lines[j].strip())
								self.system_io(lines[j].strip())
			else:
				for j in range(0, endIndex):    # second log, from start to `endIndex`
					if self.search == 'system':
						if 'CpuAndMem' in lines[j]:
							self.deal_total_time(lines[j].strip())
							self.system_cpu_mem(lines[j].strip())
						if 'disk_util' in lines[j]:
							self.deal_io_total_time(lines[j].strip())
							self.system_io(lines[j].strip())
					else:
						if 'cpu_and_mem' in lines[j]:
							self.deal_total_time(lines[j].strip())
							self.deal_cpu_and_mem(lines[j].strip())
						if self.is_io:
							if 'disk_util' in lines[j]:
								self.deal_io_for_pid(lines[j].strip())
								self.system_io(lines[j].strip())

		if len(log_list) > 2:       # If much logs
			with open(logs[log_list[0]][1], 'r') as f:
				lines = f.readlines()

			for j in range(startIndex, len(lines)):     # first log, from `startIndex` to end of log
				if self.search == 'system':
					if 'CpuAndMem' in lines[j]:
						self.deal_total_time(lines[j].strip())
						self.system_cpu_mem(lines[j].strip())
					if 'disk_util' in lines[j]:
						self.deal_io_total_time(lines[j].strip())
						self.system_io(lines[j].strip())
				else:
					if 'cpu_and_mem' in lines[j]:
						self.deal_total_time(lines[j].strip())
						self.deal_cpu_and_mem(lines[j].strip())
					if self.is_io:
						if 'disk_util' in lines[j]:
							self.deal_io_for_pid(lines[j].strip())
							self.system_io(lines[j].strip())

			for m in range(1, len(log_list)-1):         # intermediate logs
				with open(logs[log_list[m]][1], 'r') as f:
					lines = f.readlines()

				for j in range(len(lines)):
					if self.search == 'system':
						if 'CpuAndMem' in lines[j]:
							self.deal_total_time(lines[j].strip())
							self.system_cpu_mem(lines[j].strip())
						if 'disk_util' in lines[j]:
							self.deal_io_total_time(lines[j].strip())
							self.system_io(lines[j].strip())
					else:
						if 'cpu_and_mem' in lines[j]:
							self.deal_total_time(lines[j].strip())
							self.deal_cpu_and_mem(lines[j].strip())
						if self.is_io:
							if 'disk_util' in lines[j]:
								self.deal_io_for_pid(lines[j].strip())
								self.system_io(lines[j].strip())

			with open(logs[log_list[-1]][1], 'r') as f:
				lines = f.readlines()

			if endIndex == -1:          # last log
				for j in range(len(lines)):
					if self.search == 'system':
						if 'CpuAndMem' in lines[j]:
							self.deal_total_time(lines[j].strip())
							self.system_cpu_mem(lines[j].strip())
						if 'disk_util' in lines[j]:
							self.deal_io_total_time(lines[j].strip())
							self.system_io(lines[j].strip())
					else:
						if 'cpu_and_mem' in lines[j]:
							self.deal_total_time(lines[j].strip())
							self.deal_cpu_and_mem(lines[j].strip())
						if self.is_io:
							if 'disk_util' in lines[j]:
								self.deal_io_for_pid(lines[j].strip())
								self.system_io(lines[j].strip())
			else:
				for j in range(0, endIndex):
					if self.search == 'system':
						if 'CpuAndMem' in lines[j]:
							self.deal_total_time(lines[j].strip())
							self.system_cpu_mem(lines[j].strip())
						if 'disk_util' in lines[j]:
							self.deal_io_total_time(lines[j].strip())
							self.system_io(lines[j].strip())
					else:
						if 'cpu_and_mem' in lines[j]:
							self.deal_total_time(lines[j].strip())
							self.deal_cpu_and_mem(lines[j].strip())
						if self.is_io:
							if 'disk_util' in lines[j]:
								self.deal_io_for_pid(lines[j].strip())
								self.system_io(lines[j].strip())

	def system_cpu_mem(self, line):
		"""
			Get CPU and Memory from logs
		"""
		res = line.split(',')
		self.system[0].append(float(res[-2]))       # CPU
		self.system[1].append(float(res[-1]))       # Memory

	def system_io(self, line):
		"""
			Get disk read, write and util from logs
		"""
		res = line.split(',')
		self.disk_io[0].append(float(res[-3]))  # read
		self.disk_io[1].append(float(res[-2]))  # write
		self.disk_io[2].append(float(res[-1]))  # util(%)

	def deal_cpu_and_mem(self, line):
		"""
			Get CPU, memory and JVM from logs
		"""
		if self.search in line:
			res = line.split(',')
			self.cpu_and_mem[0].append(float(res[-3]))  # CPU
			self.cpu_and_mem[1].append(float(res[-2]))  # memory
			self.cpu_and_mem[2].append(float(res[-1]))  # JVM

	def deal_total_time(self, line):
		"""
			Get time from logs, for CPU and Memory
		"""
		if self.search in line:
			try:
				self.total_time.append(self.recompile(line).group())
			except Exception as err:
				logger.error(err)

	def deal_io_total_time(self, line):
		"""
			Get time from logs, for IO
		"""
		if self.search in line:
			try:
				self.io_total_time.append(self.recompile(line).group())
			except Exception as err:
				logger.error(err)

	def deal_io_for_pid(self, line):
		"""
			Get time from logs, for IO, for pid
		"""
		try:
			self.io_total_time.append(self.recompile(line).group())
		except Exception as err:
			logger.error(err)

	def recompile(self, line):
		"""
			regular expression to get time from logs
		"""
		pattern = '(20\d{2}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
		res = re.match(pattern, line)
		return res

	def read_data_from_logs(self, logs, startTime=None, endTime=None):
		results = self.get_logs(logs, startTime, endTime)
		self.get_values(results)
