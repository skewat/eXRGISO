import os
import subprocess
import sys
import utools
import ELF
import re
import json
import logging

def gather_vm_info(vm_json):
	json_dict = ELF.load_json(vm_json)
	vm_json = vm_json.split("/")[-1]
	card = ""
	vm_type = ""
	platform = ""
	version = ""

	card = json_dict['card'].split(" ")[0]
	platform = json_dict['platform'].strip()
	version = re.findall(r"[0-9]+\.[0-9]+\.[0-9]+", vm_json)[0].strip()
	vm_type = re.findall(r"SMU_blast_[\S]+_", vm_json)[0].rsplit("_", 2)[-2].strip()
	if 'xr' in vm_json:
		vm_type = 'xr'
	else:
		vm_type = 'sysadmin'

	return card, vm_type, platform, version

def smu_info(smu):
	smu_name = smu.split('/')[-1].strip()
	smu_version = re.findall(r"[0-9]+\.[0-9]+\.[0-9]+", smu_name)[0]
	smu_platform = smu_name.split("-")[0].strip()
	smu_vm_type = ""
	if 'sysadmin' in smu_name:
		smu_vm_type = 'sysadmin'
	else:
		smu_vm_type = 'xr'
	return smu_version, smu_vm_type, smu_platform	
	
def is_reload_rpm5(rpm_path):
	command = "/auto/thirdparty-sdk/host-x86_64/lib/rpm-5.1.9/rpm -qp --qf '%{RESTARTTYPE}\n' "+rpm_path+" 2> /dev/null"
	try:
		op = utools.run_cmd(command)
		if "reboot" in op.stdout.decode().strip():
			return True
		return False
	except subprocess.CalledProcessError:
		Print("Fatal Error!")
		sys.exit(1)
def is_reload(rpm_path):
	data = utools.get_group_info(rpm_path)
	if data['Restarttype'].upper() == 'REBOOT':
		#print('\n'+'-'*80+'\n\n'+path.split('/')[-1]+' is a reload SMU.\n\n'+'-'*80)
		return True
	return False

def check_inputs(json_file, SMU):
	_, giso_vm_type, giso_platform, giso_version = gather_vm_info(json_file)
	smu_version, smu_vm_type, smu_platform = smu_info(SMU)
	if (giso_platform == smu_platform) and (giso_version == smu_version) and (smu_vm_type == giso_vm_type):
		return True
	print(giso_platform, giso_version, giso_vm_type)
	print(smu_platform, smu_version, smu_vm_type)
	print("This SMU cannot be installed on the router.")
	return False
		
class RPM:
	
	def __init__(self, name, rpm_path, elfs, pkg_name, pkg_version, isReload):
		self.name = name
		self.rpm_path = rpm_path
		self.elfs = elfs
		self.pkg_name = pkg_name
		self.pkg_version = pkg_version
		self.isReload = isReload

	@classmethod
	def from_path(cls, rpm_extract_location, rpm_path):
		name = rpm_path.split('/')[-1].strip()
		elfs = RPM.get_elfs(rpm_extract_location)
		command = "rpm -qp --qf '%{NAME} %{VERSION}' "+rpm_path+ " 2>/dev/null"
		cmd = utools.run_cmd(command)
		isReload = is_reload_rpm5(rpm_path)
		pkg_name, pkg_version = cmd.stdout.decode().split(' ')
		return RPM(name, rpm_path, elfs, pkg_name, pkg_version, isReload)

	@staticmethod
	def is_elf(path):
		if os.path.isdir(path):
			return False
		try:
			with open(path, "rb") as f:
				bytes = f.read(4)
				magic = f"{bytes.hex()}"
				if magic == '7f454c46':
					return True
		except (OSError, IOError) as e:
			logging.error("Failed to read file: "+path)
			print('Error occured while reading file: '+path)
			raise
		return False
	
	@classmethod
	def get_elfs(cls, rpm_extract_location):
		command = "find "+rpm_extract_location+" -name '*'"+" 2>/dev/null"
		elfs = []
		try:
			out = utools.run_cmd(command)
			files = out.stdout.decode().split('\n')
			for f in files:
				f = f.strip()
				if f is '':
					continue
				if RPM.is_elf(f):
					md5 = os.popen('md5sum '+f).read().split(' ')[0].strip()
					elfs.append(ELF.ELF.from_path(f, md5))
			return elfs
		except Exception as e:
			print(str(e))
			raise

			
def get_RPM(rpm_path):
	folder = rpm_path.split('/')[-1].strip().replace('.rpm', '').replace('.','')
	command = './extract_rpm.sh ' + rpm_path +" "+ folder + ' 2>/dev/null'
	try:
		cmd = utools.run_cmd(command)
		extracted_path = os.path.dirname(rpm_path)+'/'+folder+'/opt/cisco/calvados/packages/'
		if 'sysadmin' not in rpm_path.split('/')[-1] or 'admin' not in rpm_path.split('/')[-1]:
			print(rpm_path.split('/')[-1])
			#sys.exit(0)
			extracted_path = os.path.dirname(rpm_path)+'/'+folder+'/opt/cisco/XR/packages/'
		return RPM.from_path(extracted_path, rpm_path)
	except Exception as e:
		print(str(e))
		raise

def get_SMU_info(SMU_path):
	try:
		SMU_path = os.path.abspath(SMU_path)
		SMU_Dir = SMU_path.rsplit('/',1)[0]+'/'+SMU_path.split('/')[-1].strip().replace('.', "")
		print(SMU_Dir)
		utools.run_cmd('rm -rf '+SMU_Dir)
		os.mkdir(SMU_Dir)
		utools.run_cmd('tar -xvf '+SMU_path+' -C '+SMU_Dir)
		RPMs = []
		for rpm in os.listdir(SMU_Dir):
			if '.rpm' in rpm:
				RPMs.append(get_RPM(SMU_Dir+'/'+rpm))
		return RPMs
		
	except FileNotFoundError as fe:
		print(str(fe))
		raise

if __name__ == "__main__":
	RPMs = get_SMU_info('test_SMUs/ncs5500-6.6.3.CSCvo72245.tar')
	for rpm in RPMs:
		print(rpm.name)
		for elf in rpm.elfs:
			print(elf.__dict__)
