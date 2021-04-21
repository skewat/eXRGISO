import os
import sys
import utools
import subprocess
import re
import logging
import concurrent.futures as confu


class Elf:
	"""
		This class is responsible for holding information on an ELF file.

		.....
		
		Parameters
		----------
			name: string
				name of the ELF file.
			rpm: string
				rpm to which it belongs.
			card: string
				card name to which it belongs(rp, lc, etc.).
			instance: string
				card instance in which it is found(FRETTA-RP, BIFROST-RP, etc.).
			path: string
				absolute path where this ELF resides.
			md5: string
				md5sum of this file.
			has_startup: Bool
				marks if this ELF file has a startup file.

		Attributes
		----------
			name: string
				name of the ELF file.
			rpm: string
				rpm to which it belongs.
			card: string
				card name to which it belongs(rp, lc, etc.).
			instance: string
				card instance in which it is found(FRETTA-RP, BIFROST-RP, etc.).
			path: string
				absolute path where this ELF resides.
			md5: string
				md5sum of this file.
			has_startup: Bool
				marks if this ELF file has a startup file.
		
	"""
	def __init__(self, name, rpm, card, instance, path, md5, has_startup):
		self.name = name
		self.rpm = rpm
		self.card = card
		self.instance = instance
		self.path = path
		self.md5 = md5
		self.has_startup = has_startup
		logging.info("ELF object for %s created successfully."%(path))
	
	@classmethod
	def from_path(cls, path, md5):
		''' Builds an ELF object when path to the ELF file and its MD5 is provided. '''
		path = os.path.abspath(path)
		has_startup = Elf.check_startup(path)
		#['ncs5500-os-5.0.0.0-r74117I', 'rp', 'instances', 'FRETTA-RP', 'lib', 'libfabric_fapid_hal.so']
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
		# ELF having name libc.so.6.0.0.1 is converted to libc.so
		if '.so.' in name:
			#print(name, end='\t')
			name_parts = parts[-1].split('.', 2)
			name = name_parts[0]+'.'+name_parts[1]
			#print(name)
		return Elf(name, rpm, card, instance, path, md5, has_startup)
	
	@staticmethod
	def check_startup(path):
		''' Given the path to an ELF, checks if a startup file exists corresponding to the ELF.'''
		#check if a startup file exists for a given executable
		path = path.strip()
		if '/bin' in path or '/sbin' in path:
			#assuming all the executables that are of interest, will be either in bin or sbin folders
			#for XR bins
			startup_path_XR = path.replace('/bin', '/startup').replace('/sbin', '/startup')+'.startup'
			#for sysadmin bins
			startup_path_sysadmin = path.replace('/bin', '/etc/startup').replace('/sbin', '/etc/startup')+'.startup'
			if os.path.exists(startup_path_XR) or os.path.exists(startup_path_sysadmin):
				logging.info("Startup file for "+path+" exists.")
				return True
		return False

#class containing an elf object and dependencies of that elf.			
class Deps:
	"""
		Holds an ELF object and its dependencies together.
		.....

		Parameters
		----------
			elf: Elf object
			deps: list
				list of shared objects needed for the ELF to work.

		Attributes
		----------
			elf: Elf object
			deps: list
				list of shared objects needed for the ELF to work.

	"""
	def __init__(self, elf, deps):
		self.elf = elf
		self.deps = deps

	@classmethod
	def from_path(cls, path):
		''' Builds Deps object from path to an ELF.'''
		path = os.path.abspath(path)
		if not Rpm.is_elf(path):
			return None
		md5 = os.popen('md5sum '+path).read().split(' ')[0].strip()
		elf = Elf.from_path(path, md5)
		if elf == None:
			return None
		deps = Deps.get_deps(path)
		if deps == None:
			return None
		return Deps(elf, deps)		
	
	@staticmethod
	def get_deps(path):
		'''Get dependencies of an ELF if its path is given.'''
		deps = []
		if not os.path.exists(path):
			logging.debug("$s - doesn't exist."%(path))
			return deps
		path = os.path.realpath(path)
		command = "objdump -p "+path+" | grep 'NEEDED'"
		logging.debug("Running system command: "+command)
		objdump_out = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
		if objdump_out.returncode != 0:
			logging.debug(command+" failed.")
			return None
		cmd_output = objdump_out.stdout.decode().split('\n')
		for line in cmd_output:
			line = line.strip()
			parts = line.split(" ")
			if parts[0].strip() == 'NEEDED':
				Sushi_deps = parts[-1].strip()
				if '.so.' in Sushi_deps:
					Sushi_name_parts = Sushi_deps.split('.', 2)
					Sushi_deps = Sushi_name_parts[0]+'.'+Sushi_name_parts[1]
				deps.append(Sushi_deps)

		return deps
		


class Rpm:
	"""
		Holds information on RPMs that maybe installed or is in a SMU that is being checked.
		......

		Parameters
		----------
			name: string
				complete name of the RPM file from which this object is to be made.
			pkgtype: string
				This parameter along with pkgpresence and packagetype are used for sorting
				the RPMs into the order in which they are to be considered while looking for
				an ELF. for example, SMUs take precedence over base packages.
			pkgpresence: string
				refer pkgtype
			packagetype: string
				refer pkgtype
			deps: list
				list of dependency objects found in the RPM.
			rpm_path: string
				absolute path where the rpm package is.
			provides: dictionary
				packges that are made available by the rpm.
				key -> package name.
				values -> package version
			requires: dictionary
				packages that are required by this rpm to work.
				key -> package name
				values -> package version
			pkg_name: string
				name of the rpm. rpm -qp --qf '%{NAME} %{VERSION}'
			pkg_version: string
				rpm version. rpm -qp --qf '%{NAME} %{VERSION}'
		Attributes
		----------
			name: string
				complete name of the RPM file from which this object is to be made.
			pkgtype: string
				This parameter along with pkgpresence and packagetype are used for sorting
				the RPMs into the order in which they are to be considered while looking for
				an ELF. for example, SMUs take precedence over base packages.
			pkgpresence: string
				refer pkgtype
			packagetype: string
				refer pkgtype
			deps: list
				list of dependency objects found in the RPM.
			rpm_path: string
				absolute path where the rpm package is.
			provides: dictionary
				packges that are made available by the rpm.
				key -> package name.
				values -> package version
			requires: dictionary
				packages that are required by this rpm to work.
				key -> package name
				values -> package version
			pkg_name: string
				name of the rpm. rpm -qp --qf '%{NAME} %{VERSION}'
			pkg_version: string
				rpm version. rpm -qp --qf '%{NAME} %{VERSION}'

	"""
	def __init__(self, name, pkgtype, pkgpresence, packagetype, deps, rpm_path, provides, requires, pkg_name, pkg_version):
		self.name = name
		self.pkgtype = pkgtype
		self.pkgpresence = pkgpresence
		self.packagetype = packagetype
		self.deps = deps
		self.rpm_path = rpm_path
		self.provides = provides
		self.requires = requires
		self.pkg_name = pkg_name
		self.pkg_version = pkg_version

	@classmethod
	def rpm_precedence(cls, rpm1, rpm2):
		'''Given two rpms, determines which rpm takes precedence. Used for sorting.'''
		if rpm1.packagetype.lower() == 'package' and rpm2.packagetype.lower() == 'smu':
			return 1
		elif rpm1.packagetype.lower() == 'smu' and rpm2.packagetype.lower() == 'package':
			return -1
		if rpm1.pkgpresence == 'optional' and rpm2.pkgpresence == 'optional':
			if rpm1.pkgtype == 'PI' and rpm2.pkgtype == 'PD':
				return 1
			elif rpm1.pkgtype == 'PI' and rpm2.pkgtype == 'PI':
				return 0
			else:
				return -1
		if rpm1.pkgpresence == 'mandatory' and rpm2.pkgpresence == 'mandatory':
			if rpm1.pkgtype == 'PI' and rpm2.pkgtype == 'PD':
				return 1
			elif rpm1.pkgtype == 'PI' and rpm2.pkgtype == 'PI':
				return 0
			else:
				return -1
		if rpm1.pkgpresence == 'optional' and rpm2.pkgpresence == 'mandatory':
			return -1
		else:
			return 1

	@classmethod
	def from_path(cls, args):
		"""
			Builds the Rpm object when path to Rpm is given.

			Arguements
			----------
			args[0]: string
				location where rpm is extracted.
			args[1]: string
				location of unextracted rpm file.

			Returns
			-------
				Rpm object.
		"""
		path = args[0]
		rpm_path = args[1]
		path = os.path.abspath(path)
		name = rpm_path.split('/')[-1].strip()
		elfs = Rpm.get_elfs(path)
		deps = []
		with confu.ProcessPoolExecutor() as executor:
			for e in executor.map(Deps.from_path, elfs): 
				if e != None:
					deps.append(e)
		try:
			#/auto/thirdparty-sdk/host-x86_64/lib/rpm-5.1.9/rpm -qp --qf "%{PKGTYPE} %{PACKAGEPRESENCE} %{PACKAGETYPE}" ncs5500-li-1.0.0.0-r711.x86_64.rpm
			info = Rpm.get_pkg_info(rpm_path)
			provides = Rpm.parse(rpm_path)
			requires = Rpm.get_reqs(rpm_path)
			command = "rpm -qp --qf '%{NAME} %{VERSION}' "+rpm_path+ " 2>/dev/null"
			cmd = utools.run_cmd(command)
			pkg_name, pkg_version = cmd.stdout.decode().split(' ')
			return Rpm(name, info[0], info[1], info[2], deps, rpm_path, provides, requires, pkg_name, pkg_version)
		except subprocess.CalledProcessError as e:
			print('Failed to find name and version for: '+rpm_path)
			return None
		except TypeError:
			print('Unable to find gather metadata from: '+rpm_path.split('/')[-1])
			print('Exiting ...')
			sys.exit(1)
		except Exception as e:
			print(str(e))
			sys.exit(1)


	@staticmethod
	def get_pkg_info(rpm_path):
		'''Gathers information from the rpm file in three custom tags: PKGTYPE, PACKAGEPRESENCE, PACKAGETYPE.'''
		try:
			info = None
			name = rpm_path.split('/')[-1].strip()
			print('Analyzing:', rpm_path.split('/')[-1].strip())
			command = "/auto/thirdparty-sdk/host-x86_64/lib/rpm-5.1.9/rpm -qp --qf '%{PKGTYPE} %{PACKAGEPRESENCE} %{PACKAGETYPE}' "+rpm_path + ' 2>/dev/null'
			cmd = utools.run_cmd(command)

			info = cmd.stdout.decode().split(' ')
			flag = 0
			for i in range(len(info)):
				info[i] = info[i].strip()
				if info[i] == '(none)':	
					flag += 1

			if flag == 3:
				return Rpm.get_groups(rpm_path)

			if info[0].strip() == '(none)':
				info[0] = 'PD'
				if 'iosxr' in name:
					info[0] = 'PI'
			for i in range(len(info)):
				info[i] = info[i].strip()
			return info
		except subprocess.CalledProcessError as e:
			logging.debug(str(e))
			return Rpm.get_groups(rpm_path)
		except Exception as e:
			logging.debug(str(e))
			print("Program encountered a fatal error. Execution cannot proceed. Exiting")
			sys.exit(1)
 
	@staticmethod
	def get_groups(rpm_path):
		try:
			data = utools.get_group_info(rpm_path)
			if data == None:
				return None
			info = [None]*3
			info[0] = data['Pkgtype']
			info[1] = data['Packagepresence']
			info[2] = data['Packagetype']

			return info
		except LookupError as e:
			print('One or more parameters could not gathered for: '+rpm_path.split('/')[-1])
			logging.error("One or more parameters not available in rpm 'GROUP' tag: "+str(e))
			sys.exit(1)	
	@classmethod
	def from_rpm(cls, rpm_path):
		'''Builds Rpm object when path to rpm file is given.'''
		folder = rpm_path.split('/')[-1].strip().replace('.rpm', '').replace('.','')
		command = './extract_rpm.sh ' + rpm_path +" "+ folder + ' 2>/dev/null'
		try:
			cmd = utools.run_cmd(command)
			extacted_path = os.path.dirname(rpm_path)+'/'+folder+'/opt/cisco/calvados/packages/' 
			if 'sysadmin' not in rpm_path.split('/')[-1]:
				extacted_path = os.path.dirname(rpm_path)+'/'+folder+'/opt/cisco/XR/packages/'
			return Rpm.from_path([extacted_path, rpm_path])
		except subprocess.CalledProcessError as e:
			logging.error(str(e))
			print('Encountered error while extracting: '+rpm_path.split('/')[-1]+' Exiting ...')
			sys.exit(1)
		except Exception as e:
			logging.error(str(e))
			print("Fatal Error!")
			sys.exit(1)

	
	@staticmethod
	def is_elf(path):
		'''Checks if a file is an ELF binary or not.'''
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
		return False

	@staticmethod
	def get_elfs(path):
		'''Gets all the elfs in a rpm.'''
		elfs = []
		command = "find "+path+" -name '*'"+" 2>/dev/null"
		cmd = utools.command_executor(command)
		if cmd == None:
			#print('Failed to find ELFs in '+path)
			return elfs
		f_elfs = cmd.stdout.decode().split('\n')
		for line in f_elfs:
			if os.path.isfile(line.strip()):
				elfs.append(line.strip())
		return elfs 

		
	@staticmethod
	def get_bins(path):
		'''Redundant method, not used anymore.'''
		startup_bins = []
		f_startup_bins = os.popen("find "+path+" -name '*.startup'")
		line = f_startup_bins.readline()
		while len(line) != 0:
			if 'casasacalvados' not in line:
				bin = line.replace('/startup', '/bin').replace('.startup', '').strip()
				sbin = line.replace('/startup', '/sbin').replace('.startup', '').strip()
				if os.path.isfile(bin):
					startup_bins.append(bin)
				if os.path.isfile(sbin):
					print(sbin)
					startup_bins.append(sbin)
			line = f_startup_bins.readline()
		f_startup_bins.close()
		return startup_bins
			
	@staticmethod
	def get_libs(path):
		'''Redundant method, not used anymore.'''
		libs = []
		f_libs = os.popen("find "+path+" -name '*.so*'")
		line = f_libs.readline()
		while len(line) != 0:
			if 'csasascalvados' not in line:
				lib = line.strip()
				libs.append(lib)
			line = f_libs.readline()
		f_libs.close()
		return libs
		
	@staticmethod
	def parse(rpm_path):
		'''Builds a dictionary of packgages that are made available by this rpm.'''
		ret = {}
		command = 'rpm -qp --provides '+rpm_path+' 2>/dev/null'
		cmd = utools.command_executor(command)
		if cmd == None:
			print('Failed to find packages provided by'+rpm_path)
			return None
		output = cmd.stdout.decode()
		regex = re.compile(r'([\S]+)\s=\s([0-9.]+)(-[\S]*)?')
		for match in regex.finditer(output):
			Tej_RPM = match.group(1)
			if Tej_RPM not in ret:
				ret[Tej_RPM] = []
			ver = match.group(2)
			ver = ver.replace('.','')
			version = int(ver)
			ret[Tej_RPM].append(version)
		return ret
	
	@classmethod
	def get_reqs(cls, rpm_path):
		'''Builds a dictionary of packages and corresponding version required by this rpm.'''
		requires = {}
		regex = re.compile(r'([\S]+)\s=\s([0-9.]+)')
		command = 'rpm -qpR '+rpm_path+' 2>/dev/null'
		cmd = utools.command_executor(command)
		if cmd == None:
			print('Failed to find packages required by'+rpm_path)
			return None
		output = cmd.stdout.decode()
		for match in regex.finditer(output):
			requires[match.group(1)] = int(match.group(2).replace('.',''))
		return requires


def get_rpms(root_fs):
	'''Given a directory having rpm files, Rpm objects out of it puts them in a list.'''
	install_path = root_fs+'/opt/cisco/calvados/packages'
	if os.path.basename(root_fs) == 'xr_root_fs':
		install_path = root_fs+'/opt/cisco/XR/packages'
	rpm_path = root_fs+'/RPM'
	
	rpms = []
	args = []
	args1 = []

	for d in os.listdir(rpm_path):
		install_dir = rpm_path+'/'+d
		args1.append(install_dir)
	
	with confu.ProcessPoolExecutor() as executor:
		for r in executor.map(Rpm.from_rpm, args1):
			rpms.append(r)
	
	return rpms


if __name__ == '__main__':
	rpm = Rpm.from_rpm('/home/pvpanda/Checker/tar/ncs5500-dpa-fwding-4.0.0.1-r711.CSCvs77558.x86_64.rpm')
	for i in rpm.deps:
		print(i.elf.__dict__)


