#!/usr/bin/env python3
"""Skript page_downloader slouzi ke stahovani stranek."""
import sys
import lzma
import subprocess
import warc
from Functions import get_setting, print_help, get_exception_info
from Page_generator import Page_generator

author = "Author:\n" + \
         "  Jmeno: Jiri Matejka\n" + \
         "  Email: xmatej52@stud.fit.vutbr.cz nebo jiri.matejkaa@gmail.com\n" + \
         "  FIT VUT v Brne, Vyzkumna skupina KNOT@FIT"

possible_arguments = [
    {
        'names'        : [ '--input',  '-i' ],
        'optional'     : True,
        'has_tail'     : 2,
        'word_index'   : 'input',
        'prerequisite' : None,
        'description'  : 'Cesta k souboru nebo souborum, ktere obsahuji adresy na ' +
                         'stranky ke stazeni. Pokud parametr neni zadan, odkazy jsou ' +
                         'ocekavany na standartnim vstupu'
    },
    {
        'names'        : [ '--output', '-o' ],
        'optional'     : False,
        'has_tail'     : 1,
        'word_index'   : 'output',
        'prerequisite' : None,
        'description'  : 'Vystupni soubor, kam se budou ukladat stazene stranky. Vystupni soubor ' +
                         'by mel mit vzdy koncovku .warc.xz.'
    },
    {
        'names'        : [ '--stored', '-s' ],
        'optional'     : True,
        'has_tail'     : 1,
        'word_index'   : 'stored',
        'prerequisite' : None,
        'description'  : 'Vystupni soubor, kam se budou ukladat odkazy na stazene stranky. Soubor ' +
                         'je otevren v rezimu append Vychozi hodnota je standardni vystup.'
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
        'names'        : [ '--wait',   '-w' ],
        'optional'     : True,
        'has_tail'     : 1,
        'word_index'   : 'wait',
        'prerequisite' : None,
        'description'  : 'Urcuje jak dlouho se ma cekat ( v sekundach ) na odpoved serveru, ze ' +
                         'ktereho se stahuje stranka s odkazy. Vychozi hodnota je 1.'
    },
    {
        'names'        : [ '--pause',   '-p' ],
        'optional'     : True,
        'has_tail'     : 1,
        'word_index'   : 'wait',
        'prerequisite' : None,
        'description'  : 'Urcuje minimalni cas mezi 2 pripojenimi k jednomu serveru. ' +
                         'Vychozi hodnota je 1.'
    },
    {
        'names'        : [ '--errors',   '-e' ],
        'optional'     : True,
        'has_tail'     : 1,
        'word_index'   : 'error',
        'prerequisite' : None,
        'description'  : 'Pokud je nastaven, tak namisto stderr jsou chyby vypisovany do souboru urcenho ' +
                         'timto parametrem.'
    },
    {
        'names'        : [ '--multithreading',   '-m' ],
        'optional'     : True,
        'has_tail'     : 1,
        'word_index'   : 'threads',
        'prerequisite' : None,
        'description'  : 'Urcuje kolik vlaken se spusti pro stahovani stranek, doporucuji pouzit' +
                         'pri velkem mnozstvi stranek. Vychozi hodnota je 0.'
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

wait = 1
if ( 'wait' in settings ):
    wait = settings[ 'wait' ][0]

pause = 1
if ( 'pause' in settings ):
    pause = settings[ 'pause' ][0]

err = sys.stderr
if ( 'error' in settings ):
    err = open( settings[ 'error' ][0], 'w' )

stored = sys.stdout
if ( 'stored' in settings ):
    stored = open( settings[ 'stored' ][0], 'a' )

threads = 0
if ( 'threads' in settings ):
    threads = int( settings[ 'threads' ][0] )

download_links = set()
if ( 'input' not in settings ):
    settings[ 'input' ] = [ sys.stdin ]

for file_name in settings[ 'input' ]:
    input_file = None
    try:
        input_file = open( file_name, 'r' ) if ( isinstance( file_name, str ) ) else file_name
    except:
        error = get_exception_info( 'Nelze otevrit vstupni soubor "' + file_name + '", soubor preskakuji a pokracuji v cinnosti.\n\n' )
        err.write( error )
        continue
    for line in input_file:
        download_links.add( line.strip() )
    input_file.close()

out       = lzma.open( settings[ 'output' ][0], 'wb' )
generator = Page_generator( pause=pause, wait=wait, iterable=download_links, threads=threads )
hostname  = subprocess.check_output( "hostname -f", shell=True).decode( 'utf-8' )
user      = subprocess.check_output( "echo $USER", shell=True).decode( 'utf-8' )

body  = "robots: classic\r\nhostname: " + str( hostname ) + "software: download.py\r\nisPartOf: Cs_media\r\n"
body += "operator: " + str( user ) + "description: Downloading cz and sk articles\r\npublisher: KNOT (https://knot.fit.vutbr.cz/)\r\n"
body += "format: WARC File Format 1.0\r\nconformsTo: http://bibnum.bnf.fr/WARC/WARC_ISO_28500_version1_latestdraft.pdf\r\n"

warc_header = warc.WARCHeader( { "WARC-Type": "warcinfo", "WARC-Filename" : settings[ 'output' ][0] }, defaults=True )
warc_record = warc.WARCRecord( warc_header, body.encode() )
warc_record.write_to( out )

for page in generator:
    warc_header = warc.WARCHeader( { "WARC-Type": "response", "WARC-Target-URI": page[ 'url' ] }, defaults=True )
    response = page[ 'response' ]
    if not( response.endswith( '\r\n\r\n' ) ):
        response += '\r\n\r\n'
    warc_record = warc.WARCRecord( warc_header, ( response + page[ 'content' ] ).encode( 'utf-8', 'replace' ) )
    warc_record.write_to( out )
    stored.write( page[ 'url' ] + '\n' )

sys.stderr.write( generator.get_errors_info() )
