import json
import datetime
# Please use Mongo in Production. Tiny DB is easy, but very Slow.
from tinydb import TinyDB, Query  
from tinydb.storages import MemoryStorage

with open('vdiskconfigprinter', 'r') as fin:
  VDISK_CONFIG_PRINTER = fin.read()

with open('statstool', 'r') as fin:
  STATS_TOOL = fin.read()

with open('nclivmls', 'r') as fin:
  NCLI_VM_LS_JSON = fin.read()

def write_json(fname, d):
  with open(fname, 'w') as f:
    f.write(json.dumps(d, indent=4))

def main():
  db = TinyDB(storage=MemoryStorage)
  vdisk_table = db.table('vdisk')
  vdisk_table.insert_multiple(get_vdisk_list(VDISK_CONFIG_PRINTER))
  stats_table = db.table('stats')
  stats_table.insert_multiple(get_stats_list(STATS_TOOL))
  vm_table = db.table('vm')
  vm_table.insert_multiple(get_vm_list(NCLI_VM_LS_JSON))
  tree_dict = get_tree_dict(vdisk_table, stats_table, vm_table)

  write_json('vdisk.json', vdisk_table.all())
  write_json('stats.json', stats_table.all())
  write_json('vm.json', vm_table.all())
  write_json('tree.json', tree_dict)

def get_vdisk_list(text):
  lines = text.splitlines()
  lines = list(map(lambda x: x.strip(), lines))
  vdisk_list = []
  d = {}
  for line in lines:
    if line == '':
      if d != {}:
        vdisk_list.append(d)
      d = {}
      continue
    words = line.split(': ')
    if len(words) != 2:
      continue
    words[1] = words[1].replace('"', '')
    d[words[0]] = words[1]
  if d != {}:
    vdisk_list.append(d)
  return vdisk_list

def get_stats_list(text):
  lines = text.splitlines()
  lines = list(map(lambda x: x.strip(), lines))
  stats_list = []
  d = {}
  tier_usage_list = {}
  flag_tier_usage_list = False
  for line in lines:
    if line == '':
      continue
    if line.startswith('Stats key:'):
      if d != {}:
        d['tier_usage_list'] = tier_usage_list
        stats_list.append(d)
      d = {
        'vdisk_id':line.split(': ')[1]
      }
      tier_usage_list = {}
      continue
    if line.startswith('tier_usage_list {'):
      flag_tier_usage_list = True
      continue
    if line.startswith('}'):
      flag_tier_usage_list = False
      continue
    words = line.split(': ')
    key = words[0].strip()
    value = words[1].strip().replace('"', '')
    if flag_tier_usage_list:
      tier_usage_list[key] = value
    else:
      d[key] = value
  if d != {}:
    d['tier_usage_list'] = tier_usage_list
    stats_list.append(d)
  return stats_list

def get_vm_list(text):
  vm_list = json.loads(text)['data']
  for vm in vm_list:
    if 'vdiskNames' not in vm:
      vm['vdisk_names'] = []
      continue
    vdisk_names = []
    for vdiskname in vm['vdiskNames']:
      words = vdiskname.split('::')
      vdisk_names.append(words[1])
    vm['vdisk_names'] = []
  return vm_list

def get_tree_dict(vdisk_table, stats_table, vm_table):
  roots = {}
  childs_dict = {}
  for vdisk in vdisk_table:
    vdisk_id = vdisk['vdisk_id']
    if 'parent_vdisk_id' not in vdisk:
      roots[vdisk_id] = {}
      continue
    parent_vdisk_id = vdisk['parent_vdisk_id']
    child_vdisk_id = vdisk_id
    if parent_vdisk_id in childs_dict:
      childs_dict[parent_vdisk_id].append(child_vdisk_id)
    else:
      childs_dict[parent_vdisk_id] = [child_vdisk_id]

  now = int(datetime.datetime.now().timestamp() * 1000 * 1000)
  def add_child_tree(vdisk_id, node):
    # vdisk
    vdisk_dict = vdisk_table.get(Query().vdisk_id==vdisk_id)
    node['vdisk_name'] = vdisk_dict.get('vdisk_name', '')
    node['vdisk_uuid'] = vdisk_dict.get('vdisk_uuid', '')
    node['vdisk_size'] = vdisk_dict['vdisk_size']
    node['parent_vdisk_id'] = vdisk_dict.get('parent_vdisk_id', '')
    node['to_remove'] = vdisk_dict.get('to_remove', False)
    node['is_leaf'] = vdisk_id not in childs_dict

    # stats
    stats_dict = stats_table.get(Query().vdisk_id==vdisk_id)
    if stats_dict:
      node['user_bytes'] = stats_dict.get('user_bytes', '?')
      node['inherited_usage_bytes'] = stats_dict.get('user_bytes', '?')
    else:
      node['user_bytes'] = '??'
      node['inherited_usage_bytes'] = '??'
    try:
      node['user_bytes_friendly'] = '{:,}'.format(int(node['user_bytes']))
    except:
      node['user_bytes_friendly'] = node['user_bytes']
    try:
      node['inherited_usage_bytes_friendly'] = '{:,}'.format(int(node['inherited_usage_bytes']))
    except:
      node['inherited_usage_bytes_friendly'] = node['inherited_usage_bytes']

    # vm
    vm_dict = vm_table.get(Query().vdisk_names.any([vdisk_id]))
    if vm_dict:
      node['is_vm'] = True
      node['vm_name'] = vm_dict['vmName']
      node['vm_uuid'] = vm_dict['uuid']
      node['vm_power_state'] = vm_dict['powerState']
    else:
      node['is_vm'] = False
      node['vm_uuid'] = ''
      node['vm_name'] = ''
      node['vm_power_state'] = ''

    # time
    last = int(vdisk_dict['last_modification_time_usecs'])
    node['no_modification_usec'] = now - last
    td = datetime.timedelta(seconds=(node['no_modification_usec']/1000000))
    node['no_modification_time'] = str(td)

    # childs
    node['child_disks'] = {}
    for child in childs_dict.get(vdisk_id, []):
      node['child_disks'][child] = {}
      add_child_tree(child, node['child_disks'][child])

  for key, value in roots.items():
    add_child_tree(key, value)
  prune_targets = set()
  for key, value in roots.items():
    if not value['is_leaf']:
      continue
    if value['vdisk_size'] != '0':
      continue
    if value['user_bytes'] not in ['0', '?', '??']:
      continue
    prune_targets.add(key)
  for target in prune_targets:
    del roots[target]
  return roots

main()