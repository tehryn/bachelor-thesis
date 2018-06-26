"""
Author: Jiri Matejka (xmatej52)

V tomto modulu je implementovano rozsireni procesu stahovani - rozsiruje tento proces o kolekci odkazu z RSS zdroju.
"""

import xml.etree.ElementTree as ET
import re
from time import time

import Functions
from Page_downloader import Page_downloader

class Link_collector( Page_downloader ):
    """
    Link_collector je tridou, ktera je urcena ke sberu odkazu z RSS a ATOM zdroju popripade
    vyhledavani techto zdroju v HTML strankach.
    """
    _dedup_links = set()

    def __init__( self, dedup=None, wait=1, tries=1 ):
        """
        Konstruktor objektu typu Link_collector.

        dedup - mnozina obsahujici deduplikacni odkazy.
        wait  - casovy udaj v sekundach, jak dlouho se ma cekat na odpoved serveru.
        tries - pocet pokusu o pripojeni na server
        """
        if ( dedup is None ):
            dedup = set()
        super().__init__( wait=wait, tries=tries )
        Link_collector._dedup_links  = dedup.union( Link_collector._dedup_links )


    def find_links( self, page ):
        """
        Metoda nalezne vsechny odkazy z RSS a ATOM souboru.
        page - XML soubor (RSS nebo ATOM feed)
        """
        custom_parse = False
        custom_links = set()
        root         = None
        # prvne zkusime mirumilovnou cestu, pokud dokument odpovida XML specifikaci
        # tak to je cajk
        try:
            root = ET.fromstring( page )
        except:
            # dokument neodpovida XML specifikaci, vyrveme z nich vsechno mozne
            custom_parse = True
            custom_links = Functions.get_data_from_xml( 'link', page )

        links_found = set()
        if ( custom_parse ):
            items = custom_links
            # pokud parsujeme data z regexu, dame si bacha, aby to, co se naslo jako odkaz,
            # nebylo na vice nez jeden radek.
            for link in items:
                if ( link and ( len( link.splitlines() ) <= 1 ) and ( link not in self._dedup_links ) ):
                    self._dedup_links.add( link )
                    links_found.add( link )
        else:
            # Jinak si vytvorime iterator a projedeme vsechny odkazy
            iterator = root.iter()
            for item in iterator:
                if ( item.tag == 'link' ):
                    link = item.text
                    if ( link ):
                        link = link.strip()
                        if ( link and ( link not in self._dedup_links ) ):
                            links_found.add( link )
                            self._dedup_links.add( link )

        return links_found

    def collect_links_from_url( self, url ):
        """
        Metoda nalezne vsechny odkazy z RSS nebo ATOM feedu.
        url - odkaz na RSS/ATOM feed.
        """
        page = super().get_page_from_url( url )
        if ( page[ 'error' ] ):
            super()._set_error( page[ 'value' ], url )
            return None

        return self.find_links( page[ 'value' ] )

    @staticmethod
    def find_rss_from_page( page ):
        """
        Metoda nalezne vsechny odkazy na RSS nebo ATOM zdroje.
        page - HTML soubor, ze ktereho budou ziskany odkazy
        """
        data = set()
        urlPat = re.compile( r'((<a|<link) [^<>]*?href=(\"|\')([^<>\"\']*?)(\"|\')[^<>]+)' )
        result = re.findall( urlPat, page )
        for link in result:
            if link[0].find( 'type="application/rss' ) > 0:
                data.add( link[3] )
        return data

    @staticmethod
    def find_rss_from_url( url ):
        """
        Metoda nalezne vsechny odkazy na RSS nebo ATOM zdroje.
        url - odkaz na HTML soubor, ze ktereho budou ziskany odkazy
        """
        page = super().get_page_from_url( url )
        if ( page[ 'error' ] ):
            super()._set_error( page[ 'value' ], url )
            return None

        return Link_collector.find_rss_from_page( page[ 'value' ] )


    def collect_links_from_urls( self, urls ):
        """
        Metoda najde odkazy ze zdroju uvedenych v iterovatelnem objektu (mnozina, seznam, ...)
        urls. Pro kazdy z prvek v objektu bude spusten jeden proces.
        """
        pages       = super().get_multiple_pages_from_urls( urls )
        links_found = set()
        for url, page in zip( urls, pages ):
            if ( page[ 'error' ] ):
                self._set_error( page[ 'value' ], url )
            else:
                links_found = links_found.union( self.find_links( page[ 'value' ] ) )
        return links_found

    @staticmethod
    def get_dedup():
        """
        Vrati mnozinu s deduplikacnimi odkazy.
        """
        return Link_collector._dedup_links

    @staticmethod
    def clear_dedup():
        """
        Odstrani vsechny deduplikacni odkazy.
        """
        Link_collector._dedup_links = set()

if __name__ == "__main__":
    collector1 = Link_collector()
    collector2 = Link_collector()
    urlss = set(
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
    for uri in urlss:
        new_links = collector1.collect_links_from_url( uri )
        if new_links:
            links1 = links1.union( new_links )
    end = time()
    print( "Sekcencni stahovani dokonceno za " + str( end - start ) + " sekund, zacina paralelni stahovani." )
    error1 = collector1.get_errors_info()
    Link_collector.clear_dedup()
    start = time()
    links2 = collector2.collect_links_from_urls( urlss )
    end = time()
    print( "Paralelni stahovani dokonceno za " + str( end - start ) + " sekund." )
    error2 = collector2.get_errors_info()
    print( "Kontrola stejne funkcionality u sekvencniho a paralelniho zpracovani: " + str( links1 == links2 ) )
    print( "Pocet rss zdroju: " + str( len( urlss ) ) + ", Pocet nalezenych stranek: " + str( len( links1.union( links2 ) ) ) )
    print( "Zacina vyhledavani rss zdroju na nalezenych URL" )
    rss_sources = set()
    for uri in links1:
        found_rss = collector1.find_rss_from_url( uri )
        if ( found_rss ):
            rss_sources = rss_sources.union( found_rss )
    print( "Nalazeno " + str( len( rss_sources ) ) + " rss zdroju." )