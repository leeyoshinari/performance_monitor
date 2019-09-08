#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
# Monitoring
import os
import re
import time
import threading
import traceback
import config as cfg
from logger import logger
from Email import sendMsg
from extern import ports_to_pids


class PerMon(object):
    def __init__(self):
        self._is_run = 0    # 是否开始监控，0为停止监控，1为开始监控
        self._pid = [1111]      # 存放待监控的进程号
        self._port = []     # 存放待监控的端口号
        self._total_time = 0     # 监控总时长，初始化为0
        self.interval = int(cfg.INTERVAL)   # 每次监控时间间隔
        self.is_monitor_system = cfg.IS_MONITOR_SYSTEM      # 是否监控系统资源
        self.error_times = cfg.ERROR_TIMES  # 命令执行失败次数
        self.disk = cfg.DISK        # 待监控的服务部署的磁盘号

        self.cpu_cores = 0  # CPU核数
        self.total_mem = 0  # 总内存

        self.re_cpu = re.compile('(\d{1,2}.\d) id')
        self.re_mem = re.compile('(\d{3,})[ ,+]free')

        self.get_cpu_cores()
        self.get_total_mem()

        self.start_time = 0     # 初始化开始监控时间
        self.run_error = 0      # 初始化命令执行失败次数
        self.FGC = 0            # 初始化Full GC次数
        self.FGC_time = []      # 存放full gc的时间

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
                            try:
                                for i in range(len(self._pid)):
                                    cpu, mem = self.get_cpu(self._pid[i])    # 获取CPU和内存

                                    if cpu is None:
                                        if self._port:
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
                                        else:
                                            if self.run_error > self.error_times:  # 如果命令执行失败次数大于设置次数，停止监控
                                                self._is_run = 0

                                            self.run_error += 1     # 命令执行失败次数加1
                                            logger.logger.error(f'The number of running command failed is {self.run_error}.')
                                            time.sleep(cfg.SLEEPTIME)
                                            continue

                                    jvm = self.get_mem(self._pid[i])     # 获取JVM内存

                                    logger.logger.info(f'cpu_and_mem: port_{self._port[i]},pid_{self._pid[i]},{cpu},{mem},{jvm}')
                                    self.run_error = 0      # 命令执行成功后，重新初始化0

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
                time.sleep(1)

    def write_io(self):
        """
            监控磁盘IO
        """
        while True:
            if self._is_run != 1 and self.is_monitor_system:
                disk_r, disk_w, disk_util, cpu, mem = self.get_system_cpu_io()
                if disk_util is not None:
                    logger.logger.info(f'system: disk_util,{disk_r},{disk_w},{disk_util}')
                if cpu is not None and mem is not None:
                    logger.logger.info(f'system: CpuAndMem,{cpu},{mem}')

            if self._is_run == 1:
                self.start_time = time.time()

                while True:
                    if time.time() - self.start_time < self._total_time:
                        try:
                            disk_r, disk_w, disk_util, cpu, mem = self.get_system_cpu_io()
                            if self.is_monitor_system:
                                if disk_util is not None:
                                    logger.logger.info(f'system: disk_util,{disk_r},{disk_w},{disk_util}')
                                if cpu is not None and mem is not None:
                                    logger.logger.info(f'system: CpuAndMem,{cpu},{mem}')

                            for i in range(len(self._pid)):
                                # ioer = self.get_io(self._pid[i])
                                logger.logger.info(f'r_w_util: port_{self._port[i]},pid_{self._pid[i]},0,0,0,{disk_r},{disk_w},{disk_util}')

                        except Exception as err:
                            logger.logger.error(traceback.format_exc())
                            time.sleep(cfg.SLEEPTIME)
                            continue

                    else:
                        self._is_run = 0
                        # logger.logger.info('Stop monitor, because total time is up.')
                        break

                    if self._is_run == 0 or self._is_run == 2:
                        # logger.logger.info('Stop monitor.')
                        break
            else:
                # time.sleep(1)
                pass

    def get_cpu(self, pid):
        """
            使用top命令获取指定进程的CPU(%)和内存(G)
        """
        result = os.popen(f'top -n 1 -b -p {pid} |tr -s " "').readlines()       # 执行top命令
        res = result[-1].strip().split(' ')
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
                self.FGC_time.append(time.time())
                if len(self.FGC_time) > 2:
                    frequency = (self.FGC_time[-1] - self.FGC_time[0]) / self.FGC
                    if frequency < 3600:
                        thread = threading.Thread(target=self.jvm_alert, args=(frequency, pid,))
                        thread.start()

                with open(cfg.FGC_TIMES, 'a') as f:
                    f.write(f"{self.FGC}--{time.strftime('%Y-%m-%d %H:%M:%S')}" + "\n")

            # 清空存放Full GC时间的变量
            if self.FGC == 0:
                self.FGC_time = []

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

        disk_r, disk_w, disk_util, _, _ = self.get_system_cpu_io()      # 获取磁盘读写速率和IO(%)

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

    def get_system_cpu_io(self):
        """
            使用iostat命令获取磁盘读写速率和IO(%)
        """
        disk_r = None
        disk_w = None
        disk_util = None
        cpu = None
        mem = None
        try:
            result = os.popen(f'iostat -x -k {self.disk} 1 2 |tr -s " "').readlines()    # 执行iostat命令
            disk_res = result[-2].strip().split(' ')
            logger.logger.debug(disk_res)

            if self.disk in disk_res:
                disk_r = float(disk_res[5])         # 读磁盘的速率(kB/s)
                disk_w = float(disk_res[6])         # 写磁盘的速率(kB/s)
                disk_util = float(disk_res[-1])     # 磁盘IO(%)

            cpu_res = result[-5].strip().split(' ')
            if len(cpu_res) > 3:
                cpu = 100 - float(cpu_res[-1])      # 系统CPU

            result = os.popen('cat /proc/meminfo| grep MemFree| uniq').readlines()[0]
            mem = float(result.split(':')[-1].split('k')[0].strip()) / 1024 / 1024      # 系统可用内存
            if mem <= cfg.MIN_MEM:
                logger.logger.warning(f'Current memory is {mem}, memory is too low.')
                thread = threading.Thread(target=self.mem_alert, args=(mem,))
                thread.start()

        except Exception as err:
            logger.logger.error(err)

        return disk_r, disk_w, disk_util, cpu, mem

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

    @staticmethod
    def mem_alert(mem):
        """
            当内存过低的时候，发出警告，并清理缓存
        """
        if cfg.IS_MEM_ALERT:    # 是否邮件发送警告
            msg = {'msg': f'当前剩余内存为{mem:.2f}G'}
            sendMsg(msg)

        if cfg.ECHO:    # 是否清理缓存
            os.popen(f'echo {cfg.ECHO} >/proc/sys/vm/drop_caches')
            logger.logger.info('Clear cache successful.')

    @staticmethod
    def jvm_alert(frequency, pid):
        """
            当Full GC频繁时，发出警告
        """
        if cfg.IS_JVM_ALERT:    # 是否邮件发送警告
            msg = {'msg': f'{pid}进程，最近一次Full GC频率为{frequency}'}
            sendMsg(msg)

    def __del__(self):
        pass
