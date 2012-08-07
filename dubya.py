import os
import re
import sys
import time
import optparse
import textwrap
from hashlib import md5
from ConfigParser import SafeConfigParser

def generate_quote_image(quote, imagefile, text_col, bg_col, font):
    quote = '\n'.join(textwrap.wrap(quote, 25))
    quote = re.sub('"', '\\"', quote)

    # Create "smart quote" images in a larger font size
    helpers = {'/tmp/q1.png': u'\\u201c', '/tmp/q2.png': u'\\u201d'}
    for f, c in helpers.items():
        if not os.path.exists(f):
            # Hack to get around inability to pass unicode to shell
            # http://www.imagemagick.org/Usage/text/#unicode
            cmd = 'env LC_CTYPE=en_AU.utf8 printf "%s" | convert -background %s -fill %s -font %s -density 90 -pointsize %d label:@- %s' % (c, bg_col, text_col, font, 70, f)
            os.system(cmd)

    cmd = 'convert -background %s -fill %s -border 10x10 -bordercolor %s -font %s -density 90 -pointsize %d label:"%s" %s' % (bg_col, text_col, bg_col, font, 40, quote, imagefile)
    os.system(cmd)
    cmd = u'convert -background %s /tmp/q1.png %s +append /tmp/dubyatmp.png' % (bg_col, imagefile)
    os.system(cmd)
    cmd = u'convert -background %s -bordercolor %s /tmp/dubyatmp.png -border 0x20 -gravity south /tmp/q2.png +append -border 20x0 %s' % (bg_col, bg_col, imagefile)
    os.system(cmd)

def build_image_cache(quotes, conf):
    """Take a list of quotes and return a list of image files
    corresponding to those quotes"""

    cache_dir = conf['Dubya']['cache_dir']
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    # TODO preset / check this
    text_col = conf['Dubya']['text_colour']
    bg_col = conf['Dubya']['bg_colour']
    font = conf['Dubya']['font']

    quote_images = []

    for quote in quotes:
        h = md5('%s-%s-%s' % (text_col, bg_col, quote))
        imagefile = '%s/dubya-%s.png' % (cache_dir, h.hexdigest()[:8])
        generate_quote_image(quote, imagefile, text_col, bg_col, font)
        quote_images.append(imagefile)

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
    c.set("Dubya", "quotes_file", "quotes.txt")
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

def process_config(filename):
    p = SafeConfigParser()
    conf = {}
    try:
        p.read(filename)
    except:
        print "Could not read file %s" % filename

    conf['Dubya'] = {}
    conf['Dubya']['cache_dir'] = "/tmp/dubya_cache"
    conf['Dubya']['quotes_file'] = "quotes.txt"

    for section in p.sections():
        for (name, value) in p.items(section):
            if not conf.has_key(section):
                conf[section] = {}
            conf[section][name] = value
    return conf

def main():
    options = parse_options()

    if options.gen_config:
        gen_config()
        return 0

    # Read from the configuration file
    config_file = "dubya.cfg"
    if options.config_file:
        config_file = options.config_file
    if not os.path.exists(config_file):
        print 'No such config file "%s"' % config_file
        print 'Run "%s -g" to output a sample configuration.' % sys.argv[0]
        return 1
    conf = process_config(config_file)

    cache_dir = conf['Dubya']['cache_dir']
    quotes_file = conf['Dubya']['quotes_file']
    if not os.path.exists(quotes_file):
        print 'No such quotes file "%s"' % config_file
        print 'Create it with one quote per line.'
        return 1
    f = open(quotes_file, "r")
    quotes = f.readlines()
    f.close()

    build_image_cache(quotes, conf)

    return 0

if __name__ == '__main__':
    sys.exit(main())
