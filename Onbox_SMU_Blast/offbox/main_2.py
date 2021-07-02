import sys
import os
import subprocess
import SMU_handler
import output
import argparse

def get_process_maps(tar_path):
	process_maps = []
	tar_path = os.path.abspath(tar_path)
	workdir, name = tar_path.rsplit("/", 1)
	json_dir = name.replace(".tar.gz", "")
	json_path = workdir+"/"+json_dir
	try:
		subprocess.call('rm -rf '+json_path, shell=True)
	except subprocess.CalledProcessError:
		pass	
	try:
		#subprocess.call('mkdir '+json_path, shell=True)
		subprocess.call('tar -xf '+tar_path + " -C "+workdir, shell=True)
		for json in os.listdir(json_path):
			process_maps.append(json_path+"/"+json)
	except subprocess.CalledProcessError as cpe:
		raise
	return process_maps

if __name__ == '__main__':
	arg_parser = argparse.ArgumentParser(description="Calculate SMU Blast Radius")

	arg_parser.add_argument("--maps", '-m', help="path/to/process map", required=True)
	arg_parser.add_argument('--smu', '-s' , help='path/to/smu', required=True)

	args = arg_parser.parse_args()

	process_map = os.path.abspath(args.maps)
	SMU = os.path.abspath(args.smu)

	SMU_VM_type = ""
	if 'sysadmin' in SMU.rsplit("/", 1)[-1]:
		SMU_VM_type = 'sysadmin'
	else:
		SMU_VM_type = 'xr'
	
	print("Extracting SMU and Gathering data. It may take several minutes ...")	
	process_maps = get_process_maps(process_map)
	VMs = {}
	output.print_name(SMU_VM_type.upper())
	for process_map in process_maps:
		card, vm_type, platform, version = SMU_handler.gather_vm_info(process_map)
		
		if card not in VMs.keys() and vm_type == SMU_VM_type:
			VMs[card] = process_map
			subprocess.call("python3 main_onbox_alt.py "+process_map+" "+SMU, shell=True)
	
	
