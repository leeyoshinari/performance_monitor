#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import os
import time
import queue
import threading
from concurrent.futures import ThreadPoolExecutor

import happybase
import config as cfg
from logger import logger
from extern import port_to_pid, register, notification


class PerMon(object):
    def __init__(self):
        self.is_system = 0    # Monitor system's CPU and Memory, 0 means start, 1 means stop.
        self._msg = {'port': [], 'pid': [], 'isRun': [], 'startTime': []}   # initialize `port`, `pid`, etc.
        self.interval = int(cfg.INTERVAL)   # interval of every monitor
        self.error_times = cfg.ERROR_TIMES  # times of run command failure, default value.
        self.disk = cfg.DISK        # disk of monitored

        self.cpu_cores = 0  # CPU core
        self.total_mem = 0  # total memory

        self.get_cpu_cores()
        self.get_total_mem()

        self.monitor_task = queue.Queue()   # create queue, FIFO
        self.executor = ThreadPoolExecutor(cfg.THREAD_NUM)  # create thread pool

        self.pool = happybase.ConnectionPool(size=cfg.THREAD_NUM, host=cfg.HBASE_IP, port=cfg.HBASE_PORT)

        self.FGC = {}           # initialize
        self.FGC_time = {}      # initialize

    @property
    def start(self):
        return self._msg

    @start.setter
    def start(self, value):
        if value['port']:
            if value['port'] in self._msg['port']:  # If this `port` was monitored, update it.
                index = self._msg['port'].index(value['port'])
                self._msg['pid'][index] = value['pid']
                if self._msg['isRun'][index] == 0:
                    self._msg['isRun'][index] = value['is_run']
                    self._msg['startTime'][index] = time.strftime('%Y-%m-%d %H:%M:%S')
                    self.monitor_task.put((self.write_cpu_mem, index))

                    self.FGC[str(value['port'])] = 0    # reset FGC
                    self.FGC_time[str(value['port'])] = []

                    if self.monitor_task.qsize() > 0:   # If task is queuing, set it to 2.
                        self._msg['isRun'][index] = 2
                else:
                    pass
            else:
                self._msg['pid'].append(value['pid'])   # If this `port` is new, append it.
                self._msg['port'].append(value['port'])
                self._msg['isRun'].append(value['is_run'])
                self._msg['startTime'].append(time.strftime('%Y-%m-%d %H:%M:%S'))
                self.monitor_task.put((self.write_cpu_mem, len(self._msg['port'])-1))

                self.FGC.update({str(value['port']): 0})    # initialize FGC
                self.FGC_time.update({str(value['port']): []})

                if self.monitor_task.qsize() > 0:
                    self._msg['isRun'][-1] = 2
        else:
            pass

        if len(self._msg['port']) > 0:
            self.is_system = 1

    @property
    def stop(self):
        return self._msg

    @stop.setter
    def stop(self, value):
        index = self._msg['port'].index(value['port'])
        self._msg['isRun'][index] = value['is_run']

    def worker(self):
        """
            Get from queue, and start monitor
        """
        while True:
            func, param = self.monitor_task.get()
            func(param)
            self.monitor_task.task_done()

    def monitor(self):
        """
            Start Monitor.
        """
        thread = threading.Thread(target=register, args=())
        thread.start()

        for i in range(cfg.THREAD_NUM):
            self.executor.submit(self.worker)   # put queue to thread pool.

        self.monitor_task.put((self.write_system_cpu_mem, 1))   # monitor system's CPU and Memory

    def write_cpu_mem(self, index):
        """
            Monitor CPU, Momory and JVM of pid.
        """
        self._msg['startTime'][index] = time.strftime('%Y-%m-%d %H:%M:%S')

        run_error = 0      # initialize, run command failure times.
        run_error_time = time.time()    # initialize, run command failure time.
        start_search_time = time.time()
        port = self._msg['port'][index]
        pid = self._msg['pid'][index]

        c_ = f'cpu:{port}'
        m_ = f'mem:{port}'
        j_ = f'jvm:{port}'

        with self.pool.connection() as connection:
            table = connection.table(cfg.IP.replace('.', ''))
            while True:
                if self._msg['isRun'][index] > 0:   # start monitor
                    self._msg['isRun'][index] = 1   # reset to 1, means monitoring, if it's queuing.
                    get_data_time = time.time()
                    if get_data_time - start_search_time > self.interval:
                        start_search_time = get_data_time
                        try:
                            cpu, mem = self.get_cpu(pid)    # get CPU and memory

                            if cpu is None:
                                if port:
                                    # If get `None`, it maybe wrong, need to get pid again.
                                    pid = port_to_pid(port)  # `port` to `pid`
                                    if pid:
                                        self._msg['pid'][index] = pid
                                        self._msg['startTime'][index] = time.strftime('%Y-%m-%d %H:%M:%S')

                                    # If the time of running error is more than 1800s, stop monitor.
                                    if time.time() - run_error_time > 1800:
                                        break

                                    time.sleep(cfg.SLEEPTIME)
                                    continue
                                else:
                                    # If times of run failure is larger than default, stop monitor.
                                    if run_error > self.error_times:
                                        logger.error(f'{pid} has been stopped monitor, some errors may be occurred.')
                                        break

                                    run_error += 1
                                    logger.error(f'The number of running command failed is {run_error}.')
                                    time.sleep(cfg.SLEEPTIME)
                                    continue

                            jvm = self.get_mem(port, pid)     # get JVM

                            table.put(str(time.time()), {c_: cpu, m_: mem, j_: jvm})
                            logger.info(f'cpu_and_mem: port_{port},pid_{pid},{cpu},{mem},{jvm}')
                            run_error_time = time.time()    # If run successfully, reset time.
                            run_error = 0      # If run successfully, set to 0, initialize.

                        except Exception as err:
                            logger.error(err)
                            time.sleep(cfg.SLEEPTIME)
                            continue

                if self._msg['isRun'][index] == 0:   # stop monitor.
                    logger.info(f'{port} has been stopped monitor')
                    break

    def write_system_cpu_mem(self, is_system):
        """
            Monitor system's CPU and free memory.
        """
        flag = True
        echo = True
        with self.pool.connection() as connection:
            table = connection.table(cfg.IP.replace('.', ''))
            while True:
                if self.is_system == 1:
                    disk_r, disk_w, disk_util, cpu, mem = self.get_system_cpu_io(types=True)
                    if disk_util is not None:
                        # table.put(str(time.time()), {'io:sdba': disk_util})
                        logger.info(f'system: disk_util,{disk_r},{disk_w},{disk_util}')
                    if cpu is not None and mem is not None:
                        table.put(str(time.time()), {'cpu:system': cpu, 'mem:system': mem})
                        logger.info(f'system: CpuAndMem,{cpu},{mem}')

                        if mem <= cfg.MIN_MEM:
                            logger.warning(f'Current memory is {mem}, memory is too low.')
                            if cfg.IS_MEM_ALERT and flag:
                                flag = False
                                notification(msg=f'Current memory is {mem}, memory is too low.')

                            if cfg.ECHO and echo:
                                echo = False
                                thread = threading.Thread(target=self.clear_cache, args=())
                                thread.start()

                        else:
                            flag = True
                            echo = True

                else:
                    time.sleep(1)

    def get_cpu(self, pid):
        """
            Use `top` to get CPU and Memory.
        """
        cpu = None
        mem = None

        try:
            # result = os.popen(f'top -n 1 -b -p {pid} |tr -s " "').readlines()
            result = os.popen(f'top -n 1 -b |grep -P {pid} |tr -s " "').readlines()
            res = result[-1].strip().split(' ')
            logger.debug(res)

            if str(pid) in res:
                ind = res.index(str(pid))
                cpu = float(res[ind + 8]) / self.cpu_cores      # CPU
                mem = float(res[ind + 9]) * self.total_mem      # memory

        except Exception as err:
            logger.error(err)

        return cpu, mem

    def get_mem(self, port, pid):
        """
            Use `jstat` to get JVM and GC, just java application.
        """
        mem = 0
        try:
            result = os.popen(f'jstat -gc {pid} |tr -s " "').readlines()[1]
            res = result.strip().split(' ')
            logger.debug(res)
            mem = float(res[2]) + float(res[3]) + float(res[5]) + float(res[7])     # calculate JVM

            # Write FGC's time to file as an additional, and send email to alert when the frequency of FGC is too high.
            fgc = int(res[14])
            if self.FGC[str(port)] != fgc:
                self.FGC[str(port)] = fgc
                self.FGC_time[str(port)].append(time.time())
                if len(self.FGC_time[str(port)]) > 2:
                    frequency = (self.FGC_time[str(port)][-1] - self.FGC_time[str(port)][0]) / self.FGC[str(port)]
                    if frequency < 3600:
                        logger.warning(f'pid--{pid} The current frequency of `Full GC` is {frequency}.')
                        if cfg.IS_JVM_ALERT:  # send email to alert
                            notification(port=port, msg=f'The frequency of `Full GC` is {frequency}')

                with open(cfg.FGC_TIMES, 'a') as f:
                    f.write(f"{port}--{self.FGC[str(port)]}--{time.strftime('%Y-%m-%d %H:%M:%S')}" + "\n")

            # If FGC's times is 0, set FGC's time to default.
            if self.FGC[str(port)] == 0:
                self.FGC_time[str(port)] = []

        except Exception as err:
            logger.info(err)

        return mem / 1024 / 1024

    def get_system_cpu_io(self, types=None):
        """
            Use `iostat` to get disk read, write and IO(%)
        """
        disk_r = None
        disk_w = None
        disk_util = None
        cpu = None
        mem = None
        try:
            result = os.popen(f'iostat -x -k {self.disk} 1 2 |tr -s " "').readlines()
            disk_res = result[-2].strip().split(' ')
            logger.debug(disk_res)

            if self.disk in disk_res:
                disk_r = float(disk_res[5])         # read(kB/s)
                disk_w = float(disk_res[6])         # write(kB/s)
                disk_util = float(disk_res[-1])     # disk IO(%)

            if types:
                cpu_res = result[-5].strip().split(' ')
                if len(cpu_res) > 3:
                    cpu = 100 - float(cpu_res[-1])      # calculate CPU

                result = os.popen('cat /proc/meminfo| grep MemFree| uniq').readlines()[0]
                mem = float(result.split(':')[-1].split('k')[0].strip()) / 1024 / 1024      # free memory

        except Exception as err:
            logger.error(err)

        return disk_r, disk_w, disk_util, cpu, mem

    '''def get_handle(pid):
        """
            Get handles' number by `lsof`.
        """
        result = os.popen("lsof -n | awk '{print $2}'| sort | uniq -c | sort -nr | " + "grep {}".format(pid)).readlines()
        res = result[0].strip().split(' ')
        logger.debug(res)
        handles = None
        if str(pid) in res:
            handles = int(res[0])

        return handles'''

    def get_cpu_cores(self):
        """
            Get the CPU's core number.
        """
        result = os.popen('cat /proc/cpuinfo| grep "processor"| wc -l').readlines()[0]
        self.cpu_cores = int(result)
        logger.info(f'CPU core number is {self.cpu_cores}')

    def get_total_mem(self):
        """
            Get total memory.
        """
        result = os.popen('cat /proc/meminfo| grep "MemTotal"| uniq').readlines()[0]
        self.total_mem = float(result.split(':')[-1].split('k')[0].strip()) / 1024 / 1024 / 100
        logger.info(f'Total memory is {self.total_mem * 100}')

    @staticmethod
    def mem_alert(mem):
        """
            When the remaining memory is too low, alerting.
        """
        msg = {'msg': f'The current remaining memory is {mem:.2f}G'}
        # sendMsg(msg)

    @staticmethod
    def clear_cache():
        """
            When the remaining memory is too low, clearing caches.
        """
        logger.info(f'Start clearing cache：echo {cfg.ECHO} >/proc/sys/vm/drop_caches')
        os.popen(f'echo {cfg.ECHO} >/proc/sys/vm/drop_caches')
        logger.info('Clear cache successful.')

    @staticmethod
    def jvm_alert(frequency, pid, port):
        """
            When the frequency of `Full GC` is too high, alerting.
        """
        msg = {'msg': f'port--{port}, pid--{pid} the frequency of `Full GC` is {frequency}'}
        # sendMsg(msg)

    def __del__(self):
        pass
