import os
import re
import sys
import time
import random
import optparse
import textwrap
from hashlib import md5
from ConfigParser import SafeConfigParser
from pinder import Campfire

# Track position in quote list
quote_image_list = []
quote_position = 0
catch_phrase = ''
match_phrase = ''
cf = None
room = None

def generate_quote_image(quote, imagefile, text_col, bg_col, font):
    quote = '\n'.join(textwrap.wrap(quote, 25))
    quote = re.sub('!', '\\!', quote)
    quote = re.sub('"', '\\"', quote)
    #quote = re.escape(quote)

    cmd = 'convert -background "%s" -fill "%s" -border 10x10 -bordercolor "%s" -font "%s" -density 90 -pointsize "%d" label:"%s" %s' % (bg_col, text_col, bg_col, font, 40, quote, imagefile)
    os.system(cmd)
    cmd = u'convert -background "%s" /tmp/q1.png "%s" +append /tmp/dubyatmp.png' % (bg_col, imagefile)
    os.system(cmd)
    cmd = u'convert -background "%s" -bordercolor "%s" /tmp/dubyatmp.png -border 0x20 -gravity south /tmp/q2.png +append -border 20x0 %s' % (bg_col, bg_col, imagefile)
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

    # Create "smart quote" images in a larger font size
    helpers = {'/tmp/q1.png': u'\\u201c', '/tmp/q2.png': u'\\u201d'}
    for f, c in helpers.items():
        # Hack to get around inability to pass unicode to shell
        # http://www.imagemagick.org/Usage/text/#unicode
        cmd = 'env LC_CTYPE=en_AU.utf8 printf "%s" | convert -background "%s" -fill "%s" -font "%s" -density 90 -pointsize "%d" label:@- %s' % (c, bg_col, text_col, font, 70, f)
        os.system(cmd)

    quote_images = []

    for quote in quotes:
        h = md5('%s-%s-%s' % (text_col, bg_col, quote))
        imagefile = '%s/dubya-%s.png' % (cache_dir, h.hexdigest()[:8])
        generate_quote_image(quote, imagefile, text_col, bg_col, font)
        quote_images.append(imagefile)

    return quote_images

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
    c.set("Dubya", "catch_phrase", "Did someone say WMD? Yeehaw!")
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
    """Reads a configuration file and returns configration options
    """

    p = SafeConfigParser()
    conf = {}
    try:
        p.read(filename)
    except:
        print "Could not read file %s" % filename

    # Set defaults for some options
    conf['Dubya'] = {}
    conf['Dubya']['quotes_file'] = "quotes.txt"
    conf['Dubya']['match_phrase'] = "WMD"
    conf['Dubya']['font'] = "Helvetica"
    conf['Dubya']['text_colour'] = "white"
    conf['Dubya']['bg_colour'] = "black"
    conf['Dubya']['cache_dir'] = "/tmp/dubya_cache"

    for section in p.sections():
        for (name, value) in p.items(section):
            if not conf.has_key(section):
                conf[section] = {}
            conf[section][name] = value
    return conf

def validate_config(conf):
    errors = []

    for key in ['text_colour', 'bg_colour', 'font']:
        if not conf['Dubya'].has_key(key):
            errors.append('Missing key %s in Dubya section' % key)
        elif not len(conf['Dubya'][key]):
            errors.append('No value for %s in Dubya section' % key)

    for key in ['auth_token', 'domain_prefix', 'room']:
        if not conf['Campfire'].has_key(key):
            errors.append('Missing key %s in Campfire section' % key)
        elif not len(conf['Campfire'][key]):
            errors.append('No value for %s in Campfire section' % key)

    if not len(errors):
        return None
    return errors

def handle_message(message):
    if message[u'type'] != u'TextMessage':
        return

    global quote_position, quote_image_list
    if re.search(match_phrase, message[u'body'], re.IGNORECASE):
        if quote_position < 0:
            quote_position = len(quote_image_list) - 1
        try:
            img = open(quote_image_list[quote_position], "r")
            room.speak(catch_phrase)
            room.upload(img)
            img.close()
        except:
            print 'Unable to upload'
        quote_position -= 1

def handle_exception(ex):
    print 'Received exception %s' % ex
    sys.exit(1)

def manage_campfire(images, conf):
    global quote_image_list
    random.shuffle(images)
    quote_image_list = images

    global catch_phrase
    catch_phrase = conf['Dubya']['catch_phrase']

    global match_phrase
    match_phrase = conf['Dubya']['match_phrase']

    subdomain  = conf['Campfire']['domain_prefix']
    room_name  = conf['Campfire']['room']
    auth_token = conf['Campfire']['auth_token']

    global cf, room
    cf = Campfire(subdomain, auth_token)
    room = cf.find_room_by_name(room_name)
    room.join()
    print 'ready'

    # Block forever
    room.listen(handle_message, handle_exception)


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

    errors = validate_config(conf)
    if errors:
        print 'There were errors in the configuration'
        for error in errors:
            print error
        return 1

    cache_dir = conf['Dubya']['cache_dir']
    quotes_file = conf['Dubya']['quotes_file']
    if not os.path.exists(quotes_file):
        print 'No such quotes file "%s"' % config_file
        print 'Create it with one quote per line.'
        return 1
    f = open(quotes_file, "r")
    quotes = f.readlines()
    f.close()

    images = build_image_cache(quotes, conf)

    manage_campfire(images, conf)

    return 0

if __name__ == '__main__':
    sys.exit(main())
