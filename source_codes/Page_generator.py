import Functions
import time
from Page_downloader import Page_downloader

class Page_generator( Page_downloader ):
    _pause         = 0
    _links         = dict()

    def __init__( self, iterable, pause=None, wait=1, tries=1 ):
        super().__init__( wait, tries )
        if ( pause ):
            self._pause = pause

        for item in iterable:
            index = -1
            if ( item.startswith( 'https://' ) or item.startswith( 'http://' ) ):
                index = Functions.find_nth( item, '/', 3 )
            else:
                index = Functions.find_nth( item, '.', 2 )
            key = item[ :index ] if ( index >= 0 ) else item
            if not ( key in self._links ):
                self._links[ key ] = list()
            self._links[ key ].append( item )

    def _get_one_page( self, key ):
            link = self._links[ key ].pop()
            if ( len( self._links[ key ] ) == 0 ):
                del self._links[ key ]
            page = super().get_page_from_url( link )
            if ( page[ 'error' ] ):
                super()._set_error( page[ 'value' ], link )
                return None
            else:
                return { 'content': page[ 'value' ], 'url' : link, 'response' : page[ 'response' ] }

    def __iter__( self ):
        cont = True
        first_download = 0
        last_download  = 0
        while ( len(self. _links ) > 0 ):
            first_download = time.time()
            cont = False
            for key in list( self._links ):
                cont = True
                page = self._get_one_page( key )
                if ( page ):
                    yield page
                last_download = time.time()

            nap_time = last_download - first_download
            if ( nap_time < self._pause ):
                time.sleep( self._pause - nap_time )

if __name__ == '__main__':
    urls = {
        'http://www.chip.cz/novinky/hry/vychazi-game-ready-ovladace-ke-hre-final-fantasy-xv-windows-edition/',
        'https://havlickobrodsky.denik.cz/z-regionu/oparene-dite-stepankova-nova-role-a-marne-skandovani-belehradskych-videa-dne-20180222.html',
        'https://havlickobrodsky.denik.cz/z-regionu/ve-viru-zacnou-po-ledove-stene-lezt-v-sobotu-20180222.html',
        'http://www.chip.cz/novinky/mobily/mobil-sony-umi-nahravat-hdr-video/',
        'http://www.chip.cz/novinky/business/prisel-cas-nastupu-nositelne-elektroniky-v-podnikovem-prostredi/',
        'https://havlickobrodsky.denik.cz/z-regionu/chripka-zabijela-potreti-epidemie-na-vysocine-stale-trva-20180226.html',
        'http://hdmag.cz/clanek/sonos-pry-chysta-novy-soundbar-s-hdmi-2-1',
        'http://www.chip.cz/novinky/business/foxconn-4tech-priveze-na-amper-2018-novinky-menici-podobu-ceskeho-prumyslu/',
        'https://hlidacipes.org/luftjarda-se-vraci-jaroslav-tvrdik-muze-diky-cinske-cefc-csa-hlavnim-vchodem/#comment-23874',
        'https://homebydleni.cz/zahrada/relax-v-zahrade/lexikon-bazenu-aneb-jak-si-vybrat/#comment-13626',
        'https://havlickobrodsky.denik.cz/z-regionu/zelene-oazy-vzniknou-v-trebici-i-na-zdarsku-20180222.html',
        'https://havlickobrodsky.denik.cz/z-regionu/do-slakhamru-miri-stale-vic-navstevniku-lakaji-je-i-tematicke-akce-20180226.html',
        'http://hdmag.cz/clanek/do-roku-2021-prijde-nastupce-kodeku-hevc',
        'https://hlidacipes.org/zavrazdeny-novinar-jan-kuciak-utoku-novinare-pribyva-ukladna-vrazda-vsak-extrem/#comment-23869',
        'https://havlickobrodsky.denik.cz/z-regionu/obec-kaliste-chce-vybudovat-pamatnik-obetem-velke-valky-20180222.html',
        'http://www.chip.cz/novinky/hardware/prohnuty-monitor-se-stereo-reproduktory/',
        'https://havlickobrodsky.denik.cz/z-regionu/tuhe-mrazy-preji-brusleni-na-zamrzlych-rybnicich-20180226.html',
        'http://www.chip.cz/novinky/trendy/bose-pro-profi-akusticke-hrani-na-verejnosti/',
        'http://www.chip.cz/temata/cizi-jazyky-jsou-pro-9-z-10-cechu-jasnou-konkurencni-vyhodou/',
        'https://hlidacipes.org/ceska-televize-rozhlas-prijdou-stovky-milionu-podle-ministerstva-financi-musi-kvuli-bruselu/#comment-23871',
        'https://homebydleni.cz/dum/navstevy-domu/neni-dum-jako-dum-upati-jizerskych-hor-stoji-staveni-ktere-vyvraci-vsechny-stereotypy/#comment-13630',
        'https://havlickobrodsky.denik.cz/z-regionu/na-cviceni-ample-strike-prileti-letouny-f-16-a-vrtulniky-apache-20180226.html',
        'http://www.chip.cz/novinky/hardware/huawei-matebook-pro-prvni-notebook-s-3k-fullview-displejem/',
        'https://hlidacipes.org/protikorupcni-special-odpis-vlada-neplanuje-boj-nej-vzdali-i-sami-statni-zastupci/#comment-23868',
        'http://www.chip.cz/novinky/hardware/levne-tablety-s-androidem-oreo/',
        'https://havlickobrodsky.denik.cz/z-regionu/luk-od-dedecka-s-laskou-opatruji-dodnes-rika-vyznavacka-cosplay-z-jihlavy-20180223.html',
        'http://www.chip.cz/novinky/hardware/nova-sluchatka-od-energy-sistem/',
        'http://www.chip.cz/temata/zbavte-se-zbytecnosti/',
        'https://homebydleni.cz/dum/drevostavby/jak-jsem-si-postavil-chatu-svepomoci/#comment-13628',
        'https://havlickobrodsky.denik.cz/z-regionu/z-jedne-strany-vita-lidi-kralovstvi-ceske-z-druhe-markrabstvi-moravske-20180221.html',
        'http://hdmag.cz/clanek/leema-acoustics-oslavuje-vyroci-novym-zesilovacem',
        'https://homebydleni.cz/zahrada/rady-a-tipy/ozivte-svou-zahradu-zastenou-osvetlenim/#comment-13624',
        'http://www.chip.cz/novinky/mobily/nove-vecko-doro-6050-pro-seniory/',
        'https://homebydleni.cz/dum/navstevy-domu/maly-pasivni-dum-navrzeny-jako-nenarocne-bydleni-zacinajici-rodinu/#comment-13629',
        'https://hlidacipes.org/mlady-gustav-husak-kreml-nej-jako-vatikan-jezis-neco-jako-prvni-komunista/#comment-23873',
        'http://www.chip.cz/novinky/mobily/smartphony-samsung-galaxy-s-v-devate-verzi/',
        'https://havlickobrodsky.denik.cz/z-regionu/skolaci-si-uzivaji-volna-na-stene-20180228.html',
        'http://www.chip.cz/novinky/bezpecnost/nejvetsi-podvodna-kampan-tezici-kryptomeny/',
        'http://www.chip.cz/novinky/trendy/sony-predstavilo-svoji-budoucnost-v-srdci-evropy/',
        'http://www.chip.cz/novinky/hardware/rychlejsi-thinkpady-pro-snadnejsi-podnikani/',
        'http://hdmag.cz/clanek/fujifilm-uvadi-fotoaparat-pro-aktivni-lidi-finepix-xp130',
        'https://havlickobrodsky.denik.cz/z-regionu/zasnezene-plane-na-zdarsku-brazdi-lyzari-s-draky-20180224.html',
        'http://www.chip.cz/novinky/trendy/lenovo-na-mwc-2018/',
        'http://www.chip.cz/novinky/bezpecnost/banan-se-vraci-a-dalsi-novinky-nokia/',
        'http://www.chip.cz/novinky/hry/total-war-arena-otevrena-beta-je-tu/',
        'https://havlickobrodsky.denik.cz/z-regionu/v-lednu-bylo-na-vysocine-tepleji-nez-rikaji-dlouhodobe-statistiky-20180226.html',
        'http://www.chip.cz/novinky/trendy/qualcomm-vyuzije-technologii-samsungu-pro-vyrobu-7nm-5g-cipu/',
        'http://hdmag.cz/clanek/asus-uvedl-kit-pro-monitory-lomem-svetla-odstrani-okraje',
        'http://hdmag.cz/clanek/philips-letos-predstavi-3-rady-oled-tv-s-hdr10',
        'https://havlickobrodsky.denik.cz/z-regionu/vlcice-utekla-ze-zoo-nemela-by-byt-nebezpecna-20180223.html',
        'http://hdmag.cz/clanek/herni-headset-asus-rog-disponuje-dac-i-7-1kanalovym-zvukem',
        'https://homebydleni.cz/dum/stavebni-materialy/stavba-domu-svepomoci-ci-klic/#comment-13622',
        'http://hdmag.cz/clanek/canon-predstavil-videokameru-pro-pokrocile-uzivatele',
        'https://havlickobrodsky.denik.cz/z-regionu/zacala-soutez-vesnice-roku-20180220.html',
        'http://www.chip.cz/novinky/foto-video/nova-bezzrcadlovka-canon-eos-m50-s-rozlisenim-4k/',
        'https://homebydleni.cz/dum/navstevy-domu/unikatni-dum-brehu-jezera/#comment-13625',
        'https://homebydleni.cz/dum/navstevy-domu/verili-byste-ze-tento-dum-postavili-ze-starych-kontejneru/#comment-13621',
        'http://www.chip.cz/novinky/bezpecnost/ransomware-pro-android-blokuje-mobil/',
        'https://havlickobrodsky.denik.cz/z-regionu/deti-v-kalistich-maji-o-tyden-delsi-jarni-prazdniny-20180220.html',
        'https://homebydleni.cz/dum/stavebni-materialy/kolik-stoji-hruba-stavba/#comment-13631',
        'https://havlickobrodsky.denik.cz/z-regionu/policiste-v-roli-hasicu-zachranuji-a-maskary-skotaci-prohlednete-si-videa-dne-20180227.html',
        'http://www.chip.cz/novinky/bezpecnost/nejaktualnejsi-hrozby-pro-chytra-domaci-zarizeni/',
        'https://havlickobrodsky.denik.cz/z-regionu/nova-zachytka-bude-z-kontejneru-20180221.html',
        'https://hlidacipes.org/zavrazdeny-novinar-jan-kuciak-utoku-novinare-pribyva-ukladna-vrazda-vsak-extrem/#comment-23867',
        'https://hlidacipes.org/zavrazdeny-novinar-jan-kuciak-utoku-novinare-pribyva-ukladna-vrazda-vsak-extrem/#comment-23866',
        'http://www.chip.cz/novinky/tipy-triky/ulozeni-ausporadani-fotografii-jako-miniatur/',
        'http://www.chip.cz/novinky/tipy-triky/nastavte-automaticke-zalohovani-kontaktu-vaseho-smartphonu/',
        'http://www.chip.cz/novinky/tipy-triky/hibernace-amisto-na-disku/',
        'https://havlickobrodsky.denik.cz/z-regionu/o-dusi-je-dulezite-pecovat-rika-101-leta-pani-20180227.html',
        'http://www.chip.cz/novinky/hardware/sesta-generace-thinkpadu-x1-carbon/',
        'http://www.chip.cz/temata/o-cem-bude-letosni-konference-security-2018/',
        'https://homebydleni.cz/zahrada/realizace-zahrad/lepsi-mala-zahrada-ve-svahu-nez-zadna/#comment-13632',
        'https://havlickobrodsky.denik.cz/z-regionu/proverte-sve-znalosti-z-matematiky-v-dnesnim-testu-deniku-20180222.html',
        'http://hdmag.cz/clanek/hisense-chce-jeste-letos-uvest-oled-televizi',
        'https://havlickobrodsky.denik.cz/z-regionu/zesnula-jaroslava-dolezalova-ktera-za-valky-zachranila-malou-holcicku-20180221.html',
        'https://hlidacipes.org/protikorupcni-special-odpis-vlada-neplanuje-boj-nej-vzdali-i-sami-statni-zastupci/#comment-23870',
        'https://havlickobrodsky.denik.cz/z-regionu/uspesny-student-matej-sagl-z-kamenice-dostal-oceneni-20180226.html',
        'https://hlidacipes.org/protikorupcni-special-odpis-vlada-neplanuje-boj-nej-vzdali-i-sami-statni-zastupci/#comment-23872',
        'http://www.chip.cz/novinky/analogovym-domovnim-zvonkum-odzvonilo-nahrazuji-je-digitalni-ip-interkomy/',
        'http://hdmag.cz/clanek/aplikace-ve-smartphonech-smiruji-vase-divacke-navyky',
        'https://havlickobrodsky.denik.cz/z-regionu/naivni-zlodeji-aut-bruslarska-magistrala-a-promrzle-koule-videa-dne-20180226.html',
        'https://havlickobrodsky.denik.cz/z-regionu/prisne-strezenym-prostorem-dukovan-proslo-116-navstevniku-20180227.html',
        'http://www.chip.cz/novinky/tipy-triky/nahlaste-neuspesnou-transakci-aziskejte-zpet-penize/',
        'https://hlidacipes.org/obeti-ruske-agrese-donbasu-pribyva-valka-evrope-prestava-byt-media-sexy/#comment-23875',
        'https://havlickobrodsky.denik.cz/z-regionu/oprava-hradu-se-da-zvladnout-i-za-provozu-20180221.html',
        'http://www.chip.cz/novinky/bezpecnost/jiz-50-webove-komunikace-je-sifrovane/'
    }

    page_generator = Page_generator( urls, pause=5 )
    for page in page_generator:
        pass