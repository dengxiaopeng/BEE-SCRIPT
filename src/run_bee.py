#! /usr/bin/python3

import time
import yaml
import requests
import os
import sys
import json
from pathlib import Path

if __package__ is None:                  
    DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(DIR.parent))
    __package__ = DIR.name

try:
    from .GLOBAL import *
except:
    from GLOBAL import *

if hasattr(yaml,'_warnings_enabled'):
    yaml._warnings_enabled['YAMLLoadWarning'] = False

def getPublicIp():
    insideUrl = "https://api.ipify.org/?format=json"
    outsideUrl = "http://ifconfig.me/ip"
    
    try:
        ipAddress = requests.get(insideUrl,timeout=2)
        return ipAddress.json()['ip']
    except Exception:
        ipAddress = requests.get(outsideUrl,timeout=2)
        return ipAddress.text


def getYamlValue(key,bee,defaultValue):
    if key in bee:
        return bee[key]
    else:
        return defaultValue


def mkBeeDataFiles():
    # check configure
    if not os.path.exists(CONF_PATH):
        os.makedirs(CONF_PATH)
    raw_yaml = os.path.join(CONF_PATH,'bee.yaml')
    if not os.path.exists(raw_yaml):
        print("check ../conf/bee.yaml is exits?")
        return
    
    with open(raw_yaml,encoding='utf-8') as f:
        temp = yaml.load(f.read())
        #check peers configure
        if not "peers" in temp:
            print("check peers configure is in bee.yaml.")
            sys.exit(2)
        peers = temp.pop("peers")
        startPort = temp.pop("startPort")

        api_addr = startPort
        p2p_addr = api_addr + 1
        debug_api_addr = api_addr + 2
        nat_addr = getPublicIp() + ':'
        welcomeMsg = getYamlValue('welcome-message',temp,'dpbee')

        gap = 10
        ret = []

        i = 0
        for p in peers:
            curConfigure = {}
            curConfigure['dataDir'] = p["data-dir"]
            curConfigure['peers'] = []
            for _ in range(p["count"]):
                temp['api-addr'] = ':'+str(api_addr + i*gap)
                temp['config'] = os.path.join(curConfigure['dataDir'],'bee'+str(i),'bee.yaml')
                temp['data-dir'] = os.path.join(curConfigure['dataDir'],'bee'+str(i))
                temp['p2p-addr'] = ':'+str(p2p_addr + i*gap)
                temp['debug-api-addr'] = '127.0.0.1:'+str(debug_api_addr + i*gap)
                temp['debug-api-enable'] = True
                temp['nat-addr'] = nat_addr + str(p2p_addr + i*gap)
                temp['welcome-message'] = welcomeMsg + "%03d"%(i)
                curConfigure['peers'].append(temp.copy())
                i+=1
                print("%d config file generated." % (i))
            ret.append(curConfigure)

    outputJson = "bee_%d_%s.json" %(i,time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime()))
    with open(os.path.join(CONF_PATH,outputJson),mode='w') as retJson:
        json.dump(ret,indent=4,sort_keys=True,fp=retJson)
    print("finish generate %d yamls"%(i))
    

def getYamls(configFile):
    if not os.path.exists(configFile):
        print('create conf file frist.%s is not exists' % configFile)
        return {}
    
    files = []
    if os.path.isdir(configFile):
        for f in os.listdir(configFile):
            if not (f.startswith("bee") and f.endswith(".json")):
                continue
            files.append(os.path.join(configFile,f))
    else:
        files.append(configFile)
    
    ret = []
    for f in files:
        with open(f) as confJson:
            for cfs in json.load(confJson):
                ret.append(cfs)
    return ret


def getPidFromFile(pidfile):
    #check pid is running
    checkcmd = 'ps -p {:d}|grep {:d}'
    if os.path.exists(pidfile):
        with open(pidfile) as pfile:
            pid = pfile.read()
            try:
                pid = int(pid)
            except:
                pid = -1
        if pid != -1:
            ret = os.popen(checkcmd.format(pid,pid))
            if not ret.read().__contains__(str(pid)):
                pid = -1
    else:
        pid = -1

    return pid


def killBees(configFile):
    allBees = getYamls(configFile)
    cnt = 0
    
    for bees in allBees:
        for bee in bees['peers']:
            data_dir = bee['data-dir']
            pidfile = os.path.join(data_dir , 'pid.txt')
            pid = getPidFromFile(pidfile)
            if pid != -1:
                cnt += 1
                os.popen('kill -9 '+str(pid))
        
    print("peers count = %d,kill count = %d"%(len(bees['peers']),cnt))


def buildRunCmd(bee) -> str:
    formatStr = "--%s '%s' "
    ret = ''
    for k in bee:
        if k == "config":
            continue
        ret += formatStr % (k,bee[k])
    return ret


def startBees(configFile):
    allBees = getYamls(configFile)

    bee_sh = "nohup bee start {config:s}> {output_file:s} 2>&1 < /dev/null & echo $! > {pidfile:s}"
    
    for bees in allBees:
        for bee in bees['peers']:
            config_file = bee['config']
            data_dir = bee['data-dir']
            output_file = os.path.join(data_dir,'output.log')
            pidfile = os.path.join(data_dir,'pid.txt')
            if getPidFromFile(pidfile) != -1 : continue
            if not os.path.exists(data_dir): os.makedirs(data_dir)
            cmdConfig = buildRunCmd(bee)
            excute_bee_sh = bee_sh.format(config=cmdConfig,output_file=output_file,pidfile=pidfile)
            ret = os.popen(excute_bee_sh)
            print(ret.read())
            ret.close()
            print(excute_bee_sh)
            print()

    print("start bee %d all"%(len(bees['peers'])))


def printHelp():
    print('Usage run_bee.py [OPTION]')
    print()
    print('  -c, --create                create peers from configure ../conf/bee.yaml')
    print('  -k PATH, --kill             kill peers whit config file or dir/*.json')
    print('  -s PATH, --start            start peers whit config file or dir/*.json')
    print('  -h, --help                  show this page')
    print()
    print('Examples:')
    print('  run_bee.py -c')
    print()
    print('Author:')
    print(' Fish Deng')



def main(argv):
    base_cmd = [
        ('-c','--create'),
        ('-k','--kill'),
        ('-s','--start'),
        ('-h','--help'),
    ]

    if len(argv) == 0:
        printHelp()
        sys.exit(1)
    
    findCmd = False
    for cmd in base_cmd:
        if argv[0] in cmd:
            findCmd = True
            break

    if not findCmd:
        printHelp()
        sys.exit(1)
    
    if argv[0] in base_cmd[0]:
        #create
        mkBeeDataFiles()
    elif argv[0] in base_cmd[1]:
        #kill
        try:
            configFile = argv[1]
            if not os.path.exists(configFile):
                print("%s is not exists!" %(configFile))
                sys.exit(2)
        except:
            printHelp()
            sys.exit(2)
        killBees(configFile=configFile)
    elif argv[0] in base_cmd[2]:
        #start
        try:
            configFile = argv[1]
            if not os.path.exists(configFile):
                print("%s is not exists!" %(configFile))
                sys.exit(2)
        except:
            printHelp()
            sys.exit(2)
        startBees(configFile=configFile)
    else:
        #help
        printHelp()


if __name__ == '__main__':
    main(sys.argv[1:])
