#!/usr/bin/env python3
import sys, os, time, subprocess
from Functions import get_setting, print_help, get_exception_info

author = "Author:\n" + \
		 "  Jmeno: Jiri Matejka\n" + \
		 "  Email: xmatej52@stud.fit.vutbr.cz nebo jiri.matejkaa@gmail.com\n" + \
		 "  FIT VUT v Brne, Vyzkumna skupina KNOT@FIT"

possible_arguments = [
	{
		'names'        : [ '--collector',  '-c' ],
		'optional'     : True,
		'has_tail'     : 1,
		'word_index'   : 'collector',
		'prerequisite' : None,
		'description'  : 'Casovy udaj v minutach (musi byt cele cislo typu Int) ' +
                         'udavajici jak casto se ma spoustet kolekce odkazu. ' +
						 'Vychozi hodnota je 120 minut.'
	},
	{
		'names'        : [ '--downloader',  '-d' ],
		'optional'     : True,
		'has_tail'     : 1,
		'word_index'   : 'downloader',
		'prerequisite' : None,
		'description'  : 'Casovy udaj v hodinach (musi byt cele cislo typu Int) ' +
                         'udavajici jak casto se ma spoustet stahovani stranek. ' +
						 'Vychozi hodnota je 24 hodin.'
	},
	{
		'names'        : [ '--email', '-e' ],
		'optional'     : False,
		'has_tail'     : 1,
		'word_index'   : 'email',
		'prerequisite' : None,
		'description'  : 'Email, na ktery se maji posilat statisticka data a informace ' +
		                 'o chybach.'
	},
	{
		'names'        : [ '--attachment', '-a' ],
		'optional'     : True,
		'has_tail'     : 0,
		'word_index'   : 'attachment',
		'prerequisite' : 'email',
		'description'  : 'Pokud je parametr nastaven, budou odeslany i soubory se statistikami ' +
		                 'jako priloha emailu.'
	},
	{
		'names'        : [ '--logs', '-l' ],
		'optional'     : True,
		'has_tail'     : 0,
		'word_index'   : 'logs',
		'prerequisite' : 'attachment',
		'description'  : 'Pokud je parametr nastaven, budou odeslany vedle statistik i logy ' +
		                 'jako priloha emailu.'
	},
	{
		'names'        : [ '--interval', '-i' ],
		'optional'     : True,
		'has_tail'     : 1,
		'word_index'   : 'interval',
		'prerequisite' : None,
		'description'  : 'Casovy udaj v hodinach (musi byt cele cislo typu Int) ' +
                         'udavajici jak casto se budou odesilat statistiky. ' +
						 'Pokud neni argument zadan, budou zasilany jen hlaseni ' +
						 'o kritickych chybach.'
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
		'names'        : [ '--statistiks',   '-s' ],
		'optional'     : False,
		'has_tail'     : 1,
		'word_index'   : 'statistiks',
		'prerequisite' : None,
		'description'  : 'Soubor, do ktereho bude vedena statistika. Soubro bude otevren v rezimu append a ve formatu csv.'
	},
	{
		'names'        : [ '--output',   '-o' ],
		'optional'     : False,
		'has_tail'     : 1,
		'word_index'   : 'output',
		'prerequisite' : None,
		'description'  : 'Slozka, ve ktere se budou ukladat stazene stranky.'
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

# Nastavim si cestu k projektu
path = os.path.abspath( '.' )

# Cesta k rss zdrojim. Klice pouziju jako jmena slozek v logach a stazenych souborech.
rss_sources = {
	'newsbrief_eu' : path + '/newsbrief_eu.txt',
	'cs_media'     : path + '/cs_media.txt',
	'blogs'        : path + '/blogs.txt',
	'other'        : path + '/other.txt'
}

trash_in_folders    = dict()
files_to_download   = dict()
downloaded_files    = dict()
for key in rss_sources:
	files_to_download[ key ] = set()
	downloaded_files[ key ]  = set()
	trash_in_folders[ key ]  = set()

# Ulozim si nastaveni parametru do promennych.
download_interval  = int( settings[ 'downloader' ][0] ) if ( 'downloader' in settings ) else 24
download_interval *= 3600
collect_interval   = int( settings[ 'collector' ][0] ) if ( 'collector' in settings ) else 120
collect_interval  *= 60
email_attachment   = True if ( 'attachment' in settings ) else False
statistiks_file    = settings[ 'statistiks' ][0]
output_directory   = settings[ 'output' ][0][::-1] if settings[ 'output' ][0].endswith( '/' ) else settings[ 'output' ][0]
email_interval     = int( settings[ 'interval' ][0] ) * 3600 if ( 'interval' in settings ) else None
email              = settings[ 'email' ][0]
email_logs         = True if ( 'logs' in settings ) else False

while ( True ):
	collection_start    = time.time()
	collection_filename = time.strftime( "%d%m%Y%H%M", time.localtime( collection_start ) )
	for key in rss_sources:
		output_file = path + '/collected_links/' + key + '/' + collection_filename + '.collected'
		files_to_download[ key ].add( output_file )
		log_file    = path + '/logs/' + key + '/' + collection_filename + '.link_collector'
		dedup_files = os.listdir( path + '/collected_links/' + key )
		dedup_files = ' '.join( dedup_files )
		collector   = [ path + '/link_collector.py', '-i', rss_source[ key ], '-o', output_file, '-e', log_file, '-d', dedup_files, '-w', '5', '-m', '50' ]
		process     = subprocess.Popen( collector, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
		stdout, stderr = process.communicate()

	download_start    = time.time()
	download_filename = time.strftime( "%d%m%Y%H%M", time.localtime( download_start ) )
	for key in rss_sources:
		if not os.path.exists( output_directory + '/' + key + '/' ):
			os.makedirs( output_directory + '/' + key + '/' )

		output_file = output_directory + '/' + key + '/' + download_filename + '.warc.xz'
		input_files = ' '.join( files_to_download[ key ] )
		log_file    = path + '/logs/' + key + '/' + download_filename + '.page_downloader'
		downloader  = [ path + '/page_downloader.py', '-i', input_files, '-o', output_file, '-e', log_file, '-w', '5' ]
		process     = subprocess.Popen( collector, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
		stdout, stderr = process.communicate()

	break;
