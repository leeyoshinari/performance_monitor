#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
# Monitoring
import os
import time
import traceback
import config as cfg
from logger import logger
from extern import ports_to_pids


class PerMon(object):
    def __init__(self):
        self._is_run = 0    # 是否开始监控，0为停止监控，1为开始监控
        self._pid = []      # 存放待监控的进程号
        self._port = []     # 存放待监控的端口号
        self.db = None
        self.cursor = None
        self._total_time = 0     # 监控总时长，初始化为0
        self.interval = int(cfg.INTERVAL)   # 每次监控时间间隔
        self.disk = cfg.DISK        # 待监控的服务部署的磁盘号

        self.cpu_cores = 0  # CPU核数
        self.total_mem = 0  # 总内存

        self.get_cpu_cores()
        self.get_total_mem()

        self.start_time = 0     # 初始化开始监控时间
        self.FGC = 0            # 初始化Full GC次数

    @property
    def is_run(self):
        return self._is_run

    @is_run.setter
    def is_run(self, value):
        self._is_run = value

    @property
    def pid(self):
        return self._pid

    @pid.setter
    def pid(self, value):
        self._pid = value

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, value):
        self._port = value

    @property
    def total_time(self):
        return self._total_time

    @total_time.setter
    def total_time(self, value):
        if value:
            self._total_time = value + 60

    def write_cpu_mem(self):
        """
            监控CPU和内存.
        """
        while True:
            if self._is_run == 1:       # 开始监控
                self.start_time = time.time()   # 开始监控时间
                start_search_time = time.time()

                while True:
                    if time.time() - self.start_time < self._total_time:    # 如果超过监控总时长，则停止监控
                        get_data_time = time.time()
                        if get_data_time - start_search_time > self.interval:   # 如果大于每次监控时间间隔，则开始监控
                            start_search_time = get_data_time
                            '''if self.cm_counter > cfg.RUN_ERROR_TIMES:
                                self._is_run = 0    # if the times of failure is larger than default, stop monitor.
                                logger.logger.error('Stop monitor, because commands run error.')
                                self.cm_counter = 0
                                break'''

                            try:
                                for port, pid in zip(self._port, self._pid):
                                    cpu, mem = self.get_cpu(pid)    # 获取CPU和内存
                                    if cpu is None:
                                        # 如果没有获取到，可能出现异常，则重新根据端口号查询进程号
                                        # 正常情况不会出现异常，如果出现异常，可能端口在重启
                                        self._is_run = 2
                                        pid_transfor = ports_to_pids(self._port)  # 端口号转进程号
                                        if pid_transfor:
                                            if isinstance(pid_transfor, str):
                                                logger.logger.error(f'The pid of {pid_transfor} is not existed.')
                                            elif isinstance(pid_transfor, list):
                                                self._pid = pid_transfor
                                                self._is_run = 1

                                        time.sleep(cfg.SLEEPTIME)
                                        continue

                                    jvm = self.get_mem(pid)     # 获取JVM内存

                                    logger.logger.info(f'cpu_and_mem: port_{port},pid_{pid},{cpu},{mem},{jvm}')

                            except Exception as err:
                                logger.logger.error(traceback.format_exc())
                                time.sleep(cfg.SLEEPTIME)
                                continue

                    else:
                        self._is_run = 0    # if the total time is up, stop monitor.
                        logger.logger.info('Stop monitor, because total time is up.')
                        break

                    if self._is_run == 0:   # if _is_run=0, stop monitor.
                        logger.logger.info('Stop monitor.')
                        break
            else:
                time.sleep(cfg.SLEEPTIME)

    def write_io(self):
        """
            监控磁盘IO
        """
        while True:
            if self._is_run == 1:
                self.start_time = time.time()

                while True:
                    if time.time() - self.start_time < self._total_time:
                        try:
                            for iport, ipid in zip(self._port, self._pid):
                                ioer = self.get_io(ipid)

                                logger.logger.info(f'r_w_util: port_{iport},pid_{ipid},{ioer[0]},{ioer[1]},{ioer[-1]},{ioer[2]},{ioer[3]},{ioer[4]}')

                        except Exception as err:
                            logger.logger.error(traceback.format_exc())
                            time.sleep(cfg.SLEEPTIME)
                            continue

                    else:
                        self._is_run = 0
                        # logger.logger.info('Stop monitor, because total time is up.')
                        break

                    if self._is_run == 0 and self._is_run == 2:
                        # logger.logger.info('Stop monitor.')
                        break
            else:
                time.sleep(cfg.SLEEPTIME)

    def write_handle(self):
        """
            监控句柄数
        """
        while True:
            if self._is_run == 1:
                self.start_time = time.time()

                while True:
                    if time.time() - self.start_time < self._total_time:
                        try:
                            for hport, hpid in zip(self._port, self._pid):
                                handles = self.get_handle(hpid)
                                if handles is None:
                                    continue

                                logger.logger.info(f'handles: port_{hport},pid_{hpid},{handles}')

                        except Exception as err:
                            logger.logger.info(traceback.format_exc())
                            time.sleep(cfg.SLEEPTIME)
                            continue

                    else:
                        self._is_run = 0
                        # logger.logger.info('Stop monitor, because total time is up.')
                        break

                    if self._is_run == 0 and self._is_run == 2:
                        # logger.logger.info('Stop monitor.')
                        break
            else:
                time.sleep(cfg.SLEEPTIME)

    def get_cpu(self, pid):
        """
            使用top命令获取指定进程的CPU(%)和内存(G)
        """
        result = os.popen(f'top -n 1 -b -p {pid} |tr -s " "').readlines()[-1]       # 执行top命令
        res = result.strip().split(' ')
        logger.logger.debug(res)

        cpu = None
        mem = None
        if str(pid) in res:
            ind = res.index(str(pid))
            cpu = float(res[ind + 8]) / self.cpu_cores      # 计算CPU使用率
            mem = float(res[ind + 9]) * self.total_mem      # 计算占用内存大小

        return cpu, mem

    def get_mem(self, pid):
        """
            使用jstat命令获取指定进程的JVM(G)，仅java应用。
        """
        mem = 0
        try:
            result = os.popen(f'jstat -gc {pid} |tr -s " "').readlines()[1]     # 执行jstat命令
            res = result.strip().split(' ')
            logger.logger.debug(res)
            mem = float(res[2]) + float(res[3]) + float(res[5]) + float(res[7])     # 计算JVM大小

            # 将Full GC变化的时间以追加写入的方式写到文件里
            fgc = int(res[14])
            if self.FGC != fgc:
                self.FGC = fgc
                with open(cfg.FGC_TIMES, 'a') as f:
                    f.write(f"{self.FGC}--{time.strftime('%Y-%m-%d %H:%M:%S')}" + "\n")

        except Exception as err:
            logger.logger.info(err)

        return mem / 1024 / 1024

    def get_io(self, pid):
        """
            使用iotop命令获取指定进程读写磁盘速率
        """
        '''result = os.popen(f'iotop -n 2 -d 1 -b -qqq -p {pid} -k |tr -s " "').readlines()[-1]    # 执行iotop命令
        res = result.strip().split(' ')
        logger.logger.debug(res)'''

        disk_r, disk_w, disk_util = self.get_disk_io()      # 获取磁盘读写速率和IO(%)

        writer = 0
        reader = 0
        '''if str(pid) in res:
            ind = res.index(str(pid))
            writer = float(res[ind + 3])    # 读磁盘的速率(kB/s)
            reader = float(res[ind + 5])    # 写磁盘的速率(kB/s)'''

        # 通过进程读写速率和整个磁盘的读写速率，计算进程的IO
        try:
            util = (writer + reader) / (disk_w + disk_r) * disk_util
        except Exception as err:
            logger.logger.warning(err)
            util = 0

        return [reader, writer, disk_r, disk_w, disk_util, util]

    def get_disk_io(self):
        """
            使用iostat命令获取磁盘读写速率和IO(%)
        """
        disk_r = None
        disk_w = None
        disk_util = None
        try:
            result = os.popen(f'iostat -d -x -k {self.disk} 1 2 |tr -s " "').readlines()    # 执行iostat命令
            res = [line for line in result if self.disk in line]
            disk_res = res[-1].strip().split(' ')
            logger.logger.debug(disk_res)

            if self.disk in disk_res:
                disk_r = float(disk_res[5])         # 读磁盘的速率(kB/s)
                disk_w = float(disk_res[6])         # 写磁盘的速率(kB/s)
                disk_util = float(disk_res[-1])     # 磁盘IO(%)

        except Exception as err:
            logger.logger.error(err)

        return disk_r, disk_w, disk_util

    @staticmethod
    def get_handle(pid):
        """
            使用lsof命令获取指定进程的句柄数
            该命令执行很慢，建议不监控
        """
        result = os.popen("lsof -n | awk '{print $2}'| sort | uniq -c | sort -nr | " + "grep {}".format(pid)).readlines()
        res = result[0].strip().split(' ')
        logger.logger.debug(res)
        handles = None
        if str(pid) in res:
            handles = int(res[0])

        return handles

    def get_cpu_cores(self):
        """
            获取CPU核数
        """
        result = os.popen('cat /proc/cpuinfo| grep "processor"| wc -l').readlines()[0]

        self.cpu_cores = int(result)

        logger.logger.info(f'CPU core number is {self.cpu_cores}')

    def get_total_mem(self):
        """
            获取总内存大小
        """
        result = os.popen('cat /proc/meminfo| grep "MemTotal"| uniq').readlines()[0]

        self.total_mem = float(result.split(':')[-1].split('k')[0].strip()) / 1024 / 1024 / 100

        logger.logger.info(f'Total memory is {self.total_mem * 100}')

    def __del__(self):
        pass
