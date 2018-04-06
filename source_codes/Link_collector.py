import xml.etree.ElementTree as ET
import Functions
import re
from Page_downloader import Page_downloader

class Link_collector( Page_downloader ):
    """docstring for Link_collecter."""
    _dedup_links = set()

    def __init__( self, dedup=set(), wait=1, tries=1 ):
        super().__init__( wait=wait, tries=tries )
        Link_collector._dedup_links  = dedup.union( Link_collector._dedup_links )


    def find_links( self, page ):
        custom_parse = False
        custom_links = set()
        root         = None
        try:
            root = ET.fromstring( page )
        except:
            custom_parse = True
            custom_links = Functions.get_data_from_xml( 'link', page )

        links_found = set()
        if ( custom_parse ):
            items = custom_links
            for link in items:
                if ( link and ( len( link.splitlines() ) <= 1 ) and ( not ( link in self._dedup_links ) ) ):
                    self._dedup_links.add( link )
                    links_found.add( link )
        else:
            iterator = root.iter()
            for item in iterator:
                if ( item.tag == 'link' ):
                    link = item.text
                    if ( link ):
                        link = link.strip()
                        if ( link and ( not ( link in self._dedup_links ) ) ):
                            links_found.add( link )
                            self._dedup_links.add( link )
        return links_found

    def collect_links_from_url( self, url ):
        page = super().get_page_from_url( url )
        if ( page[ 'error' ] ):
            super()._set_error( page[ 'value' ], url )
            return None

        return self.find_links( page[ 'value' ] )

    def find_rss_from_page( self, page ):
        data = set()
        urlPat = re.compile( r'((<a|<link) [^<>]*?href=(\"|\')([^<>\"\']*?)(\"|\')[^<>]+)' )
        result = re.findall( urlPat, page )
        for link in result:
            if link[0].find( 'type="application/rss' ) > 0:
                data.add( link[3] )
        return data

    def find_rss_from_url( self, url ):
        page = super().get_page_from_url( url )
        if ( page[ 'error' ] ):
            self._set_error( page[ 'value' ], url )
            return None

        return self.find_rss_from_page( page[ 'value' ] )


    def collect_links_from_urls( self, urls ):
        pages       = super().get_multiple_pages_from_urls( urls )
        links_found = set()
        for url, page in zip( urls, pages ):
            if ( page[ 'error' ] ):
                self._set_error( page[ 'value' ], url )
            else:
                new_links   = self.find_links( page[ 'value' ] )
                links_found = links_found.union( new_links )
        return links_found

    @staticmethod
    def get_dedup():
        return Link_collector._dedup_links

    @staticmethod
    def clear_dedup():
        Link_collector._dedup_links = set()

if __name__ == "__main__":
    from time import time

    collector1 = Link_collector()
    collector2 = Link_collector()
    urls = set(
        [
            'http://gregi.net/category/clanky/feed/',
            'http://gregi.net/feed/',
            'http://havlickobrodsky.denik.cz/rss/z-regionu.html',
            'http://hdmag.cz/rss/clanky',
            'http://hdworld.cz/atom.xml',
            'http://hlidacipes.org/comments/feed/',
            'http://hlidacipes.org/index.html/feed/',
            'http://hodoninsky.denik.cz/rss/',
            'http://homebydleni.cz/comments/feed/',
            'http://chip.cz/rss/feed.php',
            'http://chrudimka.cz/frontpage/atom.html',
            'http://chrudimka.cz/frontpage/rss.html',
        ]
    )
    links1 = set()
    links2 = set()
    print( "Stahuji se stranky, toto muze nejakou chvili trvat..." )
    start = time()
    for url in urls:
        new_links = collector1.collect_links_from_url( url )
        if new_links:
            links1 = links1.union( new_links )
    end = time()
    print( "Sekcencni stahovani dokonceno za " + str( end - start ) + " sekund, zacina paralelni stahovani." )
    error1 = collector1.get_errors_info()
    Link_collector.clear_dedup()
    start = time()
    links2 = collector2.collect_links_from_urls( urls )
    end = time()
    print( "Paralelni stahovani dokonceno za " + str( end - start ) + " sekund." )
    error2 = collector2.get_errors_info()
    print( "Kontrola stejne funkcionality u sekvencniho a paralelniho zpracovani: " + str( links1 == links2 ) )
    print( "Pocet rss zdroju: " + str( len( urls ) ) + ", Pocet nalezenych stranek: " + str( len( links1.union( links2 ) ) ) )
    print( "Zacina vyhledavani rss zdroju na nalezenych URL" )
    rss_sources = set()
    for url in links1:
        found_rss = collector1.find_rss_from_url( url )
        if ( found_rss ):
            rss_sources = rss_sources.union( found_rss )
    print( "Nalazeno " + str( len( rss_sources ) ) + " rss zdroju." )