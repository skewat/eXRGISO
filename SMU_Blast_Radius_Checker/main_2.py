#!/usr/bin/python3

import find
import graph_builder as gb
import mount
import sys
import utools
import functools
import argparse
import input_handler as iHandler
import output
import os
import logging
import tracer
import dependency_checker as depc
import execution_manager as em

utools.initialize_logger('debug.log')
arg_parser = argparse.ArgumentParser(description="Calculate SMU Blast Radius")

arg_parser.add_argument("--iso", '-i', help="path/to/iso", required=True)
arg_parser.add_argument('--smu', '-s', nargs='+', help='path/to/smu', required=True)
arg_parser.add_argument('--independent', '-I', help="Consider SMUs independently", action="store_true", required=False)

args = arg_parser.parse_args()

utools.Global_Vars.INDEPENDENT = args.independent
 
arg_list = []
arg_list.append(sys.argv[0])
arg_list.append(args.iso)
arg_list.extend(args.smu)

if not iHandler.check_input(arg_list):
	logging.error('Operation failed!')
	sys.exit(1)

try:
	#utools.initialize_logger('debug.log')
	eu_dict = em.get_execution_units(arg_list[1:])
	f = open('output.txt', 'w')
	for eu in eu_dict.keys():
		#print("\n"+utools.Format.underline+eu+utools.Format.end, '\n')
		output.print_name(eu)
		f.write(eu + '\n\n')
		affected = eu_dict[eu].execute()
		for card in affected.keys():
			#print(card, '\n')
			if not utools.is_valid(eu, card):
				continue
			blast_radius = [affected[card].blast_radius[k] for k in affected[card].blast_radius.keys() if affected[card].blast_radius[k][-1].instance == None]
			affected_elfs = set()
			for i in blast_radius:
				affected_elfs.add(i[-1].elf.name)
			output.print_exec(affected_elfs, card)
			output.print_table(affected[card].table, f, card)
			output.print_output_tree(affected[card].tree, 2 , f)
	f.close()
	print("Detailed output in: 'output.txt'\tlog file: 'debug.log'")
except Exception as e: 
	print(str(e))

