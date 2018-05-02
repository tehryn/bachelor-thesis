#!/usr/bin/env python3
import sys
import lzma
from Functions import get_setting, print_help, get_exception_info
from Page_tagger import Page_tagger

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
        'description'  : 'Cesta k vertikalnim souborum. Soubor muze byt i komprimovan nastrojem ' +
                         'gzip nebo lzma. V takovem pripade by mel mit koncovku .gz nebo .xz.'
    },
    {
        'names'        : [ '--output', '-o' ],
        'optional'     : True,
        'has_tail'     : 1,
        'word_index'   : 'output',
        'prerequisite' : None,
        'description'  : 'Vystupni soubor, kam se budou ukladat stazene stranky. Vystupni soubor ' +
                         'by mel mit vzdy koncovku tagged.xz nebo .tagged.'
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
        'description'  : 'Urcuje kolik procesu bude provadet tagging. Doporucuji pouzit ' +
                         'minimalne 3 procesy (pokud bude prilis malo procesu, vzroste pametova narocnost ' +
                         'zpracovani). Vychozi hodnota je 10.'
    },
    {
        'names'        : [ '--tagger',   '-t' ],
        'optional'     : False,
        'has_tail'     : 1,
        'word_index'   : 'tagger',
        'prerequisite' : None,
        'description'  : 'Cesta k binarnimu souboru taggeru.'
    },
    {
        'names'        : [ '--languages',   '-l' ],
        'optional'     : False,
        'has_tail'     : 2,
        'word_index'   : 'model',
        'prerequisite' : None,
        'description'  : 'Jazyk a cesta k jeho modelu. Zadavejte ve formatu "cs=/path/to/model en=/path/to/model"' +
                         'Prvni zadany jazyk a model budou pouzit jako vychozi.'
    },
    {
        'names'        : [ '--pages',   '-p' ],
        'optional'     : True,
        'has_tail'     : 1,
        'word_index'   : 'pages',
        'prerequisite' : None,
        'description'  : 'Pocet stranek, ktere se maji najednou zpracovat taggerem. ' +
                         'Vychozi hodnota je 150'
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

out = sys.stdout
if ( 'output' in settings ):
    if ( settings[ 'output' ][0].endswith('.vert') ):
        out = open( settings[ 'output' ][0], 'w' )
    else:
        use_warc = True
        out = lzma.open( settings[ 'output' ][0], 'w' )

processes = 10
if ( 'processes' in settings ):
    processes = int( settings[ 'processes' ][0] )

pages = 150
if ( 'pages' in settings ):
    pages = int( settings[ 'pages' ][0] )

if ( 'input' not in settings ):
    settings[ 'input' ] = list()
    settings[ 'input' ].append( None )


old_format = True if ( 'format' in settings ) else False
langdetect = True if ( 'langdetect' in settings ) else False

Page_tagger.interval = pages

for file in settings['input']:
    tagger = Page_tagger( filename = file, tagger_bin = settings['tagger'][0], processes = processes )

    for model in settings[ 'model' ]:
        lang, model = model.split( '=' )
        tagger.set_language( language = lang, tagger = model )

    for record in tagger.process_tagging():
        out.write( record.encode() )