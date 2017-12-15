import sys, os, chardet, traceback
import re;
from urllib.request import urlopen
from subprocess import Popen, PIPE, check_output

#Exception save on correct use
def decode_data( data, new_coding='UTF-8' ):
	encoding = chardet.detect( data )[ 'encoding' ]
	data = data.decode( encoding, data )
	return data

#Exception unsave
def get_setting ( possible_arguments, list_of_arguments ):
	def find_tag( argument ):
		found_tag = None
		for tag in possible_arguments:
			if ( argument in tag[ 'names' ] ):
				found_tag = tag
				break
		return found_tag

	current_tag      = None
	current_tag_name = None
	current_tag_int  = None
	tail       	     = list()
	settings         = { '__alone__' : True }
	possible_tags    = [ y for x in possible_arguments for y in x['names'] ]
	defined_counter  = 0
	for arg in list_of_arguments:
		defined_counter += 1
		if arg.startswith( '-' ):
			if ( ( arg in possible_tags ) ):
				if ( type( current_tag ) is dict ):
					tail_len = len( tail )
					if ( ( current_tag_int == tail_len  ) or ( current_tag_int == 2 and tail_len > 0 ) ):
						settings[ current_tag[ 'word_index' ] ] = tail
						current_tag      = find_tag( arg )
						if ( current_tag[ 'word_index' ] in settings ):
							error_str  = ', '.join( current_tag[ 'names' ] )
							if ( len( current_tag[ 'names' ] ) > 1 ):
								raise Exception( 'Argumenty "' + error_str + '" znamenaji to same a jsou zadany vicekrat nez jednou.'  )
							else:
								raise Exception( 'Argument ' + error_str + ' je zadan vicekrat nez jednou.'  )
						current_tag_int  = int( current_tag[ 'has_tail' ] )
						if ( current_tag_int == 0 ):
							settings[ current_tag[ 'word_index' ] ] = True
						current_tag_name = arg
						tail             = []
					elif ( current_tag_int == 1):
						raise Exception( 'Argument "' + current_tag_name +'" vyzaduje prave jeden dalsi parametr, zadano ' + str( tail_len ) + '.'  )
					else:
						raise Exception( 'Argument "' + current_tag_name +'" vyzaduje alespon jeden dalsi parametr.'  )
				else:
					current_tag      = find_tag( arg )
					current_tag_int  = int( current_tag[ 'has_tail' ] )
					current_tag_name = arg
			else:
				raise Exception( 'Nepodporovany argument "' + arg +'".' )
		elif ( type( current_tag ) is dict ):
			if ( current_tag_int != 0 ):
				if ( not ( arg in tail ) ):
					tail.append( arg )
				else:
					raise Exception( 'Parametr "' + arg + '"  pro argument "' + current_tag_name + '" je zadan vicekrat.' )
			else:
				raise Exception( 'Argument "' + current_tag_name +'" neocekava zadny dalsi parametr, zadal/a jste "' + arg + '".' )
		else:
			raise Exception( 'Spatne vstupni argumenty, spuste s argumentem "--help" pro ziskani napovedy.' )
	if ( not ( current_tag_int is None ) ):
		if ( current_tag_int > 0 ):
			tail_len = len( tail )
			if ( ( current_tag_int == tail_len  ) or ( current_tag_int == 2 and tail_len > 0 ) ):
				settings[ current_tag[ 'word_index' ] ] = tail
			elif ( current_tag_int == 1):
				raise Exception( 'Argument "' + current_tag_name +'" vyzaduje prave jeden dalsi parametr, zadano ' + str( tail_len ) + '.'  )
			else:
				raise Exception( 'Argument "' + current_tag_name +'" vyzaduje alespon jeden dalsi parametr.'  )
		else:
			settings[ current_tag[ 'word_index' ] ] = True

	error_list = list()
	for item in possible_arguments:
		if ( not item[ 'optional' ] ):
			if ( not ( item[ 'word_index' ] in settings ) ):
				error_list.append( item[ 'names' ][0] )
		if ( not ( item[ 'prerequisite' ] is None ) and ( item[ 'word_index' ] in settings ) ):
			if ( item[ 'prerequisite' ] == '__alone__' and defined_counter > 1 ):
				raise Exception( 'Argument "' + item[ 'names' ][0] + '" musi byt zadan samostatne' )
			elif ( not ( item[ 'prerequisite' ] in settings ) ):
				error_list = [ y for x in possible_arguments for y in x[ 'names' ] if x[ 'word_index' ] == item[ 'prerequisite' ] ]
				error_str = ', '.join ( error_list )
				if ( len( error_list ) > 1 ):
					raise Exception( 'Argument "' + item[ 'names' ][0] + '" lze spustit pouze s argumenty "' + error_str + '".' )
				else:
					raise Exception( 'Argument "' + item[ 'names' ][0] + '" lze spustit pouze s argumentem "' + error_str + '".' )
	if error_list:
		error_str  = ', '.join( error_list )
		raise Exception( 'Argumenty: "' + error_str +'" jsou povinne. Spuste s argumentem "--help" pro ziskani napovedy.' )
	return settings

#Exception save on correct use
def get_exception_info( custom_info='' ):
	type_, value_, traceback_ = sys.exc_info()
	error = traceback.format_exception(type_, value_, traceback_)
	return custom_info + '\n' + ''.join( error )

#Exception save on correct use
def print_help( possible_arguments, file_name, output=sys.stdout, author='Vyzkumna skupina KNOT@FIT' ):
	optional       = [ arg for arg in possible_arguments if arg[ 'optional' ] ]
	optional_str   = [ '[' + ', '.join( arg[ 'names' ] ) + ']' for arg in optional ]
	obligatory     = [ arg for arg in possible_arguments if not arg[ 'optional' ] ]
	obligatory_str = [ '(' + ', '.join( arg[ 'names' ] ) + ')' for arg in obligatory ]
	help_str       = file_name + ' '
	help_str      += ' '.join( obligatory_str ) + ' '
	help_str      += ' '.join( optional_str ) + '\n'
	output.write( help_str )
	for arg in obligatory:
		help_str = ', '.join( arg[ 'names' ] )
		output.write( help_str + ' - ' + arg[ 'description' ] + '\n' )
	for arg in optional:
		help_str = ', '.join( arg[ 'names' ] )
		output.write( help_str + ' - ' + arg[ 'description' ] + '\n' )
	output.write( '\n\n' + author + '\n' )

#Exception save on correct use
def get_data_from_xml( token, page ):
	data  = set()
	idx1  = page.find( '<' + token )
	found = True
	while ( found ):
		found = False
		if ( idx1 >= 0 ):
			idx1 = page.find( '>', idx1 )
			if ( idx1 >= 0 ):
				idx2 = page.find( '</' + token )
				if ( idx2 >= 0 and idx2 > idx1 ):
					found = True
					data.add( page[ idx1+1:idx2 ].strip() )
					page = page[idx2:]
	return data

def find_rss_links( page ):
	data = set()
	urlPat = re.compile(r'((<a|<link) [^<>]*?href=(\"|\')([^<>\"\']*?)(\"|\')[^<>]+)')
	result = re.findall(urlPat, page)
	for link in result:
		if link[0].find( 'type="application/rss' ) > 0:
			data.add( link[3] )
	return data;

#Exception save
def get_page_from_url( url, wait=15 ):
	data = Popen( [ 'wget', '-q', '-T', str( wait ), '-SO', '-', url ], stdout=PIPE, stderr=PIPE )
	page, response = data.communicate()
	exception      = None
	if ( data.returncode == 0 ): # Odpoved je 200 OK
		try:
			page = page.decode( 'utf-8' ) # muze vyhodit vyjimku
		except:
			try:
				page = page.decode( 'utf-8', errors='ignore' ) # muze vyhodit vyjimku
			except:
				info = get_exception_info( 'Nelze dekodovat stazenou stranku "' + url +'"' )
				return { 'error':True, 'value':info }
	else:
		try:
			page = urlopen( url ).read() # muze vyhodit vyjimku
		except:
			info = get_exception_info( 'Nelze cist ze stranky "' + url + '"' )
			return { 'error':True, 'value':info }
	return { 'error':False, 'value':page }
