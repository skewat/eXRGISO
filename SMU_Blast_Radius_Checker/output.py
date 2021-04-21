import os
from datetime import datetime
import utools



def build_output_tree(dict, output_list, index):
	'''Builds output tree from paths generated during dfs.'''
	if index >= len(output_list):
		return
	
	if output_list[index].elf.name in dict.keys():
		if ".so" in output_list[index].elf.name:
			build_output_tree(dict[output_list[index].elf.name], output_list, index+1)
		
	else:
		if ".so" in output_list[index].elf.name:
			dict[output_list[index].elf.name] = {}
			build_output_tree(dict[output_list[index].elf.name], output_list, index+1)
		else:
			dict[output_list[index].elf.name] = output_list[index].elf.name
			return


def print_output_tree(dict, tabs, f):
	'''Takes the output of build_output_tree command, formats it and writes it to a file.'''
	if len(dict) == 0:
		return
	for key in dict.keys():
		if type(dict[key]) is str:
			f.write('|   '*tabs+'|-> '+dict[key]+'\n')
		else:
			f.write("|   "*tabs+"|-> "+key+'\n')
			f.write("|   "*(tabs+2)+'\n')
			print_output_tree(dict[key], tabs+1, f)

			

def build_table(dict, parts):
	'''Builds an output table from paths generated during dfs.'''
	#parts = output.split('->')
	so = parts[0].elf.name
	exe = parts[-1].elf.name

	if so in dict.keys():
		dict[so].append(exe)
	else:
		dict[so] = []
		dict[so].append(exe)


def print_table(dict, f, name):
	'''Takes the output of build_table and outputs it to a file.'''
	f.write("\n\n"+name+":\n")
	f.write('-'*100+'\n')
	f.write('{:<50}{:>50}'.format("Shared Object", "Executable")+'\n')
	f.write('-'*100+'\n')
	out = ""
	for k in dict.keys():
		out = out+'{:<50}{:>50}'.format(k,"")+"\n"
		for e in dict[k]:
			out = out+'{:<50}{:>50}'.format("",e)+"\n"
	f.write(out+'\n\n')


def print_exec(exe_set, name):
	'''prints the affected programs to the console.'''
	print(f"Number of affected programs in {name}: {len(exe_set)}")
	if len(exe_set) == 0:
		return
	#exe_list = list(exe_set)
	width = int(os.popen('stty size', 'r').read().split()[1])
	
	output_columns = width//35
	out = ""
	i = 0
	for e in exe_set:
		out = out + '{:<35}'.format(e)
		i = i+1
		if i == output_columns:
			out = out + '\n'
			i = 0
	print('-'*(output_columns*35))
	print(out)
	print('-'*(output_columns*35))
		

def get_filename():
	'''Generated the output file name.'''
	now = datetime.now()
	dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
	return 'output-'+dt_string+'.txt'

def print_name(name):
	'''formats and outputs the name of VM/LXC.'''
	width = int(os.popen('stty size', 'r').read().split()[1])
	half = width//2
	output = " "*half+name+" "*(width-(half+len(name)))
	print('\n'+utools.Format.underline+" "*width+utools.Format.end)
	print(utools.Format.underline+output+utools.Format.end+'\n')
	
