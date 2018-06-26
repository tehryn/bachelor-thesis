#!/usr/bin/env python3

import sys

def parse_arguments( argv, argument ):
	i = 0
	for arg in argv:
		if ( arg == argument ):
			if i+1 < len( argv ):
				return argv[ i + 1 ]
			else:
				return False
		i += 1
	return False

argv = sys.argv

if "-h" in argv or "--help" in argv:
	print( "Usage:\n ./tokenizer_vert2udpipe.py -t tags_output [ -i input_file ] [ -o output_file ] [ -e error_file ]" )
	exit(0)

tag_file = parse_arguments( argv, '-t' )

if not ( tag_file ):
	print( "Usage:\n ./tokenizer_vert2udpipe.py -t tags_output [ -i input_file ] [ -o output_file ] [ -e error_file ]" )
	exit(1)

err_file = parse_arguments( argv, '-e' )
out      = open( out_file, 'w' ) if ( err_file ) else sys.stderr

out_file = parse_arguments( argv, '-o' )
out      = open( out_file, 'w' ) if ( out_file ) else sys.stdout

in_file  = parse_arguments( argv, '-i' )
input    = open( in_file, 'r' ) if ( in_file ) else sys.stdin

tags     = open( tag_file, 'w' )

sloupce1 = "\t_\t_\t_\t_\t_\t_\t_\t_"
sloupce2 = "\t_\t_\t_\t_\t_\t_\t_\tSpaceAfter=No"
index    = 1
space    = False

line_idx = 0
tag_str  = ""
cont     = True

curr_line = input.readline()
for next_line in input:
	idx = curr_line.find( '<link=' )
	if curr_line.startswith( '<' ) and curr_line.endswith( '>\n' ):
		if curr_line == "<s>\n":
			out.write('\n')
			line_idx += 1
			index = 1
		tag_str += '< ;>' + curr_line[:-1]
		cont = False
	elif idx >= 0:
			data          = curr_line.split( '\t' )
			link          = data[1][6:-3]
			length        = data[2][8:-2]
			if ( data[0] == '__IMG__' ):
				tag_str      += "< ;>%%#IMG\t" + link + "\t" + length
				cont          = False
			else:
				curr_line = data[0] + '\n'
				tag_str       += "< ;>%%#LINK\t" + link + "\t" + length
				cont          = True
	if ( cont ):
		if ( next_line ):
			if next_line == '<g/>\n':
				space = True
			else:
				space = False
		else:
			space = False
		if space:
			print( str( index ) + '\t' + curr_line[:-1] + sloupce2 )
		else:
			print( str( index ) + '\t' + curr_line[:-1] + sloupce1 )
		if ( tag_str ):
			tags.write( str( line_idx ) + tag_str + '\n' )
			tag_str = ""
		index += 1
		line_idx  += 1
	cont = True
	curr_line = next_line
tags.write( str( line_idx ) + tag_str + '< ;></doc>\n' )

input.close()
tags.close()
