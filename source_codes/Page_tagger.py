"""
Author: Jiri Matejka (xmatej52)

V tomto modulu je implementovan proces taggovani.
"""

import sys
import multiprocessing
import subprocess
import re
import lzma
import gzip

class Page_tagger( object ):
    """
    Trida, pomoci ktere lze provest tagging.
    """
    interval = 50
    def __init__( self, tagger_bin, filename = None, processes = 10 ):
        self._tagger_bin  = tagger_bin
        self._processes   = processes
        self._filename    = filename
        self._commands    = dict()
        self._def_lang    = None

    @staticmethod
    def set_interval( num ):
        """
        Nastavi pocet stranek, ktere se zpracovaji jednim cyklem taggingu.
        """
        Page_tagger.interval = num

    def set_language( self, language, tagger, default = False ):
        """
        Prida podporu noveho jazyka.
        """
        self._commands[ language ] = [ self._tagger_bin, '--input=vertical', '--output=vertical', tagger ]
        if ( ( self._def_lang is None ) or default ):
            self._def_lang = language

    def _tagger_tokenized( self, input_queue, output_queue ):
        # Tahle metoda je urcena pro procesy. Bude se zde postupne nacitat fronta vstupnich dat.
        # Vysledky se pak zapisuji do vystupni fronty.
        process = dict()
        while ( True ):
            # nacteme zaznam
            data = input_queue.get()
            # pokud je to None, tak se musime ukoncit
            if ( data is not None ):
                send_buff = dict()
                # spustime taggery. Nejakou dobu nacitaji soubory, tak at si je nactou v nez zpracujeme vertikalni data
                for key in list( self._commands ):
                    send_buff[ key ] = ''
                    process[ key ]   = subprocess.Popen( self._commands[ key ], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE )

                # a ted potrebuje vyhazet vsechny taggy a roztridit text podle jazyka.
                # Jak to ale udelat?
                # prijdeme vsechny soubory a vyhazime tagy. Vyhozene tagy ulozime do slovniku kde klicem bude cislo radku, na kterem se nachazi.
                # Zatimco budeme vyhazovat tagy, budeme si i hlidat jeden zajimavy tag - <p lang="en">. Hlavne jeho atribut znacici jazyk odstavce.
                # Text tohoto odstavce ulozime do bufferu, ktery posleze predame taggeru. Abychom ale byly schopni stranku zase slozit zpet,
                # ulozime si do promene sources jazyk. Tento seznam slouzi neco jako poradnik. Kazdy radek ve zpracovani ma ulozeny svuj jazyk
                # v poradniku. Kdyz se soubor opet sklada dohromady, ctou se jazyky z poradniku a podle poradniku se nacitaji radky z taggeru.
                removed  = dict()
                line_num = 1
                sources  = list()
                lang     = self._def_lang
                # nejdriv si rozdelime data podle radek
                for line in data.splitlines():
                    # detekujeme tagy
                    if ( re.match( r'</?doc.*>|<img.*>|</?link.*>|</?head>|</?p.*>|</?h[1-5]>|<g/>|</?s>', line ) ):
                        # detekujeme odstavec
                        if ( re.match( r'<p.*>', line ) ):
                            # detekujeme jazyk, pokud jazyk neni podporovan, pouzijeme vychozi.
                            idx = line.find( '"' )
                            if ( idx > 0 ):
                                lang = line[ idx + 1 : line.find( '"', idx + 1 ) ]
                                if ( lang not in list( self._commands ) ):
                                    lang = self._def_lang
                            else:
                                lang = self._def_lang

                        # zjistime cislo radku - pouzijeme ho jako index do slovniku
                        idx = str( line_num )
                        if ( idx not in removed ):
                            removed[ idx ] = list()
                        removed[ idx ].append( line )

                        # tagger jako konec vety bere znak noveho radku
                        if ( line == '</s>' ):
                            send_buff[ lang ] += '\n'
                            sources.append( lang )
                    # jinak zaposeme do prislusneho buffer radek a take jazyk dame do poradniku
                    elif ( len( line ) > 0 ):
                        sources.append( lang )
                        send_buff[ lang ] += line + '\n'
                        line_num  += 1

                # nyni si z taggeru precteme vysledky
                results = dict()
                for key in list( self._commands ):
                    results[ key ] = process[ key ].communicate( send_buff[ key ].encode() )[0].decode().splitlines()
                    del send_buff[ key ]

                # Ted je nacase slozit rozebranou stranku zase dohromady
                replaced = ''
                line_num = 1
                # budeme iterovat pres poradnik
                for lang in sources:
                    # vyjememe prvni polozku z taggeru urceneho poradnikem
                    line = results[ lang ].pop(0)
                    # musime zaze znicit konce radku
                    if ( len( line ) == 0 ):
                        continue

                    # potrebujeme vlozit tag zpet na sve misto
                    idx = str( line_num )
                    if ( idx in removed ):
                        for tag in removed[idx]:
                            replaced += tag + '\n'
                        del removed[idx]

                    replaced += line + '\n'
                    line_num += 1

                # nektere tagy nam zbyly, jsou to posledni tagy
                # vetsinou to je </s></p></doc>
                for key in sorted( list( removed ) ):
                    for tag in removed[key]:
                        replaced += tag + '\n'
                    del removed[key]

                # nyni ulozime vysledek do fronty
                output_queue.put( replaced )
            else:
                # predtim nez skoncime, dame rodici vedet, ze jsme skoncili.
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
                yield buff
                counter = 0
                buff    = ''
        if ( counter != 0 ):
            yield buff

        f.close()

    def process_tagging( self ):
        """
        Vrati generator, ktery postubne vraci jednotlive stranky.
        """
        # vytvorime si fronty
        input_queue  = multiprocessing.Queue()
        output_queue = multiprocessing.Queue()

        # spustime paralelni zpracovani
        for i in range( self._processes ):
            multiprocessing.Process( target = self._tagger_tokenized, args = ( input_queue, output_queue ) ).start()

        # pripravime vstupni data procesum
        num = 0
        for records in self._read_records():
            input_queue.put( records )
            try:
                # vratime vysledky, pokud jsou nejake k dispozici
                while ( True ):
                    yield output_queue.get( block = False )
                    num += 1
            except:
                pass

        # vsechna vstupni data cekaji na zpracovani, dame procesum vedet, ze se maji ukoncit
        for i in range( self._processes ):
            input_queue.put( None )

        # Pockame, nez se dokonci zbytek zpracovani.
        cond = self._processes
        while ( cond > 0 ):
            tagged = output_queue.get()
            if ( tagged is not None ):
                yield tagged
                num += 1
                #sys.stderr.write( str(num)+"/"+str(self.cnt) + "\n" )
            else:
                cond -= 1

if __name__ == '__main__':
    parser = Page_tagger( tagger_bin = '../libary/morphodita/precompiled_bin/run_tagger', filename = sys.argv[1], processes = 50 )
    parser.set_language( 'cs', tagger = '../libary/morphodita/models/czech-morfflex-pdt-161115.tagger', default = True )
    parser.set_language( 'sk', tagger = '../libary/morphodita/models/sk.tagger' )
    for x in parser.process_tagging():
        sys.stdout.write(x)
        #pass