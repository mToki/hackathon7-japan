import json

def write_json(fname, d):
  with open(fname, 'w') as f:
    f.write(json.dumps(d, indent=4))

def main():
  with open('vdiskconfigprinter', 'r') as fin:
    text = fin.read()
  vdisk_dict = get_vdisk_dict(text)
  write_json('vdisk.json', vdisk_dict)

  with open('statstool', 'r') as fin:
    text = fin.read()
  stats_dict = get_stats_dict(text)
  write_json('stats.json', stats_dict)

  with open('nclivmls', 'r') as fin:
    text = fin.read()
  vmvdisk_dict = get_vmvdisk_dict(text)
  write_json('vmvdisk.json', vmvdisk_dict)

  tree_dict = get_tree_dict(vdisk_dict, stats_dict, vmvdisk_dict)
  write_json('tree.json', tree_dict)

def get_stats_dict(text):
  lines = text.splitlines()
  lines = list(map(lambda x: x.strip(), lines))

  stats_dict = {}
  vdisk_id = ''
  d = {}
  tier_usage_list = {}
  flag_tier_usage_list = False
  for line in lines:
    if line == '':
      continue
    if line.startswith('Stats key:'):
      if vdisk_id != '':
        if len(tier_usage_list) != 0:
          d['tier_usage_list'] = tier_usage_list
        stats_dict[vdisk_id] = d
      vdisk_id = line.split(': ')[1]
      d = {}
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
      continue
    d[key] = value

  # last one
  if (vdisk_id != '') and (vdisk_id not in stats_dict):
    if len(tier_usage_list) != 0:
      d['tier_usage_list'] = tier_usage_list
    stats_dict[vdisk_id] = d

  return stats_dict


def get_vdisk_dict(text):
  lines = text.splitlines()
  lines = list(map(lambda x: x.strip(), lines))

  vdisk_dict = {}
  vdiskid = ''
  d = {}
  for line in lines:
    if line == '':
      if vdiskid != '':
        vdisk_dict[vdiskid] = d
      vdiskid = ''
      d = {}
      continue
    words = line.split(': ')
    if len(words) != 2:
      continue
    if words[0] == 'vdisk_id':
      vdiskid = words[1]
      continue
    words[1] = words[1].replace('"', '')
    d[words[0]] = words[1]

  if (vdiskid != '') and vdiskid not in vdisk_dict:
    vdisk_dict[vdiskid] = d

  return vdisk_dict


def get_vmvdisk_dict(text):
  vm_list = json.loads(text)['data']

  vmvdisk_dict = {}
  for vm in vm_list:
    if vm.get("controllerVm", False):
      continue
    if 'vdiskNames' not in vm:
      continue
    d = {}
    d['uuid'] = vm['uuid']
    d['power_state'] = vm['powerState']
    d['name'] = vm['vmName']
    for vdiskname in vm['vdiskNames']:
      words = vdiskname.split('::')
      vmvdisk_dict[words[1]] = d
  return vmvdisk_dict


def get_tree_dict(vdisk_dict, stats_dict, vmvdisk_dict):
  roots = {}
  childs_dict = {}
  for (key, value) in vdisk_dict.items():
    '''
    if value.get('to_remove', False):
      continue
    '''
    if 'parent_vdisk_id' not in value:
      roots[key] = {}
      continue
    parent = value['parent_vdisk_id']
    child = key
    if parent in childs_dict:
      d = childs_dict[parent].append(child)
    else:
      childs_dict[parent] = [child]

  def add_child_tree(vdiskid, node):
    node['vdisk_name'] = vdisk_dict[vdiskid].get('vdisk_name', '')
    if node['vdisk_name'] in vmvdisk_dict:
      node['is_vm'] = True
      node['vm_name'] = vmvdisk_dict[node['vdisk_name']]['name']
    else:
      node['is_vm'] = False
      node['vm_name'] = ''
    node['vdisk_size'] = vdisk_dict[vdiskid]['vdisk_size']
    node['vdisk_size_friendly'] = '{:,}'.format(int(node['vdisk_size']))
    node['parent_vdisk_id'] = vdisk_dict[vdiskid].get('parent_vdisk_id', '')
    node['to_remove'] = vdisk_dict[vdiskid].get('to_remove', False)
    node['is_leaf'] = vdiskid not in childs_dict

    if vdiskid in stats_dict:
      node['user_bytes'] = stats_dict[vdiskid].get('user_bytes', '?')
      node['inherited_usage_bytes'] = stats_dict[vdiskid].get('user_bytes', '?')
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

    node['child_disks'] = {}
    for child in childs_dict.get(vdiskid, []):
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