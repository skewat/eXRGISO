import os
import re
import sys


class Vertex:
	"""
		This class holds the name of a pacakge that is avaliable on the giso and
		versions availabe.

		...
		Parameters
		----------
		name: string : package name
		versions: dictionary of Rpm objects

		Attributes
		----------
		name: string : package name
		versions: dictionary :  keys -> versions available
					values -> 'Rpm' objects from find.py module
	"""
	def __init__(self, name):
		self.name = name
		self.versions = {}


	def get_appropriate(self, version):
		''' Return the Rpm file correponding to a perticular version else None. '''
		if version in self.versions.keys():
			return self.versions[version]
		return None

	def add_version(self, ver, rpm):
		''' Adds a Rpm object that provides a version of the package. '''
		if ver not in self.versions.keys():
			self.versions[ver] = []
		self.versions[ver].append(rpm)
		#self.versions[ver].sort()



class Graph:
	"""
		Holds all the packages that are available on the golden iso as vertices(Vertex Object from this package).

		.....
		
		Parameters
		----------
			vertices: dictionary of Vertex objects

		Attributes
		----------
			vertices: dictionary:   key -> Package name
						values -> Vertex object  
	""" 
	def __init__(self, vertices):
		self.vertices = vertices

	def get_deps(self, target_rpm, visited, unmet):
		"""
			Get the list of rpms that are required by Rpm object(target_rpm)

			Parameters
			----------
				target_rpm: Rpm object
					The rpm that we want to check if all its dependencies are met.
				visited: set
					Set of Rpm objects that have been checked if dependencies met.
				unmet: set
					Set of strings that shows which packages or versions that are not present but are required by target_rpm.
			Raises
			------

			Returns
			-------
				Rpm object list that are requred by target_rpm.
 
		"""
		rpm_reqs = target_rpm.requires
		rpm_path = target_rpm.rpm_path
		ret = []
		ret.append(rpm_path)
		requires = rpm_reqs
		for req in requires.keys():
			if str(req)+'-'+str(requires[req]) in visited:
				continue
			if req not in self.vertices.keys():
				unmet.add(str(req)+'-'+str(requires[req]))
			else:
				rpm = self.vertices[req].get_appropriate(requires[req])
				if rpm == None:
					 unmet.add(str(req)+'-'+str(requires[req]))
				else:
					visited.add(str(req)+'-'+str(requires[req]))
					ret.extend(self.get_deps(rpm[0], visited, unmet))
		return ret

			
	@classmethod
	def from_provides(cls, provides_list):
		"""
			class method to build Graph class.
			
			Parameters
			----------
				provides_list: list
					List of Rpm objects that are installed and the user is trying to install.
			Raises
			------

			Returns
			-------
				Graph object
			
		"""
		vertices = {}
		for rpm in provides_list:
			provision = rpm.provides
			for package in provision.keys():
				if package not in vertices.keys():
					vertices[package] = Vertex(package)
				for tVer in provision[package]:
					vertices[package].add_version(tVer, rpm)
				
		return Graph(vertices)

			

if __name__ == '__main__':
	rpm_folder = os.path.abspath(sys.argv[1])
	target_rpm = rpm_folder+'/'+sys.argv[2]

	rpms = [rpm_folder+'/'+i for i in os.listdir(rpm_folder) if '.rpm' in i]
	graph = Graph.from_rpms(rpms)
	unmet = set()
	visited = set()
	print('\n'+'-'*100+'\n')	
	print(sys.argv[2], ' requires:\n')
	deps = graph.get_deps(target_rpm, visited, unmet)
	Deps = set()
	for i in range(1,len(deps)):
		Deps.add(deps[i].split('/')[-1].strip())
	for d in Deps:
		print('\t', d)
	print('\n'+'-'*100+'\n')
	print('Unmet Dependencies: ')
	for d in unmet:
		print(d)
