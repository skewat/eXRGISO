# -*- coding: utf-8 -*-
#-------------------------------------------------------------------
from __future__ import print_function
import subprocess
import threading
from datetime import datetime
import re
import sys
import os

platform_prefix = "/opt/cisco/calvados/bin/vrfch.sh CTRL_VRF"
count = 0
class NoVersion(Exception):
	def __init__(self):
		self.msg = "Unable to gather Version infromation."
class NoLeadXR(Exception):
	def __init__(self):
		self.msg = "No lead XR VM found."

def progressBar(total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
	def printprogressbar(iteration):
		percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
		filledLength = int(length * iteration // total)
		bar = fill * filledLength + '-' * (length - filledLength)
		print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = printEnd)
	printProgressBar(0)
	for i in range(0, total):
		printprogressbar(i+1)
		yield
	print()

def progress(total, status='Complete'):
	global count
	bar_len = 60
	filled_len = int(round(bar_len * count / float(total)))

	percents = round(100.0 * count / float(total), 1)
	bar = '█' * filled_len + '-' * (bar_len - filled_len)

	sys.stdout.write('\r|%s| %s%s %s...' % (bar, percents, '%', status))
	sys.stdout.flush()

		
def get_vm_ips():
	calv_vm_ips = []
	xr_vm_ips = []
	lead_xr_vm = ""
	location = ''
	command = "/pkg/bin/install_exec_sysadmin \"source /opt/cisco/calvados/bin/install-functions.sh ; %s /opt/cisco/calvados/bin/show_cmd 'show vm' \"" % (platform_prefix)
	try:
		output = subprocess.check_output(command, shell=True)
		#print(output)
		for line in output.split(os.linesep):
			if 'Location' in line:
				location = line.split()[1]
			if 'running' in line:
				vm_name = line.split()[0]
				if 'sysadmin' in vm_name:
					vm_ip = re.findall(r'[0-9]+(?:\.[0-9]+){3}', line)
					calv_vm_ips.append (vm_ip[0])
				elif ("RP" in location or "RSP" in location):
					vm_ip = re.findall(r'[0-9]+(?:\.[0-9]+){3}', line)
					cmd = "/pkg/bin/install_exec_sysadmin \"ssh %s '/pkg/bin/placed_show sdr_instmgr | grep sdr_instmgr'\"" % (vm_ip[0])
					try:
						#print(cmd)
						op_lead_vm = subprocess.check_output(cmd, shell=True)
						if 'sdr_instmgr' in op_lead_vm and lead_xr_vm == "":
							try:
								lead = "/pkg/bin/install_exec_sysadmin \"ssh %s '/pkg/bin/placed_show sdr_instmgr | grep REDUNDANCY_ACTIVE'\"" % (vm_ip[0])
								#print(lead)
								op_rd_activ = subprocess.check_output(lead, shell=True)
								if "REDUNDANCY_ACTIVE" in op_rd_activ:
									lead_xr_vm = vm_ip[0]
							except Exception as e:
								pass
							xr_vm_ips.append(vm_ip[0])
					except subprocess.CalledProcessError as cpe:
						#print(str(cpe))
						raise
					except:
						print('No XR VM running on: %s'%(vm_ip[0]))
				else:
					vm_ip = re.findall(r'[0-9]+(?:\.[0-9]+){3}', line)
					xr_vm_ips.append(vm_ip[0])
		if lead_xr_vm == '':
			raise NoLeadXR

		return calv_vm_ips, xr_vm_ips, lead_xr_vm
	except subprocess.CalledProcessError as cpe:
		print(str(cpe))

def get_version():
	cmd1 = "/pkg/bin/ng_show_version"	
	op = ""
	version = ""
	try:
		op = subprocess.check_output(cmd1, shell=True)
		for line in op.split(os.linesep):
			if "Version" in line and ":" in line:
				version = re.findall(r"^[0-9]+\.[0-9]+\.[0-9]+", line.split(':')[-1].strip())[0]
		if version == "":
			raise NoVersion()
		return version

	except subprocess.CalledProcessError as cpe:
		print(str(cpe))
	
		
def prep_calvados(lead_xr_vm, xr_script_path):
	cmd = "/pkg/bin/install_exec_sysadmin \"scp root@%s:%s /harddisk\:/\"" % (lead_xr_vm, xr_script_path)

	try:
		op = subprocess.check_output(cmd, shell=True)
		if 'Successfully executed' in op:
			print('Prepped Sysadmin successfully.')
	except subprocess.CalledProcessError as cpe:
		print(str(cpe))
		raise

def vm_out_adapter(args):
	return get_vm_out(args[0], args[1], args[2], args[3], args[4])

def get_vm_out(ip_address, script_path, lead_xr_vm, vm_type, dirname, vm_count, total):
	global count
	script_name = script_path.split('/')[-1].strip()
	json_name = "json_out_%s.json" % (ip_address.replace('.', '_'))
	cmd1 = "/pkg/bin/install_exec_sysadmin \"scp %s root@%s:/\"" % (script_path, ip_address)
	cmd2 = "/pkg/bin/install_exec_sysadmin \"ssh %s 'python /%s > /json_out_%s.json'\"" % (ip_address, script_name, ip_address.replace('.', '_'))
	cmd3 = "/pkg/bin/install_exec_sysadmin \"scp root@%s:/json_out_%s.json .\"" % (ip_address, ip_address.replace('.', '_'))
	cmd4 = "/pkg/bin/install_exec_sysadmin \"scp %s root@%s:/%s/%s/%s\"" % (json_name, lead_xr_vm, os.getcwd(), dirname, "SMU_blast_"+vm_type+"_"+str(vm_count)+".json")	

	try:
		op1 = subprocess.check_output(cmd1, shell=True)
		#print('op1: '+op1)
		#print("Gathering information from VM: "+str(vm_count))
		op2 = subprocess.check_output(cmd2, shell=True)
		#print('op2: '+op2)
		op3 = subprocess.check_output(cmd3, shell=True)
		#print('op3: '+op3)
		op4 = subprocess.check_output(cmd4, shell=True)
		#print('op4: '+op4)
		#print("Successfully gathered information from VM: "+str(vm_count))
		#progressBar(total, prefix = 'Progress:', suffix = 'Complete', length = 50)
		count += 1
		progress(total)
	except subprocess.CalledProcessError as cpe:
		print(str(cpe))

def get_datetime():
	'''Generated the output file name.'''
	now = datetime.now()
	dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
	return dt_string
	
if __name__ == '__main__':
	print("Detecting VMs ...")
	calv, xr, lead_xr = get_vm_ips()
	#print(calv)
	#print(xr)
	#sys.exit(0)
	dirname = "SMU_blast_radius_" + get_datetime()
	os.mkdir(dirname)	
	prep_calvados(lead_xr, os.path.abspath('./gather_info_py2.py'))
	version = get_version()

	#for vm in calv:
		#get_vm_out(vm, '/harddisk\:/gather_info_py2.py', lead_xr, 'sysadmin', dirname)
	#for vm in xr:
		#get_vm_out(vm, '/harddisk\:/gather_info_py2.py', lead_xr, 'xr', dirname)
	
	threads = list()
	total = len(calv)+len(xr)
	vm_count = 1
	print("Gathering data from VMs ...")
	for vm in calv:
		t = threading.Thread(target=get_vm_out, args=(vm, '/harddisk\:/gather_info_py2.py', lead_xr, 'sysadmin_'+version, dirname, vm_count, total))
		threads.append(t)
		t.start()
		vm_count += 1
	for vm in xr:
		t = threading.Thread(target=get_vm_out, args=(vm, '/harddisk\:/gather_info_py2.py', lead_xr, 'xr_'+version, dirname, vm_count, total))
		threads.append(t)
		t.start()
		vm_count += 1
	#progressBar(total, prefix = 'Progress:', suffix = 'Complete', length = 50)
	progress(total)
	for t in threads:
		t.join()
	count = total
	progress(total)
	cmd = 'tar -cf %s %s' % (dirname+".tar.gz", dirname)
	try:
		#print(cmd)
		subprocess.call(cmd, shell=True)
		print("\nInformation gathered successfully. output in %s" % (dirname+".tar.gz"))
	except Exception as e:
		print(str(e))


