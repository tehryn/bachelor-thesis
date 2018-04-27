import sys
import lzma
import gzip
import uuid
import warc
from Page import Page

class Page_reader( object ):
    def __init__( self, filename=None, old_style = False ):
        if ( filename is None ):
            self._file = sys.stdin.buffer
        elif ( filename.endswith( '.xz' ) ):
            self._file = lzma.open( filename, 'rb' )
        elif ( filename.endswith( '.gz' ) ):
            self._file = gzip.open( filename, 'rb' )
        else:
            self._file = open( filename, 'rb' )
        self._warc = warc.WARCFile( fileobj = self._file )
        self._old_style = old_style

    def __iter__( self ):
        first = True
        cnt   = 1
        for record in self._warc:
            if ( first ):
                first = False
                continue
            content  = record.payload.read()
            response = bytes()
            index    = content.find( b'\r\n\r\n' )
            if ( index > 0 ):
                response = content[ :index ]
                content  = content[ index: ]
            uri = ''
            if ( 'WARC-Target-URI' in record ):
                uri = record[ 'WARC-Target-URI' ]
            warc_id = ''
            if ( 'WARC-Record-ID' in record ):
                warc_id = record[ 'WARC-Record-ID' ][ 10:-1 ]
            else:
                warc_id = str( uuid.uuid1() )

            try:
                yield Page( page = content, url = uri, http_response = response.decode(), page_id = warc_id, old_style = self._old_style )
                sys.stdout.write( '-----' + str( cnt ) + '-----\n' )
                cnt += 1
            except ValueError:
                pass
        sys.stderr.write( '====' + str( cnt ) + '====\n' )

if __name__ == '__main__':
    test_file = None
    if ( len( sys.argv ) == 2 ):
        test_file = sys.argv[1]
    reader = Page_reader( test_file )
    for page in reader:
        sys.stderr.write( 'parsing file\n' )
        text = page.get_text()
        print( text )