"""
Author: Jiri Matejka (xmatej52)

V tomto modulu je implementovan proces stahovani odkazu.
"""

from urllib.request import urlopen
from subprocess import Popen, PIPE
import concurrent.futures
import Functions

class Page_downloader( object ):
    """Page_downloader je tridou, ktera je schopna pomoci zadanych URL stahovat webove stranky."""

    def __init__( self, wait=1, tries=1 ):
        self._errors_info  = ""
        self._wait         = wait
        self._tries        = tries

    def _set_error( self, message, url ):
        self._errors_info += '-ERR ' + url + '\n-ERR_START\n' + message + '-ERR_END\n'

    def set_wait( self, time ):
        """
        Nastavi dobu cekani na odpoved serveru.
        """
        self._wait = time

    def set_tries( self, num ):
        """
        Nastavi pocet pokusu o pripojeni se na server.
        """
        self._tries = num

    def get_page_from_url( self, url ):
        """
        Ze zadane url stahne webovou stranku.
        """
        page = str()
        http_header = str()
        # Nejprve zkusime urlopen, je o neco rychlejsi nez wget
        try:
            page = urlopen( url, timeout=self._wait ) # muze vyhodit vyjimku
            http_header = data.info()
            http_header = Functions.decode_data( str( http_header ) )
            if data.getcode() == 200:
                http_header  = "HTTP/1.1 200 OK\r\n" + http_header
                page         = page.read() # reads content of a page
            else:
                raise Exception( 'Navratovy kod pro urllib neni 200 OK' )
        except:
            # pokud to neklapne, zkusime wget, ten je o neco chytrejsi, ale pomalejsi
            data      = Popen( [ 'wget', '-q', '-T', str( self._wait ), '-t', str( self._tries ), '-SO', '-', url ], stdout=PIPE, stderr=PIPE )
            page, http_header = data.communicate()
            http_header = Functions.decode_data( http_header ) if http_header else ''
            if ( data.returncode != 0 ): # Odpoved je 200 OK
                info_message = '\nOdpoved:' + http_header + '\n' if isinstance( http_header, str ) else ''
                info = Functions.get_exception_info( 'Nelze stahnout stranku "' + url + '"' + info_message )
                return { 'error':True, 'value':info, 'url':url, 'response':http_header }
        try:
            # Zkusime dekodovat obsah stranky pomoci odpovedi
            page = Functions.decode_page( page, http_header ) # muze vyhodit vyjimku
        except:
            # Pokud to nevyjde, pouzijeme utf-8
            try:
                page = page.decode( 'utf-8', errors='ignore' ) # muze vyhodit vyjimku
            except:
                info = Functions.get_exception_info( 'Nelze dekodovat stazenou stranku "' + url +'"' )
                return { 'error':True, 'value':info, 'url':url, 'response':http_header }
        return { 'error':False, 'value':page, 'url':url, 'response':http_header }

    def get_multiple_pages_from_urls( self, urls ):
        """
        Pro kazdou url, ktera se nachazi v urls, bude spusten jeden proces, ktery se
        postara o stazeni stranky. Pri spusteni nad velkym mnozstvim URL lze ocekavat
        podobny vysledek jako pri spusteny fork bomby.
        """
        # Toto je paralelni spusteni, nikdy to nepoustet nad velkym mnozstim odkazuself.
        # Rozdhodne to neni dobre pouzivat pro stazeni vsech url z crawlingu jednim vrzem,
        # v tom pripade to bude mit podobny ucinek jako fork bomba
        pages = list()
        with concurrent.futures.ProcessPoolExecutor() as executor:
            for page in executor.map( self.get_page_from_url, urls ):
                pages.append( page )
        return pages

    def get_errors_info( self ):
        """
        Vrati retezec s chybami, ktere nastali behem zpracovani.
        """
        message = self._errors_info
        self._errors_info = ""
        return message
