# -*- coding:utf8 -*-
# author : abel

from fabfile import *
from fabric.api import *
import socket

def getLocalIP():
    # 获取本机电脑名
    myname = socket.getfqdn(socket.gethostname())
    # 获取本机ip
    return socket.gethostbyname(myname)


if __name__=='__main__':
    modifyHostname()
    local('fab modifyHosts')
    local('fab modifySelinux')
    local('fab initStarNTP')
    local('fab modifyNTPConf1')
    local('fab uploadJDK')
    local('fab installJDK')
    local('fab uploadParcels')
    local('fab installParcels')
    local('fab uploadMysqlConn')
    local('fab runCommands')
    localIp = getLocalIP()
    modifyNTPConf2(localIp)
    initMysql()
    local('fab afterMysql')
    setScmServer()
    local('fab installSCM')