"""Modul Page_parser slouzi ke zpracovani stazenych warc archivu."""
import re
import html
from urllib.parse import urljoin

import Functions

class Page( object ):
    tag_begin = 'TagStartsWithqusdfgRnxALvnFbghE'
    def __init__( self, page, url, http_response, page_id, mark_divs = False ):
        self._response  = http_response
        self._id        = page_id
        self._url       = url
        self._mark_divs = mark_divs
        self.encoding   = 'utf-8'
        idx = http_response.find( 'charset=' )
        if ( idx >= 0 ):
            self.encoding = http_response[ idx + 8 : ]
            idx = self.encoding.find( '\n' )
            if ( idx >= 0  ):
                self.encoding = self.encoding[ :idx].strip()
            else:
                self.encoding = 'utf-8'
        try:
            self._page = page.decode( self.encoding )
        except:
            self._page = Functions.decode_data( page )

        super().__init__()

    @staticmethod
    def encode_tag( tag ):
        tag = tag.replace( '<', 'lEfTkpOecwucnsgQteuRoasjdasWqeasdXzaSf' )
        tag = tag.replace( '>', 'rIghtUqPqakasDfitpQidugHbczMxJsuwqowsG' )
        tag = tag.replace( '/', 'sLasHiqoWpasDguErtPqxZmaSkfgReqpEroSdA' )
        return Page.tag_begin + tag

    @staticmethod
    def decode_tag( tag ):
        tag = tag[ len( Page.tag_begin ): ]
        tag = tag.replace( 'lEfTkpOecwucnsgQteuRoasjdasWqeasdXzaSf', '<' )
        tag = tag.replace( 'rIghtUqPqakasDfitpQidugHbczMxJsuwqowsG', '>' )
        tag = tag.replace( 'sLasHiqoWpasDguErtPqxZmaSkfgReqpEroSdA', '/'  )
        return tag

    def remove_trash( self ):
        self._page = re.sub( r'<(script|style).*?</\1>(?s)', '', self._page, 0, re.DOTALL )

    def retrieve_page_title( self ):
        match = re.search('<title>(.*?)</title>', self._page)
        title = match.group(1) if match else ''
        return title

    def process_links( self ):
        self._page = re.sub( r'<a[^>]* href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'\n_tag_link="\1"_tag_\n\2\n_tag_/link_tag_\n', self._page, 0, re.DOTALL)

    def process_images( self ):
        self._page = re.sub( r'<img[^>]* src=["\']([^"\']*)["\'][^>]*>', r'\n_tag_img="\1"_tag_\n', self._page )

    def process_rest( self ):
        if ( self._mark_divs ):
            self._page = re.sub( r'<(/?(p|div|h[1-5]))[^>]*>', r'\n_tag_\1_tag_\n', self._page )
        else:
            self._page = re.sub( r'<(/?(p|h[1-5]))[^>]*>', r'\n_tag_\1_tag_\n', self._page )

    def process_content( self ):
        self._page = re.sub( r'<[^>]*>', '', self._page )

    def get_text( self ):
        title = self.retrieve_page_title()
        self.remove_trash()
        self.process_links()
        self.process_images()
        self.process_rest()
        self.process_content()
        self._page = re.sub( r'\n_tag_(/?(div|p|h[1-5]|/link|img="[^"]*"|link="[^"]*"))_tag_\n', r'\n<\1>\n', self._page )
        self._page = re.sub( r'([.,;?!"\'\(\)\[\]]\s)', r'\1\n<g/>\n', self._page )
        self._page = '<doc\ttitle="' + title + '"\turl="' + self._url + '"\tid="' + self._id + '">\n<head>\n' + title + '\n</head>\n' + self._page + '</doc>\n'
        self._page = re.sub( r'\s{2,}', r'\n', self._page )
        self._page = html.unescape( self._page )
        return self._page


    def get_absolute_url( self, rel ):
        return urljoin( self._url, rel )

if __name__ == "__main__":
    from urllib.request import urlopen
    uri       = 'https://www.denik.cz/spolecnost/exkluzivni-rozhovor-s-gabinou-koukalovou-konecne-se-muzu-nadechnout-20180321.html'
    html_data = urlopen( uri ).read()
    page      = Page( page = html_data, url = uri, http_response = '', page_id = '' )
    print( page.get_text() )
