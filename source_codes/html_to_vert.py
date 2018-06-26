#!/usr/bin/env python3
"""
Author: Jiri Matejka (xmatej52)

Toto je obsluzny skript pro tridu Page_tokenizer, kde je implementovan proces Vertikalizace.
"""
import sys
import lzma
from Functions import get_setting, print_help
from Page_tokenizer import Page_tokenizer

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
        'optional'     : True,
        'has_tail'     : 1,
        'word_index'   : 'output',
        'prerequisite' : None,
        'description'  : 'Vystupni soubor, kam se budou ukladat stazene stranky. Vystupni soubor ' +
                         'by mel mit vzdy koncovku vert.xz nebo .vert.'
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
        'names'        : [ '--multiprocessing',   '-m' ],
        'optional'     : True,
        'has_tail'     : 1,
        'word_index'   : 'processes',
        'prerequisite' : None,
        'description'  : 'Urcuje kolik procesu bude provadet tokenizaci a vertikalizaci. Doporucuji pouzit ' +
                         'minimalne 3 procesy (pokud bude prilis malo procesu, vzroste pametova narocnost ' +
                         'zpracovani). Vychozi hodnota je 10.'
    },
    {
        'names'        : [ '--tokenizer',   '-t' ],
        'optional'     : False,
        'has_tail'     : 1,
        'word_index'   : 'tokenizer',
        'prerequisite' : None,
        'description'  : 'Cesta k binarnimu souboru tokenizeru.'
    },
    {
        'names'        : [ '--format_new',   '-f' ],
        'optional'     : True,
        'has_tail'     : 0,
        'word_index'   : 'format',
        'prerequisite' : None,
        'description'  : 'Pokud je tento parametr zadán, použije se starý formát vertikálu.'
    },
    {
        'names'        : [ '--langdetect',   '-l' ],
        'optional'     : True,
        'has_tail'     : 0,
        'word_index'   : 'langdetect',
        'prerequisite' : 'format',
        'description'  : 'Pokud je tento parametr zadan, bude provadena detekce jazyka. Lze kombinovat pouze s parametrem --format_new'
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
    if ( len( sys.argv ) > 1 and ( sys.argv[1] == '-h' or sys.argv[1] == '--help' ) ):
        print_help( possible_arguments, sys.argv[0], sys.stdout, author )
        exit(0)
    else:
        raise

out = sys.stdout
use_lzma = False
if ( 'output' in settings ):
    if ( settings[ 'output' ][0].endswith('.xz') ):
        use_lzma = True
        out = lzma.open( settings[ 'output' ][0], 'wb' )
    else:
        out = open( settings[ 'output' ][0], 'w' )

processes = 10
if ( 'processes' in settings ):
    processes = int( settings[ 'processes' ][0] )

if ( 'input' not in settings ):
    settings[ 'input' ] = list()
    settings[ 'input' ].append( None )

old_format = True if ( 'format' in settings ) else False
langdetect = True if ( 'langdetect' in settings ) else False

for filename in settings[ 'input' ]:
    tokenizer = Page_tokenizer( filename = filename, tokenizer_bin = settings['tokenizer'][0], processes = processes, old_style = old_format, lang_detect = langdetect )

    for record in tokenizer:
        if ( use_lzma ):
            out.write( record.encode() )
        else:
            out.write( record )

    error = tokenizer.get_errors_info()
    if ( error ):
        if ( 'error' in settings ):
            with open( settings[ 'error' ][0], 'a' ) as err:
                err.write( error )
        else:
            sys.stderr.write( error )
