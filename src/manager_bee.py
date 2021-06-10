#! /usr/bin/python3
import os
import sys
import json
from pathlib import Path
import requests

if __package__ is None:                  
    DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(DIR.parent))
    __package__ = DIR.name


try:
    from .run_bee import *
except:
    from run_bee import *


def printHelp():
    print('Usage manager_bee.py [PATH] [OPTION]')
    print()
    print('  -p, --peers                show PATH connect peers')
    print('  -l, --listAllUncashed      show all uncashed peers')
    print('  -ca, --cashoutall          cashout all peers')
    print('  -h, --help                 show this page')
    print()
    print('Examples:')
    print('  manager_bee.py A.json -p  query A.json all node connect peers count')
    print()
    print('Author:')
    print(' Fish Deng')


def getDebugApi(configFile):
    ret = []
    allBees = getYamls(configFile)
    for bees in allBees:
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
    print(json.dumps(ret,indent=4))
    return ret


def getChequePeers(debugApi):
    all_peers_url = "http://%s/chequebook/cheque"
    ret = {}
    for api in debugApi:
        try:
            rep = requests.get(all_peers_url % api)
            ret[api] = [ch["peer"] for ch in rep.json()['lastcheques']]
        except:
            ret[api] = []
    return ret


def listAllUncashed(configFile):
    debugApi = getDebugApi(configFile)
    apiPeers = getChequePeers(debugApi)
    get_uncashed_amount = "http://{}//chequebook/cashout/{}"
    ret = []
    cnt = 0
    totalAmount = 0
    for api in apiPeers:
        peers = apiPeers[api]
        for p in peers:
            try:
                rep = requests.get(get_uncashed_amount.format(api,p))
                amount = rep.json()['uncashedAmount']
                ret.append((p,amount))
                cnt += 1
                totalAmount += amount
            except:
                ret.append((p,0))
    print(json.dumps(ret,indent=4))
    print("has {} uncashed cheque,total amount {}".format(cnt,totalAmount))
    return ret


def cashoutall(configFile):
    debugApi = getDebugApi(configFile)
    apiPeers = getChequePeers(debugApi)
    cashout_url = "http://{}//chequebook/cashout/{}"
    ret = []
    for api in apiPeers:
        peers = apiPeers[api]
        for p in peers:
            try:
                rep = requests.post(cashout_url.format(api,p))
                ret.append((p,rep.json()['transactionHash']))
            except:
                pass
    print(json.dumps(ret,indent=4))
    print("cashout {} cheques.".format(len(ret)))
    return ret


def main(argv):
    if len(argv) < 2:
        printHelp()
        sys.exit(2)
    if not os.path.exists(argv[0]):
        printHelp()
        sys.exit(2)
    base_cmd = [
        ('-p','--peers'),
        ('-l','--listAllUncashed'),
        ('-ca','--cashoutall'),
    ]
    if argv[1] in base_cmd[0]:
        #peers
        peers(argv[0])
    elif argv[1] in base_cmd[1]:
        #listAllUncashed
        listAllUncashed(argv[0])
    elif argv[1] in base_cmd[2]:
        #cashoutall
        cashoutall(argv[0])
    else:
        #help
        printHelp()


if __name__ == '__main__':
    main(sys.argv[1:])
    