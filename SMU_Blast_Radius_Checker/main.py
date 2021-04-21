import find
import graph_builder as gb
import mount
import sys
import utools
import functools
import input_handler as iHandler
import output
import os
import tracer
import dependency_checker as depc

if len(sys.argv) < 3:
	print(f'Usage: {sys.argv[0]} [iso-file] [rpm/tar]')
	sys.exit(1)
query_rpms = iHandler.get_rpm_sos(sys.argv)
print('\n')

root_fs = mount.get_root_fs(sys.argv[1])
#root_fs = '/home/pvpanda/Checker_Upgrade/workspace/root_fs'
print('\n\n')
installed_rpms = sorted(find.get_rpms(root_fs, 'sysadmin'), key = functools.cmp_to_key (find.Rpm.rpm_precedence))
#installed_rpms = find.get_rpms(root_fs)

depc_rpms = [depc_rpm.rpm_path for depc_rpm in installed_rpms]
depc_rpms.extend([query_rpms[k].rpm_path for k in query_rpms])
dep_graph = depc.Graph.from_rpms(depc_rpms)
for k in query_rpms:
	depc_unmet = set()
	depc_visited = set()

	my_deps = dep_graph.get_deps(query_rpms[k].rpm_path, depc_visited, depc_unmet)
	print('RPMs needed for '+ query_rpms[k].rpm_path, ':')
	for d in my_deps:
		print(d)
	if len(depc_unmet) != 0:
		print('WARNING: Following packages are missing: ')
		for r in depc_unmet:
			print(r)
		print('This may lead to incorrect results.')

"""
Tej_deps = tracer.get_deps(installed_rpms)
paths = []
unmet = set()
tracer.trace_path(paths, [], Tej_deps, 'card_mgr', set(), unmet)

for t in paths:
	for d in t:
		print(d.elf.name, end = ' ')
	print('\n')

print('Unmet Dependencies:')
for d in unmet:
	print('\t',d)

print('\n\nProbe Order: \n')
for r in installed_rpms:
	print(r.name)
"""
#query_rpms = iHandler.get_rpm_sos(sys.argv)
q_rpms = [query_rpms[k] for k in query_rpms.keys()]

rp_deps = utools.get_deps('rp', installed_rpms)
lc_deps = utools.get_deps('lc', installed_rpms)

rp_query = utools.get_deps('rp', q_rpms)
lc_query = utools.get_deps('lc', q_rpms)

rp_graph = gb.Graph.from_deps(rp_deps, 'rp')

"""
for vert in rp_graph.vertices.keys():
	print('-'*150)
	print(vert, 'affects:')
	print('-'*150)
	for ivert in rp_graph.vertices[vert].instances.keys():
		print('\t', ivert, rp_graph.vertices[vert].instances[ivert].name)
		for evert in rp_graph.vertices[vert].instances[ivert].edges:
			print('\t\t', evert.name)
		
"""
lc_graph = gb.Graph.from_deps(lc_deps, 'lc')

lc_blast_radius = {}
lc_tree = {}
lc_table = {}
rp_blast_radius = {}
rp_tree = {}
rp_table = {}

for i in lc_query:
	aff = lc_graph.get_affected(i.elf)
	for path in aff.values():
		output.build_output_tree(lc_tree, path, 0)
		output.build_table(lc_table, path)
	lc_blast_radius.update(aff)

for i in rp_query:
	aff = rp_graph.get_affected(i.elf)
	for path in aff.values():
		output.build_output_tree(rp_tree, path, 0)
		output.build_table(rp_table, path)
	rp_blast_radius.update(aff)

with open('output.txt', 'w') as f:
	f.write(sys.argv[2]+'\n')
	f.write('\nRP\n')
	output.print_output_tree(rp_tree, 3, f)
	f.write('\nLC\n')
	output.print_output_tree(lc_tree, 3, f)
	output.print_table(rp_table, f, 'RP table')
	output.print_table(lc_table, f, 'LC table')

mandetory_lc = [lc_blast_radius[k] for k in lc_blast_radius.keys() if lc_blast_radius[k][-1].instance == None]
mandetory_rp = [rp_blast_radius[k] for k in rp_blast_radius.keys() if rp_blast_radius[k][-1].instance == None]

optional_lc = [lc_blast_radius[k] for k in lc_blast_radius.keys() if lc_blast_radius[k][-1].instance != None]
optional_rp = [rp_blast_radius[k] for k in rp_blast_radius.keys() if rp_blast_radius[k][-1].instance != None]

#os.system('clear')

mn = set()
op = set()
print('Mandetory:\n\nLC:\n')
for i in mandetory_lc:
	mn.add(i[-1].elf.name)

output.print_exec(mn)
mn.clear()
print('\nRP:\n')
for i in mandetory_rp:
	mn.add(i[-1].elf.name)

output.print_exec(mn)
#print('Optional: \n\nLC:\n')
for i in optional_lc:
	op.add(i[-1].elf.name + " " + utools.get_instance(i[-1].elf.instance))

#output.print_exec(op)
op.clear()
#print('\nRP:\n')

for i in optional_rp:
	op.add(i[-1].elf.name + " " + utools.get_instance(i[-1].elf.instance))

#output.print_exec(op)
print('Detailed output written to: \'output.txt\'.')
"""
needed = set()
paths = rp_graph.get_needed('card_mgr')
if len(paths) == 0:
	sys.exit(0)
for path in paths:
	for iv in path:
		needed.add(iv)

print('so needed for card_mgr: ')
print('count: ', len(needed))
for exso in needed:
	print(exso.elf.path, end='\t')
"""
