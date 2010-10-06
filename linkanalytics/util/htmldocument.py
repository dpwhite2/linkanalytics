import re

#==============================================================================#
class BadHtmlDocument(Exception):
    pass

_HEAD = '[Hh][Ee][Aa][Dd]'
_HEADELEM = r'<'+_HEAD+r'''>
    (?P<headcontent>(?:
          [^<]
        | <[^/]
        | </[^Hh]
        | </[Hh][^Ee]
        | </[Hh][Ee][^Aa] 
        | </[Hh][Ee][Aa][^Dd]
        | </[Hh][Ee][Aa][Dd][^>]
    )*)
    </'''+_HEAD+r'>'
_BODY = '[Bb][Oo][Dd][Yy]'
_BODYELEM = r'<'+_BODY+r'''>
    (?P<bodycontent>(?:
          [^<]
        | <[^/]
        | </[^Bb]
        | </[Bb][^Oo]
        | </[Bb][Oo][^Dd] 
        | </[Bb][Oo][Dd][^Yy]
        | </[Bb][Oo][Dd][Yy][^>]
    )*)
    </'''+_BODY+r'>'
_PREFIX = r'''
    (?P<prefix>(?:
          [^<]
        | <[^HhBb]
        | <[Hh][^TtEe]
        | <[Hh][Tt][^Mm] 
        | <[Hh][Tt][Mm][^Ll]
        | <[Hh][Tt][Mm][Ll][^>]
        | <[Hh][Ee][^Aa] 
        | <[Hh][Ee][Aa][^Dd]
        | <[Hh][Ee][Aa][Dd][^>]
        | <[Bb][^Oo]
        | <[Bb][Oo][^Dd]
        | <[Bb][Oo][Dd][^Yy]
        | <[Bb][Oo][Dd][Yy][^>]
    )*)
    '''
_HTMLDOC = ( _PREFIX
             +r'(?:<[Hh][Tt][Mm][Ll]>)?\s*(?:'
             +_HEADELEM+r')?\s*(?:'+_BODYELEM
             +r')?\s*(?:</[Hh][Tt][Mm][Ll]>)?'
             )
_re_htmldoc = re.compile(_HTMLDOC, re.VERBOSE)
        
class HtmlDocument(object):
    def __init__(self, data):
        m = _re_htmldoc.match(data)
        if not m:
            msg = 'Cannot read html document.  '
            msg += 'Does it have <html>, <head>, and <body> tags?'
            raise BadHtmlDocument(msg)
        self.prefix = ''
        self.head = m.group('headcontent')  if m.group('headcontent') else  ''
        self.body = m.group('bodycontent')  if m.group('bodycontent') else  ''
        if m.group('prefix') is not None:
            # If no <head> or <body> tags are found, then use the entire 
            # content as the body.  In such a case, the content shows up in 
            # 'prefix'.
            if (m.group('headcontent') is None 
               and m.group('bodycontent') is None):
                self.body = m.group('prefix')
            else:
                self.prefix = m.group('prefix')
        
    def assemble(self):
        fmt = '{0}<html>\n<head>{1}</head>\n<body>{2}</body>\n</html>\n'
        return fmt.format(self.prefix, self.head, self.body)


#==============================================================================#

