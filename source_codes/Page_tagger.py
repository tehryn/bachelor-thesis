import sys
import multiprocessing
import subprocess
import re
import lzma
import gzip

class Page_tagger( object ):
    interval = 50
    def __init__( self, tagger_bin, filename = None, processes = 10 ):
        self._tagger_bin  = tagger_bin
        self._processes   = processes
        self._filename    = filename
        self._commands    = dict()
        self._def_lang    = None
        self.cnt          = 0 # TODO

    @staticmethod
    def set_interval( num ):
        Page_tagger.interval = num

    def set_language( self, language, tagger, default = False ):
        self._commands[ language ] = [ self._tagger_bin, '--input=vertical', '--output=vertical', tagger ]
        if ( ( self._def_lang is None ) or default ):
            self._def_lang = language

    def _tagger_tokenized( self, input_queue, output_queue ):
        process = dict()
        while ( True ):
            data = input_queue.get()
            if ( data is not None ):
                send_buff = dict()
                for key in list( self._commands ):
                    send_buff[ key ] = ''
                    process[ key ]   = subprocess.Popen( self._commands[ key ], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE )
                removed  = dict()
                line_num = 1
                sources  = list()
                lang     = self._def_lang
                for line in data.splitlines():
                    if ( re.match( r'</?doc.*>|<img.*>|</?link.*>|</?head>|</?p.*>|</?h[1-5]>|<g/>|</?s>', line ) ):
                        if ( re.match( r'<p.*>', line ) ):
                            idx = line.find( '"' )
                            if ( idx > 0 ):
                                lang = line[ idx + 1 : line.find( '"', idx + 1 ) ]
                                if ( lang not in list( self._commands ) ):
                                    lang = self._def_lang
                            else:
                                lang = self._def_lang
                        idx = str( line_num )
                        if ( idx not in removed ):
                            removed[ idx ] = list()
                        removed[ idx ].append( line )
                        if ( line == '</s>' ):
                            send_buff[ lang ] += '\n'
                            sources.append( lang )
                    elif ( len( line ) > 0 ):
                        sources.append( lang )
                        send_buff[ lang ] += line + '\n'
                        line_num  += 1
                results = dict()
                for key in list( self._commands ):
                    results[ key ] = process[ key ].communicate( send_buff[ key ].encode() )[0].decode().splitlines()
                    del send_buff[ key ]

                replaced = ''
                line_num = 1
                for lang in sources:
                    line = results[ lang ].pop(0)
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
                #sys.stderr.write( 'Hotovo\n' )
                output_queue.put( replaced )
            else:
                output_queue.put( None )
                break

    def _read_records( self ):
        counter = 0
        buff    = ''
        f = None
        must_decode = True
        if ( self._filename is None ):
            f = sys.stdin.buffer
        elif ( self._filename.endswith( '.xz' ) ):
            f = lzma.open( self._filename, 'r' )
        elif ( self._filename.endswith( '.gz' ) ):
            f = gzip.open( self._filename, 'r' )
        else:
            must_decode = False
            f = open( self._filename, 'r' )

        for line in f:
            if ( must_decode ):
                line = line.decode()
            if ( line == '</doc>\n' ):
                counter += 1
            buff += line
            if ( counter == Page_tagger.interval ):
                #sys.stderr.write( 'Odeslano ke zpracovani' + '\n' )
                self.cnt += 1
                yield buff
                counter = 0
                buff    = ''
        if ( counter != 0 ):
            self.cnt += 1
            yield buff

        f.close()

    def process_tagging( self ):
        input_queue  = multiprocessing.Queue()
        output_queue = multiprocessing.Queue()

        for i in range( self._processes ):
            multiprocessing.Process( target = self._tagger_tokenized, args = ( input_queue, output_queue ) ).start()
        num = 0
        for records in self._read_records():
            input_queue.put( records )
            try:
                while ( True ):
                    yield output_queue.get( block = False )
                    num += 1
            except:
                pass

        for i in range( self._processes ):
            input_queue.put( None )

        cond = self._processes
        while ( cond > 0 ):
            tagged = output_queue.get()
            if ( tagged is not None ):
                yield tagged
                num += 1
                sys.stderr.write( str(num)+"/"+str(self.cnt) + "\n" )
            else:
                cond -= 1

if __name__ == '__main__':
    parser = Page_tagger( tagger_bin = '../libary/morphodita/precompiled_bin/run_tagger', filename = sys.argv[1], processes = 50 )
    parser.set_language( 'cs', tagger = '../libary/morphodita/models/czech-morfflex-pdt-161115.tagger', default = True )
    parser.set_language( 'sk', tagger = '../libary/morphodita/models/sk.tagger' )
    for x in parser.process_tagging():
        sys.stdout.write(x)
        #pass