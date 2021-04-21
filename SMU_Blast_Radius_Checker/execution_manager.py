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

class Affected:
	"""
		Contains the output of each Execution_Unit - The blast radius for each card(rp, lc, etc.)
		
		.....

		Parameters
		----------
			card: string
				card to which this output belongs

			blast_radius: list
				list of paths
				each path traces from ELF file that will be changed after SMU update to the executables that will be restarted.
			
			tree: dictionary
				a dictionary that depicts how any why a program is affected.

			table: dictionary
				a mapping: modified ELF -------> affected executable binary

		Attributes
		----------
			card: string
				card to which this output belongs

			blast_radius: list
				list of paths
				each path traces from ELF file that will be changed after SMU update to the executables that will be restarted.
			
			tree: dictionary
				a dictionary that depicts how any why a program is affected.

			table: dictionary
				a mapping: modified ELF -------> affected executable binary
	"""

	def __init__(self, card, blast_radius, tree, table):
		self.card = card
		self.blast_radius = blast_radius
		self.tree = tree
		self.table = table

class Execution_Unit:
	"""
		Each execution unit has all the graphs and elf files that will be modified after smu update.
		By calling the execute function the user can determine the SMU blast radius for each LXC/VM(XR, SYSADMIN, etc.)
 
		Parameters
		----------
			graph_dict: dictionary
				graphs corresponding to each card 
					key -> card name
					values -> Graph object from graph.py

			query_dict: dictionary
				list of Deps object that will be changed for each card
					key -> card name
					values -> list of Deps objects.
	
		Attributes
		----------
			graph_dict: dictionary
				graphs corresponding to each card 
					key -> card name
					values -> Graph object from graph.py

			query_dict: dictionary
				list of Deps object that will be changed for each card
					key -> card name
					values -> list of Deps objects.
	"""	
	def __init__(self, graph_dict, query_dict):
		self.graph_dict = graph_dict
		self.query_dict = query_dict
	
	def execute(self):
		''' Finds the impact of a SMU for the LXC/VM(XR, SYSADMIN) corresponding to the Execution_Unit. Returns an Affected object.'''
		affected_dict = {}
		for card in self.query_dict.keys():
			blast_radius = {}
			tree = {}
			table = {}
			for dep in self.query_dict[card]:
				aff = self.graph_dict[card].get_affected(dep.elf)
				for path in aff.values():
					output.build_output_tree(tree, path, 0)
					output.build_table(table, path)
				blast_radius.update(aff)
			affected_dict[card] = Affected(card, blast_radius, tree, table)
		return affected_dict
			
	@classmethod
	def from_iso_smu(cls, root_fs, smus):
		''' Builds an Execution_Unit object from path to a root file system(root_fs) and list of Rpm objects(smus) built from target SMUs.'''
		installed_rpms = sorted(find.get_rpms(root_fs), key = functools.cmp_to_key (find.Rpm.rpm_precedence))
		print('\n')
		query_rpms_dict = smus
		query_rpms = [query_rpms_dict[key] for key in query_rpms_dict.keys()]
		present_rpms = utools.is_present(installed_rpms, query_rpms)
		if len(present_rpms) != 0:
			print("Following RPM(s) are allready installed: ")
			for rpm in present_rpms:
				print(rpm.name)
				query_rpms.remove(rpm)
		Execution_Unit.check_dependency(installed_rpms, query_rpms)
		cards = utools.get_cards(query_rpms)
		graph_dict = {}
		query_dict = {}
		for card in cards:
			graph_dict[card] = gb.Graph.from_deps( utools.get_deps(card, installed_rpms),card)
			query_dict[card] = utools.get_deps(card, query_rpms)
		
		return Execution_Unit(graph_dict, query_dict)

	@staticmethod
	def check_dependency(installed_rpms, query_rpms):
		''' Checks if the dependency requirements of each rpm(query_rpms) are met. outputs unmet dependencies.'''
		provides = [rpm for rpm in installed_rpms]
		provides.extend([rpm for rpm in query_rpms])
		
		dependency_graph = depc.Graph.from_provides(provides)
		for k in query_rpms:
			unmet = set()
			visited = set()

			dependency = dependency_graph.get_deps(k, visited, unmet)

			if len(unmet) != 0:
				print('WARNING: Following packages are missing: ')
				for r in unmet:
					print(r)
				print('This may lead to incorrect results.')
		
		
def get_execution_units(args):
	''' Takes paths to an iso and SMUs that will be installed. builds execution units corresponding to each VM/LXC and returns dictionary of Execution_Unit objects. '''
	xr = []
	sysadmin = []
	for i in range(1, len(args)):
		if 'sysadmin' in args[i].split('/')[-1].strip():
			sysadmin.append(args[i])
		else:
			xr.append(args[i])
	sysadmin_smus = iHandler.get_rpm_sos(sysadmin)
	xr_smus = iHandler.get_rpm_sos(xr)
	nbi_smus = {}
	nbi_smu_keys = []
	for k in sysadmin_smus:
		if '.arm.' in k:
			nbi_smus[k] = sysadmin_smus[k]
			print(k)
			nbi_smu_keys.append(k)
	for k in nbi_smu_keys:
		sysadmin_smus.pop(k)
	if len(sysadmin_smus) == 0 and len(xr_smus) == 0 and len(nbi_smus) == 0:
		return {}
	sysadmin_root_fs, xr_root_fs, nbi_root_fs = mount.get_root_fs(args[0])
	ret_dict = {}
	if len(sysadmin_smus) != 0:
		ret_dict["SYSADMIN"] = Execution_Unit.from_iso_smu(sysadmin_root_fs, sysadmin_smus)
	if len(xr_smus) != 0:
		ret_dict["XR"] = Execution_Unit.from_iso_smu(xr_root_fs, xr_smus)
	if len(nbi_smus) != 0:
		ret_dict["SYSADMIN-ARM"] = Execution_Unit.from_iso_smu(nbi_root_fs, nbi_smus)
	return ret_dict


