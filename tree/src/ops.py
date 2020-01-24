import copy
import json
import datetime
import threading
import traceback
# Please use Mongo in Production. Tiny DB is easy, but very Slow.
from tinydb import TinyDB, Query  
from tinydb.storages import MemoryStorage

class TreeGenerator:
  def __init__(self):
    self.vdisk_list = []
    self.stats_list = []
    self.vm_list = []
    self.pd_list = []
    self.rs_list = []

    self.vdisk_dict = {}
    self.vm_dict = {}
    self.pd_dict = {}
    self.rs_dict = {}

    self.creating = False
    self.vdisk_table = None
    self.stats_table = None
    self.vm_table = None
    self.pd_table = None
    self.rs_table = None
    self.tree = {}

  def prune_depth(self, node, depth, max_depth):
    if depth > max_depth:
      node['name'] = f'{node["vdisk_id"]}:{node["size_all"]}...'
      node['size'] = node['size_all']
      node['children'] = []
      return
    for child_node in node['children']:
      self.prune_depth(child_node, depth+1, max_depth)

  def get_node(self, node, vdisk_id):
    if node['vdisk_id'] == vdisk_id:
      return node
    for child_node in node['children']:
      result = self.get_node(child_node, vdisk_id)
      if result is not None:
        return result
    return None

  def get_tree(self):
    tree = copy.deepcopy(self.tree)
    self.prune_depth(tree, 0, 3)
    return tree

  def get_tree_vdisk_id(self, vdisk_id):
    tree = copy.deepcopy(self.tree)
    d = {
      'name':'',
      'vdisk_id':'',
      'size':0,
      'size_all':0,
      'to_remove':False,
      'source_cluster':'',
      'children': []
    }
    node = self.get_node(tree, vdisk_id)
    if node is not None:
      d['children'].append(node)
      d['name'] = self.get_friendly_size(node['size_all'])
    return d

  def get_pd_vdisk_chains(self, pd_name):
    if self.pd_table is None:
      return (False, '')
    pd_dict = self.pd_table.get(Query().name==pd_name)
    if pd_dict is None:
      return (False, '')

    pd_vm_chains = []
    for vm in pd_dict['vms']:
      vm_id = vm['vm_id']
      (success, chains) = self.get_vm_vdisk_chains(vm_id)
      if not success:
        return (False, chains)
      vm_dict = self.vm_table.get(Query().uuid==vm_id)
      d = {
        'vm_uuid': vm_id,
        'vm_name': vm_dict['vmName'],
        'chains':  chains
      }
      pd_vm_chains.append(d)

    return (True, pd_vm_chains)

  def get_vdisk_hierarchy(self, vdisk_id):
    try:
      if self.vdisk_table is None:
        return (False, 'vdisk_table is not ready')

      vdisk_stack = []
      while True:
        vdisk_dict = self.vdisk_table.get(Query().vdisk_id==vdisk_id)
        if vdisk_dict is None:
          return (False, f'unable to find vdisk_uuid:{vdisk_id}')
        vdisk_stack.append(vdisk_dict)
        parent_id = vdisk_dict.get('parent_vdisk_id', '')
        if parent_id == '':
          break
        vdisk_id = parent_id

      vdisk_hierarcy = {}
      d = vdisk_hierarcy
      while len(vdisk_stack) != 0:
        vdisk_dict = vdisk_stack.pop()
        size = vdisk_dict['user_bytes']
        fsize = self.get_friendly_size(size)
        vm_name = vdisk_dict['vm_name']
        if vm_name != '':
          d['name'] = f'{vdisk_dict["vdisk_id"]}:{vm_name}:{fsize}'
        else:
          d['name'] = f'{vdisk_dict["vdisk_id"]}:{fsize}'
        d['size'] = size
        d['children'] = []
        if len(vdisk_stack) != 0:
          d2 = {}
          d['children'].append(d2)
          d = d2
      return (True, vdisk_hierarcy)

    except:
      print(traceback.format_exc()) 
      return (False, 'error')

  def get_vm_vdisk_chains(self, vm_uuid):
    if self.vdisk_table is None:
      return (False, 'vdisk_table is not ready')
    if self.vm_table is None:
      return (False, 'vm_table is not ready')

    vm_dict = self.vm_table.get(Query().uuid==vm_uuid)
    if vm_dict is None:
      return (False, f'unable to find vm with uuid:{vm_uuid}')

    chains = []
    for vdisk_name in vm_dict['vdisk_names']:
      chain = []
      vdisk_dict = self.vdisk_table.get(Query().vdisk_name==vdisk_name)
      vdisk_id = vdisk_dict['vdisk_id']
      while True:
        vdisk_dict = self.vdisk_table.get(Query().vdisk_id==vdisk_id)
        parent_id = vdisk_dict.get('parent_vdisk_id', '')
        if parent_id == '':
          break
        chain.append(vdisk_dict)
        vdisk_id = parent_id
      chains.append(chain)

    return (True, chains)

  def set_vdisks(self, vdisks):
    self.vdisk_list = vdisks

  def set_stats(self, stats):
    self.stats_list = stats

  def set_vms(self, vms):
    self.vm_list = vms

  def set_pds(self, pds):
    self.pd_list = pds

  def create_tree(self):
    print('create_tree()')
    if [] in [self.vdisk_list, self.stats_list, 
      self.vm_list, self.pd_list, self.creating]:
      return (False, None)

    t = threading.Thread(target=self.create_tree2)
    t.start()
    return (True, t)

  def create_tree2(self):
    print('create_tree2()')
    try:
      self.creating = True
      self.create_tree3()
    except Exception as e:
      print(traceback.format_exc()) 
    self.creating = False

  def create_tree3(self):
    print('create_tree3()')
    db = TinyDB(storage=MemoryStorage)
    vdisk_table = db.table('vdisk')
    vdisk_table.insert_multiple(self.vdisk_list)
    stats_table = db.table('stats')
    stats_table.insert_multiple(self.stats_list)
    vm_table = db.table('vm')
    vm_table.insert_multiple(self.vm_list)
    pd_table = db.table('pd')
    pd_table.insert_multiple(self.pd_list)

    # D3JS heirarcy format
    root = {
      'name':'dummy',
      'vdisk_id':'',
      'size':0,
      'size_all':0,
      'to_remove':False,
      'source_cluster':'',
      'children': []
    }
    root_vdisks = []
    childs_dict = {}
    for vdisk in vdisk_table:
      vdisk_id = vdisk['vdisk_id']
      if 'parent_vdisk_id' not in vdisk:
        root_vdisks.append(vdisk_id)
        continue

      parent_vdisk_id = vdisk['parent_vdisk_id']
      child_vdisk_id = vdisk_id
      if parent_vdisk_id in childs_dict:
        childs_dict[parent_vdisk_id].append(child_vdisk_id)
      else:
        childs_dict[parent_vdisk_id] = [child_vdisk_id]

    # create tree recursively
    depth = 1
    current = int(datetime.datetime.now().timestamp() * 1000 * 1000)
    for vdisk_id in root_vdisks:
      node = {}
      root['children'].append(node)
      self.add_child_tree(vdisk_id, node, childs_dict, 
        vdisk_table, stats_table, vm_table, depth, current)

    # remove size0 and no child vdisk
    source_cluster_dict = {}
    self.prune(root, 1, source_cluster_dict)

    # update
    self.tree = root
    self.vdisk_table = vdisk_table
    self.stats_table = stats_table
    self.vm_table = vm_table
    self.pd_table = pd_table

  def prune(self, node, depth, source_cluster_dict):
    '''
    if depth > 5:
      return False
    '''

    alive_children = []
    for child_node in node['children']:
      alive = self.prune(child_node, depth+1, source_cluster_dict)
      if alive:
        alive_children.append(child_node)
    node['children'] = alive_children

    if node['to_remove'] and len(node['children']) == 0:
      return False

    source_cluster = node['source_cluster']
    if source_cluster != '':
      sum_size = source_cluster_dict.get(source_cluster, 0)
      source_cluster_dict[source_cluster] = sum_size + node['size']

    if node['size'] != 0:
      return True
    if len(node['children']) > 0:
      return True
    return False


  def add_child_tree(self, vdisk_id, node, childs_dict, 
    vdisk_table, stats_table, vm_table, depth, current):

    #print(vdisk_id)
    try:
      stats_dict = stats_table.get(Query().vdisk_id==vdisk_id)
      sum_user_bytes = int(stats_dict['user_bytes'])
    except:
      sum_user_bytes = 0
    num_descendant = 0

    node['children'] = []
    for child_vdisk_id in childs_dict.get(vdisk_id, []):
      child_node = {}
      node['children'].append(child_node)
      (nd, sub) = self.add_child_tree(child_vdisk_id, child_node, childs_dict,
        vdisk_table, stats_table, vm_table, depth+1, current)
      num_descendant += nd
      sum_user_bytes += sub

    (size, vm_name, to_remove, source_cluster) = self.update_tables(vdisk_id, node, childs_dict, 
      vdisk_table, stats_table, vm_table, depth, current, 
      num_descendant, sum_user_bytes)

    node['vdisk_id'] = int(vdisk_id)
    node['size'] = int(size)
    node['size_all'] = sum_user_bytes
    node['vm_name'] = vm_name
    node['source_cluster'] = source_cluster
    node['to_remove'] = to_remove
    size = self.get_friendly_size(node['size'])
    if vm_name == '':
      node['name'] = f'{vdisk_id}:{size}'
    else:
      node['name'] = f'{vdisk_id}:{vm_name}:{size}'

    return (num_descendant + 1, sum_user_bytes)

  def get_friendly_size(self, bytesize):
    def roundstr(size):
      return str(round(size, 1))

    if bytesize < 1024:
      return str(bytesize) + 'Bytes'
    elif bytesize < 1024 ** 2:
      return roundstr(bytesize / 1024.0) + 'KB'
    elif bytesize < 1024 ** 3:
      return roundstr(bytesize / (1024.0 ** 2)) + 'MB'
    elif bytesize < 1024 ** 4:
      return roundstr(bytesize / (1024.0 ** 3)) + 'GB'
    elif bytesize < 1024 ** 5:
      return roundstr(bytesize / (1024.0 ** 4)) + 'TB'
    else:
      return str(bytesize) + 'Bytes'


  def update_tables(self, vdisk_id, node, childs_dict, vdisk_table, 
    stats_table, vm_table, depth, current, num_descendant, sum_user_bytes):

    vdisk_original = vdisk_table.get(Query().vdisk_id==vdisk_id)
    vdisk_name = vdisk_original.get('vdisk_name', '')
    last = int(vdisk_original['last_modification_time_usecs'])
    no_modification_time_usec = current - last

    vdisk_update = {
      # vdisk
      'vdisk_name': vdisk_name,
      'vdisk_uuid': vdisk_original.get('vdisk_uuid', ''),
      'parent_vdisk_id': vdisk_original.get('parent_vdisk_id', ''),
      'to_remove': vdisk_original.get('to_remove', False),
      'is_leaf': vdisk_id not in childs_dict,
      'originating_cluster_id':vdisk_original.get('originating_cluster_id', ''),
      'originating_cluster_incarnation_id':vdisk_original.get('originating_cluster_incarnation_id', ''),
      'originating_vdisk_id':vdisk_original.get('originating_vdisk_id', ''),

      # new
      'depth': depth,
      'num_child': len(childs_dict.get(vdisk_id, [])),
      'num_descendant': num_descendant,
      'sum_descendant_user_bytes': sum_user_bytes,
      'no_modification_time_usec': no_modification_time_usec,
      'no_modification_time': str(datetime.timedelta(seconds=(no_modification_time_usec/1000000)))
    }
    stats_dict = stats_table.get(Query().vdisk_id==vdisk_id)
    if stats_dict is not None:
      vdisk_update['user_bytes'] = int(stats_dict.get('user_bytes', '0'))
      vdisk_update['inherited_user_bytes'] = int(stats_dict.get('inherited_user_bytes', '0'))
    else:
      vdisk_update['user_bytes'] = 0
      vdisk_update['inherited_user_bytes'] = 0

    vm_dict = vm_table.get(Query().vdisk_names.any([vdisk_name]))
    if vm_dict is not None:
      vdisk_update['is_vm'] = True
      vdisk_update['vm_name'] = vm_dict['vmName']
      vdisk_update['vm_uuid'] = vm_dict['uuid']
      vdisk_update['vm_power_state'] = vm_dict['powerState']
    else:
      vdisk_update['is_vm'] = False
      vdisk_update['vm_uuid'] = ''
      vdisk_update['vm_name'] = ''
      vdisk_update['vm_power_state'] = ''
    vdisk_table.update(vdisk_update, Query().vdisk_id==vdisk_id)

    return (vdisk_update['user_bytes'], vdisk_update['vm_name'],
      vdisk_update['to_remove'], vdisk_update['originating_cluster_id'])
    

def convert_tree(tree):
  return tree