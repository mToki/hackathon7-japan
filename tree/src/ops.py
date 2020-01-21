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

    self.creating = False
    self.vdisk_table = None
    self.stats_table = None
    self.vm_table = None
    self.pd_table = None
    self.tree = {}

  def get_tree(self):
    return self.tree

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

    # create root of tree dict and child mapping
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

    # create tree recursively
    depth = 1
    current = int(datetime.datetime.now().timestamp() * 1000 * 1000)
    for vdisk_id, tree_node in roots.items():
      self.add_child_tree(vdisk_id, tree_node, childs_dict, 
        vdisk_table, stats_table, vm_table, depth, current)

    # update
    self.tree = roots
    self.vdisk_table = vdisk_table
    self.stats_table = stats_table
    self.vm_table = vm_table
    self.pd_table = pd_table


  def add_child_tree(self, vdisk_id, node, childs_dict, 
    vdisk_table, stats_table, vm_table, depth, current):

    #print(vdisk_id)
    try:
      stats_dict = stats_table.get(Query().vdisk_id==vdisk_id)
      sum_user_bytes = int(stats_dict['user_bytes'])
    except:
      sum_user_bytes = 0
    num_descendant = 0

    for child in childs_dict.get(vdisk_id, []):
      node[child] = {}
      (nd, sub) = self.add_child_tree(child, node[child], childs_dict,
        vdisk_table, stats_table, vm_table, depth+1, current)
      num_descendant += nd
      sum_user_bytes += sub

    self.update_tables(vdisk_id, node, childs_dict, vdisk_table, 
      stats_table, vm_table, depth, current, num_descendant, sum_user_bytes)

    return (num_descendant + 1, sum_user_bytes)

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

    '''
    node['depth'] = depth
    node['num_childs'] = len(childs_dict.get(vdisk_id, []))

    # vdisk
    vdisk_dict = vdisk_table.get(Query().vdisk_id==vdisk_id)
    node['vdisk_name'] = vdisk_dict.get('vdisk_name', '')
    node['vdisk_uuid'] = vdisk_dict.get('vdisk_uuid', '')
    node['vdisk_size'] = vdisk_dict['vdisk_size']
    node['parent_vdisk_id'] = vdisk_dict.get('parent_vdisk_id', '')
    node['to_remove'] = vdisk_dict.get('to_remove', False)
    node['is_leaf'] = vdisk_id not in childs_dict

    # stats
    
    if stats_dict:
      node['user_bytes'] = stats_dict.get('user_bytes', '?')
      node['inherited_user_bytes'] = stats_dict.get('inherited_user_bytes', '?')
    else:
      node['user_bytes'] = '??'
      node['inherited_user_bytes'] = '??'
    try:
      node['user_bytes_friendly'] = '{:,}'.format(node['user_bytes'])
    except:
      node['user_bytes_friendly'] = node['user_bytes']
    try:
      node['inherited_user_bytes_friendly'] = '{:,}'.format(node['inherited_user_bytes'])
    except:
      node['inherited_user_bytes_friendly'] = node['inherited_user_bytes']

    # vm
    vm_dict = vm_table.get(Query().vdisk_names.any([node['vdisk_name']]))
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
    node['no_modification_usec'] = current - last
    td = datetime.timedelta(seconds=(node['no_modification_usec']/1000000))
    node['no_modification_time'] = str(td)

    # childs
    num_descendant = 0
    node['child_disks'] = {}
    try:
      user_bytes = int(node['user_bytes'])
    except:
      user_bytes = 0

    node['num_descendant'] = num_descendant
    node['sum_user_bytes_descendant'] = user_bytes
    node['sum_user_bytes_descendant_friendly'] = '{:,}'.format(user_bytes)
    '''

    

def convert_tree(tree):
  return tree