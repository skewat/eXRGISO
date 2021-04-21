import logging
import subprocess

def get_deps(card, rpm_list):
	failed = ['libcalvados_ios.so', 'libcm_proto.so', 'libplatform.so', 'libfuse.so.2', 'libdl.so.2', 'libfabric_fapid_hal.so', 'librt.so.1', 'libevent-2.1.so.6', 'libxr_sysctl.so', 'libplatform_pd.so', 'libpq_nodeid.so', 'libnodeid.so', 'libcm_admin_ha_capi.so', 'lib_shmwin_pl_vm.so' ]
	deps = []
	visited = set()
	for rpm in rpm_list:
		for dep in rpm.deps:
			c = dep.elf.card
			if c == card or c == 'all':
				key = get_instance(dep.elf.instance) + dep.elf.name
				if key not in visited:
					"""if dep.elf.name in failed:
						print('Got',dep.elf.name)
						print('-'*150)
						print(dep.elf.__dict__)"""
					visited.add(key)
					deps.append(dep)
				else:
					pass
					#print("'%s' found ..."%(key))
	return deps


def get_instance(inst):
	if inst == None:
		return 'None'
	return inst


def initialize_logger(path):
	logging.basicConfig(filename=path, level=logging.WARNING, format='%(asctime)s:%(levelname)s:%(filename)s:%(lineno)d:%(message)s')

def get_cards(rpm_list):
	'''Finds all the card present in list of Rpm objects.'''
	card_set = set()
	for rpm in rpm_list:
		for dep in rpm.deps:
			if dep.elf.card != 'all':
				card_set.add(dep.elf.card)
	return card_set

def is_present(installed_rpms, query_rpms):
	'''Checks if same or higher version of the SMU is already installed.'''
	checker = {}
	ret = []
	for rpm in installed_rpms:
		if rpm.pkg_name not in checker:
			checker[rpm.pkg_name] = []
		checker[rpm.pkg_name].append(int(rpm.pkg_version.replace('.','').strip()))
	for rpm in query_rpms:
		if rpm.pkg_name in checker:
			if int(rpm.pkg_version.replace('.','').strip()) <= max(checker[rpm.pkg_name]):
				ret.append(rpm)
	return ret

def command_executor(command):
	logging.debug('Executing: '+command)
	ret = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
	if ret.returncode != 0:
		logging.error(command+' failed.')
		return None
	return ret

def run_cmd(command):
	try:
		logging.debug('Executing: '+command)
		ret = subprocess.run(command, shell=True, stdout=subprocess.PIPE, check=True)
		return ret
	except CalledProcessError as e:
		logging.error(str(e))
		raise
		
def is_valid(VM, card):
	if VM == 'SYSADMIN' or VM == 'XR':
		if card == 'rp' or card == 'lc':
			return True
		else:
			return False
	elif VM == 'SYSADMIN-ARM':
		if card == 'fc' or card == 'sc':
			return True
		else:
			return False	
	return True

class Format:
	end = '\033[0m'
	underline = '\033[4m'

def get_group_info(rpm_path):
	command = "rpm -qp --qf '%{GROUP}\n' "+rpm_path+" 2>/dev/null"
	cmd = command_executor(command)
	if cmd == None:
		return None
	out = cmd.stdout.decode()
	if 'SUPPCARDS' not in out.upper():
		return None
	pairs = out.split(';')
	data = {}
	for pair in pairs:
		key, value =  pair.strip().split(':')
		data[key] = value
	return data

class Global_Vars:
	INDEPENDENT = False	
