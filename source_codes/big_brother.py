#!/usr/bin/env python3
"""Skript big_brother slouzi k pravidelnemu spouzteni celeho procesu zpracovani stranek a k vedeni statistik, logu, popripade zasilani informaci o chybach emailem"""
import sys
import os
import time
import subprocess
import threading
import smtplib
import datetime
from email.mime.text import MIMEText
from Functions import get_setting, print_help

class Email_sender( object ):
    def __init__( self, sender, to, subject ):
        self._messages   = list()
        self.sender      = sender
        self.to          = to
        self.subject     = subject
        self.lock        = threading.Lock()
        self._last_email = 0

    def __add__( self, message ):
        self._messages.append( time.strftime( "%d-%m-%Y %H:%M: ", time.localtime( time.time() ) ) + message )
        return self

    def send( self ):
        content = '\n'.join( self._messages )
        msg = MIMEText( content )
        msg['Subject'] = self.subject
        msg['From']    = self.sender
        msg['To']      = self.to
        s = smtplib.SMTP( 'localhost' )
        s.sendmail( self.sender, self.to, msg.as_string() )
        s.quit()
        self._messages = list()
        self._last_email = time.time()
        print( "Message sent" )

    def last_email( self ):
        return self._last_email

class Collector_thread ( threading.Thread ):
    """Trida, ktera se stara o spousteni kolekce odkazu."""
    def __init__( self, index, sender, rss_sources, path ):
        threading.Thread.__init__( self )
        self.key      = index
        self.input    = rss_sources
        self._sender  = sender
        self._path    = path

    def run( self ):
        collection_start    = time.time()
        collection_filename = time.strftime( "%d%m%Y%H%M", time.localtime( collection_start ) )
        output_file = self._path + '/collected_links/' + self.key + '/' + collection_filename + '.collected'
        log_file    = self._path + '/logs/' + self.key + '/' + collection_filename + '.link_collector'

        if not os.path.exists( self._path + '/collected_links/' + self.key + '/' ):
            os.makedirs( self._path + '/collected_links/' + self.key + '/' )

        if not os.path.exists( self._path + '/logs/' + self.key + '/' ):
            os.makedirs( self._path + '/logs/' + self.key + '/' )

        dedup_files = os.listdir( self._path + '/collected_links/' + self.key )
        dedup_files = [ self._path + '/collected_links/' + self.key + '/' + filename for filename in dedup_files ]
        collector   = None

        if dedup_files:
            collector   = [ self._path + '/link_collector.py', '-i', self.input, '-e', log_file, '-w', '5', '-m', '50', '-d' ] + dedup_files
        else:
            collector   = [ self._path + '/link_collector.py', '-i', self.input, '-e', log_file, '-w', '5', '-m', '50' ]

        process        = subprocess.Popen( collector, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        stdout, stderr = process.communicate()
        with self._sender.lock:
            if ( stdout ):
                num = sum( 1 for c in stdout.decode( 'utf-8' ) if c == '\n'  )
                try:
                    with open( output_file, 'w' ) as f:
                        f.write( stdout.decode( 'utf-8' ) )
                        self._sender += self.key + " - Kolekce byla dokoncena, bylo nalezeno " + str( num ) + " stranek." + ", vstupni soubory jsou " + self.input + ", vystupni souborem je: " + output_file
                except:
                    self._sender += self.key + " - Nemohl jsem ulozit nalezene stranky z rss zdroju do souboru: '" + output_file + "'"
            if ( stderr ):
                self._sender += self.key + "Kolekce skoncila s fatalni chybou: '" + stderr.decode( 'utf-8' ) + "'"

class Downloader_thread ( threading.Thread ):
    """Trida, ktera se stara o spousteni stahovani stranek."""

    def __init__( self, index, sender, path ):
        threading.Thread.__init__( self )
        self.key     = index
        self._sender = sender
        self._path   = path

    def _download_pages( self ):
        if not os.path.exists( self._path + '/downloaded/' + self.key + '/' ):
            os.makedirs( self._path + '/downloaded/' + self.key + '/' )

        input_files = list()
        for filename in os.listdir( self._path + '/collected_links/' + self.key ):
            filename = self._path + '/collected_links/' + self.key + '/' + filename
            if ( filename.endswith( '.collected' ) ):
                #os.rename( filename, filename[:-9] + 'downloading' )
                #input_files.append( filename[:-9] + 'downloading' )

        download_filename = time.strftime( "%d%m%Y%H%M", time.localtime( time.time() ) )
        output_file =  self._path + '/downloaded/' + self.key + '/' + download_filename + '.warc'
        log_file = self._path + '/logs/' + self.key + '/' + download_filename + '.page_downloader'
        if ( input_files ):
            downloader  = [ self._path + '/page_downloader.py', '-o', output_file, '-e', log_file, '-w', '5', '-i' ] + list( input_files )
            process     = subprocess.Popen( downloader, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
            stdout, stderr = process.communicate()

            with self._sender.lock:
                if ( stdout ):
                    num = sum( 1 for c in stdout.decode( 'utf-8' ) if c == '\n'  )
                    self._sender += self.key + " - stahovani bylo dokonceno. Bylo stazeno " + str( num ) + " stranek, vstupni soubory jsou " + str( input_files ) + ", vystupnim souborem je: " + output_file
                if ( stderr ):
                    self._sender += self.key + " - stahovani skoncilo s fatalni chybou: '" + stderr.decode( 'utf-8' ) + "'"

            for filename in input_files:
                os.rename( filename, filename[:-11] + 'downloaded' )

    def _tokenize( self ):
        filename = time.strftime( "%d%m%Y%H%M", time.localtime( time.time() ) )
        output_file =  self._path + '/vert/' + self.key + '/' + filename + '.vert'
        if not os.path.exists( self._path + '/vert/' + self.key + '/' ):
            os.makedirs( self._path + '/vert/' + self.key + '/' )

        input_files = list()
        for filename in os.listdir( self._path + '/downloaded/' + self.key ):
            filename = self._path + '/downloaded/' + self.key + '/' + filename
            if ( filename.endswith( '.downloaded' ) ):
                os.rename( filename, filename[:-10] + 'processing' )
                input_files.append( filename[:-10] + 'processing' )

        if ( input_files ):
            tokenizer   = self._path + '/libary/morphodita/precompiled_bin/run_tokenizer'
            params  = [ self._path + '/html_to_vert.py', '-o', output_file, '-l', '-f', '-m', '12', '-t', tokenizer, '-i' ] + list( input_files )
            process     = subprocess.Popen( params, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
            stdout, stderr = process.communicate()

            with self._sender.lock:
                if ( stdout ):
                    self._sender += self.key + " - Prevod textu do vertikalini podoby skoncil s neocekavanym vystupem na standardni vystup:\n" + str( stdout.decode( 'utf-8' ) ) + "\n"
                if ( stderr ):
                    self._sender += self.key + " - Prevod textu do vertikalini podoby skoncil s fatalni chybou:\n" + stderr.decode( 'utf-8' ) + "\n"
                    for filename in input_files:
                        os.rename( filename, filename[:-10] + 'failed' )
                else:
                    self._sender += self.key + " - Prevod textu do vertikalini podoby skoncil s fatalni chybou:\n" + stderr.decode( 'utf-8' ) + "\n"
                    for filename in input_files:
                        process = subprocess.Popen( [ 'xz', '-9', filename ], stdout=subprocess.PIPE, stderr=subprocess.PIPE )
                        os.rename( filename, filename[:-13] + 'downloaded.xz' )
                        process.communicate()

    def _tagging( self ):
        def dedup():
            pass
        filename = time.strftime( "%d%m%Y%H%M", time.localtime( time.time() ) )
        output_file =  self._path + '/tagged/' + self.key + '/' + filename + '.vert'
        if not os.path.exists( self._path + '/tagged/' + self.key + '/' ):
            os.makedirs( self._path + '/tagged/' + self.key + '/' )

        input_files = list()
        for filename in os.listdir( self._path + '/dedup/' + self.key ):
            filename = self._path + '/dedup/' + self.key + '/' + filename
            if ( filename.endswith( '.vert' ) ):
                os.rename( filename, filename[:-4] + 'processing' )
                input_files.append( filename[:-4] + 'processing' )

        if ( input_files ):
            tokenizer   = self._path + '/libary/morphodita/precompiled_bin/run_tokenizer'
            params  = [ self._path + '/html_to_vert.py', '-o', output_file, '-l', '-f', '-m', '12', '-t', tokenizer, '-i' ] + list( input_files )
            process     = subprocess.Popen( params, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
            stdout, stderr = process.communicate()

            with self._sender.lock:
                if ( stdout ):
                    self._sender += self.key + " - Prevod textu do vertikalini podoby skoncil s neocekavanym vystupem na standardni vystup:\n" + str( stdout.decode( 'utf-8' ) ) + "\n"
                if ( stderr ):
                    self._sender += self.key + " - Prevod textu do vertikalini podoby skoncil s fatalni chybou:\n" + stderr.decode( 'utf-8' ) + "\n"
                else:
                    self._sender += self.key + " - Prevod textu do vertikalini podoby skoncil s fatalni chybou:\n" + stderr.decode( 'utf-8' ) + "\n"
            for filename in input_files:
                os.rename( filename, filename[:-10] + 'finished' )
                process = subprocess.Popen( [ 'xz', '-9', filename[:-10] + 'finished' ], stdout=subprocess.PIPE, stderr=subprocess.PIPE )
                process.communicate()


    def run( self ):
        self._download_pages()
        #self._tokenize()

def main():
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
            'names'        : [ '--interval', '-i' ],
            'optional'     : True,
            'has_tail'     : 1,
            'word_index'   : 'interval',
            'prerequisite' : None,
            'description'  : 'Casovy udaj v hodinach (musi byt cele cislo typu Int) ' +
                             'udavajici jak casto se budou odesilat statistiky. ' +
                             'Pokud neni argument zadan, budou zasilany jen hlaseni ' +
                             'o kritickych chybach.'
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
            'names'        : [ '--statistiks',   '-s' ],
            'optional'     : False,
            'has_tail'     : 1,
            'word_index'   : 'statistiks',
            'prerequisite' : None,
            'description'  : 'Soubor, do ktereho bude vedena statistika. Soubor bude otevren v rezimu append a ve formatu csv.'
        },
    ]

    settings = dict()
    try:
        settings = get_setting( possible_arguments, sys.argv[1:] )
    except:
        if ( len( sys.argv ) > 1 and ( sys.argv[1] == '-h' or sys.argv[1] == '--help' ) ):
            print_help( possible_arguments, sys.argv[0], sys.stdout, author )
            print( "what" )
            exit(0)
        else:
            raise

    # Ulozim si nastaveni parametru do promennych.
    statistiks_file    = settings[ 'statistiks' ][0]
    email_interval     = int( settings[ 'interval' ][0] ) * 3600 if ( 'interval' in settings ) else None
    email              = settings[ 'email' ][0]

    path = os.path.abspath( '.' )
    email_client = Email_sender( sender = email, to = email, subject = 'Pravidelná zpráva od Velkého bratra' )
    collector_threads  = dict()
    download_threads   = dict()
    today = 0

    email_client += "Bylo spuštěno automatické zpracování dat."
    email_client.send(  )

    while ( True ):
        rss_sources = dict()
        for filename in os.listdir( path + '/rss_sources/' ):
            if ( filename.endswith( '.txt' ) and len( filename ) > 4 and filename != 'blogs.txt' ):
                rss_sources[ filename[:-4] ] = path + '/rss_sources/' + filename
            else:
                with email_client.lock:
                    email_client += "Ve složce s RSS zdroji je soubor ve spatnem formatu - " + filename

        for key in rss_sources:
            if not( key in collector_threads and collector_threads[ key ].is_alive() ):
                collector_threads[ key ] = Collector_thread( index = key, sender = email_client, rss_sources = rss_sources[ key ], path = path )
                collector_threads[ key ].start()


        if ( True or today != datetime.datetime.today().day ):
            today = datetime.datetime.today().day
            for key in rss_sources:
                download_threads[ key ] = Downloader_thread( sender = email_client, index = key, path = path )
                download_threads[ key ].start()
        time.sleep( 7200 )
        with email_client.lock:
            email_client.send()

if __name__ == '__main__':
    main()