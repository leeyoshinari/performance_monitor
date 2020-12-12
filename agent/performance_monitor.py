#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import os
import re
import time
import json
import copy
import queue
import traceback
import threading
from concurrent.futures import ThreadPoolExecutor

import requests
import influxdb
from common import handle_exception, get_ip
from logger import logger, cfg


class PerMon(object):
    def __init__(self):
        self.check_sysstat_version()
        self.IP = get_ip()
        self.thread_pool = cfg.getServer('threadPool') if cfg.getServer('threadPool') >= 0 else 0
        self._msg = {'port': [], 'pid': [], 'isRun': [], 'startTime': []}   # 端口号、进程号、监控状态、开始监控时间
        self.is_system = cfg.getMonitor('isMonSystem')             # 是否监控服务器的资源
        self.error_duration = cfg.getMonitor('errorDuration')   # 执行命令失败次数
        self.sleepTime = cfg.getMonitor('sleepTime')
        self.maxCPU = cfg.getMonitor('maxCPU')
        self.CPUDuration = cfg.getMonitor('CPUDuration')
        self.isCPUAlert = cfg.getMonitor('isCPUAlert')
        self.minMem = cfg.getMonitor('minMem')
        self.isMemAlert = cfg.getMonitor('isMemAlert')
        self.frequencyFGC = cfg.getMonitor('frequencyFGC')
        self.isJvmAlert = cfg.getMonitor('isJvmAlert')
        self.echo = cfg.getMonitor('echo')
        self.isDiskAlert = cfg.getMonitor('isDiskAlert')
        self.maxDiskUsage = cfg.getMonitor('maxDiskUsage') / 100
        self.isTCP = cfg.getMonitor('isTCP')
        self.timeSetting = cfg.getMonitor('timeSetting')

        system_interval = cfg.getMonitor('system_interval')  # 每次执行监控命令的时间间隔
        port_interval = cfg.getMonitor('port_interval')  # 每次执行监控命令的时间间隔
        self.system_interval = max(system_interval, 1)   # 设置的值如果小于1，则默认为1
        self.port_interval = max(port_interval, 1)
        self.system_interval = self.system_interval - 1.1      # 程序运行、写库时间
        self.system_interval = max(self.system_interval, 0)
        self.port_interval = self.port_interval - 1.02       # 程序运行、写库时间
        self.port_interval = max(self.port_interval, 0)

        self.system_version = ''   # 系统版本
        self.cpu_info = ''
        self.cpu_cores = 0  # CPU核数
        self.total_mem = 0  # 总内存，单位G
        self.total_mem_100 = 0  # 总内存，单位100*G，主要用于求内存占比，减少运算量
        self.nic = ''   # 系统正在使用的网卡
        self.all_disk = []  # 磁盘号
        self.total_disk = 1  # 磁盘总大小，单位M
        self.total_disk_h = 0     # 磁盘总大小，以人可读的方式展示，单位T或G
        self.network_speed = cfg.getServer('nicSpeed')  # 服务器网卡带宽

        self.get_system_version()
        self.get_cpu_cores()
        self.get_total_mem()
        self.get_system_nic()
        self.get_disks()
        self.get_system_net_speed()
        self.get_total_disk_size()

        self.monitor_task = queue.Queue()   # 创建一个FIFO队列
        self.executor = ThreadPoolExecutor(self.thread_pool + 1)  # 创建线程池, +1是需要监控系统
        self.client = influxdb.InfluxDBClient(cfg.getInflux('host'), cfg.getInflux('port'), cfg.getInflux('username'),
                                              cfg.getInflux('password'), cfg.getInflux('database'))   # 创建数据库连接

        self.FGC = {}           # 每个端口的full gc次数
        self.FGC_time = {}      # 每个端口每次full gc的时间
        self.last_cpu_io = []   # 最近一段时间的cpu的值，约100s
        self.is_java = {}       # 监控的端口是否是java服务，0 or 1

        self.monitor()

    @property
    def start(self):
        return self._msg

    @start.setter
    def start(self, value):
        if value['port']:
            self.is_java_server(value['port'])  # 判断端口是否是java服务
            if value['port'] in self._msg['port']:  # 如果端口已经监控过，则更新相关数据
                index = self._msg['port'].index(value['port'])
                self._msg['pid'][index] = value['pid']
                if self._msg['isRun'][index] == 0:  # 如果已经停止监控，则更新监控状态和开始监控时间
                    self._msg['isRun'][index] = value['is_run']
                    self._msg['startTime'][index] = time.strftime('%Y-%m-%d %H:%M:%S')
                    self.monitor_task.put((self.write_cpu_mem, index))  # 把监控的端口任务放入队列中

                    self.FGC[str(value['port'])] = 0    # 重置 FGC次数
                    self.FGC_time[str(value['port'])] = []  # 重置 FGC 时间

                    if self.monitor_task.qsize() > 0:   # 如果队列不为空，则监控状态置为2，排队中
                        self._msg['isRun'][index] = 2
                else:
                    self._msg['isRun'][index] = value['is_run']
                    self._msg['startTime'][index] = time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                self._msg['pid'].append(value['pid'])   # 如果端口未监控过，则添加该端口相关数据
                self._msg['port'].append(value['port'])
                self._msg['isRun'].append(value['is_run'])
                self._msg['startTime'].append(time.strftime('%Y-%m-%d %H:%M:%S'))
                self.monitor_task.put((self.write_cpu_mem, len(self._msg['port'])-1))   # 把监控的端口任务放入队列中

                self.FGC.update({str(value['port']): 0})    # 初始化 FGC 次数
                self.FGC_time.update({str(value['port']): []})  # 初始化 FGC 时间

                if self.monitor_task.qsize() > 0:   # 如果队列不为空，则监控状态置为2，排队中
                    self._msg['isRun'][-1] = 2

        else:
            raise Exception('参数异常')

        # if len(self._msg['port']) > 0:  # 如果已经开始监控端口，则同时开始监控整个系统
        #     self.is_system = 1

    @property
    def stop(self):
        return self._msg

    @stop.setter
    def stop(self, value):
        index = self._msg['port'].index(value['port'])
        self._msg['isRun'][index] = value['is_run']

    def worker(self):
        """
        从队列中获取数据，并开始监控
        :return:
        """
        while True:
            func, param = self.monitor_task.get()
            func(param)
            self.monitor_task.task_done()

    def monitor(self):
        """
        开始监控
        :return:
        """
        for i in range(self.thread_pool + 1):
            self.executor.submit(self.worker)   # 启动线程池监控任务

        # self.monitor_task.put((self.register_and_clear_port, 1))    # 将注册和清理任务放入队列中
        self.monitor_task.put((self.write_system_cpu_mem_and_register_clear, 1))   # 将监控系统的任务放入队列中

    def write_cpu_mem(self, index):
        """
        监控端口的CPU使用率、占用内存大小和jvm变化（Java应用）、进程磁盘读写
        :param index: 监控端口的下标索引
        :return:
        """
        self._msg['startTime'][index] = time.strftime('%Y-%m-%d %H:%M:%S')      # 更新开始监控时间

        jvm = 0.0    # java服务的JVM内存数据初始化，主要用于非java服务的端口
        run_error_time = time.time()    # 初始化执行监控命令失败的时间
        port = self._msg['port'][index]
        pid = self._msg['pid'][index]
        is_run_jvm = self.is_java.get(str(port), 0)

        line = [{'measurement': self.IP,
                 'tags': {'type': str(port)},
                 'fields': {
                     'cpu': 0.0,
                     'wait_cpu': 0.0,
                     'mem': 0.0,
                     'jvm': 0.0,
                     'rKbs': 0.0,
                     'wKbs': 0.0,
                     'iodelay': 0.0,
                     'tcp': 0,
                     'close_wait': 0,
                     'time_wait': 0
                 }}]

        while True:
            if self._msg['isRun'][index] > 0:   # 开始监控
                self._msg['isRun'][index] = 1   # 重置端口监控状态为监控中
                try:
                    pid_info = self.get_pid_cpu_mem_io(pid)    # 获取CPU使用率和占用内存大小

                    if not pid_info:     # 如果CPU使用率未获取到，说明监控命令执行异常
                        logger.warning(f'获取cpu数据异常，异常pid为{pid}')
                        pid = port_to_pid(port)  # 根据端口号查询进程号
                        if pid:     # 如果进程号存在，则更新进程号
                            self._msg['pid'][index] = pid
                            self._msg['startTime'][index] = time.strftime('%Y-%m-%d %H:%M:%S')

                        # 如果连续执行监控命令都失败，则停止监控
                        if time.time() - run_error_time > self.error_duration:
                            self._msg['isRun'][index] = 0
                            logger.error(f'{port}端口连续{self.error_duration}s执行监控命令都失败，已停止监控')
                            break

                        time.sleep(self.sleepTime)
                        continue

                    line[0]['fields']['cpu'] = pid_info['cpu']
                    line[0]['fields']['wait_cpu'] = pid_info['wait_cpu']
                    line[0]['fields']['mem'] = pid_info['mem']
                    line[0]['fields']['rKbs'] = pid_info['kB_rd']
                    line[0]['fields']['wKbs'] = pid_info['kB_wr']
                    line[0]['fields']['iodelay'] = pid_info['iodelay']

                    tcp_num = self.get_port_tcp(port)
                    line[0]['fields']['tcp'] = tcp_num.get('tcp', 0)
                    line[0]['fields']['close_wait'] = tcp_num.get('close_wait', 0)
                    line[0]['fields']['time_wait'] = tcp_num.get('time_wait', 0)

                    if is_run_jvm:
                        jvm = self.get_jvm(port, pid)     # 获取JVM内存
                        line[0]['fields']['jvm'] = jvm

                    self.client.write_points(line)    # 写数据到数据库
                    logger.info(f'cpu_and_mem: port_{port},pid_{pid},{pid_info},{jvm}')
                    run_error_time = time.time()    # 如果监控命令执行成功，则重置

                except:
                    logger.error(traceback.format_exc())
                    time.sleep(self.sleepTime)

                time.sleep(self.port_interval)

            if self._msg['isRun'][index] == 0:   # 如果监控状态为0， 则停止监控
                logger.info(f'{port}端口已经停止监控')
                self.FGC[str(port)] = 0
                self._msg['isRun'][index] = 0
                break

    def write_system_cpu_mem_and_register_clear(self, is_system):
        """
        监控系统CPU使用率、剩余内存和磁盘IO
        定时任务，总共有两个，一个是向服务端注册本机，一个是清理已经停止监控的过期端口
        :param is_system: 未使用
        :return:
        """
        cpu_flag = True     # 控制CPU过高时是否邮件通知标志
        mem_flag = True     # 控制内存过低时是否邮件通知标志
        echo = True     # 控制是否清理缓存标志
        disk_flag = True    # 控制磁盘空间使用率过高时是否邮件通知标志

        line = [{'measurement': self.IP,
                 'tags': {'type': 'system'},
                 'fields': {
                     'cpu': 0.0,
                     'iowait': 0.0,
                     'mem': 0.0,
                     'mem_available': 0.0,
                     'rec': 0.0,
                     'trans': 0.0,
                     'net': 0.0,
                     'tcp': 0,
                     'retrans': 0.0
                 }}]
        for disk in self.all_disk:
            # 系统磁盘号目前发现2种格式，分别是'sda'和'sda-1'，因为influxdb查询时，无法识别'-'，故replace。其他格式的待验证
            disk_n = disk.replace('-', '')
            line[0]['fields'].update({disk_n: 0.0})
            line[0]['fields'].update({disk_n + '_r': 0.0})
            line[0]['fields'].update({disk_n + '_w': 0.0})
            line[0]['fields'].update({disk_n + '_d': 0.0})

        disk_usage = self.get_used_disk_rate()
        # 注册本机参数
        url = f'http://{cfg.getMaster("host")}:{cfg.getMaster("port")}/Register'
        header = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/json; charset=UTF-8"}
        post_data = {
            'host': self.IP,
            'port': cfg.getServer('port'),
            'system': self.system_version,
            'cpu': self.cpu_cores,
            'cpu_usage': 0.0,
            'nic': self.nic,
            'network_speed': self.network_speed,
            'mem': round(self.total_mem, 2),
            'mem_usage': 0.0,
            'disk_size': self.total_disk_h,
            'disk_usage': disk_usage,
            'disks': ','.join(self.all_disk)
        }
        start_time = time.time()
        disk_start_time = time.time()

        while True:
            if time.time() - start_time > 5:    # 每隔5秒注册本机
                try:
                    res = requests.post(url=url, json=post_data, headers=header)
                    logger.info(f"客户端注册结果：{res.content.decode('unicode_escape')}")
                    start_time = time.time()
                    if time.strftime('%H:%M') == self.timeSetting:  # 每天定时清理一次过期的端口
                        logger.debug('正常清理停止监控的端口')
                        self.clear_port()
                except:
                    logger.error(traceback.format_exc())

            if time.time() - disk_start_time > 300:     # 每隔5分钟获取一次磁盘使用情况
                disk_usage = self.get_used_disk_rate()
                if disk_usage:
                    post_data['disk_usage'] = disk_usage    # 磁盘使用率，不带%号
                    disk_start_time = time.time()

                    if self.maxDiskUsage < disk_usage:
                        msg = f"{self.IP} 当前系统磁盘空间使用率为{disk_usage/100:.2f}%，请注意磁盘空间"
                        logger.warning(msg)
                        if self.isDiskAlert and disk_flag:
                            disk_flag = False  # 标志符置为False，防止连续不断的发送邮件
                            thread = threading.Thread(target=notification, args=(msg,))  # 开启线程发送邮件通知
                            thread.start()
                    else:
                        disk_flag = True

            if self.is_system:     # 开始监控
                try:
                    res = self.get_system_cpu_io_speed()   # 获取系统CPU、内存和磁盘IO、带宽

                    if res['disk'] and res['cpu'] is not None and res['mem'] is not None:
                        for k, v in res['disk'].items():
                            line[0]['fields'][k] = min(v, 100.0)     # 写磁盘IO数据到数据库

                        for k, v in res['disk_r'].items():
                            line[0]['fields'][k] = v

                        for k, v in res['disk_w'].items():
                            line[0]['fields'][k] = v

                        for k, v in res['disk_d'].items():
                            line[0]['fields'][k] = v

                        line[0]['fields']['cpu'] = res['cpu']
                        line[0]['fields']['iowait'] = res['iowait']
                        line[0]['fields']['mem'] = res['mem']
                        line[0]['fields']['mem_available'] = res['mem_available']
                        line[0]['fields']['rec'] = res['rece']
                        line[0]['fields']['trans'] = res['trans']
                        line[0]['fields']['net'] = res['network']
                        line[0]['fields']['tcp'] = res['tcp']
                        line[0]['fields']['retrans'] = res['retrans']
                        self.client.write_points(line)    # 写cpu和内存到数据库
                        logger.info(f"system: CpuAndMem,{res['cpu']},{res['mem']},{res['disk']},{res['disk_r']},{res['disk_w']},"
                                    f"{res['rece']},{res['trans']},{res['network']}, {res['tcp']}, {res['retrans']}")

                        if len(self.last_cpu_io) > self.CPUDuration:
                            self.last_cpu_io.pop(0)

                        self.last_cpu_io.append(res['cpu'])
                        cpu_usage = sum(self.last_cpu_io) / len(self.last_cpu_io)
                        post_data['cpu_usage'] = cpu_usage      # CPU使用率，带%号
                        post_data['mem_usage'] = 1 - res['mem'] / self.total_mem    # 内存使用率，不带%号

                        if cpu_usage > self.maxCPU:
                            msg = f'{self.IP} 当前CPU平均使用率为{cpu_usage}%，CPU使用率过高'
                            logger.warning(msg)
                            if self.isCPUAlert and cpu_flag:
                                cpu_flag = False    # 标志符置为False，防止连续不断的发送邮件
                                thread = threading.Thread(target=notification, args=(msg,))     # 开启线程发送邮件通知
                                thread.start()
                        else:
                            cpu_flag = True     # 如果CPU正常，标识符重置为True

                        if res['mem'] <= self.minMem:
                            msg = f"{self.IP} 当前系统剩余内存为{res['mem']}G，内存过低"
                            logger.warning(msg)
                            if self.isMemAlert and mem_flag:
                                mem_flag = False    # 标志符置为False，防止连续不断的发送邮件
                                thread = threading.Thread(target=notification, args=(msg, ))     # 开启线程发送邮件通知
                                thread.start()

                            if self.echo and echo:
                                echo = False    # 标志符置为False，防止连续不断的清理缓存
                                thread = threading.Thread(target=self.clear_cache, args=())     # 开启线程清理缓存
                                thread.start()

                        else:
                            # 如果内存正常，标识符重置为True
                            mem_flag = True
                            echo = True

                except:
                    logger.error(traceback.format_exc())

                time.sleep(self.system_interval)
            else:
                time.sleep(3)

    @handle_exception(is_return=True, default_value=(None, None))
    def get_cpu_mem(self, pid):
        """
        获取进程的CPU使用率和内存使用大小
        :param pid: 进程号
        :return: CPU使用率（%）和内存占用大小（G）
        """
        cpu = None
        mem = None

        # result = os.popen(f'top -n 1 -b -p {pid} |tr -s " "').readlines()
        result = os.popen(f'top -n 1 -b |grep -P {pid} |tr -s " "').readlines()     # 执行命令
        res = [ress.strip().split(' ') for ress in result]
        logger.debug(f'查询进程{pid}的CPU使用率和内存结果为：{res}')

        for r in res:
            if str(pid) == r[0]:
                ind = r.index(str(pid))
                cpu = float(r[ind + 8]) / self.cpu_cores      # CPU使用率
                mem = float(r[ind + 9]) * self.total_mem_100      # 内存占用大小

        return cpu, mem

    @handle_exception(is_return=True, default_value=[])
    def get_pid_cpu_mem_io(self, pid):
        """
            获取进程的CPU使用率和内存使用大小
            :param pid: 进程号
            :return: CPU使用率（%）、内存占用大小（G）、磁盘读写（kB/s）
        """
        pid_info = {'kB_rd': 0.0, 'kB_wr': 0.0, 'iodelay': 0.0, 'VSZ': 0.0, 'RSS': 0.0, 'mem': 0.0, 'usr_cpu': 0.0,
                    'system_cpu': 0.0, 'guest_cpu': 0.0, 'wait_cpu': 0.0, 'cpu': 0.0}

        res = os.popen(f'pidstat -u -r -d -p {pid} 1 1 |tr -s " "').readlines()[::-1][:9]

        if res:
            for i in range(len(res)):
                if 'iodelay' in res[i]:
                    io = res[i - 1].split(' ')
                    pid_info['kB_rd'] = float(io[3]) / 1024    # 每秒从磁盘读取的MB
                    pid_info['kB_wr'] = float(io[4]) / 1024   # 每秒写入磁盘MB
                    pid_info['iodelay'] = float(io[6])  # I/O 的延迟（单位是时钟周期）
                if 'MEM' in res[i]:
                    memory = res[i - 1].split(' ')
                    pid_info['VSZ'] = float(memory[5]) / 1024   # 虚拟内存
                    pid_info['RSS'] = float(memory[6]) / 1024   # 物理内存
                    pid_info['mem'] = float(memory[7])          # 物理内存使用率
                if 'CPU' in res[i]:
                    cpu_res = res[i - 1].split(' ')
                    pid_info['usr_cpu'] = float(cpu_res[3])         # 用户空间的cpu使用率
                    pid_info['system_cpu'] = float(cpu_res[4])      # 内核空间的cpu使用率
                    pid_info['guest_cpu'] = float(cpu_res[5])       # 进程在虚拟机占用cpu使用率
                    pid_info['wait_cpu'] = float(cpu_res[6])        # 等待上下文切换的cpu使用率
                    pid_info['cpu'] = float(cpu_res[7])         # 总的cpu使用率

            return pid_info
        else:
            return res

    @handle_exception(is_return=True, default_value=0)
    def get_jvm(self, port, pid):
        """
        获取JVM内存
        :param port: 端口号
        :param pid: 进程号
        :return: jvm内存大小（G）
        """
        result = os.popen(f'jstat -gc {pid} |tr -s " "').readlines()[1]     # 执行命令
        res = result.strip().split(' ')
        logger.debug(f'查询进程{pid}的JVM结果为：{res}')
        mem = float(res[2]) + float(res[3]) + float(res[5]) + float(res[7])     # 计算jvm

        # 当FGC频率过高时，发送邮件提醒
        fgc = int(res[14])
        if self.FGC[str(port)] < fgc:  # 如果FGC次数增加
            self.FGC[str(port)] = fgc
            self.FGC_time[str(port)].append(time.time())
            if len(self.FGC_time[str(port)]) > 2:   # 计算FGC频率
                frequency = self.FGC_time[str(port)][-1] - self.FGC_time[str(port)][-2]
                if frequency < self.frequencyFGC:    # 如果FGC频率大于设置值，则发送邮件提醒
                    msg = f'{self.IP}服务器上的{port}端口的Full GC频率为{frequency}.'
                    logger.warning(msg)
                    if self.isJvmAlert:
                        thread = threading.Thread(target=notification, args=(msg, ))
                        thread.start()

            # 将FGC次数和时间写到日志
            logger.warning(f"端口{port}第{self.FGC[str(port)]}次Full GC.")

        elif self.FGC[str(port)] > fgc:   # 如果FGC次数减小，说明可能重启，则重置
            self.FGC[str(port)] = 0

        if self.FGC[str(port)] == 0:    # 如果FGC次数为0，则重置
            self.FGC_time[str(port)] = []

        return mem / 1024 / 1024

    @handle_exception(is_return=True, default_value={})
    def get_system_cpu_io_speed(self):
        """
        获取系统CPU使用率、剩余内存和磁盘IO、网速和网络使用率
        网速的获取，必须得间隔一段时间；磁盘IO的获取也得间隔一段时间
        执行磁盘IO命令一般间隔1秒，故在执行磁盘IO命令前后执行网速命令，此时正好间隔约1秒
        :return: 磁盘IO，cpu使用率（%），剩余内存（G），网络上行和下行速率，单位 Mb/s
        """
        disk = {}
        disk_r = {}
        disk_w = {}
        disk_d = {}
        cpu = None
        iowait = None
        mem = None
        mem_available = None
        bps1 = None
        bps2 = None
        rece = None
        trans = None
        network = None
        if self.nic:
            bps1 = os.popen(f'cat /proc/net/dev |grep {self.nic} |tr -s " "').readlines()
            logger.debug(f'第一次获取网速的结果：{bps1}')

        result = os.popen(f'iostat -x -m 1 2 |tr -s " "').readlines()    # 执行命令
        logger.debug(f'获取磁盘IO结果：{result}')

        if self.nic:
            bps2 = os.popen(f'cat /proc/net/dev |grep {self.nic} |tr -s " "').readlines()
            logger.debug(f'第二次获取网速的结果：{bps2}')

        result.pop(0)
        disk_res = [l.strip() for l in result if len(l) > 5]
        disk_res = disk_res[int(len(disk_res)/2)-1:]

        for i in range(len(disk_res)):
            if 'avg-cpu' in disk_res[i]:
                cpu_res = disk_res[i+1].strip().split(' ')      # CPU空闲率
                if len(cpu_res) > 3:
                    cpu = 100 - float(cpu_res[-1])      # CPU使用率
                    iowait = float(cpu_res[-3])
                    logger.debug(f'系统CPU使用率为：{cpu}%')
                    continue

            if 'Device' in disk_res[i]:
                for j in range(i+1, len(disk_res)):     # 遍历所有磁盘
                    disk_line = disk_res[j].strip().split(' ')
                    disk_num = disk_line[0].replace('-', '')    # replace的原因是因为influxdb查询时，无法识别'-'
                    disk.update({disk_num: float(disk_line[-1])})      # 磁盘的IO
                    disk_r.update({disk_num + '_r': float(disk_line[2])})     # 磁盘读 Mb/s
                    disk_w.update({disk_num + '_w': float(disk_line[8])})     # 磁盘写 Mb/s
                    disk_d.update({disk_num + '_d': float(disk_line[14])})     # 磁盘丢 Mb/s

                logger.debug(f'当前获取的磁盘数据：IO: {disk}, Read: {disk_r}, Write: {disk_w}')

                break

        result = os.popen('cat /proc/meminfo |grep -E "MemAvailable|MemFree"|tr -s " "').readlines()   # 执行命令，获取系统剩余内存
        logger.debug(f'系统剩余内存为：{result}')
        for res in result:
            if 'MemFree' in res:
                mem = float(res.split(':')[-1].split('k')[0].strip()) / 1024 / 1024
            if 'MemAvailable' in res:
                mem_available = float(res.split(':')[-1].split('k')[0].strip()) / 1024 / 1024

        if bps1 and bps2:
            data1 = bps1[0].split(':')[1].strip().split(' ')
            data2 = bps2[0].split(':')[1].strip().split(' ')
            rece = (int(data2[0]) - int(data1[0])) / 1024 / 1024
            trans = (int(data2[8]) - int(data1[8])) / 1024 / 1024
            # 如果没有获取到网口带宽数据，默认为配置文件中的值；
            # 800 = 8 * 100，为什么要乘以8，因为网口带宽除以8即为网口支持的最大速率
            network = 800 * (rece + trans) / self.network_speed
            logger.debug(f'系统网络带宽：收{rece}Mb/s，发{trans}Mb/s，带宽占比{network}%')

        tcp, Retrans_ratio = self.get_tcp()

        return {'disk': disk, 'disk_r': disk_r, 'disk_w': disk_w, 'disk_d': disk_d, 'cpu': cpu, 'iowait': iowait,
                'mem': mem, 'mem_available': mem_available, 'rece': rece, 'trans': trans, 'network': network,
                'tcp': tcp, 'retrans': Retrans_ratio}

    '''def get_handle(pid):
        """
        获取进程占用的句柄数
        :param pid: 进程号
        :return: 句柄数
        """
        result = os.popen("lsof -n | awk '{print $2}'| sort | uniq -c | sort -nr | " + "grep {}".format(pid)).readlines()
        res = result[0].strip().split(' ')
        logger.debug(res)
        handles = None
        if str(pid) in res:
            handles = int(res[0])

        return handles'''

    @handle_exception(is_return=True, default_value=(0, 0.0))
    def get_tcp(self):
        """
        获取TCP数量，计算重传率
        :return:
        """
        tcp = 0
        Retrans_ratio = 0.0
        if self.isTCP:
            result = os.popen('cat /proc/net/snmp |grep Tcp |tr -s " "').readlines()
            tcps = result[-1].strip().split(' ')
            logger.debug(f'获取TCP数据为{tcps}')
            tcp = int(tcps[9])      # 当前服务器TCP连接数
            Retrans_ratio = (int(tcps[-4]) / int(tcps[-5])) * 100     # TCP重传率

        return tcp, Retrans_ratio

    @handle_exception(is_return=True, default_value={})
    def get_port_tcp(self, port):
        """
        获取端口的连接数
        :param port: 端口号
        :return:
        """
        tcp_num = {}
        res = os.popen(f'netstat -ant |grep {port} |tr -s " "').read()
        tcp_num.update({'tcp': res.count('tcp')})
        tcp_num.update({'established': res.count('ESTABLISHED')})
        tcp_num.update({'close_wait': res.count('CLOSE_WAIT')})
        tcp_num.update({'time_wait': res.count('TIME_WAIT')})
        return tcp_num

    def get_cpu_cores(self):
        """
        获取系统CPU信息
        :return:
        """
        cpu_model = ''
        cpu_num = 0
        cpu_core = 0
        try:
            result = os.popen('cat /proc/cpuinfo | grep "model name" |uniq').readlines()[0]
            cpu_model = result.strip().split(':')[1].strip()
            logger.info(f'当前系统CPU型号为{cpu_model}')
        except Exception as err:
            logger.error('CPU型号未获取到')
            logger.error(err)

        try:
            result = os.popen('cat /proc/cpuinfo | grep "physical id" | uniq | wc -l').readlines()[0]
            cpu_num = int(result)
            logger.info(f'当前系统CPU个数为{cpu_num}')
        except Exception as err:
            logger.error('CPU型号未获取到')
            logger.error(err)

        try:
            result = os.popen('cat /proc/cpuinfo | grep "cpu cores" | uniq').readlines()[0]
            cpu_core = int(result.strip().split(':')[1].strip())
            logger.info(f'当前系统每个CPU的核数为{cpu_core}')
        except Exception as err:
            logger.error('每个CPU的核数未获取到')
            logger.error(err)

        result = os.popen('cat /proc/cpuinfo| grep "processor"| wc -l').readlines()[0]
        self.cpu_cores = int(result)
        logger.info(f'当前系统CPU核数为{self.cpu_cores}')

        if cpu_model and cpu_num and cpu_core:
            self.cpu_info = f'{cpu_num}个{cpu_core}核CPU，共有{self.cpu_cores}核，CPU型号为{cpu_model}'
        else:
            self.cpu_info = f'CPU核数为{self.cpu_cores}'

    @handle_exception(is_return=True)
    def get_total_mem(self):
        """
        获取系统总内存
        :return:
        """
        result = os.popen('cat /proc/meminfo| grep "MemTotal"| uniq').readlines()[0]
        self.total_mem = float(result.split(':')[-1].split('k')[0].strip()) / 1024 / 1024
        self.total_mem_100 = self.total_mem / 100
        logger.info(f'当前系统总内存为{self.total_mem}G')

    @handle_exception()
    def get_disks(self):
        """
        获取系统所有磁盘号
        :return:
        """
        result = os.popen(f'iostat -x -k |tr -s " "').readlines()
        if result:
            disk_res = [l.strip() for l in result if len(l) > 5]
            for i in range(len(disk_res)):
                if 'Device' in disk_res[i]:
                    for j in range(i + 1, len(disk_res)):
                        disk_line = disk_res[j].strip().split(' ')
                        self.all_disk.append(disk_line[0])

            logger.info(f'当前系统共有{len(self.all_disk)}个磁盘，磁盘号分别为{"、".join(self.all_disk)}')
        else:
            raise Exception('服务器不支持iostat命令，请安装。')

    @handle_exception(is_return=True)
    def get_system_nic(self):
        """
        获取系统使用的网卡。
        只能获取一个网卡，如果系统使用多个网卡，只能获取第一个，网卡排序使用 cat /proc/net/dev 查看
        :return:
        """
        network_card = []
        result = os.popen('cat /proc/net/dev |tr -s " "').readlines()   # 获取网卡
        logger.debug(f'查询网卡时，第一次执行命令结果：{result}')
        time.sleep(1)
        result1 = os.popen('cat /proc/net/dev |tr -s " "').readlines()  # 一秒后再次获取网卡
        logger.debug(f'查询网卡时，第二次执行命令结果：{result1}')
        for i in range(len(result)):
            if ':' in result[i]:
                title = result[i].strip().split(':')[0]
                data = result[i].strip().split(':')[1]
                title1 = result1[i].strip().split(':')[0]
                data1 = result1[i].strip().split(':')[1]
                if title == title1:
                    logger.debug(f'第一次数据有变化的网卡数据：{data}')
                    logger.debug(f'第二次数据有变化的网卡数据：{data1}')
                    rec = data.strip().split(' ')[0]
                    rec1 = data1.strip().split(' ')[0]
                    if rec != rec1:     # 如果这个网卡数据有变化，则说明此卡在使用
                        network_card.append(title)

        logger.debug(f'当前获得网卡数据：{network_card}')
        if 'lo' in network_card:    # 'lo'卡是本地127.0.0.1，需要去掉
            network_card.pop(network_card.index('lo'))

        if len(network_card) > 0:  # 获取第一个卡
            self.nic = network_card[0]
            logger.info(f'当前服务器使用的网卡为{self.nic}')
        else:
            logger.error('当前服务器网卡未找到')

    @handle_exception(is_return=True)
    def get_total_disk_size(self):
        """
        获取磁盘总大小
        :return:
        """
        result = os.popen('df -m |tr -s " "').readlines()
        logger.debug(f'查询磁盘执行命令结果：{result}')
        for line in result:
            res = line.strip().split(' ')
            if '/dev/' in res[0]:
                size = float(res[1])
                self.total_disk += size
        logger.debug(f'当前磁盘大小为：{self.total_disk}M')

        self.total_disk_h = self.total_disk / 1024
        if self.total_disk_h > 1024:
            total = round(self.total_disk_h / 1024, 2)
            self.total_disk_h = f'{total}T'
        else:
            total = round(self.total_disk_h, 2)
            self.total_disk_h = f'{total}G'

        logger.info(f'当前服务器磁盘总大小为{self.total_disk_h}')

    @handle_exception(is_return=True, default_value=0)
    def get_used_disk_rate(self):
        """
        获取磁盘使用的大小
        :return:
        """
        used_disk_size = 0
        result = os.popen('df -m |tr -s " "').readlines()
        logger.debug(f'查询磁盘执行命令结果：{result}')
        for line in result:
            res = line.strip().split(' ')
            if '/dev/' in res[0]:
                size = float(res[2])
                used_disk_size += size
        logger.info(f'当前磁盘已使用{used_disk_size}M')
        return used_disk_size / self.total_disk

    @handle_exception(is_return=True)
    def get_system_net_speed(self):
        """
        获取系统的带宽，单位是 Mbs
        :return:
        """
        if self.nic:
            result = os.popen(f'ethtool {self.nic}').readlines()
            logger.debug(f'查询网络带宽执行命令结果：{result}')
            for line in result:
                if 'Speed' in line:
                    logger.debug(f'当前网络带宽为：{line}')
                    res = re.findall("(\d+)", line)
                    speed = int(res[0])
                    if 'G' in line:
                        speed = speed * 1024
                    if 'K' in line:
                        speed = speed / 1024

                    self.network_speed = speed
                    break

            logger.info(f'当前服务器网口带宽为{self.network_speed}Mb/s')

    @handle_exception(is_return=True)
    def get_system_version(self):
        """
        获取系统发行版本或内核版本
        :return:
        """
        try:
            result = os.popen('cat /etc/redhat-release').readlines()    # 获取系统发行版本
            logger.debug(f'查询系统发行版本执行命令结果：{result}')
            self.system_version = result[0].strip()
        except Exception as err:
            logger.warning(err)
            result = os.popen('cat /proc/version').readlines()[0]   # 获取系统内核版本
            logger.debug(f'查询系统内核版本执行命令结果：{result}')
            res = re.findall("gcc.*\((.*?)\).*GCC", result.strip())
            if res:
                self.system_version = res[0]
            else:
                res = re.findall("gcc.*\((.*?)\)", result.strip())
                self.system_version = res[0]

        logger.info(f'当前系统发行/内核版本为{self.system_version}')

    def is_java_server(self, port):
        """
        判断端口是否是java服务
        :param port: 端口号
        """
        pid = port_to_pid(port)
        try:
            result = os.popen(f'jstat -gc {pid} |tr -s " "').readlines()[1]  # 执行命令
            res = result.strip().split(' ')
            logger.info(f'查询进程{pid}的JVM结果为：{res}')
            _ = float(res[2]) + float(res[3]) + float(res[5]) + float(res[7])  # 计算jvm

            self.is_java.update({str(port): 1})

        except Exception as err:
            logger.warning(err)
            self.is_java.update({str(port): 0})

    def check_sysstat_version(self):
        """
        检查 sysstat 版本，因为不同版本输出的内容可能不一样
        """
        try:
            version = os.popen("iostat -V |grep ersion |awk '{print $3}' |awk -F '.' '{print $1}'").readlines()[0]
            v = int(version.strip())
            if v < 12:
                raise Exception('当前sysstat版本过低，请升级到最新版本，下载地址：http://sebastien.godard.pagesperso-orange.fr/download.html')
        except IndexError:
            logger.error(traceback.format_exc())
            raise Exception('请安装最新版本的sysstat，下载地址：http://sebastien.godard.pagesperso-orange.fr/download.html')

    @handle_exception(is_return=True)
    def clear_port(self):
        """
        清理系统存储的已经停止监控的端口信息
        :return:
        """
        stop_num = self._msg['isRun'].count(0)

        if stop_num > 0:
            port_list = copy.deepcopy(self._msg)
            # 停止所有监控
            for ind in range(len(self._msg['port'])):
                if self._msg['isRun'][ind] > 0:
                    self._msg['isRun'][ind] = 0

            self.FGC = {}   # 清理GC次数
            self.FGC_time = {}  # 清理GC时间
            self.is_java = {}
            time.sleep(self.port_interval + 5)  # 等待所有端口监控停止
            self._msg = {'port': [], 'pid': [], 'isRun': [], 'startTime': []}

            # 开始重新监控
            for ind in range(len(port_list['port'])):
                if port_list['isRun'][ind] > 0:
                    self.start = {'port': port_list['port'][ind], 'pid': port_list['pid'][ind], 'is_run': 1}

            del port_list
            logger.info(f'清理过期停止监控端口成功')
        else:
            logger.info(f'没有停止监控的端口')

    def register_and_clear_port(self, flag=None):
        """
        已弃用，该功能已放在 self.write_system_cpu_mem_and_register_clear 函数中执行
        定时任务，总共有两个，一个是向服务端注册本机，一个是清理已经停止监控的过期端口
        :param
        :return:
        """
        pass
        '''url = f'http://{cfg.getMaster("host")}:{cfg.getMaster("port")}/Register'

        header = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/json; charset=UTF-8"}

        post_data = {
            'host': self.IP,
            'port': cfg.getServer('port'),
            'system': self.system_version,
            'cpu': self.cpu_cores,
            'nic': self.nic,
            'network_speed': self.network_speed,
            'mem': round(self.total_mem*100, 2),
            'disk_size': self.total_disk,
            'disks': ','.join(self.all_disk)
        }

        clear_time = time.time()
        while True:
            try:
                res = requests.post(url=url, json=post_data, headers=header)
                if time.time() - clear_time > 600:
                    self.clear_port()
                    clear_time = time.time()
            except Exception as err:
                logger.error(err)

            time.sleep(5)'''

    def clear_cache(self):
        """
        清理缓存
        :return:
        """
        logger.info(f'开始清理缓存：echo {self.echo} >/proc/sys/vm/drop_caches')
        os.popen(f'echo {self.echo} >/proc/sys/vm/drop_caches')
        logger.info('清理缓存成功')

    def __del__(self):
        pass


@handle_exception(is_return=True)
def port_to_pid(port):
    """
    根据端口号查询进程号
    :param port: 端口号
    :return: 进程号
    """
    pid = None
    result = os.popen(f'netstat -nlp|grep {port} |tr -s " "').readlines()
    logger.debug(f'{port}端口的进程结果为：{result}')
    flag = f':{port}'
    res = [line.strip() for line in result if flag in line]
    logger.debug(res[0])
    p = res[0].split(' ')
    pp = p[3].split(':')[-1]
    if str(port) == pp:
        pid = p[p.index('LISTEN') + 1].split('/')[0]
        logger.info(f'端口 {port} 的进程号为 {pid}.')

    return pid


@handle_exception(is_return=True)
def notification(msg):
    """
    发送邮件通知
    :param msg: 邮件正文信息
    :return:
    """
    url = f'http://{cfg.getMaster("host")}:{cfg.getMaster("port")}/Notification'

    header = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/json; charset=UTF-8"}

    post_data = {
        'host': get_ip(),
        'msg': msg
    }

    logger.debug(f'发送邮件信息的内容：{msg}')

    res = requests.post(url=url, json=post_data, headers=header)
    if res.status_code == 200:
        response = json.loads(res.content.decode())
        if response['code'] == 0:
            logger.info('邮件发送成功')
        else:
            logger.error(response['msg'])
    else:
        logger.error('邮件发送失败')
