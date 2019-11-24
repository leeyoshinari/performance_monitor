#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: leeyoshinari

import json
import traceback
from flask import Flask, request, render_template
from flask_bootstrap import Bootstrap

import config as cfg
from logger import logger
from draw_performance import draw_data_from_log
from performance_monitor import PerMon
from extern import port_to_pid

server = Flask(__name__)
bootstrap = Bootstrap(server)

permon = PerMon()
permon.monitor()


@server.route('/', methods=['get'])
def get_home():
	return render_template('home.html')


@server.route('/startMonitor', methods=['get'])
def start_monitor():
	return render_template('runMonitor.html')


@server.route('/runMonitor', methods=['post'])
def run_monitor():
	try:
		is_run = int(request.form.get('isRun'))

		if request.form.get('type') and request.form.get('num'):
			if request.form.get('type') == 'port':
				port = request.form.get('num')
				pid = port_to_pid(port)
				if pid is None:
					return json.dumps({
						'code': 0, 'msg': f"The pid of {port} is not existed.", 'data': None}, ensure_ascii=False)

				if is_run == 0:
					if port in permon.stop['port']:
						permon.stop = {'port': port, 'pid': pid, 'is_run': 0}  # stop monitor
						return json.dumps({
							'code': 1, 'msg': 'Stop monitor successfully.',
							'data': {'port': port, 'pid': pid}}, ensure_ascii=False)
					else:
						return json.dumps({
							'code': 0, 'msg': f"Please monitor {port} firstly.",
							'data': {'port': port, 'pid': pid}}, ensure_ascii=False)

				if is_run == 1:
					permon.start = {'port': port, 'pid': pid, 'is_run': 1}  # start monitor
					return json.dumps({
						'code': 1, 'msg': 'Start monitor successfully.',
						'data': {'port': port, 'pid': pid}}, ensure_ascii=False)

			if request.form.get('type') == 'pid':
				return json.dumps({
					'code': 0, 'msg': 'This request is not supported', 'data': None}, ensure_ascii=False)

		else:
			return json.dumps({
				'code': 0, 'msg': 'This request is not supported', 'data': None}, ensure_ascii=False)

	except Exception as err:
		logger.error(err)
		raise Exception(traceback.format_exc())


@server.route('/getMonitor', methods=['get'])
def get_monitor():
	msg = permon.start
	msg.update({'threadpool': cfg.THREAD_NUM, 'currentthread': msg['isRun'].count(1)})

	return json.dumps(msg, ensure_ascii=False)


@server.route('/Visualize', methods=['get'])
def visualize():
	return render_template('visualize.html')


@server.route('/plotMonitor', methods=['post'])
def plot_monitor():
	start_time = None
	end_time = None
	system = None
	is_io = True
	print(request.form.get('type'), request.form.get('endTime'), request.form.get('num'))
	try:
		if request.form.get('startTime'):
			start_time = str(request.form.get('startTime'))

		if request.form.get('endTime'):
			end_time = str(request.form.get('endTime'))

		if request.form.get('showIO'):
			is_io = int(request.form.get('showIO'))

		if request.form.get('type') == 'port':
			port = request.form.get('num')
			pid = port_to_pid(port)

			if start_time is None:
				start_time = permon.stop['startTime'][permon.stop['port'].index(port)]

			if port and pid:
				res = draw_data_from_log(port=f'port_{port}', pid=f'pid_{pid}', start_time=start_time, end_time=end_time, is_io=is_io)
				return render_template('figure.html', data=res['data'], line75=res['line75'], line90=res['line90'],
				                       line95=res['line95'], line99=res['line99'], ygc=res['ygc'], ygct=res['ygct'],
				                       fgc=res['fgc'], fgct=res['fgct'], fygc=res['fygc'], ffgc=res['ffgc'])
			else:
				return render_template('warn.html', msg='The PID is not existed.')

		if request.form.get('type') == 'pid':
			pid = request.form.get('num')

			if start_time is None:
				start_time = permon.stop['startTime'][permon.stop['pid'].index(pid)]

			res = draw_data_from_log(pid=f'pid_{pid}', start_time=start_time, end_time=end_time, is_io=is_io)
			return render_template('figure.html', data=res['data'], line75=res['line75'], line90=res['line90'],
			                       line95=res['line95'], line99=res['line99'], ygc=res['ygc'], ygct=res['ygct'],
			                       fgc=res['fgc'], fgct=res['fgct'], fygc=res['fygc'], ffgc=res['ffgc'])

		# plot system
		if request.form.get('type') == 'system':
			system = 1

		res = draw_data_from_log(start_time=start_time, end_time=end_time, system=system)
		return render_template('figure.html', data=res['data'], line75=res['line75'], line90=res['line90'],
		                       line95=res['line95'], line99=res['line99'], ygc=res['ygc'], ygct=res['ygct'],
		                       fgc=res['fgc'], fgct=res['fgct'], fygc=res['fygc'], ffgc=res['ffgc'])

	except Exception as err:
		logger.error(err)
		return render_template('warn.html', msg=traceback.format_exc())


@server.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404


@server.errorhandler(500)
def internal_server_error(e):
	return render_template('500.html'), 500


server.run(port=cfg.PORT, debug=True, host=cfg.IP)  # start flask server
