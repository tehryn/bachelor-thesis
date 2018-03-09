#!/usr/bin/env python3
import sys, os
from Link_collector import Link_collector
from Functions import get_setting, print_help, get_exception_info

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
		'prerequisite' : None,
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
						 'ktereho se stahuje stranka s odkazy. Vychozi hodnota je 1.'
	},
	{
		'names'        : [ '--multithreading',   '-m' ],
		'optional'     : True,
		'has_tail'     : 1,
		'word_index'   : 'threads',
		'prerequisite' : None,
		'description'  : 'Urcuje kolik vlaken se spusti pro stahovani stranek, doporucuji pouzit ' +
						 'pri nastaveni wait > 1 nebo pri velkem nozstvi rss zdroju. Vychozi hodnota je 0.'
	},
	{
		'names'        : [ '--errors',   '-e' ],
		'optional'     : True,
		'has_tail'     : 1,
		'word_index'   : 'error',
		'prerequisite' : None,
		'description'  : 'Pokud je nastaven, tak namisto stderr jsou chyby vypisovany do souboru urcenho ' +
						 'timto parametrem.'
	}
]

settings = dict()
try:
	settings = get_setting( possible_arguments, sys.argv[1:] )
except:
	if ( len( sys.argv ) > 1 and ( '-h' == sys.argv[1] or '--help' == sys.argv[1] ) ):
		print_help( possible_arguments, sys.argv[0], sys.stdout, author )
		exit(0)
	else:
		raise

if ( 'help' in settings):
	print_help( possible_arguments, sys.argv[0], sys.stdout, author )
	exit(0)

wait = 1
if ( 'wait' in settings ):
	wait = int( settings[ 'wait' ][0] )

threads = 0
if ( 'threads' in settings ):
	threads = int( settings[ 'threads' ][0] )
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

err = sys.stderr
if ( 'error' in settings ):
	err = open( settings[ 'error' ][0], 'w' )

rss_links = set()
for file_name in settings[ 'input' ]:
	input_file = None
	try:
		input_file = open( file_name, 'r' ) if ( type( file_name ) is str ) else file_name
	except:
		error = get_exception_info( 'Nelze otevrit vstupni soubor "' + file_name + '", soubor preskakuji a pokracuji v cinnosti.\n\n' )
		err.write( error );
		continue
	for line in input_file:
		rss_links.add( line.strip() )
	input_file.close()


collector = Link_collector( dedup=dedup_links, wait=wait )
test      = True if ( 'test' in settings ) else False
if threads == 0:
	for rss_source in rss_links:
		new_links = collector.collect_links_from_url( rss_source )
		if new_links:
			for link in new_links:
				out.write( link + '\n' )
			errors = collector.get_errors_info();
			err.write( errors )

else:
	pages = list()
	rss_sources = list()
	for rss_source in rss_links:
		rss_sources.append( rss_source )
		if len( rss_sources ) <= threads:
			continue
		else:
			new_links = collector.collect_links_from_urls( rss_sources )
			for link in new_links:
				out.write( link + '\n' )
			errors = collector.get_errors_info();
			err.write( errors )
			rss_sources = list()

	if ( len( rss_sources ) > 0 ):
		new_links = collector.collect_links_from_urls( rss_sources )
		for link in new_links:
			out.write( link + '\n' )
		errors = collector.get_errors_info();
		err.write( errors )
