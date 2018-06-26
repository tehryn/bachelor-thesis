#!/usr/bin/env python3
import sys

def find_nth(string, substr, n):
	start = string.find(substr)
	while start >= 0 and n > 1:
		start = string.find(substr, start + len(substr))
		n -= 1
	return start

argv = sys.argv

if "-h" in argv or "--help" in argv:
	print( "Usage:\n ./reparser_udpipe.py tags" )
	exit(0)

out = sys.stdout
err = sys.stderr
input_data = sys.stdin.readlines()

if len(argv) != 2:
	print( "Usage:\n ./reparser_udpipe.py tags" )
	exit(0)

try:
	input = open( argv[1], "r" )
except:
	err.write( "Can't open '" + argv[1] + "' as input file." )
	exit(2)

try:
	tags_data = input.readlines()
except Exception as exc:
	err.write( "Can't read from '" + argv[1] + "'\n" + exc )
	exit(1)

for i in  range( len( input_data ) ):
	if input_data[i] == '\n':
		input_data[i] = ''
	else:
		data       = input_data[i].split( "\t" )
		spaceAfter = "0" if ( data[9].strip() == '_' ) else "1"
		line       = data[0] + '\t' +  data[1] + '\t' + data[4] + '\t' + data[2] + '\t' + data[6] + '\t' + data[7]
		if (data[6].isdigit()):
			number = int( data[6] )
			if number == 0:
				relat = 0
			else:
				relat = number - int( line[ :find_nth( line, "\t", 1 ) ] )
			w_line = input_data[ i + relat ].split('\t')
			if relat > 0:
				line = line + "\t" + w_line[1] + "\t" + w_line[4] + "\t" + w_line[2] + "\t+" + str( relat ) + "\t" + spaceAfter + "\n"
				#line = line + "\t" + w_line[1] + "\t" + w_line[2] + "\t+" + str( relat ) + "\t" + spaceAfter + "\n"
			elif relat == 0:
				line = line + "\t" + w_line[1] + "\t" + w_line[4] + "\t" + w_line[2] + "\t" + str( relat ) + "\t" + spaceAfter + "\n"
				#line = line + "\t" + w_line[1] + "\t" + w_line[2] + "\t" + str( relat ) + "\t" + spaceAfter + "\n"
			else:
				line = line + "\t" + w_line[1] + "\t" + w_line[2] + "\t" + w_line[3] + "\t" + str( relat ) + "\t" + spaceAfter + "\n"
				#line = line + "\t" + w_line[1] + "\t" + w_line[3] + "\t" + str( relat ) + "\t" + spaceAfter + "\n"
		input_data[i] = line

add = 0
for i in range( len( tags_data ) ):
	data = tags_data[i].split( "< ;>" )
	idx = int( data[0] )
	del data[0]
	data[-1] = data[-1][:-1]
	if ( idx < len( input_data ) ):
		diff = 0
		for tag in data:
			input_data.insert( idx + add + diff, tag + '\n' )
			diff += 1
		add += len(data)
	else:
		for tag in data:
			input_data.append( tag + '\n' )

link   = ""
length = ""
add    = False

for line in input_data:
	if line.startswith( '%%#IMG' ) or line.startswith( '%%#LINK' ):
		data   = line.split( '\t' )
		link   = data[1].strip()
		length = data[2].strip()
		add    = True
	else:
		if line.startswith( '<' ) and line.endswith( '>\n' ):
			out.write( line )
		elif ( add ):
			out.write( line[:-2] + link + '\t' + length + '\t' + line[-2:] )
			add = False
		elif ( line ):
			out.write( line[:-2] + '0\t0\t' + line[-2:] )
