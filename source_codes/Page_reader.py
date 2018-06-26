"""
Author: Jiri Matejka (xmatej52)

V tomto modulu je implementovano cteni warc archivu.
"""
import sys
import lzma
import gzip
import uuid
import warc
from Page import Page

class Page_reader( object ):
    """
    Trida nacita a vraci postupne zaznamy z warc archivu.
    """
    def __init__( self, filename=None, old_style = False ):
        # podporujeme i cteni z archivu, ne? Hlavne vsechno cist po bajtech
        if ( filename is None ):
            self._file = sys.stdin.buffer
        elif ( filename.endswith( '.xz' ) ):
            self._file = lzma.open( filename, 'rb' )
        elif ( filename.endswith( '.gz' ) ):
            self._file = gzip.open( filename, 'rb' )
        else:
            self._file = open( filename, 'rb' )

        # Tak tohle jsem musel musel vycist ze samotnych zdrojaku knihovny warc.
        # Dokumentaci maji fakt dost spatnou.
        self._warc = warc.WARCFile( fileobj = self._file )
        self._old_style = old_style

    def __iter__( self ):
        first = True
        # Ted je cas iterovat po jednotlivych zaznamech warc archivu
        for record in self._warc:
            # Prvni zaznam se ignoruje, je tam kvuli informacim o warc archivu.
            if ( first ):
                first = False
                continue

            # nacteme obsah
            # bacha, obsah je nacteny v bajtech
            content  = record.payload.read()
            response = bytes()
            # najdeme http odpoved a telo
            index    = content.find( b'\r\n\r\n' )
            if ( index > 0 ):
                response = content[ :index ]
                content  = content[ index: ]

            # zjistime uri
            uri = ''
            if ( 'WARC-Target-URI' in record ):
                uri = record[ 'WARC-Target-URI' ]

            # a id zaznamu by take bodlo
            warc_id = ''
            if ( 'WARC-Record-ID' in record ):
                warc_id = record[ 'WARC-Record-ID' ][ 10:-1 ]
            # ale pokud nam ID chybi, musime si ho vygenerovat.
            else:
                warc_id = str( uuid.uuid1() )

            # pokusime se vytvorit stranku. Pokud selze dekodovani obsahu, je nam stranka k nicemu.
            try:
                yield Page( page = content, url = uri, http_response = response.decode(), page_id = warc_id, old_style = self._old_style )
            except ValueError:
                pass

if __name__ == '__main__':
    test_file = None
    if ( len( sys.argv ) == 2 ):
        test_file = sys.argv[1]
    reader = Page_reader( test_file )
    for page in reader:
        sys.stderr.write( 'parsing file\n' )
        text = page.get_text()
        print( text )