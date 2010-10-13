from HTMLParser import HTMLParser
import htmlentitydefs
import codecs
import functools

# Purpose: to convert an HTML document intended for email content into plain 
#          text.

class HTMLtoText(HTMLParser):
    def __init__(self, full_document=True):
        """If full_document is True, only text within the <body> element will 
           be output to plain text--all other text will be ignored.  If False, 
           all text will be output.
        """
        # Base class of HTMLParser.HTMLParser is an old-style class.  Cannot 
        # use 'super()' here.
        HTMLParser.__init__(self)
        self._init_handlers()
        self.width = 80
        self.buf = ''
        self.full_document = full_document
        self.inbody = False
        
    def __str__(self):
        return self.buf
    
    def _init_handlers(self):
        """Initializes dictionary of element-specific handler functions."""
        self.handlers = {
            'p': (self.p_start, self.p_end),
            'br': (self.br_tag, self._donothing_endtag),
            'body': (self.body_start, self.body_end),
            #'ul': (ul_start, ul_end),
            #'ol': (ol_start, ol_end),
            #'li': (li_start, li_end),
            'h1': (functools.partial(HTMLtoText.heading_start,self,level=1), 
                   functools.partial(HTMLtoText.heading_end,self,level=1)
                  ),
            }
            
    def _donothing_starttag(self, attrs):
        """Default element handler function that does nothing."""
        pass
    def _donothing_endtag(self):
        """Default element handler function that does nothing."""
        pass
        
    def br_tag(self, attrs):
        """Handle a <br/> tag."""
        self.buf += '\n'
        
    def p_start(self, attrs):
        """Handle an opening paragraph tag."""
        self.buf += '\n'
    def p_end(self):
        """Handle a closing paragraph tag."""
        self.buf += '\n'
        
    def heading_start(self, attrs, level):
        """Handle an opening heading tag."""
        self.buf += '\n'
    def heading_end(self, level):
        """Handle a closing heading tag."""
        self.buf += '\n'
        
    def body_start(self, attrs):
        """Handle an opening body tag."""
        self.inbody = True
    def body_end(self):
        """Handle a closing body tag."""
        self.inbody = False
    
    def handle_starttag(self, tag, attrs):
        """Handle a start tag by dispatching to the appropriate 
           element-specific function."""
        self.handlers.get(tag, (self._donothing_starttag,))[0](attrs)

    def handle_endtag(self, tag):
        """Handle a end tag by dispatching to the appropriate 
           element-specific function."""
        self.handlers.get(tag, (None, self._donothing_endtag))[1]()
        
    def handle_entityref(self, name):
        cp = htmlentitydefs.name2codepoint[name]
        u = unichr(cp)
        self.buf += codecs.iterencode(u, 'utf-8')
        
    def handle_charref(self, name):
        if name.startswith('x') or name.startswith('X'):
            cp = int(name[1:], 16)
        else:
            cp = int(name)
        u = unichr(cp)
        self.buf += codecs.iterencode(u, 'utf-8')
        
    def handle_data(self, data):
        if (not self.full_document) or self.inbody:
            self.buf += data






