#!/usr/bin/env python3
"""
Author: Jiri Matejka (xmatej52)

Skript big_brother slouzi k pravidelnemu spouzteni celeho procesu zpracovani stranek a k vedeni statistik, logu, popripade zasilani informaci o chybach emailem
"""
import sys
import os
import time
import subprocess
import threading
import smtplib
import datetime
import signal
from email.mime.text import MIMEText
import Functions

class Task_manager( object ):
    """
    Modul, ktery eviduje veskere procesy zpracovani.
    """
    def __init__( self ):
        self._tasks = list()
        self.lock   = threading.Lock()

    def add_task( self, key ):
        """
        Prida novou ulohu do manazeru.
        """
        task_info = dict()
        task_info[ 'start' ] = time.time()
        task_info[ 'id' ]    = key
        self._tasks.append( task_info )

    def remove_task( self, key ):
        """
        Odebere ulohu z manazeru.
        """
        for idx, task in enumerate( self._tasks ):
            if ( task[ 'id' ] == key ):
                del self._tasks[ idx ]
                break

    def exists( self, key ):
        """
        Otestuje, zda uloha existuje.
        """
        for task in self._tasks:
            if ( task[ 'id' ] == key ):
                return True
        return False

    def __iter__( self ):
        for task in self._tasks:
            # Vytvorim kopii, abych needitoval puvodni zaznam
            task = { **task }
            duration = time.time() - task[ 'start' ]
            task[ 'start' ]     = time.strftime( "%d-%m-%Y %H:%M", time.localtime( task[ 'start' ] ) )
            task[ 'duration' ]  = str( datetime.timedelta( seconds = duration ) )
            yield task

    def __len__( self ):
        return len( self._tasks )

class Email_sender( object ):
    """
    Trida urcena k odesilani pravidelnych emailu.
    """
    def __init__( self, sender, to, subject, task_manager=None ):
        self._messages   = dict()
        self._messages[ 'debug' ] = list()
        self._messages[ 'stats' ] = list()
        self._messages[ 'warns' ] = list()
        self._messages[ 'error' ] = list()
        self.sender      = sender
        self.to          = to
        self.subject     = subject
        self.lock        = threading.Lock()
        self._last_email = 0
        self._task_manager = task_manager

    def debug( self, message ):
        """
        Prida debugovaci zpravu.
        """
        self._messages[ 'debug' ].append( time.strftime( "%d-%m-%Y %H:%M: ", time.localtime( time.time() ) ) + message )

    def warning( self, message ):
        """
        Prida upozornujici zpravu.
        """
        self._messages[ 'warns' ].append( time.strftime( "%d-%m-%Y %H:%M: ", time.localtime( time.time() ) ) + message )

    def error( self, message ):
        """
        Prida zpravu upozornujici na chybu.
        """
        self._messages[ 'error' ].append( time.strftime( "%d-%m-%Y %H:%M: ", time.localtime( time.time() ) ) + message )

    def statistics( self, message ):
        """
        Prida zpravu se statistickymi udaji.
        """
        self._messages[ 'stats' ].append( time.strftime( "%d-%m-%Y %H:%M: ", time.localtime( time.time() ) ) + message )

    def send( self ):
        """
        Odesle pripravene zprave.
        """
        content = 'Muj pane,\nomlouvam se ze vyrusuji, ale poveril jste me dohledem nad automatickym zpracovanim webovych kolekci a mam pro vas dulezite informace.\n'
        content += '\nChyby behem zpracovani:\n'
        if ( self._messages[ 'error' ] ):
            content += '-- ' + '\n-- '.join( self._messages[ 'error' ] ) + '\n'
        else:
            content += '-- Nedoslo k zadnym chybam behem zpracovani.\n'

        content += '\nZpravy, kterym je vhodne venovat pozornost:\n'
        if ( self._messages[ 'warns' ] ):
            content += '-- ' + '\n-- '.join( self._messages[ 'warns' ] ) + '\n'
        else:
            content += '-- Zadne informace k zobrazeni.\n'

        content += '\nPrubezne vedena statistika:\n'
        if ( self._messages[ 'stats' ] ):
            content += '-- ' + '\n-- '.join( self._messages[ 'stats' ] ) + '\n'
        else:
            content += '-- Zadne informace k zobrazeni.\n'

        # Pokud je Task_manager aktivni a jsou spusteny procesy, vypisu je
        if ( self._task_manager and len( self._task_manager ) > 0 ):
            content += '\nAktualne spustene programy:\n'
            for task in self._task_manager:
                content += '-- ' + task[ 'id' ] + ', spusteno: ' + task[ 'start' ] + ', aktualni doba zpracovani: ' + task[ 'duration' ] + '\n'

        content += '\nLadici informace:\n'
        if ( self._messages[ 'debug' ] ):
            content += '-- ' + '\n-- '.join( self._messages[ 'debug' ] ) + '\n'
        else:
            content += '-- Zadne informace k zobrazeni.\n'

        content += '\n\nHezky zbytek dne a mnoho zdaru preje vas oddany sluzebnik Velky Bratr'
        self._messages[ 'debug' ] = list()
        self._messages[ 'stats' ] = list()
        self._messages[ 'warns' ] = list()
        self._messages[ 'error' ] = list()

        # Ted uz zbyva jen vytvoreny text odeslat.
        msg = MIMEText( content )
        msg['Subject'] = self.subject
        msg['From']    = self.sender
        msg['To']      = self.to
        s = smtplib.SMTP( 'localhost' )
        s.sendmail( self.sender, self.to, msg.as_string() )
        s.quit()
        self._last_email = time.time()

    def last_email( self ):
        """
        Metoda vrati cas, kdy byl odeslan posledni email.
        """
        return self._last_email

class Statistics_manager( object ):
    """
    Trida ma na starost vedeni statistik.
    """
    def __init__( self ):
        self.total_downloads   = 0
        self.total_collections = 0
        self.today_downloads   = 0
        self.today_collections = 0
        self.lock = threading.Lock()

    def write_statistics( self, filename ):
        """
        Zapise statistiky do souboru.
        """
        # Zjistim nasbirana data
        msg = self.generate_string()
        content = None
        # Nactu cely soubor do pameti
        with open( filename, 'r' ) as f:
            content = f.readlines()
            if ( len( content ) > 0 ):
                del content[0]
            if ( len( content ) > 0 ):
                del content[0]
        # Rozsirim soubor o par dalsich radek
        content = "Collected=" + str( self.total_collections ) + "\nDownloaded=" + str( self.total_downloads ) + "\n" + ''.join( content ) + msg
        # Zapisi novy obsah
        with open( filename, 'w' ) as f:
            f.write( content )

    def load_statistics( self, filename ):
        """
        Nacte statisticka data ze souboru.
        """
        with open( filename, 'r' ) as f:
            content = f.readlines()
            # zajimaji me jen prvni 2 radky
            if ( len( content ) > 1 ):
                self.total_downloads   = int( content[0].split( '=' )[1][:-1] )
                self.total_collections = int( content[1].split( '=' )[1][:-1] )

    def generate_string( self ):
        """
        Vrati retezec aktualne nasbiranymi daty.
        """
        curr_time = time.strftime( "%d-%m-%Y %H:%M", time.localtime( time.time() ) )
        return curr_time + "\tCollected=" + str( self.today_collections ) + ";Downloaded=" + str( self.today_downloads ) + '\n'

class Locksmith( object ):
    """
    Zámečník, který zajišťuje přístup ke sdílené paměti.
    """
    def __init__( self ):
        self._locks = dict()
        self.lock = threading.Lock()

    def exist( self, name ):
        """
        Zjisti zda existuje zamek.
        """
        return name in self._locks

    def get( self, name ):
        """
        Vrati vybrany zamek.
        """
        return self._locks[ name ]

    def add( self, name ):
        """
        Vytvori novy zamek.
        """
        self._locks[ name ] = threading.Lock()

class Collector_thread ( threading.Thread ):
    """
    Trida, ktera se stara o spousteni kolekce odkazu.
    """
    def __init__( self, index, sender, rss_sources, path, locksmith, statistics, task_manager ):
        threading.Thread.__init__( self )
        self.key      = index
        self.input    = rss_sources
        self._sender  = sender
        self._path    = path
        self._locksmith = locksmith
        self._stat_manager = statistics
        self._task_manager = task_manager

    def _collect( self ):
        # Inicializujeme jmena souboru a nastavime ID zpracovani podle aktualniho casu
        collection_start    = time.time()
        collection_filename = time.strftime( "%d%m%Y%H%M", time.localtime( collection_start ) )
        task_id             = self.key + '-kolekce-' + collection_filename
        output_file = self._path + '/../collected_links/' + self.key + '/' + collection_filename + '.collected'
        log_file    = self._path + '/../logs/' + self.key + '/' + collection_filename + '.link_collector'

        # Overime existenci vsech potrebnych slozek, popripade je vytvorime.
        # Dale potrebujeme zamknout ty slozky, se kterymi pracujeme.
        if not os.path.exists( self._path + '/../logs/' + self.key ):
            try:
                os.makedirs( self._path + '/../logs/' + self.key )
            except FileExistsError:
                pass

        directory = self._path + '/../collected_links/' + self.key
        stdout = None
        stderr = None
        with self._locksmith.lock:
            if ( not self._locksmith.exist( directory ) ):
                self._locksmith.add( directory )
        with self._task_manager.lock:
            self._task_manager.add_task( key = task_id )
        with self._locksmith.get( directory ):
            if not os.path.exists( directory ):
                os.makedirs( directory )

            # Nacteme vsechny soubory urcene k deduplikaci dat.
            dedup_files = os.listdir( self._path + '/../collected_links/' + self.key )
            dedup_files = [ self._path + '/../collected_links/' + self.key + '/' + filename for filename in dedup_files ]

            collector   = None
            if dedup_files:
                collector   = [ self._path + '/link_collector.py', '-i', self.input, '-e', log_file, '-w', '5', '-m', '50', '-d' ] + dedup_files
            else:
                collector   = [ self._path + '/link_collector.py', '-i', self.input, '-e', log_file, '-w', '5', '-m', '50' ]

            process        = subprocess.Popen( collector, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
            stdout, stderr = process.communicate()

        # Po dokonceni zpracovani nastavime zpravy a aktualizujeme statisticka data.
        num = 0
        with self._sender.lock:
            if ( stdout ):
                num = sum( 1 for c in stdout.decode( 'utf-8' ) if c == '\n'  )
                try:
                    with open( output_file, 'w' ) as f:
                        f.write( stdout.decode( 'utf-8' ) )
                        self._sender.statistics(  self.key + " - Kolekce byla dokoncena, bylo nalezeno " + str( num ) + " stranek." )
                except:
                    self._sender.error( self.key + " - Nemohl jsem ulozit nalezene stranky z rss zdroju do souboru: '" + output_file + "'" )
                    num = 0
            if ( stderr ):
                self._sender.debug(  self.key + " - Kolekce skoncila s fatalni chybou: '" + stderr.decode( 'utf-8' ) + "'" )

        # Aktualizuji data pro statisiku
        with self._stat_manager.lock:
            self._stat_manager.today_collections += num
            self._stat_manager.total_collections += num

        # Odeberu ulohu
        with self._task_manager.lock:
            self._task_manager.remove_task( task_id )

    def run( self ):
        # Spustim kolekci, pokud nastane jakakoliv chyba, podam zpravu o ni v emailu
        try:
            self._collect()
        except:
            with self._sender.lock:
                err = Functions.get_exception_info( "Behem kolekce dat nastala kriticka chyba:" )
                self._sender.error( err )

class Parser_thread ( threading.Thread ):
    """
    Trida, ktera se stara o spousteni stahovani stranek a o nasledne zpracovani archivu.
    """

    def __init__( self, index, sender, path, locksmith, statistics, task_manager, rss ):
        threading.Thread.__init__( self )
        self.key     = index
        self._sender = sender
        self._path   = path
        self._locksmith = locksmith
        self._stat_manager = statistics
        self._task_manager = task_manager
        self._rss = rss

    def _find_rss( self, input_file ):
        add = 0
        task_id     = self.key + '-vyhledavani_rss-' + time.strftime( "%d%m%Y%H%M", time.localtime( time.time() ) )
        with self._task_manager.lock:
            while ( self._task_manager.exists( task_id ) ):
                add += 60
                task_id = self.key + '-vyhledavani_rss-' + time.strftime( "%d%m%Y%H%M", time.localtime( time.time() + add ) )
            self._task_manager.add_task( task_id )
        if ( add > 0 ):
            time.sleep( add )

        directory = self._path + '/../rss_sources/'
        with self._locksmith.lock:
            if ( not self._locksmith.exist( directory ) ):
                self._locksmith.add( directory )

        with self._locksmith.get( directory ):
            dedup_files = list()
            for filename in os.listdir( directory ):
                filename = directory + filename
                dedup_files.append( filename )

            output_file = directory + '/automatic_collection.txt'

            # spustime kolekci
            downloader  = [ self._path + '/rss_collector.py', '-o', output_file, '-i', input_file , '-d' ] + list( dedup_files )
            process     = subprocess.Popen( downloader, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
            stdout, stderr = process.communicate()

        # Nastavime zpravy do emailu
        num = 0
        with self._sender.lock:
            if ( stdout ):
                num = sum( 1 for c in stdout.decode( 'utf-8' ) if c == '\n'  )
                self._sender.statistics(  self.key + " - vyhledavani novych rss zdroju bylo dokonceno. Bylo nalezeno " + str( num ) + " novych zdroju." )
            if ( stderr ):
                self._sender.error(  self.key + " - vyhledavani novych rss zdroju skoncilo s fatalni chybou: '" + stderr.decode( 'utf-8' ) + "'" )

        with self._task_manager.lock:
            self._task_manager.remove_task( task_id )

    def _download_pages( self ):
        # Nejprve overim existenci slozek a popripade je vytvorim.
        if not os.path.exists( self._path + '/../downloaded/' + self.key + '/' ):
            try:
                os.makedirs( self._path + '/../downloaded/' + self.key + '/' )
            except FileExistsError:
                pass

        # Prejmenuji soubory, se kterymi pracuji, aby nevznikli zbytecne duplicity
        # Behem prejmenovani souboru musim uzamknout slozku.
        input_files = list()
        directory = self._path + '/../collected_links/' + self.key

        if ( os.path.exists( directory ) ):
            with self._locksmith.lock:
                if ( not self._locksmith.exist( directory ) ):
                    self._locksmith.add( directory )

            with self._locksmith.get( directory ):
                for filename in os.listdir( directory ):
                    filename = directory + '/' + filename
                    if ( filename.endswith( '.collected' ) ):
                        os.rename( filename, filename[:-9] + 'downloading' )
                        input_files.append( filename[:-9] + 'downloading' )


        # Dale potrebujeme nastavit ID ulohy a jmena souboru
        download_filename = time.strftime( "%d%m%Y%H%M", time.localtime( time.time() ) )
        task_id           = self.key + '-stahovani-' + download_filename
        log_file          = self._path + '/../logs/' + self.key + '/' + download_filename + '.page_downloader'

        # A pokud vubec existuji nejake vstupni soubory, spustime stahovani
        if ( input_files ):
            # Zaradime ulohu do manageru, ale BACHA na to, aby uz uloha se stejnym ID neexisovala
            # to by totiz znamenalo, ze 2 procesy maji nastaveny uplne stejny vystupni soubor
            add = 0
            with self._task_manager.lock:
                while ( self._task_manager.exists( task_id ) ):
                    add += 60
                    download_filename = time.strftime( "%d%m%Y%H%M", time.localtime( time.time() + add ) )
                    task_id           = self.key + '-stahovani-' + download_filename
                self._task_manager.add_task( task_id )
            if ( add > 0 ):
                time.sleep( add )

            # spustime stahovani
            output_file =  self._path + '/../downloaded/' + self.key + '/' + download_filename + '.warc.downloading'
            downloader  = [ self._path + '/page_downloader.py', '-o', output_file, '-e', log_file, '-w', '5', '-i' ] + list( input_files )
            process     = subprocess.Popen( downloader, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
            stdout, stderr = process.communicate()

            # Nastavime zpravy do emailu
            all_ok = False
            num = 0
            with self._sender.lock:
                if ( stdout ):
                    num = sum( 1 for c in stdout.decode( 'utf-8' ) if c == '\n'  )
                    self._sender.statistics(  self.key + " - stahovani bylo dokonceno. Bylo stazeno " + str( num ) + " stranek." )
                if ( stderr ):
                    self._sender.error(  self.key + " - stahovani skoncilo s fatalni chybou: '" + stderr.decode( 'utf-8' ) + "'" )
                else:
                    all_ok = True

            # Aktualizujeme statistiky
            with self._stat_manager.lock:
                self._stat_manager.today_downloads += num
                self._stat_manager.total_downloads += num

            # A nakonec odebere ulohu z manageru
            with self._task_manager.lock:
                self._task_manager.remove_task( task_id )

            if ( all_ok and self._rss ):
                try:
                    self._find_rss( output_file )
                except:
                    with self._sender.lock:
                        self._sender.error(  self.key + " - vyhledavani rss zdrojdu skoncilo s fatalni chybou pro soubor " + output_file[:-12] )

            # prejmenujeme soubory
            downloaded_dir  = self._path + '/../downloaded/' + self.key
            with self._locksmith.lock:
                if ( not self._locksmith.exist( downloaded_dir ) ):
                    self._locksmith.add( downloaded_dir )
            if ( all_ok ):
                with self._locksmith.get( downloaded_dir ):
                    os.rename( output_file, output_file[:-12] )
            else:
                with self._locksmith.get( downloaded_dir ):
                    os.rename( output_file, output_file[:-12] + '.failed' )

            with self._locksmith.lock:
                if ( not self._locksmith.exist( directory ) ):
                    self._locksmith.add( directory )

            with self._locksmith.get( directory ):
                for filename in input_files:
                    if ( all_ok ):
                        os.rename( filename, filename[:-11] + 'downloaded' )
                    else:
                        os.rename( filename, filename[:-11] + 'failed' )



    def _tokenize( self ):
        # Pokud neexistuje slozka, vytvorime ji
        if not os.path.exists( self._path + '/../vert/' + self.key + '/' ):
            try:
                os.makedirs( self._path + '/../vert/' + self.key + '/' )
            except FileExistsError:
                pass

        input_files = list()
        directory   = self._path + '/../downloaded/' + self.key
        with self._locksmith.lock:
            if ( not self._locksmith.exist( directory ) ):
                self._locksmith.add( directory )

        with self._locksmith.get( directory ):
            for filename in os.listdir( directory ):
                filename = directory + '/' + filename
                if ( filename.endswith( '.warc' ) ):
                    os.rename( filename, filename + '.processing' )
                    input_files.append( filename + '.processing' )

        if ( input_files ):
            # Nastavime ID ulohy a jmena souboru
            filename = time.strftime( "%d%m%Y%H%M", time.localtime( time.time() ) )
            task_id  = self.key + '-vertikalizace-' + filename

            # Zaradime ulohu do manageru, ale BACHA na to, aby uz uloha se stejnym ID neexisovala
            # to by totiz znamenalo, ze 2 procesy maji nastaveny uplne stejny vystupni soubor
            add = 0
            with self._task_manager.lock:
                while ( self._task_manager.exists( task_id ) ):
                    add += 60
                    filename = time.strftime( "%d%m%Y%H%M", time.localtime( time.time() + add ) )
                    task_id  = self.key + '-vertikalizace-' + filename
                self._task_manager.add_task( task_id )
            if ( add > 0 ):
                time.sleep( add )

            # Spustime tokenizaci
            output_file =  self._path + '/../vert/' + self.key + '/' + filename + '.vert.processing'
            tokenizer   = self._path + '/../libary/morphodita/precompiled_bin/run_tokenizer'
            params  = [ self._path + '/html_to_vert.py', '-o', output_file, '-l', '-f', '-m', '12', '-t', tokenizer, '-i' ] + list( input_files )
            process     = subprocess.Popen( params, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
            stdout, stderr = process.communicate()

            # Nastavime emaily
            all_ok = False
            with self._sender.lock:
                if ( stdout ):
                    self._sender.warning(  self.key + " - Prevod textu do vertikalini podoby skoncil s neocekavanym vystupem na standardni vystup:\n" + str( stdout.decode( 'utf-8' ) ) )
                if ( stderr ):
                    self._sender.error(  self.key + " - Prevod textu do vertikalini podoby skoncil s fatalni chybou:\n" + stderr.decode( 'utf-8' ) )
                    for filename in input_files:
                        os.rename( filename, filename[:-10] + 'failed' )
                else:
                    self._sender.debug(  self.key + " - Prevod textu do vertikalini podoby byl dokoncen." )
                    all_ok = True

            # odebereme ulohu z manageru
            with self._task_manager.lock:
                self._task_manager.remove_task( task_id )

            # prejmenujeme soubory
            if ( all_ok ):
                with self._locksmith.get( directory ):
                    for filename in input_files:
                        process = subprocess.Popen( [ 'xz', '-9', filename ], stdout=subprocess.PIPE, stderr=subprocess.PIPE )
                        process.communicate()
                        os.rename( filename + '.xz', filename[:-11] + '.xz' )
                        directory   = self._path + '/../vert/' + self.key
                with self._locksmith.lock:
                    if ( not self._locksmith.exist( directory ) ):
                        self._locksmith.add( directory )
                with self._locksmith.get( directory ):
                    os.rename( output_file, output_file[:-11] )

    def _tagging( self ):

        # Vytvorime slozky, pokud neexistuji
        if not os.path.exists( self._path + '/../tagged/' + self.key + '/' ):
            try:
                os.makedirs( self._path + '/../tagged/' + self.key + '/' )
            except FileExistsError:
                pass

        # Prejmenujeme soubory, sek terymi budeme pracovat
        input_files = list()
        directory   = self._path + '/../vert/' + self.key
        with self._locksmith.lock:
            if ( not self._locksmith.exist( directory ) ):
                self._locksmith.add( directory )
        with self._locksmith.get( directory ):
            for filename in os.listdir( self._path + '/../vert/' + self.key ):
                filename = self._path + '/../vert/' + self.key + '/' + filename
                if ( filename.endswith( '.vert' ) ):
                    os.rename( filename, filename + '.processing' )
                    input_files.append( filename + '.processing' )

        # Zpracujeme souborym pokud nejake ke zpracovani existuji
        if ( input_files ):
            # zjistime dostupne modely a nastavime jazyky
            tagger = self._path + '/../libary/morphodita/precompiled_bin/run_tagger'
            models = list()
            for filename in os.listdir( self._path + '/../libary/morphodita/models' ):
                if ( filename.endswith( '.tagger' ) ):
                    models.append( filename[:-7] + '=' + self._path + '/../libary/morphodita/models/' + filename )
                else:
                    with self._sender.lock:
                        self._sender.warn(  "Ve slozce '" + self._path + '/../libary/morphodita/precompiled_bin/run_tagger\' se nachazi soubor ve spatnem formatu - ' + filename )

            # Nastavime jmena souboru a ID operace
            filename = time.strftime( "%d%m%Y%H%M", time.localtime( time.time() ) )
            task_id  = self.key + '-tagging-' + filename
            add = 0
            with self._task_manager.lock:
                while ( self._task_manager.exists( task_id ) ):
                    add += 60
                    filename = time.strftime( "%d%m%Y%H%M", time.localtime( time.time() + add ) )
                    task_id  = self.key + '-tagging-' + filename

                self._task_manager.add_task( task_id )

            # spustime tagger
            output_file =  self._path + '/../tagged/' + self.key + '/' + filename + '.tagged.processing'
            params   = [ self._path + '/tagger.py', '-o', output_file, '-l' ] + models + [ '-m', '8', '-t', tagger, '-p', '50', '-i', ] + list( input_files )
            process  = subprocess.Popen( params, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
            stdout, stderr = process.communicate()

            # odeberu ulohu z manageru
            all_ok = False
            with self._task_manager.lock:
                self._task_manager.remove_task( task_id )

            # odesleme emaily s informacemi o zpracovani
            with self._sender.lock:
                if ( stdout ):
                    self._sender.warn(  self.key + " - Tagging skoncil s neocekavanym vystupem na standardni vystup:\n" + str( stdout.decode( 'utf-8' ) ) )
                if ( stderr ):
                    self._sender.error(  self.key + " - Tagging skoncil s fatalni chybou:\n" + stderr.decode( 'utf-8' ) )
                else:
                    self._sender.debug(  self.key + " - Tagging byl uspesne proveden." )
                    all_ok = True

            # prejmenuji soubory
            if ( all_ok ):
                with self._locksmith.get( directory ):
                    for filename in input_files:
                        os.rename( filename, filename[:-11] )
                        process = subprocess.Popen( [ 'xz', '-9', filename[:-11] ], stdout=subprocess.PIPE, stderr=subprocess.PIPE )
                        process.communicate()
                    directory = self._path + '/../tagged/' + self.key
                with self._locksmith.lock:
                    if ( not self._locksmith.exist( directory ) ):
                        self._locksmith.add( directory )
                with self._locksmith.get( directory ):
                    os.rename( output_file, output_file[:-11] )

    def run( self ):
        # Spustim stahovani, pokud nastane jakakoliv chyba, podam zpravu o ni v emailu
        try:
            self._download_pages()
        except:
            with self._sender.lock:
                err = Functions.get_exception_info( "Behem stahovani dat nastala kriticka chyba:" )
                self._sender.error( err )
            return

        # Spustim kolekci, pokud nastane jakakoliv chyba, podam zpravu o ni v emailu
        try:
            self._tokenize()
        except:
            with self._sender.lock:
                err = Functions.get_exception_info( "Behem vertikalizace nastala kriticka chyba:" )
                self._sender.error( err )
            return

        # Spustim kolekci, pokud nastane jakakoliv chyba, podam zpravu o ni v emailu
        try:
            self._tagging()
        except:
            with self._sender.lock:
                err = Functions.get_exception_info( "Behem taggingu nastala kriticka chyba:" )
                self._sender.error( err )
            return

def main():
    """
    Hlavni funkce velkeho bratra - sposteni vlaken, zpracovani signalu, zpracovani argumentu programu, synchronizace zpracovani.
    """
    class Reaper( object ):
        """
        Trida zpracuje signaly a odesle zpravy informujici o ukonceni zpracovani.
        """
        def __init__( self, email ):
            self.die = False
            self.email = email
            signal.signal(signal.SIGINT, self.die_with_honor )
            signal.signal(signal.SIGTERM, self.die_with_honor )

        def die_with_honor( self, signum, frame ):
            """
            Korektni ukonceni programu.
            """
            email_client = Email_sender( sender = self.email, to = self.email, subject = 'Velky Bratr - ukonceni zpracovani' )
            msg = "Automaticke zpracovani velkym bratrem bude ukonceno pred zahajenim dalsiho cyklu zpracovani."
            email_client.warning( msg )
            email_client.send()
            self.die = True

        def die_without_honor( self ):
            """
            Ukonceni programu na zaklade chyby.
            """
            email_client = Email_sender( sender = self.email, to = self.email, subject = 'Velky Bratr - ukonceni zpracovani na zaklade chyby' )
            msg = Functions.get_exception_info( "Automaticke zpracovani velkym bratrem bylo ukonceno na zaklade chyby:" )
            email_client.error( msg )
            email_client.send()
            self.die = True

        def end( self ):
            """
            Zprava o ukonceni programu.
            """
            email_client = Email_sender( sender = self.email, to = self.email, subject = 'Velky Bratr - Konec' )
            email_client.warning( "Velky Bratr uspesne ukoncil svou cinnost. Nyni se ceka na dokonceni prace vsech spustenych skriptu (muze to trvat i nekolik hodin)." )
            email_client.send()

    author = "Author:\n" + \
             "  Jmeno: Jiri Matejka\n" + \
             "  Email: xmatej52@stud.fit.vutbr.cz nebo jiri.matejkaa@gmail.com\n" + \
             "  FIT VUT v Brne, Vyzkumna skupina KNOT@FIT"

    possible_arguments = [
        {
            'names'        : [ '--email', '-e' ],
            'optional'     : False,
            'has_tail'     : 1,
            'word_index'   : 'email',
            'prerequisite' : None,
            'description'  : 'Email, na ktery se maji posilat statisticka data a informace ' +
                             'o chybach.'
        },
        {
            'names'        : [ '--help',   '-h' ],
            'optional'     : True,
            'has_tail'     : 0,
            'word_index'   : 'help',
            'prerequisite' : '__alone__',
            'description'  : 'Zobrazi napovedu k programu.'
        },
        {
            'names'        : [ '--statistics',   '-s' ],
            'optional'     : False,
            'has_tail'     : 1,
            'word_index'   : 'statistics',
            'prerequisite' : None,
            'description'  : 'Soubor, do ktereho bude vedena statistika. Soubor bude otevren v rezimu append a ve formatu csv.'
        },
        {
            'names'        : [ '--collection',   '-c' ],
            'optional'     : True,
            'has_tail'     : 0,
            'word_index'   : 'collect',
            'prerequisite' : None,
            'description'  : 'Zapne se kolekce ATOM a RSS zdroju a z nalezenych zdroju se vygeneruje novy projekt.'
        },
        {
            'names'        : [ '--alternative',   '-a' ],
            'optional'     : True,
            'has_tail'     : 0,
            'word_index'   : 'alternative',
            'prerequisite' : None,
            'description'  : 'Namisto aby se emaily odesilaly a stranky stahovaly jednou za den, bude se tato akce provadet kazdy cyklus (2 hodiny). '
        }
    ]

    # zpracuji argumenty
    settings = dict()
    try:
        settings = Functions.get_setting( possible_arguments, sys.argv[1:] )
    except:
        if ( len( sys.argv ) > 1 and ( sys.argv[1] == '-h' or sys.argv[1] == '--help' ) ):
            Functions.print_help( possible_arguments, sys.argv[0], sys.stdout, author )
            exit(0)
        else:
            raise

    # Ulozim si nastaveni parametru do promennych.
    statistics_file = settings[ 'statistics' ][0]
    email           = settings[ 'email' ][0]
    rss_collection  = True if 'collect' in settings else False

    # Zjistime ve ktere slozce se nachazi Velky bratr
    path = os.path.dirname( os.path.realpath( __file__ ) )

    # vytvorime spravce uloh, emailoveho klienta, zamecnika, spravce statistik a smrtku
    task_manager = Task_manager()
    email_client = Email_sender( sender = email, to = email, subject = 'Velky Bratr - prubezne informace', task_manager = task_manager )
    locksmith    = Locksmith()
    stat_manager = Statistics_manager()
    reaper       = Reaper( email )


    # nacteme statistiky ze souboru nebo vytvorime novy soubor
    try:
        stat_manager.load_statistics( statistics_file )
    except FileNotFoundError:
        if ( os.path.isfile( statistics_file ) ):
            raise
        else:
            with open( statistics_file, 'w' ) as f:
                f.write( 'Collected=0\nDownloaded=0\n' )
            stat_manager.total_downloads   = 0
            stat_manager.total_collections = 0

    # Upozrnime na spusteni zpracovani
    email_client.warning( "Bylo spuštěno automatické zpracování dat." )
    email_client.send()
    today = None
    collector_threads = dict()
    download_threads  = dict()
    try:
        # zpracovani bude aktivni, dokud smrtka neobdrzila SIGKILL nebo SIGINT
        while ( reaper.die is False ):
            # Nacteme vsechny RSS zdroje - zdroje se mohou v prubehu zpracovani aktualizovat
            rss_sources = dict()
            for filename in os.listdir( path + '/../rss_sources/' ):
                if ( filename.endswith( '.txt' ) and len( filename ) > 4 ):
                    rss_sources[ filename[:-4] ] = path + '/../rss_sources/' + filename
                else:
                    with email_client.lock:
                        email_client.warning( "Ve složce s RSS zdroji je soubor ve spatnem formatu - " + filename )

            # Pro kazdy zdroj spustime vlakno s kolekci, nikdy nesmi bezet 2 kolekce najednou
            for key in rss_sources:
                if not( key in collector_threads and collector_threads[ key ].is_alive() ):
                    collector_threads[ key ] = Collector_thread( index = key, sender = email_client, rss_sources = rss_sources[ key ], path = path, locksmith = locksmith, statistics = stat_manager, task_manager = task_manager )
                    collector_threads[ key ].start()

            # Pokud nastal novy den, odesleme statisticke udaje a spustime i stahovani
            if ( 'alternative' in settings or today is None or today != datetime.datetime.today().day ):
                if ( today is not None ):
                    all_collections  = 0
                    all_downloads    = 0
                    curr_collections = 0
                    curr_downloads   = 0
                    with stat_manager.lock:
                        stat_manager.write_statistics( statistics_file )
                        all_collections  = stat_manager.total_collections
                        all_downloads    = stat_manager.total_downloads
                        curr_collections = stat_manager.today_collections
                        curr_downloads   = stat_manager.today_downloads
                        stat_manager.today_collections = 0
                        stat_manager.today_downloads = 0
                    with email_client.lock:
                        email_client.statistics( "Doposud bylo nasbirano " + str( all_collections ) + " odkazu." )
                        email_client.statistics( "Doposud bylo stazeno " + str( all_downloads ) + " stranek." )
                        email_client.statistics( "Tento cyklus bylo nasbirano " + str( curr_collections ) + " odkazu." )
                        email_client.statistics( "Doposud bylo stazeno " + str( curr_downloads ) + " stranek." )
                        email_client.send()
                    for key in rss_sources:
                        download_threads[ key ] = Parser_thread( sender = email_client, index = key, path = path, locksmith = locksmith, statistics = stat_manager, task_manager = task_manager, rss = rss_collection )
                        download_threads[ key ].start()
                today = datetime.datetime.today().day

            # Uspime skript na 2 hodiny, pak muze zacit nova kolekce dat.
            time.sleep( 7200 )
    except:
        # nastala chyba, posleme zpravu emailem a ukoncime zpracovani.
        reaper.die_without_honor()
        raise
    # Konec programu
    reaper.end()

if __name__ == '__main__':
    main()
