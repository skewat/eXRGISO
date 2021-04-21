import os
import shutil
import find
import sys
import re
import utools
import logging


def handle_tar(path):
	'''Process SMU; builds Rpm objects from rpms inside SMus returns a list of rpm objects.'''
	print("\nExtracting "+path.split('/')[-1]+'...', flush=True)
	logging.info("Extracting "+path.split('/')[-1])
	ret_dict = {}
	work_dir = os.path.dirname(path)+"/tar-extracted"
	os.system("rm -rf "+work_dir)
	os.mkdir(work_dir)
	os.system("tar -xvf "+path+" -C "+work_dir)
	for rpm in os.listdir(work_dir):
		if ".rpm" in rpm:
			if '.host.arm' in rpm or '.host.x86_64' in rpm:
				continue
			print('\nChecking for reload SMU: '+rpm, end=' ---- ')
			command = "/auto/thirdparty-sdk/host-x86_64/lib/rpm-5.1.9/rpm -qp --qf '%{RESTARTTYPE}\n' "+work_dir+"/"+rpm +" 2> /dev/null"
			cmd = utools.command_executor(command)
			if cmd == None or cmd.stdout.decode().strip() == '(none)':
				data = utools.get_group_info(work_dir+"/"+rpm)
				try:
					if data['Restarttype'].upper() == 'REBOOT':
						print('\n'+'-'*80+'\n\n'+path.split('/')[-1]+' is a reload SMU.\n\n'+'-'*80)
						if not utools.Global_Vars.INDEPENDENT:
							sys.exit(0)
						return {}
				except Exception as e:
					print(e)
					sys.exit(1)
			elif 'reboot' in cmd.stdout.decode():
				print('\n'+'-'*80+'\n\n'+path.split('/')[-1]+' is a reload SMU.\n\n'+'-'*80)
				if not utools.Global_Vars.INDEPENDENT:
					sys.exit(0)
				return {}
			print('Not a reload SMU.')
			ret_dict[rpm] = find.Rpm.from_rpm(work_dir+"/"+rpm)

	return ret_dict

def get_rpm_sos(args):
	'''Iterates over the input SMUs and returns dictionary of Rpms.'''
	ret_dict = {}
	for i in range(0,len(args)):
		abs_path = os.path.abspath(args[i])
		if ".tar" in abs_path:
			rpm_n_deps = handle_tar(abs_path)
			for k in rpm_n_deps.keys():
				ret_dict[k] = rpm_n_deps[k]

	return ret_dict


def check_input(argvs):
	'''Checks for errors in the input.'''
	if shutil.disk_usage('.').free < 5*(1024**3):
		logging.warning("Insufficient Disk Space!")
		print("Space left on disk is less than 5GB. This may lead to program crash.")
	flag = True
	args = argvs[:]
	if len(args) < 3:
		logging.error("Insufficient number of arguements.")
		return False

	for i in range(1,len(args)):
		if os.path.exists(args[i]):
			args[i] = os.path.basename(args[i])
		else:
			print(args[i], 'does not exist.')
			logging.error("%s does not exist!"%(args[i]))
			return False

	if '.iso' not in args[1]:
		logging.error("%s - Not an iso."%(args[1]))
		flag = False
	else:
		for i in range(2, len(args)):
			if '.tar' not in args[i]:
				logging.error("%s - Not a SMU."%(args[i]))
				print("%s - Not a SMU."%(args[i]))
				flag = False
				break
		if flag == False:
			return flag	
		platform = args[1].split('-')[0].strip()
		release = re.search(r'(\d)+\.(\d)+\.+(\d)+', args[1]).group()
		logging.info('Platform: '+platform+' Release: '+release)
		for i in range(2, len(args)):
			smu_platform = args[i].split('-')[0].strip()
			smu_release = re.search(r'(\d)+\.(\d)+\.+(\d)+', args[i]).group()
			logging.info('SMU_Platform: '+smu_platform+' SMU_Release: '+smu_release)
			if smu_platform != platform or smu_release != release:
				logging.error('ISO and SMUs are from different platform.')
				print('ISO and SMUs are from different platform or release.\nExiting...')
				flag = False
			else:
				logging.debug('ISO and SMU are for same platform and release.')
	return flag

if __name__ == "__main__":
	utools.initialize_logger('debug.log')
	check_input(sys.argv)		
