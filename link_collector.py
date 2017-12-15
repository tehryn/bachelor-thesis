#!/usr/bin/env python3
import sys, os
import xml.etree.ElementTree as ET

from Functions import get_setting, print_help, get_data_from_xml, get_page_from_url, find_rss_links

author = "Author:\n" + \
		 "  Jmeno: Jiri Matejka\n" + \
		 "  Email: xmatej52@stud.fit.vutbr.cz nebo jiri.matejkaa@gmail.com\n" + \
		 "  FIT VUT v Brne, Vyzkumna skupina KNOT@FIT"

possible_arguments = [
	{
		'names'        : [ '--dedup',  '-d' ],
		'optional'     : True,
		'has_tail'     : 2,
		'word_index'   : 'dedup',
		'prerequisite' : None,
		'description'  : 'Cesta k souboru nebo souborum, kde jsou odkazy, ktere ' +
						 'nemaji byt zarazeny do fronty pro stahovani.'
	},
	{
		'names'        : [ '--input',  '-i' ],
		'optional'     : True,
		'has_tail'     : 2,
		'word_index'   : 'input',
		'prerequisite' : None,
		'description'  : 'Cesta k souboru nebo souborum, ktere obsahuji adresy na ' +
                         'rss/atom zdroje. Pokud parametr neni zadan, odkazy jsou ' +
						 'ocekavany na standartnim vstupu'
	},
	{
		'names'        : [ '--output', '-o' ],
		'optional'     : True,
		'has_tail'     : 1,
		'word_index'   : 'output',
		'prerequisite' : None,
		'description'  : 'Vystupni soubor, kde bude generovana fronta pro stahovani ' +
                         'Pokud parametr neni zadan, odkazy pro frontu budou ' +
						 'vypisovany na standartni vystup'
	},
	{
		'names'        : [ '--append', '-a' ],
		'optional'     : True,
		'has_tail'     : 0,
		'word_index'   : 'append',
		'prerequisite' : 'output',
		'description'  : 'Vystupni soubor bude otevren v modu "append", tzn. pokud ' +
						 'soubor jiz existuje, nebude jeho puvodni obsah smazan, ' +
						 'odkazy budou pridany na jeho konec. Navic se obsah souboru ' +
						 'pouzije pro deduplikaci - odkazy obsazene v souboru nebudou ' +
						 'znovu zarazeny do fronty.'
	},
	{
		'names'        : [ '--help',   '-h' ],
		'optional'     : True,
		'has_tail'     : 0,
		'word_index'   : 'help',
		'prerequisite' : '__alone__',
		'description'  : 'Zobrazi napovedu k programu.'
	},
	{
		'names'        : [ '--test',   '-t' ],
		'optional'     : True,
		'has_tail'     : 0,
		'word_index'   : 'test',
		'prerequisite' : '__alone__',
		'description'  : 'Misto kolekce odkazu provede test spravnosti rss zdroju. ' +
						 'Pri nalezeni nekorektniho zdroje se pokusi na strance vyhledat ' +
						 'alternativni zdroje pro rss.'
	},
	{
		'names'        : [ '--wait',   '-w' ],
		'optional'     : True,
		'has_tail'     : 1,
		'word_index'   : 'wait',
		'prerequisite' : None,
		'description'  : 'Urcuje jak dlouho se ma cekat ( v sekundach ) na odpoved serveru, ze ' +
						 'ktereho se stahuje stranka s odkazy. Vychozi hodnota je 15.'
	},
]

settings = dict()
try:
	settings = get_setting( possible_arguments, sys.argv[1:] )
except:
	if ( '-h' == sys.argv[1] or '--help' == sys.argv[1]) :
		print_help( possible_arguments, sys.argv[0], sys.stdout, author )
		exit(0)
	else:
		raise

if (  'help' in settings):
	print_help( possible_arguments, sys.argv[0], sys.stdout, author )
	exit(0)

wait = 15
if ( 'wait' in settings ):
	wait = settings[ 'wait' ]

if ( not ( 'input' in settings ) ):
	settings[ 'input' ] = [ sys.stdin ]

if ( 'append' in settings ):
	if ( 'dedup' in settings ):
		settings[ 'dedup' ].append( settings[ 'append' ][0] )
	else:
		settings[ 'dedup' ] = settings[ 'append' ]

dedup_links = set()
if ( 'dedup' in settings ):
	for file_name in settings[ 'dedup' ]:
		with open( file_name, 'r' ) as dedup_file:
			for line in dedup_file:
				dedup_links.add( line.strip() )
out = sys.stdout
if ( 'output' in settings ):
	if ( 'append' in settings ):
		out = open( settings[ 'output' ][0], 'a' )
	else:
		out = open( settings[ 'output' ][0], 'w' )

rss_links = set()
test      = True if ( 'test' in settings ) else False

for file_name in settings[ 'input' ]:
	input_file = None
	try:
		input_file = open( file_name, 'r' ) if ( type( file_name ) is str ) else file_name
	except Exception as ext:
		sys.stderr.write( 'Nelze otevrit vstupni soubor"' + file_name + '", soubor preskakuji a pokracuji v cinnosti.\n\n' )
		sys.stderr.write( str( ext ) + '\n\n==\n' )
		continue
	for line in input_file:
		rss_links.add( line.strip() )
	input_file.close()

for rss_source in rss_links:
	custom_parse = False
	custom_links = list()
	page         = get_page_from_url( rss_source, wait )
	if ( page[ 'error' ] ):
		sys.stderr.write( '-ERR ' + rss_source + '\n' )
		sys.stderr.write( '-ERR_START\n' )
		sys.stderr.write( page[ 'value' ] )
		sys.stderr.write( '-ERR_END\n' )
		continue
	else:
		page = page[ 'value' ]
	try:
		root = ET.fromstring( page )
		if ( test ):
			continue
	except:
		custom_parse = True
		if ( test ):
			custom_links = find_rss_links( page )
		else:
			custom_links = get_data_from_xml( 'link', page )
	items = list()
	if ( custom_parse ):
		items = custom_links
		for link in items:
			if ( link and ( not ( link in dedup_links ) ) ):
				out.write( link + '\n' )
				dedup_links.add( link )
	else:
		items = [ x for x in root.getchildren()[0].getchildren() if x.tag == "item" ]
		for item in items:
				link = item.find( 'link' )
				if ( not ( link is None ) ):
					link = link.text
					link = link.strip()
					if ( link and ( not ( link in dedup_links ) ) ):
						out.write( link + '\n' )
						dedup_links.add( link )
	if ( not test ):
		sys.stderr.write( '+OK ' + rss_source + '\n' )
