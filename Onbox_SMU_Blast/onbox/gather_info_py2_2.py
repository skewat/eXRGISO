import os
import re
import subprocess
import json
import sys

class NoPlatform(Exception):
	def __init__(self):
		self.msg = "Unable to gather Platform information."
		

class NoVersion(Exception):
	def __init__(self):
		self.msg = "Unable to gather Version infromation."


def run_cmd(cmd):
	pass

class Dependency:
	'''Info on Shared objects needed by a process.'''
	def __init__(self, path, md5):
		self.path = path
		self.md5 = md5

class Program:
	'''Holds all the info on programs.'''
	def __init__(self, path, md5, dependencies):
		self.path = path
		self.md5 = md5
		self.dependencies = dependencies
	
	@classmethod
	def from_path(cls, path_to_process, md5_dict):
		try:
			path = os.readlink(path_to_process+'/exe')
			#print(path)
			dependencies = Program.get_map_info(path_to_process+'/maps', md5_dict)
			md5 = md5_dict[path]
			return Program(path, md5, dependencies)
			
		except Exception as e:
			pass
			#print(str(e))
		except subprocess.CalledProcessError as e:
			print(str(e))
		except KeyError as k:
			print(str(k))
		except FileNotFoundError as f:
			print(str(f))
		except OSError as o:
			pass
			#print(str(o))
	
	@staticmethod
	def get_map_info(maps_path, md5_dict):
		IDENTIFIER = "/opt/cisco/XR/packages/"
		IDENTIFIER2 = "/opt/cisco/calvados/packages/"
		dependencies = []
		present = set()
		try:
			f = open(maps_path, 'r')
			out = f.readline()
			while len(out) != 0:
				dep_path = out.split(' ')[-1].strip()
				if dep_path in present:
					out = f.readline()
					continue
				present.add(dep_path)
				if IDENTIFIER in dep_path or IDENTIFIER2 in dep_path:
					dependencies.append(Dependency(dep_path, md5_dict[dep_path]))
				out = f.readline()
			return dependencies
		except KeyError as k:
			print(str(k))

			
				
		
def get_version():
	cmd1 = "ng_show_version"
	cmd2 = "/opt/cisco/calvados/bin/show_cmd 'show version'"
	cmd3 = "chvrf 0 /opt/cisco/calvados/bin/show_cmd 'show version'"
	op = ""
	version = ""
	try:
		op = subprocess.check_output(cmd1, shell=True)
	except subprocess.CalledProcessError:
		try:
			op = subprocess.check_output(cmd2, shell=True)
		except subprocess.CallerProcessError:
			op = subprocess.check_output(cmd3, shell=True)
	for line in op.split(os.linesep):
		if "Version" in line and ":" in line:
			version = re.findall(r"^[0-9]+\.[0-9]+\.[0-9]+", line.split(':')[-1].strip())[0]
	if version == "":
		raise NoVersion()
	return version
			
def get_platform():
	platform = ""
	cmd1 = "grep PLATFORM_EXT /etc/init.d/calvados_bootstrap.cfg"
	cmd2 = "grep PLATFORM /etc/init.d/calvados_bootstrap.cfg"

	try:
		cp1 = subprocess.check_output(cmd1, shell=True)
		for line in cp1.split(os.linesep):
			if "PLATFORM_EXT" in line:
				platform = line.split("=")[-1].strip()
	except subprocess.CalledProcessError as cpe:
		try:
			cp2 = subprocess.check_output(cmd2, shell=True)
			#print(cp2+'\n\n')
			for line in cp2.split(os.linesep):
				if "PLATFORM" in line:
					temp = re.findall(r"PLATFORM[\s]*=[\s]*[\S]+", line)
					if len(temp) != 0:
						platform = temp[0].split("=")[-1].strip()
		except subprocess.CalledProcessError as cpe:
			print(str(cpe))
		except Exception as e:
			print(str(e))
	if platform == "":
		raise NoPlatform()
	return platform		

def get_md5s():
	IDENTIFIER = "/opt/cisco/XR/packages/"
	IDENTIFIER2 = "/opt/cisco/calvados/packages/"
	md5_dict = {}
	#out = utools.run_cmd('for rpm in $(rpm -qa); do rpm -q --qf "[%{FILENAMES} %{FILEMD5S} \n]" $rpm; done;').stdout.decode().split('\n')
	out = subprocess.check_output('for rpm in $(rpm -qa); do rpm -q --qf "[%{FILENAMES} %{FILEMD5S} \n]" $rpm; done;', shell=True).split('\n')
	for line in out:
		#print(line)
		line = line.strip()
		parts = line.split(" ")
		if (IDENTIFIER in parts[0] or IDENTIFIER2 in parts[0]) and bool(re.match("[a-f0-9]+", parts[-1].strip())):
			#print parts[0]
			#print parts[-1]
			md5_dict[parts[0].strip()] = parts[-1].strip()

	return md5_dict	
	
def get_process_info(path):
	try:	
		process_info = {}
		'''
			key -> path to process exe
			value -> Process Object
		'''
		md5_dict = get_md5s()
		for process_dir in os.listdir(path):
			if process_dir.isdigit():
				#print(process_dir)	
				prog = Program.from_path(path+"/"+process_dir, md5_dict)
				if prog != None:
					process_info[prog.path] = prog
		return process_info
	except Exception as e:
		print(str(e))

def get_card():
	try:
		inst = ""
		with open("/root/card_instances.txt", 'r') as f:
			inst = f.read()
		return inst
	except FileNotFoundError as fnf:
		print(str(fnf))
		raise

def to_dict(p_dict):
	ret = {}
	for k in p_dict.keys():
		ret[k] = {}
		ret[k]['path'] = p_dict[k].path
		ret[k]['md5'] = p_dict[k].md5
		ret[k]['deps'] = [d.__dict__ for d in p_dict[k].dependencies]
	card = get_card()
	json_dict = {}
	json_dict['card'] = card
	json_dict['platform'] = get_platform()
	json_dict['version'] = get_version()
	json_dict['info'] = ret
	return json_dict

if __name__ == "__main__":
	info = get_process_info("/proc/")
	output = json.dumps(to_dict(info), indent = 4)
	print output
	sys.exit(0)

