import sys
import time
import optparse
from ConfigParser import SafeConfigParser

def gen_dubya_images():
    cmd = 'convert -background black -fill white -font code/personal/eplfl/site_python/fonts/Helvetica.ttf -density 90 -pointsize 40 label:"%s"'
    dubya_quotes = []
    for quote in dubya_quotes:
        pass

def parse_options():
    p = optparse.OptionParser()
    p.add_option("-c", "--config", dest="config_file", metavar="FILE",
        default="dubya.cfg", help="configuration file")
    p.add_option("-g", "--gen-config", dest="gen_config", default=False,
        action="store_true", help="generate configuration file to stdout")
    (options, args) = p.parse_args()
    return options

def gen_config():
    """Generate a sample configuration
    """
    c = SafeConfigParser()
    c.add_section('Dubya')
    c.set("Dubya", "quotes", "quotes.txt")
    c.set("Dubya", "match_phrase", "WMD")
    c.set("Dubya", "font", "Helvetica")
    c.set("Dubya", "text_colour", "white")
    c.set("Dubya", "bg_colour", "black")
    c.set("Dubya", "cache_dir", "/tmp/dubya_cache")
    c.add_section("Campfire")
    c.set("Campfire", "auth_token", "YOUR TOKEN HERE")
    c.set("Campfire", "domain_prefix", "dubya (if you use dubya.campfirenow.com)")
    c.set("Campfire", "room", "Yeehaw Texas")
    c.write(sys.stdout)


def main():
    options = parse_options()

    if options.gen_config:
        gen_config()
        return 0

    print 'first arg %s' % argv[1]
    return 0

if __name__ == '__main__':
    sys.exit(main())
