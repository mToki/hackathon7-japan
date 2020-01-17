import json

def write_json(fname, d):
  with open(fname, 'w') as f:
    f.write(json.dumps(d, indent=4))

def main():
  lines = get_lines()
  vdisk_dict = get_vdisk_dict(lines)
  write_json('vdisk.json', vdisk_dict)
  #vm_dict = get_vm_dict(vdisk_dict)
  tree = get_tree(vdisk_dict)
  write_json('tree.json', tree)

def get_lines():
  with open('vdiskconfigprinter', 'r') as fin:
    lines = fin.readlines()
  lines = list(map(lambda x: x.strip(), lines))
  return lines

def get_vdisk_dict(lines):
  vdisk_dict = {}
  vdiskid = ''
  d = {}
  for line in lines:
    if line == '':
      if vdiskid != '':
        vdisk_dict[vdiskid] = d
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
  return vdisk_dict

def get_vm_dict(vdisk_dict):
  with open('nclivmls', 'r') as fin:
    vm_list = json.loads(fin.read())['data']
  write_json('vm.json', vm_list)

  uuid2id = {}
  for key, value in vdisk_dict.items():
    found = False

    if 'vdisk_uuid' in value:
      uuid2id[value['vdisk_uuid']] = key
      found = True
    if 'nfs_file_name' in value:
      uuid2id[value['nfs_file_name']] = key
      found = True
    if value.get('to_remove', False):
      continue
    if not found:
      raise Exception()

  vm_dict = {}
  for vm in vm_list:
    if vm.get("controllerVm", False):
      continue
    uuids = vm['nutanixVirtualDiskUuids']
    for uuid in uuids:
      vdiskid = uuid2id[uuid]
      vm_dict[vdiskid] = vm
  print(vm_dict)

  print(uuid2id)

def get_tree(vdisk_dict):
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
    node['vdisk_size'] = vdisk_dict[vdiskid]['vdisk_size']
    node['parent_vdisk_id'] = vdisk_dict[vdiskid].get('parent_vdisk_id', '')
    node['is_leaf'] = vdiskid not in childs_dict
    node['child_disks'] = {}
    for child in childs_dict.get(vdiskid, []):
      node['child_disks'][child] = {}
      add_child_tree(child, node['child_disks'][child])
  for key, value in roots.items():
    add_child_tree(key, value)
  return roots

main()