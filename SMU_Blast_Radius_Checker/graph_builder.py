


class Instance_vertex:
	"""
		Works as the vertex of directed graph.
		
		Parameters
		----------
			elf: Elf object
				The ELF file for which this graph is created.
		Attributes
		----------
			name: string
				Name of the ELF file for which vertex is created.
			instance: string
				name of the card instance to which the ELF belongs(FRETTA-RP, etc.,)
			elf: Elf object
			edges: list
				list of Instance_Vertices which will be affected if current vertex is modified.
			rEdges: list
				Redundant: list of Instance_Vertices which are required by the current vertex.
	"""
	def __init__(self, elf):
		self.name = elf.name
		self.instance = elf.instance
		self.elf = elf
		self.edges = []
		self.rEdges = []
	
	def add_edge(self, iVertex):
		''' Adds a new Instance_Vertex object to edges attribute.''' 
		self.edges.append(iVertex)
	def add_rEdge(self, iVertex):
		''' Redundant: adds a new Instance_Vertex object to rEdges attribute.'''
		self.rEdges.append(iVertex)

class Vertex:
	"""
		Holds Instance_Vertices with same name but coming from different instances.

		Parameters
		----------
			name: string
				name of the Instance_Vertices
		Attributes
		----------
			name: string
				name of the Instance_Vertices
			instances: dictionary
				key -> instance name
				values -> Instance_Vertex object.
	"""
	def __init__(self, name):
		self.name = name
		self.instances = {}
	
	def add_iVertex(self, iVertex):
		'''Adds a new vertex from a different instance.'''
		key = iVertex.instance
		if key not in self.instances.keys():
			self.instances[key] = iVertex

	def get_iVertex_dfs(self, elf):
		'''Used during dfs innitiation to find Instance_Vertex corresponding to a elf in the target SMU i.e., checks if vertex with same name and instance exists and if md5s match.'''
		inst = elf.instance
		if inst in self.instances.keys():
			if elf.md5 != self.instances[inst].elf.md5:
				return self.instances[inst]
		return None
	
	def get_iVertex(self, inst):
		'''Returns Instance_Vertex corresponding to a preticular instance(inst).'''
		if inst in self.instances.keys():
			return [self.instances[inst],]
		if None in self.instances.keys():
			return [self.instances[None],]
		ret = []
		for k in self.instances.keys():
			ret.append(self.instances[k])
		return ret

class Graph:
	"""
		This is a directed graph if vertex A points to B then
		if A is modified then B will be affected.

		Each vertex is an Instance_Vertex object. 

		......
		Parameters
		----------
			card: string
				Identifies the card to which this Graph belongs(lc, rp, sc, etc.)
			vertices: dictionary
				dictionary of Vertex objects.

		Attributes
		----------
			card: string
				Identifies the card to which this Graph belongs(lc, rp, sc, etc.)
			vertices: dictionary
				dictionary of Vertex objects.
			visited: set
				vertices that have been visited during depth first searches.

	"""
	def __init__(self, card, vertices):
		self.card = card
		self.vertices = vertices
		self.visited = set()

	
	def dfs(self, iVertex, paths, affected):
		"""
			Depth First Search on the graph to find all the affected vertices.
			
			Arguments
			---------
				iVertex: Instance_Vertex object
					The target vertex for dfs.
				paths: list
					contains paths leading from a Instance_Vertex that will be modified after SMU update
					to each Instance_Vertex found during dfs
				affected: list
					constains all the vertices in the current dfs path.

			Returns
			-------
				None
				
		"""
		if iVertex in self.visited:
			return
		self.visited.add(iVertex)
		a = affected[:]
		a.append(iVertex)
		#if '.so' not in iVertex.name:
		if iVertex.elf.has_startup:
			paths[iVertex.name] = a
		for v in iVertex.edges:
			self.dfs(v, paths, a)
				
	def rdfs(self, iVertex, paths, needed, visited):
		'''Redundant'''
		n = needed[:]
		n.append(iVertex)
		if iVertex in visited:
			paths.append(n)
			return
		visited.add(iVertex)
		for e in iVertex.rEdges:
			self.rdfs(e, paths, n, visited)
			 
				
		
	def get_affected(self, elf):
		'''Entry point for dfs. checks if Instance_Vertex with same name and instance and different md5 exists; innitates dfs.'''
		name = elf.name
		#print('Checking: ', name, end='\t')
		if name in self.vertices.keys():
			vtex = self.vertices[name].get_iVertex_dfs(elf)
			if vtex != None:
				paths = {}
				affected = []
				#print(vtex.elf.name)
				#if '.so' not in vtex.name:
				if vtex.elf.has_startup:
					paths[vtex.name] = [vtex,]
					return paths
				self.dfs(vtex, paths, affected)
				return paths
			else:
				pass
				#print("Match: "+name)
		
		return {}

	def get_needed(self, name):
		'''Redundant'''
		if name in self.vertices.keys():
			print(name, ' is in the graph.')
			paths = []
			needed = []
			for ivert in self.vertices[name].instances.keys():
				self.rdfs(self.vertices[name].instances[ivert], paths, needed, set())
			return paths
		else:
			print(name, 'is not in graph.')
				
			
	@classmethod
	def from_deps(cls, dep_list, card):
		''' Buids a graph from list of Deps(dep_list) objects for specified card.'''
		vertices = {}
		for dep in dep_list:
			elf = dep.elf
			iVertex = Instance_vertex(elf)
			name = elf.name
			if name not in vertices.keys():
				vertices[name] = Vertex(name)
			vertices[name].add_iVertex(iVertex)
		
		for dep in dep_list:
			deps = dep.deps
			
			for d in deps:
				if d in vertices.keys():
					iVertex = vertices[d].get_iVertex(dep.elf.instance)
					for iv in iVertex:
						iv.add_edge(vertices[dep.elf.name].instances[dep.elf.instance])
						vertices[dep.elf.name].instances[dep.elf.instance].add_rEdge(iv)

		return Graph(card, vertices)
			
