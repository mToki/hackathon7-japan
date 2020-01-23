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

def test():
  tg = ops.TreeGenerator()
  tg.set_vdisks(vdisk_json)
  tg.set_stats(stats_json)
  tg.set_vms(vms_json)
  tg.set_pds(pds_json)
  (success, trd) = tg.create_tree()
  trd.join()

  tree = tg.get_tree()
  print(json.dumps(tree, indent=2))
  print(len(tree['children']))

  with open('test_out_tree.json', 'w') as fout:
    fout.write(json.dumps(tree, indent=2))

  '''
  (success, chains) = tg.get_vm_vdisk_chains('9c2cd24e-5346-474c-b17d-e835cb00f7c1')
  if success:
    ...
    #print(json.dumps(chains, indent=2))
  else:
    print(chains)

  (success, pd_chains) = tg.get_pd_vdisk_chains('tttt')
  if success:
    print(json.dumps(pd_chains, indent=2))
  else:
    print(chains)
  '''

if __name__ == '__main__':
  test()