import json
import os
import paramiko
import requests
import time
import traceback

import ops

NUTANIX_VIP = os.environ['NUTANIX_VIP']
CVM_USER = os.environ['CVM_USER']
CVM_PASS = os.environ['CVM_PASS']
PRISM_USER = os.environ['PRISM_USER']
PRISM_PASS = os.environ['PRISM_PASS']
TREE_SERVER = os.environ['TREE_SERVER']
TREE_URL = f'http://{TREE_SERVER}/api/v1/tree/'
INTERVAL = int(os.environ['INTERVAL'])
DEBUG = os.environ['DEBUG'].lower() == 'true'

def print_debug(message):
  if not DEBUG:
    return
  print('\n' * 3)
  print(message)

def main():
  while(True):
    try:
      handle_vdisks()
      handle_stats()
      handle_vms()
      handle_pds()
      request_building_tree()
    except Exception as e:
      print(traceback.format_exc())

    count = INTERVAL
    while(count > 1):
      if count % 10 == 0:
        print(f'wait {count} secs')
      count -= 1
      time.sleep(1)

    if DEBUG:
      print('Since debug mode, finish.')
      return

def get_command_result(command):
  client = paramiko.SSHClient()
  client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
  client.connect(NUTANIX_VIP, username=CVM_USER, password=CVM_PASS, timeout=5.0)
  stdin, stdout, stderr = client.exec_command(command)
  result = stdout.read().decode()
  print_debug(result)
  return result


def handle_vdisks():
  result = get_command_result('/usr/local/nutanix/bin/vdisk_config_printer')
  vdisk_list = ops.get_vdisk_list(result)
  json_string = json.dumps(vdisk_list, indent=2)
  print_debug(json_string)
  if not DEBUG:
    requests.put(TREE_URL + 'vdisks/', json_string)


def handle_stats():
  result = get_command_result('/usr/local/nutanix/bin/stats_tool -stats_type=vdisk_usage')
  stats_list = ops.get_stats_list(result)
  json_string = json.dumps(stats_list, indent=2)
  print_debug(json_string)
  if not DEBUG:
    requests.put(TREE_URL + 'stats/', json_string)


def handle_vms():
  result = get_command_result('/usr/local/nutanix/prism/cli/ncli vm ls --json=true')
  vm_list = ops.get_vm_list(result)
  json_string = json.dumps(vm_list, indent=2)
  print_debug(json_string)
  if not DEBUG:
    requests.put(TREE_URL + 'vms/', json_string)


def handle_pds():
  session = requests.Session()
  session.auth = (PRISM_USER, PRISM_PASS)
  session.verify = False                              
  session.headers.update({'Content-Type': 'application/json; charset=utf-8'})
  url = f'https://{NUTANIX_VIP}:9440/PrismGateway/services/rest/v2.0/protection_domains/'
  response = session.get(url)
  if not response.ok:
    print('error at handle_pds()')
  json_string = json.dumps(response.json()['entities'], indent=2)
  print_debug(json_string)
  if not DEBUG:
    requests.put(TREE_URL + 'pds/', json_string)

def handle_remotesites():
  session = requests.Session()
  session.auth = (PRISM_USER, PRISM_PASS)
  session.verify = False                              
  session.headers.update({'Content-Type': 'application/json; charset=utf-8'})
  url = f'https://{NUTANIX_VIP}:9440/PrismGateway/services/rest/v2.0/remote_sites/'
  response = session.get(url)
  if not response.ok:
    print('error at handle_remotesites()')
  json_string = json.dumps(response.json()['entities'], indent=2)
  print_debug(json_string)
  if not DEBUG:
    requests.put(TREE_URL + 'remotesites/', json_string)

def request_building_tree():
  requests.post(TREE_URL)

if __name__ == '__main__':
  main()