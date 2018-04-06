"""Modul Page_parser slouzi ke zpracovani stazenych warc archivu."""
import re
import langdetect
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from Link_collector import Link_collector


class Page( object ):
    tag_begin = 'TagStartsWithAsQpeQeporSxfsSwerfSffeWSfWrSFSXwwrqwsSDrwqwesaSewwasdropiUbHDBAJin'
    def __init__( self, page, url, http_response, page_id ):
        self._soup        = BeautifulSoup( page, 'html.parser' )
        self._collector   = Link_collector()
        self._response    = http_response
        self._id          = page_id
        self._link_key    = 0
        self._img_key     = 0
        self._par_key     = 0
        self._head_key    = 0
        self._div_key     = 0
        self._url         = url
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

    def _get_link_key( self ):
        key = '__LINK_' + str( self._link_key ) + '__'
        self._link_key += 1
        return key

    def _get_img_key( self ):
        key = '__IMG_' + str( self._img_key ) + '__'
        self._img_key += 1
        return key

    def _get_paragraph_key( self ):
        key = '__PAR_' + str( self._par_key ) + '__'
        self._par_key += 1
        return key

    def _get_header_key( self, name ):
        key = '__HEAD_' + name + '_' + str( self._par_key ) + '__'
        self._head_key += 1
        return key

    def _get_div_key( self ):
        key = '__DIV_' + str( self._div_key ) + '__'
        self._div_key += 1
        return key

    def find_rss( self ):
        """Metoda nalezne veskere rss zdroje na strance a vrati mnozinu s odkazy."""
        links = set()
        for link in self._soup.find_all( "link", { "type" : "application/rss+xml" } ):
            links.add( link.get( 'href' ) )
        return links

    def remove_trash( self ):
        trash = [ 'script', 'style', 'ul', 'li', 'hr', 'ol' ]
        for punk in self._soup( trash ):
            punk.decompose()

    def retrieve_page_title( self ):
        title = self._soup.find( 'title' )
        if ( title ):
            title = title.text.strip()
        return title

    def retrieve_links( self ):
        links_on_page = dict()
        for a in self._soup.findAll( 'a' ):
            link = a.get( 'href' )
            if ( link ):
                key  = self._get_link_key()
                links_on_page[ key ] = dict()
                links_on_page[ key ][ 'link' ] = self.get_absolute_url( link )
                links_on_page[ key ][ 'content' ] = a.text.strip()
                a.string = '\n' + key + '\n'
                a.name   = 'span'
        return links_on_page

    def retrieve_images( self ):
        images_on_page = dict()
        for img in self._soup.findAll( 'img' ):
            link = img.get( 'src' )
            if ( link ):
                key  = self._get_img_key()
                images_on_page[ key ] = self.get_absolute_url( link )
                img.name   = 'span'
                img.string = '\n' + key + '\n'
        return images_on_page

    def retrieve_headers( self ):
        headers_on_page = dict()
        for h in self._soup( [ 'h1', 'h2', 'h3', 'h4', 'h5' ] ):
            if ( h.text ):
                key = self._get_header_key( str( h.name ) )
                headers_on_page[ key ] = h.text.strip()
                h.string = '\n' + key + '\n'
        return headers_on_page

    def retrieve_paragraphs( self ):
        paragraphs_on_page = dict()
        for p in self._soup.findAll( 'p' ):
            key  = self._get_paragraph_key()
            cont = p.text.strip()
            if ( p.text ):
                paragraphs_on_page[ key ] = dict()
                paragraphs_on_page[ key ][ 'content' ]  = cont
                p.string = '\n' + key + '\n'
        return paragraphs_on_page

    def retrieve_divs( self ):
        divs_on_page = dict()
        all_divs = self._soup.findAll( 'div' )
        prev_text = ''
        for div in all_divs[::-1]:
            content = div.text.strip()
            if ( content ):
                if ( content == prev_text ):
                    div.string = '\n' + prev_text + '\n'
                else:
                    key = self._get_div_key()
                    divs_on_page[ key ] = div.text
                    div.string = '\n' + key + '\n'
                    prev_text  = key
            else:
                div.decompose()
        return divs_on_page

    def retrieve_content( self ):
        body    = self._soup.find( 'body' )
        content = ''
        if ( body ):
            content = body.text
        return content

    def get_text( self, lang_detect = True ):
        self.remove_trash()
        title      = self.retrieve_page_title()
        urls       = self.retrieve_links()
        images     = self.retrieve_images()
        headers    = self.retrieve_headers()
        paragraphs = self.retrieve_paragraphs()
        divs       = self.retrieve_divs()
        content    = self.retrieve_content()
        cond       = True
        while ( cond ):
            new_content = ''
            cond        = False
            for line in content.splitlines():
                if ( line.startswith( '__LINK_' ) ):
                    #TODO relativni cesta
                    cond = True
                    href = urls[ line ][ 'link' ]
                    text = urls[ line ][ 'content' ]
                    if ( text ):
                        new_content += '\n<link="'+ href +'">\n' + text + '\n</link>\n'
                elif ( line.startswith( '__IMG_' ) ):
                    #TODO relativni cesta
                    cond = True
                    new_content += '\n<img="'+ images[ line ] +'">'
                elif ( line.startswith( '__PAR_' ) ):
                    cond = True
                    text = paragraphs[ line ][ 'content' ]
                    if ( text ):
                        new_content += '\n<p>\n' + text + '\n</p>\n'
                elif ( line.startswith( '__HEAD_' ) ):
                    cond = True
                    text = headers[ line ]
                    if ( text ):
                        new_content += '\n<h>\n' + text + '\n</h>\n'
                elif ( line.startswith( '__DIV_' ) ):
                    cond = True
                    text = divs[ line ]
                    new_content += '\n<div>\n' + text + '\n</div>\n'
                else:
                    new_content += '\n' + line + '\n'
            if ( cond ):
                content = re.sub( r'[\s]{2,}', '\n', new_content )
        if ( title ):
            content = '<doc\ttitle="' + title + '"\turl="' + self._url + '"\tid="' + self._id + '">\n<head>\n' + title + '\n</head>\n' + content + '</doc>\n'
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
