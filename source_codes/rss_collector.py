#!/usr/bin/env python3
"""
Tento skript slouzi ke kolekci odkazu.
Autor: Jiří Matějka
Verze: 2.002 (2018-04-10)
"""
import sys
from Page_reader import Page_reader
from Functions import get_setting, print_help

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
                         'nemaji oznaceny jako nove RSS zdroje.'
    },
    {
        'names'        : [ '--input',  '-i' ],
        'optional'     : True,
        'has_tail'     : 2,
        'word_index'   : 'input',
        'prerequisite' : None,
        'description'  : 'Cesta k souboru nebo souborum, kde se nachazeji stazene stranky.'
    },
    {
        'names'        : [ '--output', '-o' ],
        'optional'     : True,
        'has_tail'     : 1,
        'word_index'   : 'output',
        'prerequisite' : None,
        'description'  : 'Vystupni soubor, kam se ulozi nalezene odkazy. Soubor je otevren v rezimu append.'
    },
    {
        'names'        : [ '--help',   '-h' ],
        'optional'     : True,
        'has_tail'     : 0,
        'word_index'   : 'help',
        'prerequisite' : '__alone__',
        'description'  : 'Zobrazi napovedu k programu.'
    },
]

settings = dict()
try:
    settings = get_setting( possible_arguments, sys.argv[1:] )
except:
    if ( len( sys.argv ) > 1 and ( sys.argv[1] == '-h' or sys.argv[1] == '--help' ) ):
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

if ( 'input' not in settings ):
    settings[ 'input' ] = [ None ]

dedup_links = set()
if ( 'dedup' in settings ):
    for file_name in settings[ 'dedup' ]:
        with open( file_name, 'r' ) as dedup_file:
            for line in dedup_file:
                dedup_links.add( line.strip() )

out = sys.stdout
if ( 'output' in settings ):
    out = open( settings[ 'output' ][0], 'a' )

for file_name in settings[ 'input' ]:
    page_reader = Page_reader( filename = settings[ 'input' ][0] )
    for page in page_reader:
        for link in page.find_rss():
            if ( link not in dedup_links ):
                dedup_links.add( link )
                out.write( link + '\n' )
