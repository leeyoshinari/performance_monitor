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

from logger import logger, cfg, handle_exception
from process import Process
from Email import sendEmail
from request import Request
from draw_performance import draw_data_from_db


server = Process()
http = Request()


@handle_exception(is_return=True, default_value='127.0.0.1')
def get_ip():
    """
    Get server's IP address
    :return: IP
    """
    if cfg.getServer('host'):
        IP = cfg.getServer('host')
    else:
        result = os.popen("hostname -I |awk '{print $1}'").readlines()
        logger.debug(result)
        if result:
            IP = result[0].strip()
            logger.info(f'The IP address is {IP}')
        else:
            logger.warning('Server IP address not found!')
            IP = '127.0.0.1'

    return IP


async def index(request):
    """
    Home, Url: http://ip:port/context
    :param request:
    :return:
    """
    return aiohttp_jinja2.render_template('home.html', request, context={
        'ip': server.agents['ip'], 'port': server.agents['port'], 'system': server.agents['system'],
        'cpu': server.agents['cpu'], 'mem': server.agents['mem'], 'disk': server.agents['disk_size'],
        'net': server.agents['network_speed'], 'cpu_usage': server.agents['cpu_usage'],
        'mem_usage': list(map(lambda x: x * 100, server.agents['mem_usage'])),
        'disk_usage': list(map(lambda x: x * 100, server.agents['disk_usage'])), 'max_cpu': cfg.getMonitor('maxCPU'),
        'max_mem': cfg.getMonitor('maxMem'), 'max_disk': cfg.getMonitor('maxDisk'),
        'server_context': cfg.getServer('serverContext')
    })


async def start_monitor(request):
    """
    Start monitoring
    :param request:
    :return:
    """
    monitor_list = server.get_monitor()
    return aiohttp_jinja2.render_template('runMonitor.html', request, context={
        'ip': server.agents['ip'], 'foos': monitor_list, 'run_status': ['stopped', 'monitoring', 'queuing'],
        'server_context': cfg.getServer('serverContext')
    })


async def visualize(request):
    """
    Visualization
    :param request:
    :return:
    """
    starttime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()-600))
    endtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    if server.agents['ip']:
        monitor_list = server.get_monitor(host=server.agents['ip'][0])
    else:
        monitor_list = {'port': []}
    return aiohttp_jinja2.render_template('visualize.html', request, context={
        'disks': server.agents['disk'], 'ip': server.agents['ip'], 'port': monitor_list['port'], 'starttime': starttime,
        'endtime': endtime, 'row_name': ['75%', '90%', '95%', '99%'], 'server_context': cfg.getServer('serverContext')})


async def course_zh_CN(request):
    return aiohttp_jinja2.render_template('course_zh_CN.html', request,
                                          context={'server_context': cfg.getServer('serverContext')})


async def course_en(request):
    return aiohttp_jinja2.render_template('course_en.html', request,
                                          context={'server_context': cfg.getServer('serverContext')})


async def registers(request):
    """
    register
    :param request:
    :return:
    """
    data = json.loads(await request.text())
    logger.debug(f'The request parameters are {data}')
    server.agents = data
    return web.json_response({'code': 0, 'msg': 'registered successfully!', 'data': None})


async def run_monitor(request):
    """
    start/stop monitoring port.
    :param request:
    :return:
    """
    try:
        data = json.loads(await request.text())
        logger.debug(f'The request parameters are {data}')
        host = data.get('host')
        port = data.get('port')
        is_run = data.get('isRun')  # Whether to start monitoring，0-stop monitoring, 1-start monitoring
        post_data = {
            'host': host,
            'port': port,
            'isRun': is_run
        }
        ind = server.agents['ip'].index(host)
        res = http.request('post', host, server.agents['port'][ind], 'runMonitor', json=post_data)

        if res.status_code == 200:
            return web.Response(body=res.content.decode())
        else:
            return web.json_response({'code': 2, 'msg': f"System exception, the message comes from {host}", 'data': None})

    except Exception as err:
        logger.error(err)
        logger.error(traceback.format_exc())
        return web.json_response({'code': 2, 'msg': 'System exception!', 'data': None})


async def get_monitor(request):
    """
    Get the list of monitoring ports
    :param request:
    :return:
    """
    ip = request.match_info['host']
    monitor_list = {'host': [], 'port': [], 'pid': [], 'isRun': [], 'startTime': []}
    try:
        port = server.agents['port'][server.agents['ip'].index(ip)]
        post_data = {
            'host': ip,
        }
        res = http.request('post', ip, port, 'getMonitor', json=post_data)
        if res.status_code == 200:
            response = json.loads(res.content.decode())
            logger.debug(f'The return value of server {ip} of getting monitoring list is {response}')
            if response['code'] == 0:
                monitor_list['host'] += response['data']['host']
                monitor_list['port'] += response['data']['port']
                monitor_list['pid'] += response['data']['pid']
                monitor_list['isRun'] += response['data']['isRun']
                monitor_list['startTime'] += response['data']['startTime']

                return web.json_response({'code': 0, 'msg': 'Successful!', 'data': monitor_list})
            else:   # If an exception is returned, skip
                logger.warning(f'It returns an exception from server {ip} when getting monitoring list. '
                               f'Exception is {response["msg"]}')
                return web.json_response({'code': response['code'], 'msg': response["msg"], 'data': None})
        else:   # If an exception is returned, skip
            logger.warning(f'The monitoring list from server {ip} is abnormal, the response status code is {res.status_code}.')
            return web.json_response({'code': 2, 'msg': "System exception!", 'data': None})

    except Exception as err:
        logger.error(err)
        logger.error(traceback.format_exc())
        return web.json_response({'code': 2, 'msg': "System exception!", 'data': None})


async def plot_monitor(request):
    """
    Visualize
    :param request:
    :return:
    """
    data = json.loads(await request.text())
    logger.debug(f'The request parameters are {data}')
    host = data.get('host')
    start_time = data.get('startTime')
    end_time = data.get('endTime')
    type_ = data.get('type')
    port_pid = data.get('port')
    disk = data.get('disk')
    if host in server.agents['ip']:
        try:
            if type_ == 'port':
                res = draw_data_from_db(host=host, port=port_pid, startTime=start_time, endTime=end_time, disk=disk)
                if res['code'] == 0:
                    raise Exception(res['message'])
                res.update({'gc': server.get_gc(host, server.agents['port'][server.agents['ip'].index(host)],
                                                f'getGC/{port_pid}')})
                if res['gc'][0] == -1 and res['gc'][2] == -1:
                    res['flag'] = 0
                return web.json_response(res)

            '''if type_ == 'pid':
                res = draw_data_from_db(host=host, pid=port_pid, startTime=start_time, endTime=end_time, disk=disk)
                if res['code'] == 0:
                    raise Exception(res['message'])
                res.update({'gc': server.get_gc(host, server.agents['port'][server.agents['ip'].index(host)],
                                                f'getGC/{port_pid}')})
                if res['gc'][0] == -1 and res['gc'][2] == -1:
                    res['flag'] = 0
                return web.json_response(res)'''

            if type_ == 'system':
                res = draw_data_from_db(host=host, startTime=start_time, endTime=end_time, system=1, disk=disk)
                if res['code'] == 0:
                    raise Exception(res['message'])
                res['flag'] = 0
                return web.json_response(res)

        except Exception as err:
            logger.error(traceback.format_exc())
            return web.json_response({'code': 0, 'message': str(err)})
    else:
        logger.error(f'{host} agent may not register.')
        return web.json_response({'code': 0, 'message': f'{host} agent may not register.'})


async def get_port_disk(request):
    """
     Get all the disk numbers and all monitored ports of the client.
    :param request:
    :return:
    """
    host = request.match_info['host']
    if host in server.agents['ip']:
        try:
            disks = server.agents['disk'][server.agents['ip'].index(host)]
            monitor_list = server.get_monitor(host=host)
            return web.json_response({'code': 0, 'msg': 'Successful!', 'data': {'disk': disks, 'port': monitor_list['port']}})
        except Exception as err:
            logger.error(traceback.format_exc())
            return web.json_response({'code': 2, 'msg': "System Exception", 'data': err})
    else:
        return web.json_response({'code': 1, 'msg': f"{host} agent may not register.", 'data': None})


async def notice(request):
    """
     Send email.
    :param request:
    :return:
    """
    data = json.loads(await request.text())
    msg = data.get('msg')
    try:
        sendEmail(msg)
        return web.json_response({'code': 0, 'msg': 'Successful!', 'data': None})
    except Exception as err:
        logger.error(traceback.format_exc())
        return web.json_response({'code': 1, 'msg': err, 'data': None})


async def main():
    app = web.Application()
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))  # Add template to search path
    app.router.add_static(f'{cfg.getServer("serverContext")}/static/',
                          path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'),
                          append_version=True)  # Add static files to the search path

    app.router.add_route('GET', f'{cfg.getServer("serverContext")}', index)
    app.router.add_route('GET', f'{cfg.getServer("serverContext")}/home', index)
    app.router.add_route('GET', f'{cfg.getServer("serverContext")}/startMonitor', start_monitor)
    app.router.add_route('GET', f'{cfg.getServer("serverContext")}/getMonitor/{{host}}', get_monitor)
    app.router.add_route('GET', f'{cfg.getServer("serverContext")}/Visualize', visualize)
    app.router.add_route('GET', f'{cfg.getServer("serverContext")}/course_zh_CN', course_zh_CN)
    app.router.add_route('GET', f'{cfg.getServer("serverContext")}/course', course_en)
    app.router.add_route('GET', f'{cfg.getServer("serverContext")}/getPortAndDisk/{{host}}', get_port_disk)

    app.router.add_route('POST', f'{cfg.getServer("serverContext")}/Register', registers)
    app.router.add_route('POST', f'{cfg.getServer("serverContext")}/runMonitor', run_monitor)
    app.router.add_route('POST', f'{cfg.getServer("serverContext")}/plotMonitor', plot_monitor)
    app.router.add_route('POST', f'{cfg.getServer("serverContext")}/Notification', notice)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, get_ip(), cfg.getServer('port'))
    await site.start()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.run_forever()
