import ELF
import SMU_handler
import sys
import output
import os

def get_affected(elf, ref_table, card):
	aff = []
	card = card.lower()
	#print(card)
	#print(elf.__dict__)
	try:
		if card != ref_table[elf.name][elf.instance]['ELF'].card and ref_table[elf.name][elf.instance]['ELF'].card != 'all':
			return []
		if ref_table[elf.name][elf.instance]['ELF'].md5 != elf.md5:
			for affected in ref_table[elf.name][elf.instance]['affected']:
				aff.append(ref_table[elf.name][elf.instance]['affected'][affected])
		return aff
	except Exception as e:
		return []

json_file = os.path.abspath(sys.argv[1])
SMU = os.path.abspath(sys.argv[2])

card, vm_type, platform, version = SMU_handler.gather_vm_info(os.path.abspath(json_file))

inputsOK = SMU_handler.check_inputs(json_file, SMU)
if not inputsOK:
	print("Execution failed due to previous errors!")
	sys.exit(1)


RPMs = SMU_handler.get_SMU_info(SMU)
print("Got RPMs from SMU")
for rpm in RPMs:
	if rpm.isReload:
		print("-"*150)
		print("Reload SMU: "+SMU.split('/')[-1])
		print("-"*150)
		sys.exit(0)

ref_table = ELF.get_reference_table(os.path.abspath(json_file))


"""
for so in ref_table:
	print(so)
	for inst in ref_table[so]:
		print('\t\t'+str(inst))
		for aff in ref_table[so][inst]['affected']:
			print('\t\t\t\t'+aff)



"""
programs = []
for rpm in RPMs:
	#print(rpm.name)
	#print('\naffected:\n')
	for elf in rpm.elfs:
		aff = get_affected(elf, ref_table, card)
		programs.extend(aff)
s = set()
for p in programs:
	if p.name not in s:
		#print(p.name, end=', ')
		s.add(p.name)

print('\n')
output.print_name(vm_type.upper())
output.print_exec(s, card)


	

		

