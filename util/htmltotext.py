from HTMLParser import HTMLParser
#from cStringIO import StringIO
import htmlentitydefs
import codecs

# Purpose: to convert an HTML document intended for email content into plain text.

class HTMLtoText(HTMLParser):
    def __init__(self):
        # Base class of HTMLParser.HTMLParser is an old-style class.  Cannot 
        # use 'super()' here.
        HTMLParser.__init__(self)
        self._init_handlers()
        self.width = 80
        self.buf = ''
        
    def __str__(self):
        return self.buf
    
    def _init_handlers(self):
        self.handlers = {
            'p': (self.p_start, self.p_end),
            'br': (self.br_tag, self._donothing_endtag),
            #'ul': (ul_start, ul_end),
            #'ol': (ol_start, ol_end),
            #'li': (li_start, li_end),
            #'h1': (h1_start, h1_end),
            }
            
    def _donothing_starttag(self, attrs):
        pass
    def _donothing_endtag(self):
        pass
        
    def br_tag(self, attrs):
        self.buf += '\n'
        
    def p_start(self, attrs):
        self.buf += '\n'
    def p_end(self):
        self.buf += '\n'
    
    def handle_starttag(self, tag, attrs):
        self.handlers.get(tag, (self._donothing_starttag,))[0](attrs)

    def handle_endtag(self, tag):
        self.handlers.get(tag, (None,self._donothing_endtag))[1]()
        
    def handle_entityref(self, name):
        cp = htmlentitydefs.name2codepoint[name]
        u = unichr(cp)
        self.buf += codecs.iterencode(u,'utf-8')
        
    def handle_charref(self, name):
        if name.startswith('x') or name.startswith('X'):
            cp = int(name[1:],16)
        else:
            cp = int(name)
        u = unichr(cp)
        self.buf += codecs.iterencode(u,'utf-8')
        
    def handle_data(self, data):
        self.buf += data






