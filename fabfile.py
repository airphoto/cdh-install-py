# -*- coding:utf8 -*-
# author : abel
from fabric.api import *
import os
import paramiko
import MySQLdb

from utils import FileUtils as fu

username = 'root'
pwd = 'qwer1234'
hts = fu.getHosts('hosts')
hostFields = hts[0].split('.')
pre = '%s.%s.%s.0'%(hostFields[0],hostFields[1],hostFields[2])
managerIP = fu.getHostIPPairs('hosts')['hadoop-manager1']
mysqlMaps = fu.getMysqlProp('mysql.properties')
env.timeout=20

env.user = username
env.password = pwd
env.hosts = hts
# env.warn_only = True

#修改主机名
def modifyHostname():
    ipHostPairs = fu.getIPHostPairs('hosts')
    for ip,hostName in ipHostPairs.items():
        # print ip,hostName
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port=22, username=username, password=pwd)
        command = '''sed -i \'s/HOSTNAME=.*/HOSTNAME=%s/\' /etc/sysconfig/network''' % hostName
        ssh.exec_command(command)
        ssh.exec_command('hostname %s'%hostName)
        ssh.close()

#修改hosts
def modifyHosts():
    lines = fu.getLines('hosts')
    for line in lines:
        run('echo \'%s\' >> /etc/hosts'%line)

#禁止selinux
def modifySelinux():
    run('sed -i "s/^SELINUX=.*/SELINUX=disabled/" /etc/sysconfig/selinux')


# #生成ssh
# def modifySSH():
#     run('ssh-keygen -t rsa  -f ~/.ssh/id_rsa -P \'\'')
#
# #ssh互信
# def copySSH():
#     for ip,host in fu.getIPHostPairs('hosts').items():
#         command = 'ssh-copy-id %s'%ip
#         print command
#         run(command)

#安装时间服务器
# def installNTP():
#     run('yum install -y ntp')

def initStarNTP():
    run('service ntpd start')
    run('chkconfig ntpd on')

#修改ntp
def modifyNTPConf1():
    with cd('/etc'):
        run('sed -i "s/#restrict.*/restrict %s mask 255.255.255.0 nomodify notrap/" ntp.conf'%pre)
        run('sed -i "/^server.*/d" ntp.conf')

#修改ntp
def modifyNTPConf2(ntpServer):
    ipHostPairs = fu.getIPHostPairs('hosts')
    for ip, hostName in ipHostPairs.items():
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port=22, username=username, password=pwd)
        if hostName=='hadoop-manager1':
            ssh.exec_command('echo "server 127.127.1.0" >> /etc/ntp.conf')
            ssh.exec_command('echo "fudge  127.127.1.0 startum 10" >> /etc/ntp.conf')
        else:
            ssh.exec_command('echo "server %s" >> /etc/ntp.conf'%managerIP)
            ssh.exec_command('echo "0-59/3 * * * * /usr/sbin/ntpdate -u hadoop-manager1" >> /var/spool/cron/root')

        ssh.exec_command('ntpdate -u %s' % ntpServer)
        ssh.exec_command('hwclock --localtime')
        ssh.exec_command('hwclock --localtime -w')
        ssh.exec_command('echo "SYNC_HWCLOCK=yes" >> /etc/sysconfig/ntpd')
        ssh.exec_command('sed -i "s/SYNC_HWCLOCK=.*/SYNC_HWCLOCK=yes/" /etc/sysconfig/ntpdate')
        ssh.exec_command('service ntpd restart')
        ssh.close()

#上传jdk文件
def uploadJDK():
    director = 'jdk'
    remote = '/root'
    for f in os.listdir(director):
        put('%s/%s'%(director,f),remote)
#安装jdk
def installJDK():
    run('mkdir /usr/java')
    with cd('/root'):
        run('tar -xf jdk-7u79-linux-x64.tar.gz -C /usr/java')
    run('echo "export JAVA_HOME=/usr/java/jdk1.7.0_79" >> /etc/profile')
    run('echo "export CLASSPATH=.:$JAVA_HOME/lib:$JAVA_HOME/jre/lib" >> /etc/profile')
    run('echo "export PATH=$JAVA_HOME/bin:$JAVA_HOME/jre/bin:$PATH" >> /etc/profile')
    run('source /etc/profile')
    run('rm -f jdk*')

#上传parcels文件
def uploadParcels():
    director = 'cdh'
    remote = '/root'
    for f in os.listdir(director):
        put('%s/%s'%(director,f),remote)

def installParcels():
    run('mkdir /opt/cloudera-manager')
    run('tar -xf /root/cloudera-manager-el6-cm5.7.4_x86_64.tar.gz -C /opt/cloudera-manager')
    run('useradd --system --home=/opt/cloudera-manager/cm-5.7.4/run/cloudera-scm-server --no-create-home --shell=/bin/false --comment "Cloudera SCM User" cloudera-scm')
    run('mkdir -p /opt/cloudera/parcel-repo')
    run('chown cloudera-scm:cloudera-scm /opt/cloudera/parcel-repo')
    run('mkdir -p /opt/cloudera/parcels')
    run('chown cloudera-scm:cloudera-scm /opt/cloudera/parcels')
    run('mkdir /var/lib/cloudera-scm-server')
    run('chown cloudera-scm:cloudera-scm /var/lib/cloudera-scm-server')
    run('mkdir /var/log/cloudera-scm-server')
    run('chown cloudera-scm:cloudera-scm /var/log/cloudera-scm-server')
    run('mkdir -p /var/cm_logs/cloudera-scm-headlamp')
    run('chown cloudera-scm /var/cm_logs/cloudera-scm-headlamp')
    run('mv /root/CDH* /opt/cloudera/parcel-repo')
    run('mv /root/manifest.json /opt/cloudera/parcel-repo')

#上传mysql驱动
def uploadMysqlConn():
    director = 'mysql'
    remote = '/opt/cloudera-manager/cm-5.7.4/share/cmf/lib'
    for f in os.listdir(director):
        put('%s/%s'%(director,f),remote)

#
def initScm():
    db = 'scm'
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(managerIP, port=22, username=username, password=pwd)
    command = '/opt/cloudera-manager/cm-5.7.4/share/cmf/schema/scm_prepare_database.sh mysql %s %s %s > /root/sshlog/scm.log'%(db,mysqlMaps['username'],mysqlMaps['pwd'])
    ssh.exec_command(command)
    ssh.close()

def initMysql():
    print managerIP,mysqlMaps['username'],mysqlMaps['pwd']
    conn = MySQLdb.connect(host=managerIP, port=3306, user=mysqlMaps['username'], passwd=mysqlMaps['pwd'])
    cur = conn.cursor()
    commandsForMysql = mysqlMaps['command'].split(';')
    for command in commandsForMysql:
        cur.execute(command)
    cur.close()
    conn.commit()
    conn.close()

def runCommands():
    name = 'commands'
    for command in fu.getCommands(name):
        run(command)

#配置scm server
def setScmServer():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(managerIP, port=22, username=username, password=pwd)
    start_command = '/opt/cloudera-manager/cm-5.7.4/etc/init.d/cloudera-scm-server start > /root/sshlog/scm_server.log'
    cp_command = 'cp /opt/cloudera-manager/cm-5.7.4/etc/init.d/cloudera-scm-server /etc/init.d/cloudera-scm-server'
    init_start_command = 'r'
    sed_command = 'sed -i \'s/CMF_DEFAULTS=${CMF_DEFAULTS.*/CMF_DEFAULTS=\/opt\/cloudera-manager\/cm-5.7.4\/etc\/default/\' /etc/init.d/cloudera-scm-server'
    ssh.exec_command(start_command)
    ssh.exec_command(cp_command)
    ssh.exec_command(init_start_command)
    ssh.exec_command(sed_command)
    ssh.close()

def setScmAgent():
    run('/opt/cloudera-manager/cm-5.7.4/etc/init.d/cloudera-scm-agent start > /root/sshlog/scm_agent.log')
    run('cp /opt/cloudera-manager/cm-5.7.4/etc/init.d/cloudera-scm-agent /etc/init.d/cloudera-scm-agent')
    run('chkconfig cloudera-scm-agent on')
    sed_command = 'sed -i \'s/CMF_DEFAULTS=${CMF_DEFAULTS.*/CMF_DEFAULTS=\/opt\/cloudera-manager\/cm-5.7.4\/etc\/default/\' /etc/init.d/cloudera-scm-agent'
    run(sed_command)

# def beforeMysql():
#     modifyHosts()
#     modifySelinux()
#     #installNTP()#如果有的话就不要装了呗
#     initStarNTP()
#     modifyNTPConf1()
#     uploadJDK()
#     installJDK()
#     uploadParcels()
#     uploadMysqlConn()
#     runCommands()


def afterMysql():
    initScm()

def installSCM():
    setScmAgent()
