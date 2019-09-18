#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import os
import re
import time
import datetime
from logger import logger
import config as cfg


def ports_to_pids(ports):
	"""
		端口号转进程号
	"""
	pids = []
	for p in ports:
		pid = port_to_pid(p)
		if pid:
			pids.append(pid)
		else:
			return str(p)

	return pids


def port_to_pid(port):
	"""
		使用netstat命令将端口号转进程号.
	"""
	pid = None
	try:
		result = os.popen(f'netstat -nlp|grep {port} |tr -s " "').readlines()       # 执行netstat命令
		res = [line.strip() for line in result if str(port) in line]
		logger.debug(res[0])
		p = res[0].split(' ')
		pp = p[3].split(':')[-1]
		if str(port) == pp:
			pid = p[-1].split('/')[0]
	except Exception as err:
		logger.error(err)

	return pid


# 处理日志，从日志中读取出监控结果
class DealLogs(object):
	def __init__(self, search):
		self.search = search    # 带端口号或进程号查询
		self.is_monitor_system = cfg.IS_MONITOR_SYSTEM  # 是否监控系统资源
		self.total_time = []
		self.io_total_time = []
		self.system = [[], []]      # cpu、内存
		self.disk_io = [[], [], []]   # 磁盘读、写、使用率
		self.cpu_and_mem = [[], [], []]     # cpu、内存、jvm
		self.io = [[], [], [], [], [], []]  # 进程读、写、使用率，磁盘读、写、使用率

	def get_logs(self, logs, startTime=None, endTime=None):
		"""
			查找一段时间内的监控结果
			logs：所有日志的文件路径，数据类型：list
			startTime：查找监控结果开始时间，单位为 1970纪元后经过的浮点秒数
			endTime：查找监控结果结束时间，单位为 1970纪元后经过的浮点秒数
		"""
		logs_modify_time = []       # 日志文件修改时间
		logs_create_time = []       # 日志文件创建时间
		for log in logs:
			# logs_modify_time.append(os.path.getmtime(log))
			# logs_create_time.append(os.path.getctime(log))
			with open(log, 'r') as f:
				lines = f.readlines()
				logs_modify_time.append(time.mktime(datetime.datetime.strptime(self.get_start_end_time(lines, 1), '%Y-%m-%d %H:%M:%S').timetuple()))
				logs_create_time.append(time.mktime(datetime.datetime.strptime(self.get_start_end_time(lines, 0), '%Y-%m-%d %H:%M:%S').timetuple()))

		# 把日志修改时间、创建时间和日志路径放在一个元组里
		data = [(modify_time, log_name, create_time) for modify_time, log_name, create_time in zip(logs_modify_time, logs, logs_create_time)]
		data.sort(reverse=True)     # 对元组按照修改时间从大到小排序

		flag = 0
		startIndex = -1     # 监控结果开始索引
		startLogSort = 0    # 监控结果开始时间所在日志索引
		endIndex = -1       # 监控结果结束索引
		endLogSort = 0      # 监控结果结束时间所在日志索引

		if startTime and endTime:
			for d in data:
				if d[0] <= endTime:     # 如果修改时间小于结束时间
					if d[2] <= startTime:   # 如果创建时间小于开始时间
						if d[0] >= startTime:   # 如果修改时间大于开始时间，避免修改时间也小于开始时间
							# 监控结果开始时间和结束时间均在最新的日志中
							with open(d[1], 'r') as f:
								lines = f.readlines()

							startIndex = self.get_index(lines, 0, len(lines), startTime)     # 监控结果开始索引
							flag = 2    # 查找到监控结果开始的索引，结束循环
						else:
							raise Exception('ERROR: "startTime" is wrong. please input "startTime" again.')
					else:
						startLogSort += 1   # 监控结果开始时间所在日志索引加1
						continue

				else:    # 如果修改时间大于结束时间
					if flag != 1:       # 如果查找到监控结果结束的索引，不再查找监控结果结束索引
						if d[2] > endTime:      # 如果创建时间也大于结束时间，则监控结果开始时间和结束时间均不在最新的日志中
							endLogSort += 1     # 监控结果结束时间所在日志索引加1
							startLogSort += 1   # 监控结果开始时间所在日志索引加1
							continue
						else:                   # 如果创建时间小于结束时间，则监控结果结束时间在最新的日志中
							with open(d[1], 'r') as f:
								lines = f.readlines()

							endIndex = self.get_index(lines, 0, len(lines), endTime)     # 监控结果结束索引
							flag = 1    # 查找到监控结果结束的索引，不再查找监控结果结束索引

					if d[2] > startTime:    # 如果创建时间大于开始时间
						startLogSort += 1   # 监控结果开始时间所在日志索引加1
						continue
					else:       # 如果创建时间小于开始时间
						if d[0] >= startTime:   # 如果修改时间大于开始时间
							with open(d[1], 'r') as f:
								lines = f.readlines()

							startIndex = self.get_index(lines, 0, len(lines), startTime)
							flag = 2    # 查找到监控结果开始的索引，结束循环
						else:
							raise Exception('ERROR: "startTime" is wrong. please input "startTime" again.')

				if flag == 2:   # 如果找到结果，则结束循环
					break

			# 如果监控结果开始索引等于日志总数，且没有找到日志开始索引，则表明需要从所有日志中读取结果，设置startIndex为0
			if startLogSort == len(logs) and startIndex == -1:
				startLogSort -= 1
				startIndex = 0

			return {'startIndex': startIndex, 'startLogSort': startLogSort, 'endIndex': endIndex, 'endLogSort': endLogSort, 'logs': data}

		else:   # 如果没有按时间查找，则查找最后一次开始监控开始的日志
			for d in data:      # 遍历所有日志
				with open(d[1], 'r') as f:
					lines = f.readlines()

				total_lines = len(lines)
				for i in range(total_lines):
					if 'Start monitor' in lines[total_lines - i - 1]:   # 倒着查找最近一次开始监控的时间
						startIndex = total_lines - i - 1
						flag = 1
						break

				if flag == 1:
					break

				startLogSort += 1

			# 如果监控结果开始索引等于日志总数，且没有找到日志开始索引，则表明需要从所有日志中读取结果，设置startIndex为0
			if startLogSort == len(logs) and startIndex == -1:
				startLogSort -= 1
				startIndex = 0

			return {'startIndex': startIndex, 'startLogSort': startLogSort, 'endIndex': endIndex, 'endLogSort': endLogSort, 'logs': data}

	def get_start_end_time(self, lines, type):
		"""
			获取第一行时间和最后一行的时间，type=0表示从前往后，type=1表示从后往前。
		"""
		if type == 0:
			for i in range(len(lines)):
				res = self.recompile(lines[i])
				if res:
					return res.group()
				else:
					logger.warning(lines[i])
		if type == 1:
			total_lines = len(lines)
			for i in range(total_lines):
				res = self.recompile(lines[total_lines - i - 1])
				if res:
					return res.group()
				else:
					logger.warning(lines[i])

	def get_index(self, lines, start_index, end_index, search_time):
		"""
			在一个日志文件中，找到指定时间所在的位置，使用二分法查找
			lines: 日志文件的所有行
			start_index: 开始寻找的位置
			end_index: 结束寻找的位置
			search_time: 寻找的值，单位为 1970纪元后经过的浮点秒数
		"""
		# 防止输入错的时间，或有较长的监控空白，无法跳出循环
		if end_index - start_index < 2:
			return start_index

		# 获取中间值，二分法查找
		index = int((start_index + end_index) / 2)
		try:
			t = time.mktime(datetime.datetime.strptime(self.recompile(lines[index]).group(), '%Y-%m-%d %H:%M:%S').timetuple())
			if -1 <= search_time - t <= 1:
				return index
			else:
				return self.get_index(lines, start_index, index, search_time)

		except Exception as err:
			logger.warning(err)
			return self.get_index(lines, start_index+1, end_index, search_time)

	def get_values(self, results):
		"""
			返回包含监控结果的日志
		"""
		# 如果监控结果开始时间索引为-1，则数据有问题，抛出异常
		startIndex = results['startIndex']
		if startIndex == -1:
			raise Exception('ERROR: "startTime" is wrong. please input "startTime" again.')

		startLogSort = results['startLogSort']      # 监控结果开始时间所在日志索引
		endIndex = results['endIndex']              # 监控结果结束时间索引
		endLogSort = results['endLogSort']          # 监控结果开始时间所在日志索引
		logs = results['logs']                      # 日志路径，按修改时间从大到小排序

		log_list = list(range(startLogSort, endLogSort-1, -1))      # 包含监控结果的日志文件索引

		if len(log_list) == 1:      # 如果只有一个监控日志文件
			with open(logs[log_list[0]][1], 'r') as f:
				lines = f.readlines()

			if endIndex == -1:      # 从startIndex开始，到日志结束
				for j in range(startIndex, len(lines)):
					if 'cpu_and_mem' in lines[j]:
						self.deal_total_time(lines[j].strip())
						self.deal_cpu_and_mem(lines[j].strip())
					if 'CpuAndMem' in lines[j]:
						self.deal_total_time(lines[j].strip())
						self.system_cpu_mem(lines[j].strip())
					if 'disk_util' in lines[j]:
						self.deal_io_total_time(lines[j].strip())
						self.system_io(lines[j].strip())
					if 'r_w_util' in lines[j]:
						self.deal_io_total_time(lines[j].strip())
						self.deal_io(lines[j].strip())
			else:       # 从startIndex开始到endIndex
				for j in range(startIndex, endIndex):
					if 'cpu_and_mem' in lines[j]:
						self.deal_total_time(lines[j].strip())
						self.deal_cpu_and_mem(lines[j].strip())
					if 'CpuAndMem' in lines[j]:
						self.deal_total_time(lines[j].strip())
						self.system_cpu_mem(lines[j].strip())
					if 'disk_util' in lines[j]:
						self.deal_io_total_time(lines[j].strip())
						self.system_io(lines[j].strip())
					if 'r_w_util' in lines[j]:
						self.deal_io_total_time(lines[j].strip())
						self.deal_io(lines[j].strip())

		if len(log_list) == 2:      # 如果有两个监控日志文件
			with open(logs[log_list[0]][1], 'r') as f:
				lines = f.readlines()

			for j in range(startIndex, len(lines)):     # 第一个日志，从startIndex开始，到日志结束
				if 'cpu_and_mem' in lines[j]:
					self.deal_total_time(lines[j].strip())
					self.deal_cpu_and_mem(lines[j].strip())
				if 'CpuAndMem' in lines[j]:
					self.deal_total_time(lines[j].strip())
					self.system_cpu_mem(lines[j].strip())
				if 'disk_util' in lines[j]:
					self.deal_io_total_time(lines[j].strip())
					self.system_io(lines[j].strip())
				if 'r_w_util' in lines[j]:
					self.deal_io_total_time(lines[j].strip())
					self.deal_io(lines[j].strip())

			with open(logs[log_list[1]][1], 'r') as f:
				lines = f.readlines()

			if endIndex == -1:      # 遍历整个日志
				for j in range(len(lines)):
					if 'cpu_and_mem' in lines[j]:
						self.deal_total_time(lines[j].strip())
						self.deal_cpu_and_mem(lines[j].strip())
					if 'CpuAndMem' in lines[j]:
						self.deal_total_time(lines[j].strip())
						self.system_cpu_mem(lines[j].strip())
					if 'disk_util' in lines[j]:
						self.deal_io_total_time(lines[j].strip())
						self.system_io(lines[j].strip())
					if 'r_w_util' in lines[j]:
						self.deal_io_total_time(lines[j].strip())
						self.deal_io(lines[j].strip())
			else:
				for j in range(0, endIndex):    # 从日志第一行开始，直到endIndex
					if 'cpu_and_mem' in lines[j]:
						self.deal_total_time(lines[j].strip())
						self.deal_cpu_and_mem(lines[j].strip())
					if 'CpuAndMem' in lines[j]:
						self.deal_total_time(lines[j].strip())
						self.system_cpu_mem(lines[j].strip())
					if 'disk_util' in lines[j]:
						self.deal_io_total_time(lines[j].strip())
						self.system_io(lines[j].strip())
					if 'r_w_util' in lines[j]:
						self.deal_io_total_time(lines[j].strip())
						self.deal_io(lines[j].strip())

		if len(log_list) > 2:       # 如果有大于两个监控日志文件
			with open(logs[log_list[0]][1], 'r') as f:
				lines = f.readlines()

			for j in range(startIndex, len(lines)):     # 第一个日志，从startIndex开始，到日志结束
				if 'cpu_and_mem' in lines[j]:
					self.deal_total_time(lines[j].strip())
					self.deal_cpu_and_mem(lines[j].strip())
				if 'CpuAndMem' in lines[j]:
					self.deal_total_time(lines[j].strip())
					self.system_cpu_mem(lines[j].strip())
				if 'disk_util' in lines[j]:
					self.deal_io_total_time(lines[j].strip())
					self.system_io(lines[j].strip())
				if 'r_w_util' in lines[j]:
					self.deal_io_total_time(lines[j].strip())
					self.deal_io(lines[j].strip())

			for m in range(1, len(log_list)-1):         # 遍历中间所有日志
				with open(logs[log_list[m]][1], 'r') as f:
					lines = f.readlines()

				for j in range(len(lines)):
					if 'cpu_and_mem' in lines[j]:
						self.deal_total_time(lines[j].strip())
						self.deal_cpu_and_mem(lines[j].strip())
					if 'CpuAndMem' in lines[j]:
						self.deal_total_time(lines[j].strip())
						self.system_cpu_mem(lines[j].strip())
					if 'disk_util' in lines[j]:
						self.deal_io_total_time(lines[j].strip())
						self.system_io(lines[j].strip())
					if 'r_w_util' in lines[j]:
						self.deal_io_total_time(lines[j].strip())
						self.deal_io(lines[j].strip())

			with open(logs[log_list[-1]][1], 'r') as f:
				lines = f.readlines()

			if endIndex == -1:          # 遍历最后一个日志
				for j in range(len(lines)):
					if 'cpu_and_mem' in lines[j]:
						self.deal_total_time(lines[j].strip())
						self.deal_cpu_and_mem(lines[j].strip())
					if 'CpuAndMem' in lines[j]:
						self.deal_total_time(lines[j].strip())
						self.system_cpu_mem(lines[j].strip())
					if 'disk_util' in lines[j]:
						self.deal_io_total_time(lines[j].strip())
						self.system_io(lines[j].strip())
					if 'r_w_util' in lines[j]:
						self.deal_io_total_time(lines[j].strip())
						self.deal_io(lines[j].strip())
			else:
				for j in range(0, endIndex):        # 从日志第一行开始，直到endIndex
					if 'cpu_and_mem' in lines[j]:
						self.deal_total_time(lines[j].strip())
						self.deal_cpu_and_mem(lines[j].strip())
					if 'CpuAndMem' in lines[j]:
						self.deal_total_time(lines[j].strip())
						self.system_cpu_mem(lines[j].strip())
					if 'disk_util' in lines[j]:
						self.deal_io_total_time(lines[j].strip())
						self.system_io(lines[j].strip())
					if 'r_w_util' in lines[j]:
						self.deal_io_total_time(lines[j].strip())
						self.deal_io(lines[j].strip())

	def system_cpu_mem(self, line):
		"""
			从日志的每一行找出CPU、内存
		"""
		if self.is_monitor_system:
			if self.search == 'system':
				res = line.split(',')
				self.system[0].append(float(res[-2]))       # CPU
				self.system[1].append(float(res[-1]))       # 内存

	def system_io(self, line):
		"""
			从日志的每一行找出磁盘读、写、使用率
		"""
		if self.is_monitor_system:
			if self.search == 'system':
				res = line.split(',')
				self.disk_io[0].append(float(res[-3]))  # 磁盘读
				self.disk_io[1].append(float(res[-2]))  # 磁盘写
				self.disk_io[2].append(float(res[-1]))  # 磁盘总使用率

	def deal_cpu_and_mem(self, line):
		"""
			从日志的每一行找出CPU、内存、JVM数据
		"""
		if self.search in line:
			res = line.split(',')
			self.cpu_and_mem[0].append(float(res[-3]))  # CPU
			self.cpu_and_mem[1].append(float(res[-2]))  # 内存
			self.cpu_and_mem[2].append(float(res[-1]))  # JVM

	def deal_total_time(self, line):
		"""
			找到监控结果的时间
		"""
		if self.search in line:
			try:
				self.total_time.append(self.recompile(line).group())
			except Exception as err:
				logger.error(err)

	def deal_io_total_time(self, line):
		"""
			找到监控结果的时间
		"""
		if self.search in line:
			try:
				self.io_total_time.append(self.recompile(line).group())
			except Exception as err:
				logger.error(err)

	def deal_io(self, line):
		"""
			从日志的每一行找出IO数据
		"""
		if self.search in line:
			res = line.split(',')
			self.io[0].append(float(res[-6]))  # 进程读
			self.io[1].append(float(res[-5]))  # 进程写
			self.io[2].append(float(res[-4]))  # 进程磁盘使用率
			self.io[3].append(float(res[-3]))  # 磁盘读
			self.io[4].append(float(res[-2]))  # 磁盘写
			self.io[5].append(float(res[-1]))  # 磁盘总使用率

	def recompile(self, line):
		"""
		从一行日志中匹配出时间
		"""
		pattern = '(20\d{2}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'     # 正则表达式
		res = re.match(pattern, line)
		return res

	def read_data_from_logs(self, logs, startTime=None, endTime=None):
		results = self.get_logs(logs, startTime, endTime)
		self.get_values(results)
