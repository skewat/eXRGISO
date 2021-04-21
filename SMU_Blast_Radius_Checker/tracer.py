

def get_deps(rpms):
	elf_dict = {}
	visited = set()
	for rpm in rpms:
		for dep in rpm.deps:
			if dep.elf.name not in visited:
				elf_dict[dep.elf.name] = dep
				visited.add(dep.elf.name)
	return elf_dict

def trace_path(paths, curr, deps, target, visited, unmet):
	if target not in deps.keys():
		unmet.add(target)
		cla = curr[:]
		paths.append(cla)
		return
	c = curr[:]
	c.append(deps[target])
	if target in visited:
		paths.append(c)
		return
	visited.add(target)
	for d in deps[target].deps:
		trace_path(paths, c, deps, d, visited, unmet)
		
