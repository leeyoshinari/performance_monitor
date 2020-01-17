#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: leeyoshinari

import os
import asyncio
from aiohttp import web

import config as cfg
from logger import logger
from performance_monitor import PerMon
from extern import port_to_pid

permon = PerMon()
permon.monitor()


async def index(request):
	return web.Response(body=f'当前服务器CPU核数为{permon.cpu_cores}，总内存为{permon.total_mem * 100}G')


async def run_monitor(request):
	try:
		data = await request.json()
		host = data.get('host')
		port = data.get('port')
		is_run = data.get('isRun')

		if host == cfg.IP:
			if port:
				pid = port_to_pid(port)
				if pid is None:
					logger.warning(f"端口 {port} 未启动！")
					return web.json_response({
						'code': 1, 'msg': f"端口 {port} 未启动！", 'data': {'host': host, 'port': port, 'pid': None}})

				if is_run == '0':
					if port in permon.stop['port']:
						permon.stop = {'port': port, 'pid': pid, 'is_run': 0}  # stop monitor
						logger.info('停止监控成功！')
						return web.json_response({
							'code': 0, 'msg': '停止监控成功！', 'data': {'host': host, 'port': port, 'pid': pid}})
					else:
						logger.warning(f"端口 {port} 未监控，请先监控！")
						return web.json_response({
							'code': 1, 'msg': f"端口 {port} 未监控，请先监控！", 'data': {'host': host, 'port': port, 'pid': pid}})

				if is_run == '1':
					permon.start = {'port': port, 'pid': pid, 'is_run': 1}  # start monitor
					logger.info('开始监控成功！')
					return web.json_response({
						'code': 0, 'msg': '开始监控成功！', 'data': {'host': host, 'port': port, 'pid': pid}})

			else:
				logger.error('请求参数异常')
				return web.json_response({
					'code': 2, 'msg': '请求参数异常', 'data': {'host': host, 'port': port, 'pid': None}})
		else:
			logger.error('请求参数异常')
			return web.json_response({
				'code': 2, 'msg': '请求参数异常', 'data': {'host': host, 'port': port, 'pid': None}})

	except Exception as err:
		logger.error(err)
		return web.json_response({
			'code': 2, 'msg': err, 'data': {'host': cfg.IP, 'port': None, 'pid': None}})


async def get_monitor(request):
	data = await request.json()
	host = data.get('host')
	if host == cfg.IP:
		msg = permon.start
		if len(msg['port']) > 0:
			data = {'host': [host]*len(msg['port'])}
			data.update(msg)
			return web.json_response({'code': 0, 'msg': '操作成功', 'data': data})
		else:
			logger.error('暂未监控任何端口')
			return web.json_response({
				'code': 1, 'msg': '暂未监控任何端口', 'data': {'host': host, 'port': None, 'pid': None}})
	else:
		logger.error('请求参数异常')
		return web.json_response({
			'code': 2, 'msg': '请求参数异常', 'data': {'host': host, 'port': None, 'pid': None}})


async def get_gc(request):
	data = await request.json()
	types = data.get('type')
	port = data.get('port')
	host = data.get('host')
	if host == cfg.IP:
		if types == 'system':
			ygc, ygct, fgc, fgct, fygc, ffgc = -1, -1, -1, -1, -1, -1
		else:
			try:
				pid = port_to_pid(port)
				if pid is None:
					logger.warning(f"端口 {port} 未启动！")
					return web.json_response({
						'code': 1, 'msg': f"端口 {port} 未启动！", 'data': {'host': host, 'port': port, 'pid': None}})

				result = os.popen(f'jstat -gc {pid} |tr -s " "').readlines()[1]
				res = result.strip().split(' ')

				ygc = int(res[12])
				ygct = float(res[13])
				fgc = int(res[14])
				fgct = float(res[15])
				fygc = 0
				ffgc = 0

				result = os.popen(f'ps -p {pid} -o etimes').readlines()[1]
				runtime = int(result.strip())

				if ygc > 0:
					fygc = runtime / ygc
				if fgc > 0:
					ffgc = runtime / fgc

			except Exception as err:
				logger.error(err)
				ygc, ygct, fgc, fgct, fygc, ffgc = -1, -1, -1, -1, -1, -1

		return web.json_response({
			'code': 0, 'msg': '操作成功', 'data': {
				'ygc': ygc, 'ygct': ygct, 'fgc': fgc, 'fgct': fgct,
				'fygc': f'{fygc:.2f}', 'ffgc': f'{ffgc:.2f}'}})


async def check_status(request):
	return web.json_response({'code': 0})


async def main():
	app = web.Application()

	app.router.add_route('GET', '/', index)
	app.router.add_route('GET', '/checkStatus', check_status)
	app.router.add_route('POST', '/runMonitor', run_monitor)
	app.router.add_route('POST', '/getMonitor', get_monitor)
	app.router.add_route('POST', '/getGC', get_gc)

	runner = web.AppRunner(app)
	await runner.setup()
	site = web.TCPSite(runner, cfg.IP, cfg.PORT)
	await site.start()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.run_forever()
