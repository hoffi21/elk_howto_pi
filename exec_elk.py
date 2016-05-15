# coding: utf-8

import subprocess
from pexpect import pxssh
import getpass
import socket
import paramiko, base64
import sys, os
import time

host1 = '10.20.30.251'
host2 = '10.20.30.252'
port = 9200
#port = 22

host_dec = input('Which host do you want to manage? ')
if host_dec == 1:
    host = host1
    user = raw_input('username: ')
    password = getpass.getpass('password: ')

    client = paramiko.SSHClient()
    #client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #client.get_host_keys().add('suricata.local', 'ssh-ecdsa', key)
    client.connect(host1, username=user, password=password)
    stdin, stdout, stderr = client.exec_command('/usr/src/elasticsearch-2.2.1/bin/elasticsearch')
    client.close()

    print('Look for open elasticsearch...')
    s = socket(AF_INET, SOCK_STREAM)
    response = s.connect_ex((host1, port))
    while response != 0:
        time.sleep(5)
        response = s.connect_ex((host1, port))
        print ('Waiting for elasticsearch...')
    else response == 0:
        print ('Elasticsearch has been started.')

    user = raw_input('root username: ')
    password = getpass.getpass('root password: ')

    client = paramiko.SSHClient()
    #client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host1, username=user, password=password)
    stdin, stdout, stderr = client.exec_command('cd /etc/init.d/ && ./kibana_init')
    client.close()
elif host_dec == 2:
    host = host2
else:
    print('Not a known host.')
if host_dec != 1 and host_dec != 2:
    print('Not a known host.')
    sys.exit()




#stdin, stdout, stderr = client.exec_command('/var/www/kibana-4.4.1-linux-x86/bin/kibana')
    #stdout.readlines()
    #for line in stdout:
    #    print '... ' + line.strip('\n')
