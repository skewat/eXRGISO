import os


def get_root_fs(path):
	'''Calls a helper script to unpack an iso and prepare root filesystem for each VM/LXC and returns the same.'''	
	workspace = os.getcwd()+'/workspace'
	os.system('rm -rf '+workspace)
	os.mkdir(workspace)
	command = "./get_all_root_fs.sh "+path+" "+workspace+" 2> /dev/null"
	os.system(command)
	dirs = os.listdir(workspace)
	if "sysadmin_root_fs" not in dirs or "xr_root_fs" not in dirs:
		print("Error: Cannot mount")
		return ""
	nbi_root_fs = None
	if 'nbi_root_fs' in dirs:
		nbi_root_fs = workspace+"/nbi_root_fs"
	return workspace+"/sysadmin_root_fs", workspace+"/xr_root_fs", nbi_root_fs
