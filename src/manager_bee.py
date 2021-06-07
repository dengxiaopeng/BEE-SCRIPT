#! /usr/bin/python3
import os
import sys
from pathlib import Path
import requests

if __package__ is None:                  
    DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(DIR.parent))
    __package__ = DIR.name

from .run_bee import getYamls


def printHelp():
    print('Usage manager_bee.py [PATH] [OPTION]')
    print()
    print('  -p, --peers      show PATH connect peers')
    print()
    print('Examples:')
    print('  manager_bee.py A.json -p  query A.json all node connect peers count')
    print()
    print('Author:')
    print(' Fish Deng')


def getDebugApi(configFile):
    ret = []
    bees = getYamls(configFile)
    for bee in bees['peers']:
        ret.append(bee['debug-api-addr'])
    return ret


def peers(configFile):
    debugApi = getDebugApi(configFile)
    ret = {}
    peers_url = "http://%s/peers"
    for api in debugApi:
        try:
            rep = requests.get(peers_url % api)
            ret[api] = len(rep.json()['peers'])
        except:
            ret[api] = 0
    print(ret)


def main(argv):
    if len(argv) < 2:
        printHelp()
        sys.exit(2)
    if not os.path.exists(argv[0]):
        printHelp()
        sys.exit(2)
    base_cmd = [
        ('-p','--peers'),
    ]
    if argv[1] in base_cmd[0]:
        #peers
        peers(argv[0])

if __name__ == '__main__':
    main(sys.argv[1:])
    