"""Modul Page_parser slouzi ke zpracovani stazenych warc archivu."""
import re
import langdetect
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from Link_collector import Link_collector


class Page( object ):
    tag_begin = 'TagStartsWithAsQpeQeporSxfsSwerfSffeWSfWrSFSXwwrqwsSDrwqwesaSewwasdropiUbHDBAJin'
    def __init__( self, page, url, http_response, page_id ):
        self._response    = http_response
        self._id          = page_id
        self._url         = url
        self._page        = page
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
        tag = tag.replace( 'lEfTkpoecwucnsgqteuroasjdaswqeasdxzasf', '<' )
        tag = tag.replace( 'rIghtUqPqakasDfitpQidugHbczMxJsuwqowsG', '>' )
        tag = tag.replace( 'sLasHiqoWpasDguErtPqxZmaSkfgReqpEroSdA', '/'  )
        return tag

    def remove_trash( self ):
        return re.subn( r'<(script|style).*?</\1>(?s)', '', self._page )

    def retrieve_page_title( self ):
        match = re.search('<title>(.*?)</title>', self._page)
        title = match.group(1) if match else ''
        return title

    def retrieve_links( self ):
        self._page = re.sub( r'<a[^>]* href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'\n_tag_link="\1"_tag_\n\2\n_tag_/link_tag_\n', self._page )

    def retrieve_images( self ):
        self._page = re.sub( r'<img[^>]* src=["\']([^"\']*)["\'][^>]*>', r'\n_tag_img="\1"_tag_\n', self._page )

    def retrieve_headers( self ):
        self._page = re.sub( r'<(h[1-5])[^>]*>(.*?)</h', r'\n_tag_\1_tag_\n\2\n_tag_/\1_tag_\n', self._page )

    def retrieve_paragraphs( self ):
        self._page = re.sub( r'<p[^>]*>(.*?)</p>', r'\n_tag_p_tag\n\2\n_tag_/p_tag_\n', self._page )

    def retrieve_divs( self ):
        self._page = re.sub( r'<div[^>]+>(.*)</div>', r'\n_tag_div_tag_\n\2\n_tag_/div_tag_\n', self._page )

    def retrieve_content( self ):
        self._page = re.sub( r'<[^>]*>', '', self._page )

    def get_text( self ):
        self.remove_trash()
        title = self.retrieve_page_title()
        self.retrieve_links()
        self.retrieve_images()
        self.retrieve_headers()
        self.retrieve_paragraphs()
        self.retrieve_divs()
        self.retrieve_content()
        self._page = re.sub( r'\n_tag_(/?div|p|img|link)_tag_\n', r'<\1>', self._page )
        content = '<doc\ttitle="' + title + '"\turl="' + self._url + '"\tid="' + self._id + '">\n<head>\n' + title + '\n</head>\n' + self._page + '</doc>\n'

        content = re.sub( r'[\s]{2,}', '\n', content )
        return content

    def get_absolute_url( self, rel ):
        return urljoin( self._url, rel )

if __name__ == "__main__":
    from urllib.request import urlopen
    uri  = 'https://zpravy.idnes.cz/domaci.aspx'
    html = urlopen( uri ).read()
    page = Page( page = html, url = uri, http_response = '', page_id = '' )
    # uri = 'https://zpravy.idnes.cz/domaci.aspx'
    # content = urlopen( uri ).read()
    # page = Page( page = content, url = uri, http_response = '', warc_header = '', filtr_rules = '../easylist.txt' )
    print( page.get_text() )
    # page.get_text()
