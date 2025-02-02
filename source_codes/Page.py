"""
Author: Jiri Matejka (xmatej52)

V tomto modulu je implementovan proces odstraneni HTML tagu.
"""
import re
import html
from urllib.parse import urljoin
from urllib.request import urlopen

import Functions
from Link_collector import Link_collector

class Page( object ):
    """
    Trida, ktera pracuje nad jednotlivymi HTML strankami a pripravuje je na tokenizaci a vertikalizaci.
    """
    tag_begin = 'TagStartsWithqusdfgRnxALvnFbghE'
    def __init__( self, page, url, http_response, page_id, old_style = False ):
        self.id         = page_id
        self._url       = url
        self._old_style = old_style
        try:
            self._page = Functions.decode_data( page )
        except:
            self._page = Functions.decode_page( page, http_response )
        super().__init__()

    @staticmethod
    def encode_tag( tag ):
        """
        Funkce zakoduje tag zpusobem, aby ho tokenizace zachovala jako jedno slovo
        """
        tag = tag.replace( '<', 'lEfTkpOecwucnsgQteuRoasjdasWqeasdXzaSf' )
        tag = tag.replace( '>', 'rIghtUqPqakasDfitpQidugHbczMxJsuwqowsG' )
        tag = tag.replace( '/', 'sLasHiqoWpasDguErtPqxZmaSkfgReqpEroSdA' )
        tag = tag.replace( '1', 'oNeiqoWpasDguErtPqxZmaSkfgReqpEroSdA' )
        tag = tag.replace( '2', 'tWOiqoWpasDguErtPqxZmaSkfgReqpEroSdA' )
        tag = tag.replace( '3', 'thREeiqoWpasDguErtPqxZmaSkfgReqpEroSdA' )
        tag = tag.replace( '4', 'FoURiqoWpasDguErtPqxZmaSkfgReqpEroSdA' )
        tag = tag.replace( '5', 'fivEHiqoWpasDguErtPqxZmaSkfgReqpEroSdA' )
        return Page.tag_begin + tag

    @staticmethod
    def decode_tag( tag ):
        """
        Funkce dekoduje zakodovany tag.
        """
        tag = tag[ len( Page.tag_begin ): ]
        tag = tag.replace( 'lEfTkpOecwucnsgQteuRoasjdasWqeasdXzaSf', '<' )
        tag = tag.replace( 'rIghtUqPqakasDfitpQidugHbczMxJsuwqowsG', '>' )
        tag = tag.replace( 'sLasHiqoWpasDguErtPqxZmaSkfgReqpEroSdA', '/'  )
        tag = tag.replace( 'oNeiqoWpasDguErtPqxZmaSkfgReqpEroSdA', '1' )
        tag = tag.replace( 'tWOiqoWpasDguErtPqxZmaSkfgReqpEroSdA', '2' )
        tag = tag.replace( 'thREeiqoWpasDguErtPqxZmaSkfgReqpEroSdA', '3' )
        tag = tag.replace( 'FoURiqoWpasDguErtPqxZmaSkfgReqpEroSdA', '4' )
        tag = tag.replace( 'fivEHiqoWpasDguErtPqxZmaSkfgReqpEroSdA', '5' )
        return tag

    def find_rss( self ):
        """
        Najde odkazy na RSS a ATOM zdroje.
        """
        return Link_collector.find_rss_from_page( self._page )

    def _remove_trash( self ):
        self._page = re.sub( r'<(script|style).*?</\1>(?s)', '', self._page, 0, re.DOTALL )

    def retrieve_page_title( self ):
        """
        Funkce vrati titulek stranky.
        """
        match = re.search('<title>(.*?)</title>', self._page)
        title = match.group(1) if match else ''
        return title

    def _process_links( self ):
        self._page = re.sub( r'<a[^>]* href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'\n_tag_link="\1"_tag_\n\2\n_tag_/link_tag_\n', self._page, 0, re.DOTALL)

    def _process_images( self ):
        self._page = re.sub( r'<img[^>]* src=["\']([^"\']*)["\'][^>]*>', r'\n_tag_img="\1"_tag_\n', self._page )

    def _process_rest( self ):
        if ( self._old_style ):
            self._page = re.sub( r'</?p[^>]*>', r'\n_tag_p_tag_\n', self._page )
        else:
            self._page = re.sub( r'<(/?(p|div|h[1-5]))[^>]*>', r'\n_tag_\1_tag_\n', self._page )

    def _process_content( self ):
        self._page = re.sub( r'<[^>]*>', '', self._page )

    def get_text( self ):
        """
        Spusti zpracovani stranky. Objekt je po provedeni teto cinnosti nenavratne zmenen.
        """
        title = html.unescape( self.retrieve_page_title() )
        self._remove_trash()
        self._process_links()
        self._process_images()
        self._process_rest()
        self._process_content()
        self._page = '<head>\n' + title + '\n</head>\n' + self._page
        self._page = html.unescape( self._page )
        self._page = re.sub( r'\n_tag_(/?(div|p|h[1-5]|/link|img="[^"]*"|link="[^"]*"))_tag_\n', r'\n<\1>\n', self._page )
        self._page = re.sub( r'\s{2,}', r'\n', self._page )
        self._page = '<doc\ttitle="' + title + '"\turl="' + self._url + '"\tid="' + self.id + '">\n' + self._page + '</doc>\n'
        return self._page

    def get_absolute_url( self, rel ):
        """
        Prevede relativni URL na absolutni.
        """
        return urljoin( self._url, rel )

    def clear( self ):
        """
        Uvolni smaza data stranky.
        """
        del self._page

    def get_url( self ):
        """
        wrati URL stranky.
        """
        return self._url

if __name__ == "__main__":
    uri       = 'https://www.denik.cz/spolecnost/exkluzivni-rozhovor-s-gabinou-koukalovou-konecne-se-muzu-nadechnout-20180321.html'
    html_data = urlopen( uri ).read()
    pagee      = Page( page = html_data, url = uri, http_response = '', page_id = '' )
    print( pagee.get_text() )
