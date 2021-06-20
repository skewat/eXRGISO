import json
import re
import os

class ELF:
	def __init__(self, name, path, md5, instance, card):
		self.name = name
		self.path = path
		self.md5 = md5
		self.card = card
		self.instance = instance

	@classmethod
	def from_path(cls, path, md5):
		parts = None
		if 'opt/cisco/calvados/packages/' in path:
			parts = re.split(r'opt/cisco/calvados/packages/', path)[-1].split('/')
		elif 'opt/cisco/XR/packages' in path:
			parts = re.split(r'opt/cisco/XR/packages/', path)[-1].split('/')
		else:
			logging.debug(path+' - Failed to create ELF object.')
		if parts == None:
			return None
		rpm = parts[0]
		card = parts[1]
		instance = None
		if parts[2] == 'instances':
			instance = parts[3]
		name = parts[-1]
		return ELF(name, path, md5, instance, card)
		


def load_json(json_file):
	data = None
	with open(json_file, 'r') as jf:
		data = json.load(jf)
	return data
'''
<libxp.so> ----> <INSTANCE-NAME 1>
	   |
	   |---> <INSTANCE-NAME 2> ----> <ELF> ---- > ELF object
				   |
				   |---> <affected> -----> <ELF.path> ---- > ELF object
				   		    |----> <ELF.path> ---- > ELF object


'''

def build_affects(json_data):
	affected_dict = {}
	for k in json_data.keys():
		executable = ELF.from_path(json_data[k]['path'], json_data[k]['md5'])
		for so in json_data[k]['deps']:
			shared_obj = ELF.from_path(so['path'], so['md5']) 
			if shared_obj.name not in affected_dict:
				affected_dict[shared_obj.name] = {}
			if shared_obj.instance not in affected_dict[shared_obj.name]:
				affected_dict[shared_obj.name][shared_obj.instance] = {}
				affected_dict[shared_obj.name][shared_obj.instance]['ELF'] = shared_obj
				affected_dict[shared_obj.name][shared_obj.instance]['affected'] = {}
			
			affected_dict[shared_obj.name][shared_obj.instance]['affected'][executable.path] = executable
	return affected_dict
			
def get_reference_table(json_path):
	json_path = os.path.abspath(json_path)
	data = load_json(json_path)['info']
	return build_affects(data)
