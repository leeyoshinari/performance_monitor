#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: leeyoshinari
import os
import time
import json
import asyncio
import traceback
import jinja2
import aiohttp_jinja2
from aiohttp import web

import config as cfg
from logger import logger
from master import Master
from request import Request
from extern import port_to_pid
from draw_performance import draw_data_from_log


master = Master()
http = Request()


async def index(request):
	return aiohttp_jinja2.render_template('home.html', request, context={'hosts': master.slaves})


async def start_monitor(request):
	return aiohttp_jinja2.render_template('runMonitor.html', request, context={'hosts': master.slaves})


async def visualize(request):
	starttime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()-3600))
	endtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
	return aiohttp_jinja2.render_template('visualize.html', request, context={
		'hosts': master.slaves, 'starttime': starttime, 'endtime': endtime})


async def registers(request):
	data = await request.json()
	host = data.get('host')
	port = data.get('port')
	master.slaves = f"{host}:{port}+{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}"
	return web.json_response({'code': 0, 'msg': '注册成功!', 'data': None})


async def run_monitor(request):
	try:
		data = await request.post()
		host = data.get('host')
		port = data.get('port')
		is_run = data.get('isRun')
		slaves = [s[0].split(':')[0] for s in master.slaves]
		if host in slaves:
			post_data = {
				'host': host,
				'port': port,
				'isRun': is_run
			}
			res = http.request('post', master.slaves[slaves.index(host)][0], 'runMonitor', json=post_data)

			if res.status_code == 200:
				return web.Response(body=res.content.decode())
			else:
				return web.json_response({
					'code': 2,
					'msg': f"系统异常，消息来自{host.split(':')[0]}",
					'data': None})

	except Exception as err:
		logger.error(err)
		return web.json_response({'code': 2, 'msg': '系统异常',	'data': None})


async def get_monitor(request):
	monitor_list = {'host': [], 'port': [], 'pid': [], 'isRun': [], 'startTime': []}
	hosts = master.slaves
	try:
		for host in hosts:
			ip = host[0].split(':')[0]
			post_data = {
				'host': ip,
			}
			res = http.request('post', host[0], 'getMonitor', json=post_data)
			if res.status_code == 200:
				response = json.loads(res.content.decode())
				if response['code'] == 0:
					monitor_list['host'] += response['data']['host']
					monitor_list['port'] += response['data']['port']
					monitor_list['pid'] += response['data']['pid']
					monitor_list['isRun'] += response['data']['isRun']
					monitor_list['startTime'] += response['data']['startTime']

				else:
					continue
					# return web.json_response({'code': 2, 'msg': f"系统异常，消息来自{ip}", 'data': None})
			else:
				continue
				# return web.json_response({'code': 2, 'msg': f"系统异常，消息来自{ip}", 'data': None})

		if monitor_list['host']:
			return web.json_response({'code': 1, 'msg': '暂未监控端口', 'data': None})

		return web.json_response({'code': 0, 'msg': '操作成功', 'data': monitor_list})

	except Exception as err:
		logger.error(err)
		return web.json_response({'code': 2, 'msg': "系统异常", 'data': None})


async def plot_monitor(request):
	data = await request.json()
	host = data.get('host')
	start_time = data.get('startTime')
	end_time = data.get('endTime')
	type_ = data.get('type')
	port_pid = data.get('num')
	try:
		if start_time is None:
			start_time = None

		if type_ == 'port':
			pid = port_to_pid(port_pid)

			if port_pid and pid:
				res = draw_data_from_log(host=host, port=f'port_{port_pid}', pid=f'pid_{pid}', start_time=start_time, end_time=end_time)
				return aiohttp_jinja2.render_template('figure.html', request, context={
					'data': res['data'], 'line75': res['line75'], 'line90': res['line90'], 'line95': res['line95'],
					'line99': res['line99'], 'ygc': res['ygc'], 'ygct': res['ygct'],
					'fgc': res['fgc'], 'fgct': res['fgct'], 'fygc': res['fygc'], 'ffgc': res['ffgc']})
			else:
				return aiohttp_jinja2.render_template('warn.html', request, context={'msg': '进程不存在！'})

		if type_ == 'pid':
			res = draw_data_from_log(pid=f'pid_{port_pid}', start_time=start_time, end_time=end_time)
			return aiohttp_jinja2.render_template('figure.html', request, context={
					'data': res['data'], 'line75': res['line75'], 'line90': res['line90'], 'line95': res['line95'],
					'line99': res['line99'], 'ygc': res['ygc'], 'ygct': res['ygct'],
					'fgc': res['fgc'], 'fgct': res['fgct'], 'fygc': res['fygc'], 'ffgc': res['ffgc']})

		# plot system
		if type_ == 'system':
			system = 1

			res = draw_data_from_log(start_time=start_time, end_time=end_time, system=system)
			return aiohttp_jinja2.render_template('figure.html', request, context={
						'data': res['data'], 'line75': res['line75'], 'line90': res['line90'], 'line95': res['line95'],
						'line99': res['line99'], 'ygc': res['ygc'], 'ygct': res['ygct'],
						'fgc': res['fgc'], 'fgct': res['fgct'], 'fygc': res['fygc'], 'ffgc': res['ffgc']})

	except Exception as err:
		logger.error(err)
		return aiohttp_jinja2.render_template('warn.html', request, context={'msg': traceback.format_exc()})


async def notice(request):
	data = await request.json()
	host = data.get('host')
	port = data.get('port')
	msg = data.get('msg')
	# sendmsg()
	return web.json_response({'code': 0, 'msg': '操作成功', 'data': None})


async def main():
	app = web.Application()
	aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))
	app.router.add_static('/static/', path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))

	app.router.add_route('GET', '/', index)
	app.router.add_route('GET', '/startMonitor', start_monitor)
	app.router.add_route('GET', '/getMonitor', get_monitor)
	app.router.add_route('GET', '/Visualize', visualize)

	app.router.add_route('POST', '/Register', registers)
	app.router.add_route('POST', '/runMonitor', run_monitor)
	app.router.add_route('POST', '/plotMonitor', plot_monitor)
	app.router.add_route('POST', '/Notification', notice)

	runner = web.AppRunner(app)
	await runner.setup()
	site = web.TCPSite(runner, cfg.IP, cfg.PORT)
	await site.start()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.run_forever()
