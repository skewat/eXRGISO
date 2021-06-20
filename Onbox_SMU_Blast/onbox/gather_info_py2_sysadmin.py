import os
import re
import subprocess
import json
import sys

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
		try:
			f = open(maps_path, 'r')
			out = f.readline()
			while len(out) != 0:
				dep_path = out.split(' ')[-1].strip()
				if IDENTIFIER in dep_path or IDENTIFIER2 in dep_path:
					dependencies.append(Dependency(dep_path, md5_dict[dep_path]))
				out = f.readline()
			return dependencies
		except KeyError as k:
			pass

			
				
		

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

def to_dict(p_dict):
	ret = {}
	for k in p_dict.keys():
		ret[k] = {}
		ret[k]['path'] = p_dict[k].path
		ret[k]['md5'] = p_dict[k].md5
		ret[k]['deps'] = [d.__dict__ for d in p_dict[k].dependencies]
	return ret

if __name__ == "__main__":
	info = get_process_info("/proc/")
	output = json.dumps(to_dict(info), indent = 4)
	print output
	sys.exit(0)

