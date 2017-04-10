#!/usr/local/easyops/python/bin/python
# encoding: utf-8
#主机巡检

import os
import psutil
import platform


# cpu
cpu = psutil.cpu_percent(interval=3)
info = "IP=%s&CPU=%s" % (EASYOPS_LOCAL_IP, cpu)
print info
PutRow("table", info)

# loads
if platform.system() != 'Windows':
    load = os.getloadavg()
    info = 'IP=%s&LOAD=%.4s, %.4s, %.4s' % (EASYOPS_LOCAL_IP, load[0], load[1], load[2])
    print info
    PutRow("table", info)

# memory
print "memory使用情况(单位: M):"
memory = psutil.virtual_memory()
memory_free = memory.free / 1024.0 / 1024
memory_percent = memory.percent
info = "IP=%s&MEMORY=%.2fM&MEM_PER=%.1f%%" % (EASYOPS_LOCAL_IP, memory_free, memory_percent)
print info
PutRow("table", info)


# disk
print "磁盘使用情况(单位: G):"
disk = psutil.disk_usage('/')
disk_free = disk.free / 1024.0 / 1024 / 1024
disk_percent = disk.percent
info = "IP=%s&DISK=%.2fG&DISK_PER=%.1f%%" % (EASYOPS_LOCAL_IP, disk_free, disk_percent)
print info
PutRow("table", info)