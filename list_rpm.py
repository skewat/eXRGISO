import os
import sys
import subprocess
import argparse
DEBUG = False 
img_rel_path = "boot/initrd.img"

bg_white = '\033[107m'
fg_black = '\033[30m'
clr_reset = '\033[0m'

'''
Prints only if 'DEGUB' is True.
Parameters:
s: string to be printed.
'''
def log (s):
	if DEBUG:
		print(s)

'''
Prints the passed string 's' with white background and black foregreound.
Parameters:
s: string to be printed
'''
def print_spl (s):
	print(bg_white + fg_black + s + clr_reset)	# Clears the formatting after printing the string.

'''
Runs the passed command 'cmd' on the Terminal.
Parameters:
cmd: command in the form of a single string
'''
def run_cmd (cmd):
	os.system(cmd)

'''
Extracts the iso file to the passed directory
Parameters:
iso_path: path (absolute) to .iso file
extract_iso_path: path (absolute) to the directory into which .iso file is extracted
'''
def extract_iso_files (iso_path, extract_iso_path):
	log("Extracting: " + iso_path + "...")
	
	if not os.path.isdir(extract_iso_path):
		run_cmd("mkdir " + extract_iso_path)	# Creates the directory to which .iso file is extracted.

	# List out all the files, directories and sub-directories in the iso, and store them in 'list_'
	files_in_iso = subprocess.run(["isoinfo", "-f", "-R", "-i", iso_path], stdout=subprocess.PIPE)
	list_ = files_in_iso.stdout.decode("utf-8").split('\n')
	list_.remove("")

	# Copy everything in .iso file to the directory
	for item in list_:
		out_file = extract_iso_path + item
		if os.path.isfile(os.path.dirname(out_file)):
			run_cmd("rm -f " + os.path.dirname(out_file))
		if not os.path.isdir(os.path.dirname(out_file)):
			run_cmd("mkdir -p " + os.path.dirname(out_file))
		
		# Copy the content of the file to the 'extract_iso_path'
		run_cmd("isoinfo -R -i " + iso_path + " -x " + item + " > " + out_file)

	log("Extracted: " + iso_path)

'''
Extracts the .iso file, creates a directory to which the it will be extracted.
Parameters:
save_path: path (absolute) to which all the extracted iso's and img files will be saved.
iso_path: path (absolute) to the iso file.
'''
def extract_iso (save_path, iso_path):
	iso_name = os.path.basename(iso_path)	
	extract_iso_dir_name = iso_name[:-4]	# Remove '.iso' from the iso file's name
	extract_iso_path = os.path.join(save_path, extract_iso_dir_name)

	extract_iso_files(iso_path, extract_iso_path)
	return extract_iso_dir_name, extract_iso_path

'''
Extracts the img file from the iso.
Parameters:
save_path: path (absolute) to which all the extracted iso's and img files will be saved.
iso_path: path (absolute) to the iso file.
'''
def extract_img (save_path, iso_path):
	extract_iso_dir_name, extract_iso_path = extract_iso(save_path, iso_path)

	img_path = os.path.join(extract_iso_path, img_rel_path)
	extract_img_dir_name = extract_iso_dir_name + "-img"	# Directory to which the img file will be saved.
								# Example: The img of "file.iso" will be saved to
								# 'file-img' directory.
	extract_img_path = os.path.join(save_path, extract_img_dir_name)
	run_cmd("mkdir " + extract_img_path)

	# Extract the .img file.
	temp = os.getcwd()
	os.chdir(extract_img_path)
	log("Extracting: " + img_path + "...")
	run_cmd("zcat " + img_path + " | cpio -imd")
	log("Extracted: " + img_path)
	os.chdir(temp)

'''
Check if the path exists or not.
Parameters:
path: path of the directory which is to be checked.
'''
def check_path (path):
	return os.path.exists(path)

'''
Prints the list in two columns.
Parameters:
list_: List that needs to be printed
'''
def print_list (list_):
	i = 0
	for item in list_:
		print(item.ljust(60, ' '), end='')
		i += 1
		if i % 2 == 0 or i == len(list_):
			print('\n', end='')

'''
Merges all the items in list of lists into one single list.
Parameters:
list_of_lists: List of lists.
'''
def merge_lists (list_of_lists):
	l = []

	for list_ in list_of_lists:
		for item in list_:
			l.append(item)

	return l

'''
Check if the substring follows the pattern 'CSCab12345'.
Parameters:
s: the substring that needs to be checked.
'''
def check (s):
	if s[:3] != "CSC":
		return False
	if not s[3].isalpha() or not s[4].isalpha():
		return False
	if not s[5:].isnumeric():
		return False
	
	return True
'''
Check if the passed file name is SMU or not.
Parameters:
file_name: the name of the file.
'''
def if_smu (file_name):
	t = file_name.split('.')
	for part in t:
		if 'CSC' in part and check(part):
			return True
	return False

'''
Segregates the SMUs from the list of all RPM files.
Parameters:
list_: List of the files.
'''
def segregate (list_):
	smu = []
	rpm = []
	for item in list_:
		if if_smu(item):
			smu.append(item)
		else:
			rpm.append(item)

	return smu, rpm

'''
Prints the SMU's and the RPM's files
Parameters:
save_path: path (absolute) to which all the img and iso files are extracted.
list_of_directories: list of paths of directories which contain the rpm files.
'''
def print_rpm_files (save_path, list_of_directories):
	list_of_lists = []

	for directory in list_of_directories:
		path = os.path.join(save_path, directory)
		list_of_lists.append(os.listdir(path))

	l = merge_lists(list_of_lists)	
	
	smu, rpm = segregate(l)

	print_spl("Following are SMU's:")
	print_list(smu)

	print_spl("Following are RPM's:")
	print_list(rpm)
	
def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("iso_path", help="Path of the iso file which needs to be extracted.")
	parser.add_argument("save_path", help="Path of the directory where we want to save the files.")
	parser.add_argument("--debug", dest="debug", type=bool, default=False, nargs='?', const=True)

	global DEBUG
	DEBUG = parser.parse_args().debug

	iso_path = parser.parse_args().iso_path
	save_path = parser.parse_args().save_path

	iso_path = os.path.abspath(iso_path)
	if not check_path(iso_path):
		raise AssertionError("File {} does not exists.".format(iso_path))

	save_path = os.path.abspath(save_path)
	if not check_path(save_path):
		raise AssertionError("Directory {} does not exist.".format(save_path))
	
	extract_img(save_path, iso_path)
	
	xr_iso_path = os.path.join(save_path, "asr9k-goldenk9-x64-7.3.1-SID1-img/iso/asr9k-xr.iso")
	extract_iso(save_path, xr_iso_path)
	
	l1 = "asr9k-goldenk9-x64-7.3.1-SID1-img/xr_rpms"
	l2 = "asr9k-xr/rpm/xr"
	
	list_of_directories = [l1, l2]
	print_rpm_files(save_path, list_of_directories)

	cfg_path = os.path.join(save_path, "asr9k-goldenk9-x64-7.3.1-SID1")
	cfg_files = []

	for item in os.listdir(cfg_path):
		if '.cfg' in item:
			cfg_files.append(item)

	print_spl("Following are the CFG files:")
	print_list(cfg_files)

	if "autorun" in os.listdir(cfg_path):
		print_spl("Following are the Bash Scripts:")
		print("autorun")

if __name__ == "__main__":
	main()
