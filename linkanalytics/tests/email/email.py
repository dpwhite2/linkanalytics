from linkanalytics.email import _email

from .. import helpers, base
#from linkanalytics.tests import helpers, base

#==============================================================================#

class CompileEmail_TestCase(base.LinkAnalytics_TestCaseBase):
    def test_basic(self):
        htmlsrc = "<html><head></head><body></body></html>"
        text, html = _email.compile_email(htmlsrc)
        self.assertEquals(text, '')
        self.assertEqualsHtml(html, htmlsrc)
        
    def test_headcontent(self):
        htmlsrc = "<html><head><title>A Title</title></head>"
        htmlsrc += "<body></body></html>"
        text, html = _email.compile_email(htmlsrc)
        self.assertEquals(text, '')
        self.assertEqualsHtml(html, htmlsrc)
        
    def test_bodycontent(self):
        htmlsrc = "<html><head></head><body><p>A paragraph.</p></body></html>"
        text, html = _email.compile_email(htmlsrc)
        self.assertEquals(text, '\nA paragraph.\n')
        self.assertEqualsHtml(html, htmlsrc)
        
    def test_trackTrail(self):
        htmlsrc = "<html><head></head>"
        htmlsrc += "<body>{% track 'trail' 'path/file.ext' %}</body></html>"
        tag = '{% trackedurl linkid "path/file.ext" %}'
        htmlres = """<html><head></head><body>{0}</body></html>""".format(tag)
        text, html = _email.compile_email(htmlsrc)
        self.assertEquals(text, tag)
        self.assertEqualsHtml(html, htmlres)
        
    def test_header_footer(self):
        htmlsrc = "<html><head></head><body><p>A paragraph.</p></body></html>"
        header = '<h1>A Header</h1>'
        footer = '<div>A footer.</div>'
        body = "<body>{0}<p>A paragraph.</p>{1}</body>".format(header, footer)
        htmlres = "<html><head></head>{0}</html>".format(body)
        textres = "\n{0}\n\nA paragraph.\n{1}".format("A Header", "A footer.")
        text, html = _email.compile_email(htmlsrc, 
                                          html_header=header, 
                                          html_footer=footer)
        self.assertEquals(text, textres)
        self.assertEqualsHtml(html, htmlres)
        
        
#==============================================================================#
        
class InstantiateEmails_TestCase(base.LinkAnalytics_TestCaseBase):
    def test_basic(self):
        htmlsrc = "<html><head></head><body></body></html>"
        textsrc = ""
        urlbase = 'http://example.com'
        uuid = '0'*32
        inst = _email.email_instantiator(textsrc, htmlsrc, urlbase)
        text, html = inst(uuid)
        self.assertEquals(text, textsrc)
        self.assertEquals(html, htmlsrc)
        
    def test_trail(self):
        htmlsrc = "<html><head></head><body>"
        htmlsrc += "{% trackedurl linkid 'r/path/to/file.ext' %}"
        htmlsrc += "</body></html>"
        textsrc = "{% trackedurl linkid 'r/path/to/file.ext' %}"
        urlbase = 'http://example.com'
        uuid = '0'*32
        inst = _email.email_instantiator(textsrc, htmlsrc, urlbase)
        text, html = inst(uuid)
        url = helpers.urlreverse_redirect_local(uuid=uuid, 
                                                filepath='path/to/file.ext')
        self.assertEquals(text, '{0}{1}'.format(urlbase, url))
        expecthtml = "<html><head></head><body>{0}{1}</body></html>"
        expecthtml = expecthtml.format(urlbase, url)
        self.assertEquals(html, expecthtml)

        
#==============================================================================#