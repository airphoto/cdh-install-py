# -*- coding:utf8 -*-
# author : abel

def getLines(name):
    fileName = 'configs/%s'%name
    with open(fileName) as f:
        return map(lambda x:x.strip('\r\n'),f.readlines())

def getHosts(name):
    lines = getLines(name)
    return map(lambda x:x.split(' ')[0],lines)

def getIPHostPairs(name):
    maps = {}
    for line in getLines(name):
        fields = line.split(' ')
        maps[fields[0]] = fields[1]
    return maps

def getHostIPPairs(name):
    maps = {}
    for line in getLines(name):
        fields = line.split(' ')
        maps[fields[1]] = fields[0]
    return maps

def getCommands(name):
    return filter(lambda x:not x.startswith('#'),getLines(name))

def getMysqlProp(name):
    maps = {}
    for line in getLines(name):
        field = line.split('=')
        maps[field[0]] = field[1]
    return maps

if __name__ == '__main__':
    commands = []
    with open('F:\pycharm\cdh-install\configs\commands') as f:
        commands = map(lambda x: x.strip('\r\n'), f.readlines())

    fi = filter(lambda x:not x.startswith('#'),commands)
    for line in fi:
        print line