import yaml
import requests
import os
import shutil
import sys
from GLOBAL import *


def getPublicIp():
    insideUrl = "http://ip.42.pl/raw"
    outsideUrl = "http://ifconfig.me/ip"
    
    try:
        ipAddress = requests.get(insideUrl,timeout=2)
        return ipAddress.text
    except Exception:
        ipAddress = requests.get(outsideUrl,timeout=2)
        return ipAddress.text


def mkBeeDataFiles(nodeCount:int):
    raw_yaml = os.path.join(CONF_PATH,'bee.yaml')
    if not os.path.exists(raw_yaml):
        print("check ../conf/bee.yaml is exits?")
        return
    shutil.rmtree(YAMLS_PATH)
    with open(raw_yaml,encoding='utf-8') as f:
        temp = yaml.load(f.read(),Loader=yaml.FullLoader)
        api_addr = 1633
        p2p_addr = 1634
        debug_api_addr = 1635
        dataDir = '/data/data/'
        nat_addr = getPublicIp() + ':'
        gap = 10
        if not os.path.exists(YAMLS_PATH):os.mkdir(YAMLS_PATH)
        
        for i in range(nodeCount):
            temp['api-addr'] = ':'+str(api_addr + i*gap)
            temp['config'] = dataDir + 'bee'+str(i)+'/'+ 'bee.yaml'
            temp['data-dir'] = dataDir + 'bee'+str(i)
            temp['p2p-addr'] = ':'+str(p2p_addr + i*gap)
            temp['debug-api-addr'] = '127.0.0.1:'+str(debug_api_addr + i*gap)
            temp['nat-addr'] = nat_addr + str(p2p_addr + i*gap)
            temp['welcome-message'] = "dpbee" + "%03d"%(i)
            output_path = os.path.join(YAMLS_PATH,'bee'+str(i)+'.yaml')
            with open(output_path,mode='w',encoding='utf-8') as b:
                yaml.dump(temp,b)
            print(temp)
            print()
    print("finish generate %d yamls"%(nodeCount))
    

def startBees():
    if not os.path.exists(YAMLS_PATH):
        print('create conf file frist.')
        return
    yamls = []
    for y in os.listdir(YAMLS_PATH):
        if y.endswith('.yaml'):
            yamls.append(os.path.join(YAMLS_PATH,y))
    if len(yamls) == 0:
        print('init conf file frist.')
        return
    bee_sh = "nohup bee start --config {config_file:s} >> {output_file:s} 2>&1 < /dev/null & echo $! > {pidfile:s}"
    
    for bee in yamls:
        temp = open(bee,encoding='utf-8')
        bee_yaml = yaml.load(temp.read(),Loader=yaml.FullLoader)
        temp.close()
        config_file = bee_yaml['config']
        data_dir = bee_yaml['data-dir']
        output_file = data_dir + '/output.log'
        pidfile = data_dir + '/pid.txt'
        if not os.path.exists(data_dir): os.mkdir(data_dir)
        shutil.copy(bee,config_file)
        excute_bee_sh = bee_sh.format(config_file=config_file,output_file=output_file,pidfile=pidfile)
        ret = os.popen(excute_bee_sh)
        print(excute_bee_sh)
        print(ret.read())
        print(config_file)
        print()
        ret.close()

    print("start bee %d all"%(len(yamls)))


def printHelp():
    print('Usage run_bee.py [OPTION]')
    print()
    print('  -c, --create\tcreate N peers conf')
    print('  -s, --start\tstart all peers')
    print()
    print('Examples:')
    print('  run_bee.py -c 100\tcreate 100 peers config files')
    print()
    print('Author:')
    print(' Fish Deng')



def main(argv):
    import getopt
    try:
        opts, args = getopt.getopt(argv,"hc:s",["help","create","start"])
    except getopt.GetoptError:
        printHelp()
        sys.exit(1)
    if len(opts) == 0:
        printHelp()
        sys.exit()
    for opt,arg in opts:
        if opt in ('-h','--help'):
            printHelp()
            sys.exit()
        elif opt in ('-c','--create'):
            try:
                arg = int(arg)
                mkBeeDataFiles(arg)
            except:
                printHelp()
                sys.exit(2)
        elif opt in ('-s','--create'):
            startBees()


if __name__ == '__main__':
    main(sys.argv[1:])
