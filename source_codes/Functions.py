"""Modul, jehoz obsahem jsou uzitecne funkce, ktere se pouzivaji napric skriptu a modulu."""
import sys
import traceback
import chardet

#Exception save on correct use
def decode_data( data, new_coding='UTF-8' ):
    """Metoda zjisti, v jakem kodovani je obsah a prelozi ho do jineho kodovani."""
    encoding = chardet.detect( data )[ 'encoding' ]
    data = data.decode( encoding )
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
    tail                = list()
    settings         = { '__alone__' : True }
    possible_tags    = [ y for x in possible_arguments for y in x['names'] ]
    defined_counter  = 0
    for arg in list_of_arguments:
        defined_counter += 1
        if arg.startswith( '-' ):
            if ( ( arg in possible_tags ) ):
                if ( isinstance( current_tag, dict ) ):
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
        elif ( isinstance( current_tag, dict ) ):
            if ( current_tag_int != 0 ):
                if ( arg not in tail ):
                    tail.append( arg )
                else:
                    raise Exception( 'Parametr "' + arg + '"  pro argument "' + current_tag_name + '" je zadan vicekrat.' )
            else:
                raise Exception( 'Argument "' + current_tag_name +'" neocekava zadny dalsi parametr, zadal/a jste "' + arg + '".' )
        else:
            raise Exception( 'Spatne vstupni argumenty, spuste s argumentem "--help" pro ziskani napovedy.' )
    if ( current_tag_int is not None ):
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
            if ( item[ 'word_index' ] not in settings ):
                error_list.append( item[ 'names' ][0] )
        if ( ( item[ 'prerequisite' ] is not None ) and ( item[ 'word_index' ] in settings ) ):
            if ( item[ 'prerequisite' ] == '__alone__' and defined_counter > 1 ):
                raise Exception( 'Argument "' + item[ 'names' ][0] + '" musi byt zadan samostatne' )
            elif ( item[ 'prerequisite' ] not in settings ):
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
    """Metoda vrati veskere informace o aktualnim miste v kodu. Vhodne pro vypis chyb."""
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
        output.write( help_str + ' - ' + arg[ 'description' ] + '\n\n' )
    for arg in optional:
        help_str = ', '.join( arg[ 'names' ] )
        output.write( help_str + ' - ' + arg[ 'description' ] + '\n\n' )
    output.write( author + '\n' )

#Exception save on correct use
def get_data_from_xml( token, page ):
    """Funkce nalezne potrebny obsah tokenu v xml strance. Vrati mnozinu vsech techto obsahu."""
    data  = set()
    found = True
    while ( found ):
        found = False
        idx1  = page.find( '<' + token )
        if ( idx1 >= 0 ):
            idx1 = page.find( '>', idx1 )
            if ( idx1 >= 0 ):
                idx2 = page.find( '</' + token )
                if ( idx2 >= 0 and idx2 > idx1 ):
                    found = True
                    data.add( page[ idx1+1:idx2 ].strip() )
                    page = page[idx2+1:]
    return data

def find_nth( string, substr, n ):
    """Funkce najde N-ty prvek v retezci. Pokud je prvek nalezen, je vracen jeho index, jinak je vracena -1"""
    start = string.find( substr )
    while start >= 0 and n > 1:
        start = string.find( substr, start + len( substr ) )
        n -= 1
    return start
