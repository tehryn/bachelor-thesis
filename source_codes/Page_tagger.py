import sys
import multiprocessing
import subprocess
import re
import lzma
import gzip
from Page import Page
from Page_reader import Page_reader

class Page_tagger( object ):
    interval = 500
    def __init__( self, tagger_bin, tagger_file, filename = None, input_tokenized = False, processes = 10 ):
        self._tagger_bin  = tagger_bin
        self._tagger_file = tagger_file
        self._tokenized   = input_tokenized
        self._processes   = processes
        self._filename    = filename

    @staticmethod
    def set_interval( num ):
        Page_tagger.interval = num

    def _tagger_tokenized( self, input_queue, output_queue ):
        command = [ self._tagger_bin, '--input=untokenized', '--output=vertical', self._tagger_file ]
        while ( True ):
            data = input_queue.get()
            if ( data is not None ):
                process = subprocess.Popen( command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE )
                removed = dict()
                send_buff = ''
                line_num = 1
                for line in data.splitlines():
                    if ( re.match( r'</?doc.*>|<img.*>|</?link.*>|</?head>|</?p.*>|</?h[1-5]>|<g/>|</?s>', line ) ):
                        idx = str( line_num )
                        if ( idx not in removed ):
                            removed[ idx ] = list()
                        removed[ idx ].append( line )
                        if ( line == '</s>' ):
                            send_buff += '\n'
                    elif ( len( line ) > 0 ):
                        send_buff += line + '\n'
                        line_num  += 1
                sys.stderr.write( send_buff )
                ret_value = process.communicate( send_buff.encode() )[0].decode()
                replaced = ''
                line_num = 1
                for line in ret_value.splitlines():
                    if ( len( line ) == 0 ):
                        continue
                    idx = str( line_num )
                    if ( idx in removed ):
                        for tag in removed[idx]:
                            replaced += tag + '\n'
                        del removed[idx]
                    replaced += line + '\n'
                    line_num += 1
                for key in sorted( list( removed ) ):
                    for tag in removed[key]:
                        replaced += tag + '\n'
                    del removed[key]
                sys.stderr.write( str(removed) + '\n' )
                output_queue.put( replaced )
            else:
                output_queue.put( None )
                break

    def _read_records( self ):
        counter = 0
        buff    = ''
        f = None
        if ( self._filename is None ):
            f = sys.stdin.buffer
        elif ( self._filename.endswith( '.xz' ) ):
            f = lzma.open( self._filename, 'r' )
        elif ( self._filename.endswith( '.gz' ) ):
            f = gzip.open( self._filename, 'r' )
        else:
            f = open( self._filename, 'r' )

        for line in f:
            line = line.decode()
            if ( line == '</doc>\n' ):
                counter += 1
            buff += line
            if ( counter == Page_tagger.interval ):
                yield buff
                counter = 0
                buff    = ''
        if ( counter != 0 ):
            yield buff

        f.close()

    def process_tagging( self ):
        input_queue  = multiprocessing.Queue()
        output_queue = multiprocessing.Queue()

        for i in range( self._processes ):
            multiprocessing.Process( target = self._tagger_tokenized, args = ( input_queue, output_queue ) ).start()

        for records in self._read_records():
            input_queue.put( records )
            try:
                while ( True ):
                    yield output_queue.get( block = False )
            except:
                pass

        for i in range( self._processes ):
            input_queue.put( None )

        cond = self._processes
        while ( cond > 0 ):
            tagged = output_queue.get()
            if ( tagged is not None ):
                yield tagged
            else:
                cond -= 1

if __name__ == '__main__':
    parser = Page_tagger( tagger_bin = '../libary/morphodita/precompiled_bin/run_tagger', tagger_file = '../libary/morphodita/models/czech-morfflex-pdt-161115.tagger', filename = sys.argv[1], processes = 1 )
    for x in parser.process_tagging():
        print(x)