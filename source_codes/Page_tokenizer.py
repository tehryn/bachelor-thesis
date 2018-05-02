import multiprocessing
import subprocess
import re
import langdetect
import time
from Page_reader import Page_reader
from Page import Page
import sys

class Page_tokenizer( object ):
    def __init__( self, tokenizer_bin, filename = None, language = 'english', processes = 10, lang_detect = False, old_style = False ):
        self._page_reader = Page_reader( filename, old_style = old_style )
        self._tokenizer_bin  = tokenizer_bin
        if ( language == 'english' or language == 'czech' ):
            self._detect = language
        else:
            self._detect = 'generic'
        self._processes = processes
        self._langdetect = lang_detect

    @staticmethod
    def _translator( input_paragraphs, output_languages ):
        par = ''
        while ( True ):
            par = input_paragraphs.get()
            if ( par is not None ):
                lang = ''
                if ( len( par ) > 10 ):
                    try:
                        lang = langdetect.detect( par )
                    except:
                        lang = None
                else:
                    lang = None
                output_languages.put( lang )
            else:
                sys.stderr.write( 'koncim\n' )
                break
        time.sleep(0.1)

    def _tokenizer( self, input_queue, output_queue ):
        command = [ self._tokenizer_bin, '--tokenizer=' + self._detect, '--output=vertical' ]
        translator_inqueue  = multiprocessing.Queue()
        translator_outqueue = multiprocessing.Queue()
        while ( True ):
            page = input_queue.get()
            send_buff = ''
            if ( page is not None ):
                removed = list()
                tmp      = ''
                new_page = ''
                for line in page.get_text().splitlines():
                    if ( re.match( r'</?doc.*>|<img.*>|</?link.*>|</?head>|</?p>|</?div>|</?h[1-5]>', line ) ):
                        if ( line == '<div>' ):
                            line = '<p>'
                        elif ( line == '</div>' ):
                            line = '</p>'
                        new_page += tmp + line + '\n'
                        tmp = ''
                        continue
                    else:
                        line = re.sub( r'([\w])([^\w\s])|([^\w\s])([\w])', r'\1\3\n<g/>\n\2\4', line )
                    tmp += line  + '\n'
                page.clear()
                for line in new_page.splitlines():
                    if ( re.match( r'</?doc.*>|<img.*>|</?link.*>|</?head>|</?p>|</?h[1-5]>|<g/>', line ) ):
                        if ( line.startswith( '<link' ) ):
                            removed.append( '="' + page.get_absolute_url( line[7] ) )
                            line = '<link>'
                        elif ( line.startswith( '<img' ) ):
                            removed.append( '="' + page.get_absolute_url( line[6:] ) )
                            line = '<img>'
                        elif ( line.startswith( '<doc' ) ):
                            removed.append( line[4:] )
                            line = '<doc>'
                        line = Page.encode_tag( line )
                    send_buff += line + '\n'

                if ( self._langdetect ):
                    multiprocessing.Process( target = self._translator, args = ( translator_inqueue, translator_outqueue ) ).start()

                process = subprocess.Popen( command, stdout=subprocess.PIPE, stdin=subprocess.PIPE )
                try:
                    ret_value = process.communicate( send_buff.encode(), timeout=0.5 )[0].decode()
                except:
                    process.kill()
                    ret_value = process.communicate()[0].decode()
                #    sys.stderr.write( 'skipped: ' + page.get_url() +'\n' )
                replaced  = ''
                sentence  = 0 # 0 - mimo vetu, 1 - ve vete, 3 - ukoncit
                paragraph = 0 # 0 - mimo, 1 - mozna zacina, 2 - unvnitr, 3 - ukoncit
                link_len  = -1
                odeslano  = 0
                translator_buffer = ''
                for line in ret_value.splitlines():
                    if ( line.startswith( Page.tag_begin ) ):
                        line = Page.decode_tag( line )
                        if ( paragraph == 2 and re.match( r'<(/?p|/?h[1-5]|/?head|/?doc)>', line ) ):
                            paragraph = 0
                            if ( line == '<p>' ):
                                paragraph = 1
                            elif ( line == '<doc>' ):
                                rest = removed.pop(0)
                                line = '<doc' + rest
                            if ( line != '</p>' ):
                                line = '</p>\n' + line
                            if ( sentence == 1 ):
                                line = '</s>\n' + line
                                sentence = 0
                        else:
                            if ( line == '<p>' or line == '</p>' ):
                                continue
                            elif ( line == '<link>' ):
                                rest = removed.pop(0)
                                link_str = '<link' + rest
                                link_len = 0
                                continue
                            elif ( line == '<doc>' ):
                                rest = removed.pop(0)
                                line = '<doc' + rest
                            elif ( line == '<g/>' and replaced[-5:-1] == '</s>' ):
                                replaced = replaced[:-5] + '<g/>\n</s>\n'
                                continue
                            elif ( line == '<img>' ):
                                rest = removed.pop(0)
                                line = '<img' + rest + '\t<lenght=1>'
                                if ( paragraph == 0 ):
                                    line = '<p>\n<s>\n' + line
                                paragraph = 2
                            elif ( line == '</link>' ):
                                if ( link_len < 0 ): # Obcas nejaky chytrak da odkaz dovnitr odkazu...
                                    link_len = 0
                                if ( paragraph == 0 ):
                                    link_str = '<p>\n<s>\n' + link_str
                                paragraph = 2
                                sentence  = 1
                                line = link_str + '\t<lenght=' + str( link_len ) + '>'
                                link_len = -1
                            elif ( paragraph == 1 and line == '</doc>' ):
                                replaced = replaced[:-4]
                    else:
                        if ( self._langdetect ):
                            translator_buffer += line + '\n'
                        if ( len( line ) > 0 ):
                            if ( sentence == 0 ):
                                line     = '<s>\n' + line
                                sentence = 1
                            if ( paragraph == 0 ):
                                line = '<p>\n' + line
                                paragraph = 2
                            elif ( paragraph == 1 ):
                                paragraph = 2
                        elif ( sentence == 1 ):
                            line = '</s>' + line
                            sentence = 0
                    if ( link_len >= 0 ):
                        link_len += 1
                    if ( self._langdetect and '</p>' in line ):
                        odeslano += 1
                        translator_inqueue.put( translator_buffer )
                        translator_buffer = ''
                    replaced += line + '\n'

                if ( self._langdetect ):
                    translated = ''
                    translator_inqueue.put( None )
                    for line in replaced.splitlines():
                        if ( line == '<p>' ):
                            if ( odeslano == 0 ):
                                sys.stderr.write( "DEADLOCK\n" )
                                break
                            else:
                                lang = translator_outqueue.get()
                                odeslano -= 1
                                if ( lang ):
                                    line = '<p lang="' + lang + '">'
                        translated += line + '\n'
                    output_queue.put( translated )
                    if ( odeslano != 0 ):
                        sys.stderr.write( "NEBYLO PRELOZENO VSE\n" )
                        sys.stderr.write( replaced )

                else:
                    output_queue.put( replaced )
            else:
                output_queue.put( None )
                time.sleep(0.1) # Tohle by se delat nemelo - je to tu jen pro jistotu
                break

    def __iter__( self ):
        input_queue  = multiprocessing.Queue()
        output_queue = multiprocessing.Queue()

        for i in range( self._processes ):
            multiprocessing.Process( target = self._tokenizer, args = ( input_queue, output_queue ) ).start()

        cnt = 1
        for page in self._page_reader:
            input_queue.put( page )
            try:
                while ( True ):
                    yield output_queue.get( block = False )
                    sys.stderr.write( str(cnt) + '\n' )
                    cnt += 1
            except:
                pass
        for i in range( self._processes ):
            input_queue.put( None )
        input_queue.close()
        cond = self._processes
        while ( cond > 0 ):
            tokenized = output_queue.get()
            if ( tokenized is not None ):
                yield tokenized
                sys.stderr.write( str(cnt) + '\n' )
                cnt += 1
            else:
                cond -= 1
        input_queue.join_thread()
        output_queue.close()
        output_queue.join_thread()

if __name__ == '__main__':
    # input_file tagger_bin tagger_file timeout
    parser = Page_tokenizer( tokenizer_bin = sys.argv[2], filename = sys.argv[1], lang_detect = True, processes = 10)
    for tagged in parser:
        print( tagged )
        #pass