#!/usr/bin/env python3
"""Skript big_brother slouzi k pravidelnemu spouzteni celeho procesu zpracovani stranek a k vedeni statistik, logu, popripade zasilani informaci o chybach emailem"""
import sys
import os
import time
import subprocess
import threading
import smtplib
from email.mime.text import MIMEText
from Functions import get_setting, print_help

author = "Author:\n" + \
         "  Jmeno: Jiri Matejka\n" + \
         "  Email: xmatej52@stud.fit.vutbr.cz nebo jiri.matejkaa@gmail.com\n" + \
         "  FIT VUT v Brne, Vyzkumna skupina KNOT@FIT"

possible_arguments = [
    {
        'names'        : [ '--collector',  '-c' ],
        'optional'     : True,
        'has_tail'     : 1,
        'word_index'   : 'collector',
        'prerequisite' : None,
        'description'  : 'Casovy udaj v minutach (musi byt cele cislo typu Int) ' +
                         'udavajici jak casto se ma spoustet kolekce odkazu. ' +
                         'Vychozi hodnota je 120 minut.'
    },
    {
        'names'        : [ '--downloader',  '-d' ],
        'optional'     : True,
        'has_tail'     : 1,
        'word_index'   : 'downloader',
        'prerequisite' : None,
        'description'  : 'Casovy udaj v hodinach (musi byt cele cislo typu Int) ' +
                         'udavajici jak casto se ma spoustet stahovani stranek. ' +
                         'Vychozi hodnota je 24 hodin.'
    },
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
        'names'        : [ '--attachment', '-a' ],
        'optional'     : True,
        'has_tail'     : 0,
        'word_index'   : 'attachment',
        'prerequisite' : 'email',
        'description'  : 'Pokud je parametr nastaven, budou odeslany i soubory se statistikami ' +
                         'jako priloha emailu.'
    },
    {
        'names'        : [ '--logs', '-l' ],
        'optional'     : True,
        'has_tail'     : 0,
        'word_index'   : 'logs',
        'prerequisite' : 'attachment',
        'description'  : 'Pokud je parametr nastaven, budou odeslany vedle statistik i logy ' +
                         'jako priloha emailu.'
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
    {
        'names'        : [ '--output',   '-o' ],
        'optional'     : False,
        'has_tail'     : 1,
        'word_index'   : 'output',
        'prerequisite' : None,
        'description'  : 'Slozka, ve ktere se budou ukladat stazene stranky.'
    }
]

settings = dict()
try:
    settings = get_setting( possible_arguments, sys.argv[1:] )
except:
    if ( len( sys.argv ) > 1 and ( sys.argv[1] == '-h' or sys.argv[1] == '--help' ) ):
        print_help( possible_arguments, sys.argv[0], sys.stdout, author )
        exit(0)
    else:
        raise

# Nastavim si cestu k projektu
path = os.path.abspath( '.' )

# Cesta k rss zdrojim. Klice pouziju jako jmena slozek v logach a stazenych souborech.
rss_sources = {
    'newsbrief_eu' : path + '/rss_sources/newsbrief_eu.txt',
    'cs_media'     : path + '/rss_sources/cs_media.txt',
    'blogs'        : path + '/rss_sources/blogs.txt',
    'other'        : path + '/rss_sources/other.txt'
}

# Ulozim si nastaveni parametru do promennych.
download_interval  = int( settings[ 'downloader' ][0] ) if ( 'downloader' in settings ) else 24
download_interval *= 3600
collect_interval   = int( settings[ 'collector' ][0] ) if ( 'collector' in settings ) else 120
collect_interval  *= 60
email_attachment   = True if ( 'attachment' in settings ) else False
statistiks_file    = settings[ 'statistiks' ][0]
output_directory   = settings[ 'output' ][0][:-1] if settings[ 'output' ][0].endswith( '/' ) else settings[ 'output' ][0]
email_interval     = int( settings[ 'interval' ][0] ) * 3600 if ( 'interval' in settings ) else None
email              = settings[ 'email' ][0]
email_logs         = True if ( 'logs' in settings ) else False

email_messages       = list()
email_messages_l     = threading.Lock()
collector_finished_s = threading.Semaphore( len( rss_sources ) )
trash_in_folders     = dict()
files_to_download    = dict()
downloaded_files     = dict()
last_collections     = dict()
last_downloads       = dict()
collector_threads    = dict()
download_threads     = dict()
semaphores           = dict()
for key in rss_sources:
    files_to_download[ key ] = set()
    downloaded_files[ key ]  = set()
    trash_in_folders[ key ]  = set()
    last_collections[ key ]  = time.time()
    last_downloads[ key ]    = time.time()
    collector_threads[ key ] = None
    download_threads[ key ]  = None
    semaphores[ key ] = { 'files_to_download':threading.Lock() }
    if not os.path.exists( output_directory + '/' + key + '/' ):
        os.makedirs( output_directory + '/' + key + '/' )

class Collector_thread ( threading.Thread ):
    """Trida, ktera se stara o spousteni kolekce odkazu."""
    def __init__( self, index ):
        threading.Thread.__init__( self )
        self.key = index

    def run( self ):
        collection_start = time.time()
        collection_filename = time.strftime( "%d%m%Y%H%M", time.localtime( collection_start ) )
        output_file = path + '/collected_links/' + self.key + '/' + collection_filename + '.collected'
        log_file    = path + '/logs/' + self.key + '/' + collection_filename + '.link_collector'
        dedup_files = os.listdir( path + '/collected_links/' + self.key )
        dedup_files = [ path + '/collected_links/' + self.key + '/' + filename for filename in dedup_files ]
        collector   = None

        if dedup_files:
            collector   = [ path + '/link_collector.py', '-i', rss_sources[ self.key ], '-e', log_file, '-w', '5', '-m', '50', '-d' ] + dedup_files
        else:
            collector   = [ path + '/link_collector.py', '-i', rss_sources[ self.key ], '-e', log_file, '-w', '5', '-m', '50' ]

        process        = subprocess.Popen( collector, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        stdout, stderr = process.communicate()
        collector_finished_s.release()

        with email_messages_l:
            if ( stdout ):
                num = sum( 1 for c in stdout.decode( 'utf-8' ) if c == '\n'  )
                try:
                    with open( output_file, 'w' ) as f:
                        f.write( stdout.decode( 'utf-8' ) )
                    email_messages.append(
                        time.strftime(
                            "%d-%m-%Y %H:%M " + self.key + ": ",
                            time.localtime( time.time() )
                        )
                        + "Kolekce byla dokoncena," + "bylo nalezeno " + str( num ) + " stranek."
                        + ", vstupni soubory jsou " + rss_sources[ self.key ] + ", vystupni souborem je: " + output_file
                    )
                except:
                    email_messages.append(
                        time.strftime(
                            "%d-%m-%Y %H:%M " + self.key + ": ",
                            time.localtime( time.time() )
                        )
                        + "Nemohl jsem ulozit nalezene stranky z rss zdroju do souboru: '" + output_file + "'"
                    )
            if ( stderr ):
                email_messages.append(
                    time.strftime(
                        "%d-%m-%Y %H:%M " + self.key + ": ",
                        time.localtime( time.time() )
                    )
                    + "Kolekce skoncila s fatalni chybou: '" + stderr.decode( 'utf-8' ) + "'"
                )

        with semaphores[ key ][ 'files_to_download' ]:
            files_to_download[ self.key ].add( output_file )

        last_collections[ self.key ] = time.time()
        return

class Downloader_thread ( threading.Thread ):
    """Trida, ktera se stara o spousteni stahovani stranek."""
    def __init__( self, index ):
        threading.Thread.__init__( self )
        self.key = index

    def run( self ):
        download_start = time.time()
        download_filename = time.strftime( "%d%m%Y%H%M", time.localtime( download_start ) )
        output_file = output_directory + '/' + self.key + '/' + download_filename + '.warc.xz'

        with semaphores[ key ][ 'files_to_download' ]:
            input_files = files_to_download[ self.key ].copy()
            files_to_download[ key ] = set()

        log_file = path + '/logs/' + self.key + '/' + download_filename + '.page_downloader'
        if ( input_files ):
            downloader  = [ path + '/page_downloader.py', '-o', output_file, '-e', log_file, '-w', '5', '-i' ] + list( input_files )
            process     = subprocess.Popen( downloader, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
            stdout, stderr = process.communicate()

            with email_messages_l:
                if ( stdout ):
                    num = sum( 1 for c in stdout.decode( 'utf-8' ) if c == '\n'  )
                    email_messages.append(
                        time.strftime(
                            "%d-%m-%Y %H:%M " + self.key + ": ",
                            time.localtime( time.time() )
                        )
                        + "Stahovani bylo dokonceno," + "bylo stazeno " + str( num ) + " stranek."
                        + ", vstupni soubory jsou " + str( input_files ) + ", vystupni souborem je: " + output_file
                    )
                if ( stderr ):
                    email_messages.append(
                        time.strftime(
                            "%d-%m-%Y %H:%M " + self.key + ": ",
                            time.localtime( time.time() )
                        )
                        + "Stahovani skoncilo s fatalni chybou: '" + stderr.decode( 'utf-8' ) + "'"
                    )
            for filename in input_files:
                os.rename( filename, filename[:-9] + '.downloaded' )
        last_downloads[ self.key ] = time.time()
        return

email_cnt       = 0
last_email_sent = 0
while ( True ):
    for key in rss_sources:
        if not( collector_threads[ key ] and collector_threads[ key ].is_alive() ):
            collector_threads[ key ] = Collector_thread( key )
            collector_finished_s.acquire()
            collector_threads[ key ].start()

        if ( ( time.time() - last_downloads[ key ] ) >= download_interval ):
            if not( download_threads[ key ] and download_threads[ key ].is_alive() ):
                download_threads[ key ] = Downloader_thread( key )
                download_threads[ key ].start()

    if ( email_interval ):
        if ( ( time.time() - last_email_sent ) > email_interval ):
            with email_messages_l:
                if ( len( email_messages ) > 0 ):
                    if ( email_cnt < 10 ):
                        email_cnt += 1
                        content = '\n'.join( email_messages )
                        email_messages = list()
                        msg = MIMEText( content )
                        msg['Subject'] = 'Pravidelna zprava od Velkeho bratra'
                        msg['From']    = email
                        msg['To']      = email

                        s = smtplib.SMTP( 'localhost' )
                        s.sendmail( email, email, msg.as_string() )
                        s.quit()
                last_email_sent = time.time()
    nap_time = collect_interval
    for key in rss_sources:
        difference = time.time() - last_collections[ key ]
        if ( difference < collect_interval and difference < nap_time ):
            nap_time = collect_interval - difference
        elif ( difference > collect_interval ):
            nap_time = 0
    if ( nap_time > 0 ):
        time.sleep( nap_time )

    # Cekam dokud alespon jedna kolekce nedokonci svou cinnost
    collector_finished_s.acquire()
    collector_finished_s.release()