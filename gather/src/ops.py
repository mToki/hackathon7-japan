import json

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
    if words[1].lower() == 'true':
      words[1] = True
    elif words[1].lower() == 'false':
      words[1] = False
    else:
      try:
        words[1] = int(words[1])
      except:
        ...
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
        'vdisk_id':int(line.split(': ')[1])
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
    try:
      value = int(value)
    except:
      ...
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
    vm['vdisk_names'] = vdisk_names
  return vm_list