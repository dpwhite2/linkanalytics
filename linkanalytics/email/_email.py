import re

from django.template import Template, Context

from linkanalytics.util.htmltotext import HTMLtoText
from linkanalytics.util.htmldocument import HtmlDocument

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
        assert imgtype in ('png','gif')
        imgfmt = '''<img src="{{% track 'pixel' '{0}' %}}" '''
        imgfmt += '''height="1" width="1"/>'''
        imgtag = imgfmt.format(imgtype)
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
        text = _html_to_text(HtmlDocument(html).assemble())
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
def email_instantiator(texttpl, htmltpl, urlbase):
    """Returns a function that can be used to instantiate individual emails.  
       The function will take one argument, the uuid.
    """
    ttext = Template('{% load tracked_links %}'+texttpl)
    thtml = Template('{% load tracked_links %}'+htmltpl)
    ctx = Context({'urlbase': urlbase})
    
    def _instantiate_email(uuid):
        ctx['linkid'] = uuid
        return (ttext.render(ctx),thtml.render(ctx))
        
    return _instantiate_email
    

