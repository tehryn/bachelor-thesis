import multiprocessing
import pexpect
import langdetect
from Page_reader import Page_reader
from Page import Page

class Page_parser( object ):
    def __init__( self, tagger_bin, tagger_file, timeout = 0, filename = None, method = 'clean' ):
        self._page_reader = Page_reader( filename )
        self._tagger_bin  = tagger_bin
        self._tagger_file = tagger_file
        self._timeout     = timeout
        self._method      = method

    @staticmethod
    def _translator( par_queue, lock_ready, lock_done ):
        par = ''
        while ( True ):
            lock_ready.acquire()
            par = par_queue.get()
            if ( par is not None ):
                lang = ''
                try:
                    lang = langdetect.detect( par )
                except:
                    lang = '?'
                par_queue.put( lang )
                lock_done.release()
            else:
                break

    def _morphodita_clean( self, input_queue, output_queue ):
        par_lang        = multiprocessing.Queue( maxsize=1 )
        lang_lock_start = multiprocessing.Lock()
        lang_lock_read  = multiprocessing.Lock()
        lang_lock_start.acquire()
        lang_lock_read.acquire()
        translator = multiprocessing.Process( target = self._translator, args = ( par_lang, lang_lock_start, lang_lock_read ) )
        translator.start()
        ret_value = ''
        send_buff = ''
        command   = self._tagger_bin + ' --input=untokenized --output=vertical ' + self._tagger_file
        process   = pexpect.spawn( command )
        process.setecho(False)
        process.readline()
        process.timeout = self._timeout
        while ( True ):
            page = input_queue.get()
            if ( page is not None ):
                for line in page.splitlines():
                    if ( line.startswith( '<' ) ):
                        if ( send_buff ):
                            par_lang.put( send_buff )
                            lang_lock_start.release()
                            process.send( send_buff + '\n' )
                            send_buff   = ''
                            try:
                                while ( True ):
                                    tagged_text = process.read_nonblocking( size=10000 )
                                    ret_value += tagged_text.decode()
                            except pexpect.exceptions.TIMEOUT:
                                lang_lock_read.acquire()
                                ret_value += line[:-1] + ' lang="' + par_lang.get() + '">' + '\n'
                    else:
                        send_buff += line + '\n'
                output_queue.put( ret_value )
                sys.stderr.write( 'done\n' )
                ret_value = ''
            else:
                par_lang.put( None )
                lang_lock_start.release()
                output_queue.put( None )
                break

    def _morphodita_replace( self, input_queue, output_queue ):
        command   = self._tagger_bin + ' --input=untokenized --output=vertical ' + self._tagger_file
        process   = pexpect.spawn( command )
        process.setecho(False)
        process.readline()
        process.timeout = self._timeout
        removed_links = list()
        while ( True ):
            ret_value = ''
            send_buff = ''
            page = input_queue.get()
            if ( page is not None ):
                for line in page.splitlines():
                    if ( line.startswith( '<' ) ):
                        if ( line.startswith( '<link' ) ):
                            removed_links.append( line[7:-2] )
                            line = '<link>'
                        elif ( line.startswith( '<img' ) ):
                            removed_links.append( line[6:-2] )
                            line = '<img>'
                        line = Page.decode_tag( line )
                        line = '\n' + line + '\n'
                    send_buff += line + '\n'
                sys.stderr.write( 'sending' + str( len( send_buff ) ) + '\n' )
                process.send( send_buff + '\n' )
                sys.stderr.write( 'sent\n' )
                try:
                    while ( True ):
                        tagged_text = process.read_nonblocking( size = 999999 )
                        ret_value += tagged_text.decode()
                except pexpect.exceptions.TIMEOUT:
                    pass
                replaced = ''
                for line in ret_value.splitlines():
                    if ( line.startswith( Page.tag_begin ) ):
                        idx = line.find( '\t' )
                        line = line[:idx]
                        line = Page.decode_tag( line )
                        if ( line == '<link>' ):
                            href = removed_links.pop()
                            line = '<link="' + href +'">'
                        elif ( line == '<img>' ):
                            href = removed_links.pop()
                            line = '<img="' + href +'">'
                    replaced += line
                output_queue.put( ret_value )
                sys.stderr.write( 'done\n' )
                ret_value = ''
            else:
                output_queue.put( None )
                break

    def __iter__( self ):
        input_queue  = multiprocessing.Queue()
        output_queue = multiprocessing.Queue()
        finished     = multiprocessing.Lock()
        finished.acquire()

        morphodita = None
        if ( self._method == 'clean' ):
            morphodita = multiprocessing.Process( target = self._morphodita_clean, args = ( input_queue, output_queue ) )
        else:
            morphodita = multiprocessing.Process( target = self._morphodita_replace, args = ( input_queue, output_queue ) )
        morphodita.start()

        for page in self._page_reader:
            input_queue.put( page.get_text() )
            try:
                while ( True ):
                    yield output_queue.get( block = False )
            except:
                pass
        input_queue.put( None )
        while ( True ):
            tagged = output_queue.get()
            if ( tagged is not None ):
                yield tagged
            else:
                break



if __name__ == '__main__':
    # input_file tagger_bin tagger_file timeout method
    import sys
    parser = Page_parser( tagger_bin = sys.argv[2], tagger_file = sys.argv[3], filename = sys.argv[1], timeout = float( sys.argv[4] ), method = sys.argv[5] )
    for tagged in parser:
        print( tagged )