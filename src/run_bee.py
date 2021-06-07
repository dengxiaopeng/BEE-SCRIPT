import time
import yaml
import requests
import os
import shutil
import sys
import json
from GLOBAL import *

yaml._warnings_enabled['YAMLLoadWarning'] = False

def getPublicIp():
    insideUrl = "http://ip.42.pl/raw"
    outsideUrl = "http://ifconfig.me/ip"
    
    try:
        ipAddress = requests.get(insideUrl,timeout=2)
        return ipAddress.text
    except Exception:
        ipAddress = requests.get(outsideUrl,timeout=2)
        return ipAddress.text


def getYamlValue(key,bee,defaultValue):
    if key in bee:
        return bee[key]
    else:
        return defaultValue


def mkBeeDataFiles(nodeCount:int,dataPath:str=None):
    if not os.path.exists(CONF_PATH):
        os.makedirs(CONF_PATH)
    raw_yaml = os.path.join(CONF_PATH,'bee.yaml')
    if not os.path.exists(raw_yaml):
        print("check ../conf/bee.yaml is exits?")
        return
    with open(raw_yaml,encoding='utf-8') as f:
        temp = yaml.load(f.read())
        api_addr = getYamlValue('api-addr',temp,1633)
        api_addr = int(api_addr[1:]) if isinstance(api_addr,str) else api_addr
        p2p_addr = api_addr + 1
        debug_api_addr = api_addr + 2
        dataDir = getYamlValue('data-dir',temp,'/data/') if dataPath is None else dataPath
        nat_addr = getPublicIp() + ':'
        welcomeMsg = getYamlValue('welcome-message',temp,'dpbee')
        gap = 10
        ret = {}
        ret['dataDir'] = dataDir
        ret['peers'] = []

        for i in range(nodeCount):
            temp['api-addr'] = ':'+str(api_addr + i*gap)
            temp['config'] = os.path.join(dataDir,'bee'+str(i),'bee.yaml')
            temp['data-dir'] = os.path.join(dataDir,'bee'+str(i))
            temp['p2p-addr'] = ':'+str(p2p_addr + i*gap)
            temp['debug-api-addr'] = '127.0.0.1:'+str(debug_api_addr + i*gap)
            temp['nat-addr'] = nat_addr + str(p2p_addr + i*gap)
            temp['welcome-message'] = welcomeMsg + "%03d"%(i)
            ret['peers'].append(temp.copy())
            print("%d config file generated." % (i+1))
    outputJson = "bee_%d_%s.json" %(nodeCount,time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime()))
    with open(os.path.join(CONF_PATH,outputJson),mode='w') as retJson:
        json.dump(ret,indent=4,sort_keys=True,fp=retJson)
    print("finish generate %d yamls"%(nodeCount))
    

def getYamls(configFile):
    if not os.path.exists(configFile):
        print('create conf file frist.')
        return {}
    with open(configFile) as confJson:
        ret = json.load(confJson)
        return ret


def getPidFromFile(pidfile):
    #check pid is running
    checkcmd = 'ps -p {pid:d}|grep {pid:d}'
    if os.path.exists(pidfile):
        with open(pidfile) as pfile:
            pid = pfile.read()
            try:
                pid = int(pid)
            except:
                pid = -1
        if pid != -1:
            ret = os.popen(checkcmd.format(checkcmd.format(pid,pid)))
            if not ret.read().__contains__(str(pid)):
                pid = -1
    else:
        pid = -1

    return pid


def killBees(configFile):
    bees = getYamls(configFile)
    cnt = 0
    for bee in bees['peers']:
        data_dir = bee['data-dir']
        pidfile = os.path.join(data_dir , 'pid.txt')
        pid = getPidFromFile(pidfile)
        if pid != -1:
            cnt += 1
            os.popen('kill -9 '+str(pid))
        
    print("peers count = %d,kill count = %d"%(len(bees['peers'],cnt)))


def startBees(configFile):
    bees = getYamls(configFile)

    bee_sh = "nohup bee start --config {config_file:s} > {output_file:s} 2>&1 < /dev/null & echo $! > {pidfile:s}"
    
    for bee in bees['peers']:
        config_file = bee['config']
        data_dir = bee['data-dir']
        output_file = os.path.join(data_dir,'output.log')
        pidfile = os.path.join(data_dir,'pid.txt')
        if getPidFromFile(pidfile) != -1 : continue
        if not os.path.exists(data_dir): os.makedirs(data_dir)
        with open(config_file,mode='w') as conFile:
            yaml.dump(bee,conFile)
        excute_bee_sh = bee_sh.format(config_file=config_file,output_file=output_file,pidfile=pidfile)
        ret = os.popen(excute_bee_sh)
        print(ret.read())
        ret.close()
        print(excute_bee_sh)
        print()

    print("start bee %d all"%(len(bees['peers'])))


def printHelp():
    print('Usage run_bee.py [OPTION]')
    print()
    print('  -c N DATA_DIR, --create     create N peers conf,base DATA_DIR')
    print('  -k PATH, --kill             kill peers whit config file')
    print('  -s PATH, --start            start peers whit config file')
    print('  -h, --help                  show this page')
    print()
    print('Examples:')
    print('  run_bee.py -c 100 /data/  create 100 peers config files data path is /data/')
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
        try:
            cnt = int(argv[1])
            path = argv[2] if len(argv) >= 3 else None
        except:
            printHelp()
            sys.exit(2)
        mkBeeDataFiles(nodeCount=cnt,dataPath=path)
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
    elif argv[0] in base_cmd[3]:
        #help
        printHelp()


if __name__ == '__main__':
    main(sys.argv[1:])
