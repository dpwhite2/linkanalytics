
#from linkanalytics.tests import LinkAnalytics_TestCaseBase
#from linkanalytics.tests import urlreverse_redirect_http
#from linkanalytics.tests import urlreverse_redirect_local

from linkanalytics import email as LAemail
from linkanalytics.util import htmltotext

import helpers
import base

#==============================================================================#
class HtmlDocument_TestCase(base.LinkAnalytics_TestCaseBase):
    def test_basic(self):
        html = "<html><head></head><body></body></html>"
        doc = LAemail.HtmlDocument(html)
        
        self.assertEquals(doc.prefix, '')
        self.assertEquals(doc.head, '')
        self.assertEquals(doc.body, '')
        self.assertEqualsHtml(doc.assemble(), html)
        
    def test_with_title(self):
        html = "<html><head><title>A Title</title></head><body></body></html>"
        doc = LAemail.HtmlDocument(html)
        
        self.assertEquals(doc.prefix, '')
        self.assertEquals(doc.head, '<title>A Title</title>')
        self.assertEquals(doc.body, '')
        self.assertEqualsHtml(doc.assemble(), html)
        
    def test_with_bodycontent(self):
        html = "<html><head></head><body><h1>A heading.</h1>"
        html += "<p>A paragraph.</p></body></html>"
        #nlhtml = _put_htmldoc_newlines(html)
        doc = LAemail.HtmlDocument(html)
        
        self.assertEquals(doc.prefix, '')
        self.assertEquals(doc.head, '')
        self.assertEquals(doc.body, '<h1>A heading.</h1><p>A paragraph.</p>')
        self.assertEqualsHtml(doc.assemble(), html)
        
    def test_with_pi(self):
        html = "<?xml version='1.0'?><html><head></head><body></body></html>"
        #nlhtml = _put_htmldoc_newlines(html)
        doc = LAemail.HtmlDocument(html)
        
        self.assertEquals(doc.prefix, "<?xml version='1.0'?>")
        self.assertEquals(doc.head, '')
        self.assertEquals(doc.body, '')
        self.assertEqualsHtml(doc.assemble(), html)
        
    def test_blank_document(self):
        html = ""
        doc = LAemail.HtmlDocument(html)
        
        self.assertEquals(doc.prefix, '')
        self.assertEquals(doc.head, '')
        self.assertEquals(doc.body, '')
        self.assertEqualsHtml(doc.assemble(), 
                              "<html><head></head><body></body></html>")
        
    def test_tagless(self):
        html = "Some content."
        doc = LAemail.HtmlDocument(html)
        
        self.assertEquals(doc.prefix, '')
        self.assertEquals(doc.head, '')
        self.assertEquals(doc.body, 'Some content.')
        self.assertEqualsHtml(
                doc.assemble(), 
                "<html><head></head><body>Some content.</body></html>")
        
    def test_bodyonly(self):
        html = "<body>The body.</body>"
        doc = LAemail.HtmlDocument(html)
        
        self.assertEquals(doc.prefix, '')
        self.assertEquals(doc.head, '')
        self.assertEquals(doc.body, 'The body.')
        self.assertEqualsHtml(
                doc.assemble(), 
                "<html><head></head><body>The body.</body></html>")
        
    def test_nohtmlelem(self):
        html = "<head>The head.</head><body>The body.</body>"
        doc = LAemail.HtmlDocument(html)
        
        self.assertEquals(doc.prefix, '')
        self.assertEquals(doc.head, 'The head.')
        self.assertEquals(doc.body, 'The body.')
        self.assertEqualsHtml(
                doc.assemble(), 
                "<html><head>The head.</head><body>The body.</body></html>")
        

#==============================================================================#

class CompileEmail_TestCase(base.LinkAnalytics_TestCaseBase):
    def test_basic(self):
        htmlsrc = "<html><head></head><body></body></html>"
        text,html = LAemail.compile_email(htmlsrc)
        self.assertEquals(text, '')
        self.assertEqualsHtml(html, htmlsrc)
        
    def test_headcontent(self):
        htmlsrc = "<html><head><title>A Title</title></head>"
        htmlsrc += "<body></body></html>"
        text,html = LAemail.compile_email(htmlsrc)
        self.assertEquals(text, '')
        self.assertEqualsHtml(html, htmlsrc)
        
    def test_bodycontent(self):
        htmlsrc = "<html><head></head><body><p>A paragraph.</p></body></html>"
        text,html = LAemail.compile_email(htmlsrc)
        self.assertEquals(text, '\nA paragraph.\n')
        self.assertEqualsHtml(html, htmlsrc)
        
    def test_trackTrail(self):
        htmlsrc = "<html><head></head>"
        htmlsrc += "<body>{% track 'trail' 'path/file.ext' %}</body></html>"
        tag = '{% trackedurl linkid "path/file.ext" %}'
        htmlres = """<html><head></head><body>{0}</body></html>""".format(tag)
        text,html = LAemail.compile_email(htmlsrc)
        self.assertEquals(text, tag)
        self.assertEqualsHtml(html, htmlres)
        
    def test_header_footer(self):
        htmlsrc = "<html><head></head><body><p>A paragraph.</p></body></html>"
        header = '<h1>A Header</h1>'
        footer = '<div>A footer.</div>'
        body = "<body>{0}<p>A paragraph.</p>{1}</body>".format(header,footer)
        htmlres = "<html><head></head>{0}</html>".format(body)
        textres = "\n{0}\n\nA paragraph.\n{1}".format("A Header","A footer.")
        text,html = LAemail.compile_email(htmlsrc, 
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
        inst = LAemail.email_instantiator(textsrc,htmlsrc,urlbase)
        text,html = inst(uuid)
        self.assertEquals(text, textsrc)
        self.assertEquals(html, htmlsrc)
        
    def test_trail(self):
        htmlsrc = "<html><head></head><body>"
        htmlsrc += "{% trackedurl linkid 'r/path/to/file.ext' %}"
        htmlsrc += "</body></html>"
        textsrc = "{% trackedurl linkid 'r/path/to/file.ext' %}"
        urlbase = 'http://example.com'
        uuid = '0'*32
        inst = LAemail.email_instantiator(textsrc,htmlsrc,urlbase)
        text,html = inst(uuid)
        url = helpers.urlreverse_redirect_local(uuid=uuid, 
                                                filepath='path/to/file.ext')
        self.assertEquals(text, '{0}{1}'.format(urlbase,url))
        expecthtml = "<html><head></head><body>{0}{1}</body></html>"
        expecthtml = expecthtml.format(urlbase,url)
        self.assertEquals(html, expecthtml)

        
#==============================================================================#

class HTMLtoText_TestCase(base.LinkAnalytics_TestCaseBase):
    htmloutline = "<html><head></head><body>{0}</body></html>"
    
    def test_basic(self):
        html = self.htmloutline.format("This is some text.")
        htt = htmltotext.HTMLtoText()
        htt.feed(html)
        text = str(htt)
        self.assertEquals(text, "This is some text.")
        
    def test_simple_paragraph(self):
        html = self.htmloutline.format("<p>A paragraph.</p>")
        htt = htmltotext.HTMLtoText()
        htt.feed(html)
        text = str(htt)
        self.assertEquals(text, "\nA paragraph.\n")
        
    def test_two_paragraphs(self):
        body = "<p>A paragraph.</p><p>Another paragraph.</p>"
        html = self.htmloutline.format(body)
        htt = htmltotext.HTMLtoText()
        htt.feed(html)
        text = str(htt)
        self.assertEquals(text, "\nA paragraph.\n\nAnother paragraph.\n")
        
    def test_linebreak(self):
        html = self.htmloutline.format("One line.<br/>Two lines.")
        htt = htmltotext.HTMLtoText()
        htt.feed(html)
        text = str(htt)
        self.assertEquals(text, "One line.\nTwo lines.")

    
#==============================================================================#
