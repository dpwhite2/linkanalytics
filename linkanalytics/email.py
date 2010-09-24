import re

from django.template import Template, Context

from linkanalytics.util.htmltotext import HTMLtoText

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
_HTMLDOC = r'(?P<prefix>.*)<[Hh][Tt][Mm][Ll]>\s*'+_HEADELEM+r'\s*'+_BODYELEM+r'\s*</[Hh][Tt][Mm][Ll]>'
_re_htmldoc = re.compile(_HTMLDOC, re.VERBOSE)
        
class HtmlDocument(object):
    def __init__(self, data):
        m = _re_htmldoc.match(data)
        if not m:
            raise BadHtmlDocument('Cannot read html document.  Does it have <html>, <head>, and <body> tags?')
        self.prefix = m.group('prefix')
        self.head = m.group('headcontent')
        self.body = m.group('bodycontent')
    def assemble(self):
        return '{0}<html>\n<head>{1}</head>\n<body>{2}</body>\n</html>\n'.format(self.prefix, self.head, self.body)


#==============================================================================#
class EmailContent(object):
    def compile(self):
        raise NotImplementedError()
    def process_template(self, data):
        data = '{% load tracked_links %}' + data
        t = Template(data)
        c = Context({})
        return t.render(c)
        
class HtmlEmailContent(EmailContent):
    def __init__(self, data):
        self.html = HtmlDocument(data)
    def compile(self):
        r = self.process_template(self.docify())
        return r
    def add_header(self, header):
        self.html.body = header + self.html.body
    def add_footer(self, footer):
        self.html.body = self.html.body + footer
    def add_pixel_image(self, imgtype='png'):
        """Adds a img tag referring to a 1x1 pixel image to the email.  It 
           assumes adding the tag to the beginning of the body element content 
           is safe.
           
           imgtype must be 'png' or 'gif'.
        """
        imgtag = '''<img src="{{% track 'pixel' '{0}' %}}" height="1" width="1"/>'''.format(imgtype)
        self.html.body = imgtag + self.html.body
    def add_headcontent(self, content):
        self.html.head += content
    def docify(self):
        return self.html.assemble()
    
class TextEmailContent(EmailContent):
    def __init__(self, text):
        self.text = text
    def compile(self):
        r = self.process_template(self.text)
        return r
    def add_header(self, header):
        self.text = header + self.text
    def add_footer(self, footer):
        self.text = self.text + footer


#==============================================================================#
def _html_to_text(html, full_document=True):
    htt = HTMLtoText(full_document)
    htt.feed(html)
    return str(htt)

def compile_email(content, **kwargs):
    """Default content_type is html."""
    content_type = kwargs.get('content_type','html').lower()
    html_header = kwargs.get('html_header','')
    html_footer = kwargs.get('html_footer','')
    text_header = kwargs.get('text_header',None)
    text_footer = kwargs.get('text_footer',None)
    pixelimage_type = kwargs.get('pixelimage_type',None)
    
    if text_header is None:
        text_header = _html_to_text(html_header, full_document=False)
    if text_footer is None:
        text_footer = _html_to_text(html_footer, full_document=False)
    
    if content_type=='html':
        html = content
        text = _html_to_text(html)
    elif content_type=='txt' or content_type=='text':
        raise RuntimeError('Compiling email from text is not yet implemented.')
    html = compile_html_email(html, html_header, html_footer, pixelimage_type)
    text = compile_text_email(text, text_header, text_footer)
    return (text,html)
    
def compile_html_email(content, header='', footer='', pixelimage_type=None):
    html = HtmlEmailContent(content)
    html.add_header(header)
    html.add_footer(footer)
    if pixelimage_type is not None:
        html.add_pixel_image(pixelimage_type)
    return html.compile()
    
def compile_text_email(content, header='', footer=''):
    text = TextEmailContent(content)
    text.add_header(header)
    text.add_footer(footer)
    return text.compile()


#==============================================================================#
def instantiate_emails(text, html, urlbase, uuid_iter):
    """An iterator that returns pairs of instanted email contents.  The return 
       value is a tuple: (text,html).
    """
    # TODO: in progress....
    # TODO: make urlbase a settings variable
    ttext = Template('{% load tracked_links %}'+text)
    thtml = Template('{% load tracked_links %}'+html)
    
    for uuid in uuid_iter:
        c = Context({'linkid': uuid, 'urlbase': urlbase})
        yield (ttext.render(c),thtml.render(c))
    


