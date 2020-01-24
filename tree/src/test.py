import json
import ops

# vdisk_config_printer
with open('test_vdisk.json', 'r') as fin:
  vdisk_json = json.loads(fin.read())

# stats_tool -stats_type=vdisk_usage
with open('test_stats.json', 'r') as fin:
  stats_json = json.loads(fin.read())

# ncli vm ls --json=true
with open('test_vm.json', 'r') as fin:
  vms_json = json.loads(fin.read())

with open('test_pd.json', 'r') as fin:
  pds_json = json.loads(fin.read())

def build():
  tg = ops.TreeGenerator()
  tg.set_vdisks(vdisk_json)
  tg.set_stats(stats_json)
  tg.set_vms(vms_json)
  tg.set_pds(pds_json)
  (success, trd) = tg.create_tree()
  trd.join()
  return tg

def test_tree():
  tg = build()
  tree = tg.get_tree()
  print()
  print(len(tree['children']))

  with open('test_out_tree.json', 'w') as fout:
    fout.write(json.dumps(tree, indent=2))

def test_stats():
  sum = 0
  for i in stats_json:
    sum += i['user_bytes']
  print('{:,}'.format(sum))

def test_vdisk_chain():
  tg = build()
  hierarcy = tg.get_vdisk_chanins(8133218)
  print(hierarcy)

if __name__ == '__main__':
  test_vdisk_chain()