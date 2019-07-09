#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import os
import time
import datetime
from logger import logger


def ports_to_pids(ports):
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
	Get PID by port. It uses `netstat`.
	"""
	pid = None
	try:
		result = os.popen('netstat -nlp|grep {} |tr -s " "'.format(port)).readlines()
		res = [line.strip() for line in result if str(port) in line]
		logger.logger.debug(res[0])
		p = res[0].split(' ')
		pp = p[3].split(':')[-1]
		if str(port) == pp:
			pid = p[-1].split('/')[0]
	except Exception as err:
		logger.logger.error(err)

	return pid


def get_logs(logs, startTime=None, endTime=None):
	logs_modify_time = []
	logs_create_time = []
	for log in logs:
		logs_modify_time.append(os.path.getmtime(log))
		logs_create_time.append(os.path.getctime(log))

	data = [(modify_time, log_name, create_time) for modify_time, log_name, create_time in zip(logs_modify_time, logs, logs_create_time)]
	data.sort(reverse=True)

	flag = 0
	startIndex = -1
	startLogSort = 0
	endIndex = -1
	endLogSort = 0

	if startTime and endTime:
		for d in data:
			if d[0] <= endTime:     # 如果修改时间小于结束时间
				if d[2] <= startTime:   # 如果创建时间小于开始时间
					if d[0] >= startTime:
						with open(d[1], 'r') as f:
							lines = f.readlines()

						startIndex = get_index(lines, 0, len(lines), startTime)
						flag = 2
					else:
						raise Exception('ERROR: "startTime" is wrong. please input "startTime" again.')
				else:
					startLogSort += 1
					continue

			else:    # 如果修改时间大于结束时间
				if flag != 1:
					if d[2] > endTime:     # 如果创建时间大于结束时间
						endLogSort += 1
						startLogSort += 1
						continue
					else:
						with open(d[1], 'r') as f:
							lines = f.readlines()

						endIndex = get_index(lines, 0, len(lines), endTime)
						flag = 1

				if d[2] > startTime:    # 如果创建时间大于开始时间
					startLogSort += 1
					continue
				else:
					if d[0] >= startTime:
						with open(d[1], 'r') as f:
							lines = f.readlines()

						startIndex = get_index(lines, 0, len(lines), startTime)
						flag = 2
					else:
						raise Exception('ERROR: "startTime" is wrong. please input "startTime" again.')

			if flag == 2:
				break

		return {'startIndex': startIndex, 'startLogSort': startLogSort, 'endIndex': endIndex, 'endLogSort': endLogSort, 'logs': data}

	else:   # 如果没有按时间查找，则查找最后一次开始监控开始的日志
		for d in data:
			with open(d[1], 'r') as f:
				lines = f.readlines()

			total_lines = len(lines)
			for i in range(total_lines):
				if 'Start monitor' in lines[total_lines - i - 1]:
					startIndex = total_lines - i - 1
					startLogSort += 1
					flag = 1
					break

			if flag == 1:
				break

		return {'startIndex': startIndex, 'startLogSort': startLogSort, 'endIndex': endIndex, 'endLogSort': endLogSort, 'logs': data}


def get_index(lines, start_index, end_index, search_time):
	index = int((start_index + end_index) / 2)
	try:
		t = time.mktime(datetime.datetime.strptime(lines[index][0:19], '%Y-%m-%d %H:%M:%S').timetuple())
		if search_time - t > 2:
			return get_index(lines, index, end_index, search_time)
		elif search_time - t < -2:
			return get_index(lines, start_index, index, search_time)
		else:
			return index
	except Exception as err:
		logger.logger.warning(err)
		return get_index(lines, start_index+1, end_index-1, search_time)


def get_values(results):
	startIndex = results['startIndex']
	if startIndex == -1:
		raise Exception('ERROR: "startTime" is wrong. please input "startTime" again.')

	startLogSort = results['startLogSort']
	endIndex = results['endIndex']
	endLogSort = results['endLogSort']
	logs = results['logs']

	cm_line = []
	io_line = []
	handle_line = []

	if endLogSort == -1:
		log_list = list(range(startLogSort, endLogSort, -1))
	else:
		log_list = list(range(startLogSort, endLogSort-1, -1))

	if len(log_list) == 1:
		with open(logs[log_list[0]][1], 'r') as f:
			lines = f.readlines()

		if endIndex == -1:
			for j in range(startIndex, len(lines)):
				if 'cpu_and_mem' in lines[j]:
					cm_line.append(lines[j].strip())
				if 'r_w_util' in lines[j]:
					io_line.append(lines[j].strip())
				if 'handles' in lines[j]:
					handle_line.append(lines[j].strip())
		else:
			for j in range(startIndex, endIndex):
				if 'cpu_and_mem' in lines[j]:
					cm_line.append(lines[j].strip())
				if 'r_w_util' in lines[j]:
					io_line.append(lines[j].strip())
				if 'handles' in lines[j]:
					handle_line.append(lines[j].strip())

	if len(log_list) == 2:
		with open(logs[log_list[0]][1], 'r') as f:
			lines = f.readlines()

		for j in range(startIndex, len(lines)):
			if 'cpu_and_mem' in lines[j]:
				cm_line.append(lines[j].strip())
			if 'r_w_util' in lines[j]:
				io_line.append(lines[j].strip())
			if 'handles' in lines[j]:
				handle_line.append(lines[j].strip())

		with open(logs[log_list[1]][1], 'r') as f:
			lines = f.readlines()

		if endIndex == -1:
			for j in range(len(lines)):
				if 'cpu_and_mem' in lines[j]:
					cm_line.append(lines[j].strip())
				if 'r_w_util' in lines[j]:
					io_line.append(lines[j].strip())
				if 'handles' in lines[j]:
					handle_line.append(lines[j].strip())
		else:
			for j in range(0, endIndex):
				if 'cpu_and_mem' in lines[j]:
					cm_line.append(lines[j].strip())
				if 'r_w_util' in lines[j]:
					io_line.append(lines[j].strip())
				if 'handles' in lines[j]:
					handle_line.append(lines[j].strip())

	if len(log_list) > 2:
		with open(logs[log_list[0]][1], 'r') as f:
			lines = f.readlines()

		for j in range(startIndex, len(lines)):
			if 'cpu_and_mem' in lines[j]:
				cm_line.append(lines[j].strip())
			if 'r_w_util' in lines[j]:
				io_line.append(lines[j].strip())
			if 'handles' in lines[j]:
				handle_line.append(lines[j].strip())

		for m in range(1, len(log_list)-1):
			with open(logs[log_list[m]][1], 'r') as f:
				lines = f.readlines()

			for n in range(len(lines)):
				if 'cpu_and_mem' in lines[n]:
					cm_line.append(lines[n].strip())
				if 'r_w_util' in lines[n]:
					io_line.append(lines[n].strip())
				if 'handles' in lines[n]:
					handle_line.append(lines[n].strip())

		with open(logs[log_list[-1]][1], 'r') as f:
			lines = f.readlines()

		if endIndex == -1:
			for j in range(len(lines)):
				if 'cpu_and_mem' in lines[j]:
					cm_line.append(lines[j].strip())
				if 'r_w_util' in lines[j]:
					io_line.append(lines[j].strip())
				if 'handles' in lines[j]:
					handle_line.append(lines[j].strip())
		else:
			for j in range(0, endIndex):
				if 'cpu_and_mem' in lines[j]:
					cm_line.append(lines[j].strip())
				if 'r_w_util' in lines[j]:
					io_line.append(lines[j].strip())
				if 'handles' in lines[j]:
					handle_line.append(lines[j].strip())

	return {'cpu_and_mem': cm_line, 'r_w_util': io_line, 'handles': handle_line}


def read_data_from_logs(logs, startTime=None, endTime=None):
	results = get_logs(logs, startTime, endTime)
	data = get_values(results)
	return data
