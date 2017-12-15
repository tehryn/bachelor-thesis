import sys, os
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
						 'nemaji byt stazeny.'
	},
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
		'description'  : 'Vystupni soubor, kam se budou ukladat stazene stranky ' +
                         'Berte na vedomi, ze k souboru bude pridana pripona _lang.warc.xz, ' +
						 'kde lang znaci jazyk stranek v souboru (napr cz nebo sk)'
	},
	{
		'names'        : [ '--append', '-a' ],
		'optional'     : True,
		'has_tail'     : 0,
		'word_index'   : 'append',
		'prerequisite' : 'output',
		'description'  : 'Vystupni soubor bude otevren v modu "append", tzn. pokud ' +
						 'soubor jiz existuje, nebude jeho puvodni obsah smazan, ' +
						 'stazene stranky budou pridany na jeho konec. Navic se obsah souboru ' +
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
		'names'        : [ '--wait',   '-w' ],
		'optional'     : True,
		'has_tail'     : 1,
		'word_index'   : 'wait',
		'prerequisite' : None,
		'description'  : 'Urcuje jak dlouho se ma cekat ( v sekundach ) na odpoved serveru, ze ' +
						 'ktereho se stahuje stranka s odkazy. Vychozi hodnota je 15.'
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
		'names'        : [ '--languages', '-l' ],
		'optional'     : False,
		'has_tail'     : 2,
		'word_index'   : 'lang',
		'prerequisite' : None,
		'description'  : 'Povolene jazyky stranek. Berte na vedomi, ze pro kazdy ' +
						 'zadany jazyk bude otevren novy soubor. Stranky, ktere ' +
						 'nebudou v jednom ze zadanych jazyku, budou ulozeny v souboru ' +
						 's priponou _other.warc.xz. Detekci jazyka lze vypnout parametrem ' +
						 '-n, tehdy se ocekava pouze jeden zadany jazyk a soubor s priponou ' +
						 '_other.warc.xz nebude vytvoren. Podporovane jazyky jsou cz a sk (cestina a slovenstina).'
	},
	{
		'names'        : [ '--no_lang_detect', '-n' ],
		'optional'     : True,
		'has_tail'     : 0,
		'word_index'   : 'no_lang',
		'prerequisite' : None,
		'description'  : 'Vypne detekci jazyka. Berte na vedomi ze stale musite pouzit ' +
						 'argument -l prave s jednim parametrem.'
	}
]
settings = dict()
try:
	settings = get_setting( possible_arguments, sys.argv[1:] )
except:
	print( sys.argv )
	if ( '-h' == sys.argv[1] or '--help' == sys.argv[1]) :
		print_help( possible_arguments, sys.argv[0], sys.stdout, author )
		exit(0)
	else:
		raise

wait = 15
if ( 'wait' in settings ):
	wait = settings[ 'wait' ]

pause = 1
if ( 'pause' in settings ):
	pause = settings[ 'pause' ]

supported_languages = { 'cz', 'sk' }
languages = set()
for lang in settings[ 'lang' ]:
	if ( lang in supported_languages ):
		languages.add(lang)
	else:
		sys.stderr.write( "-FATAL Jazyk " + lang + " neni podporovan.\n" )
		exit(1)

if ( ( 'no_lang' in settings ) and ( languages.size() != 1 ) ):
		sys.stderr.write( "-FATAL Zadal jste vice jazyku spolu s parametrem --no_lang_detect." )
		sys.stderr.write( " Pokud si nevite rady, spuste program s parametrem -h\n" )
		exit(1)

print( settings )
