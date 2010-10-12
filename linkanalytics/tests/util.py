
from linkanalytics.email import _email
from linkanalytics.util.htmltotext import HTMLtoText
from linkanalytics.util.htmldocument import  HtmlDocument

import base

#==============================================================================#
class HtmlDocument_TestCase(base.LinkAnalytics_TestCaseBase):
    def test_basic(self):
        html = "<html><head></head><body></body></html>"
        doc = HtmlDocument(html)
        
        self.assertEquals(doc.prefix, '')
        self.assertEquals(doc.head, '')
        self.assertEquals(doc.body, '')
        self.assertEqualsHtml(doc.assemble(), html)
        
    def test_with_title(self):
        html = "<html><head><title>A Title</title></head><body></body></html>"
        doc = HtmlDocument(html)
        
        self.assertEquals(doc.prefix, '')
        self.assertEquals(doc.head, '<title>A Title</title>')
        self.assertEquals(doc.body, '')
        self.assertEqualsHtml(doc.assemble(), html)
        
    def test_with_bodycontent(self):
        html = "<html><head></head><body><h1>A heading.</h1>"
        html += "<p>A paragraph.</p></body></html>"
        #nlhtml = _put_htmldoc_newlines(html)
        doc = HtmlDocument(html)
        
        self.assertEquals(doc.prefix, '')
        self.assertEquals(doc.head, '')
        self.assertEquals(doc.body, '<h1>A heading.</h1><p>A paragraph.</p>')
        self.assertEqualsHtml(doc.assemble(), html)
        
    def test_with_pi(self):
        html = "<?xml version='1.0'?><html><head></head><body></body></html>"
        #nlhtml = _put_htmldoc_newlines(html)
        doc = HtmlDocument(html)
        
        self.assertEquals(doc.prefix, "<?xml version='1.0'?>")
        self.assertEquals(doc.head, '')
        self.assertEquals(doc.body, '')
        self.assertEqualsHtml(doc.assemble(), html)
        
    def test_blank_document(self):
        html = ""
        doc = HtmlDocument(html)
        
        self.assertEquals(doc.prefix, '')
        self.assertEquals(doc.head, '')
        self.assertEquals(doc.body, '')
        self.assertEqualsHtml(doc.assemble(), 
                              "<html><head></head><body></body></html>")
        
    def test_tagless(self):
        html = "Some content."
        doc = HtmlDocument(html)
        
        self.assertEquals(doc.prefix, '')
        self.assertEquals(doc.head, '')
        self.assertEquals(doc.body, 'Some content.')
        self.assertEqualsHtml(
                doc.assemble(), 
                "<html><head></head><body>Some content.</body></html>")
        
    def test_bodyonly(self):
        html = "<body>The body.</body>"
        doc = HtmlDocument(html)
        
        self.assertEquals(doc.prefix, '')
        self.assertEquals(doc.head, '')
        self.assertEquals(doc.body, 'The body.')
        self.assertEqualsHtml(
                doc.assemble(), 
                "<html><head></head><body>The body.</body></html>")
        
    def test_nohtmlelem(self):
        html = "<head>The head.</head><body>The body.</body>"
        doc = HtmlDocument(html)
        
        self.assertEquals(doc.prefix, '')
        self.assertEquals(doc.head, 'The head.')
        self.assertEquals(doc.body, 'The body.')
        self.assertEqualsHtml(
                doc.assemble(), 
                "<html><head>The head.</head><body>The body.</body></html>")
        
#==============================================================================#

class HTMLtoText_TestCase(base.LinkAnalytics_TestCaseBase):
    htmloutline = "<html><head></head><body>{0}</body></html>"
    
    def test_basic(self):
        html = self.htmloutline.format("This is some text.")
        htt = HTMLtoText()
        htt.feed(html)
        text = str(htt)
        self.assertEquals(text, "This is some text.")
        
    def test_simple_paragraph(self):
        html = self.htmloutline.format("<p>A paragraph.</p>")
        htt = HTMLtoText()
        htt.feed(html)
        text = str(htt)
        self.assertEquals(text, "\nA paragraph.\n")
        
    def test_two_paragraphs(self):
        body = "<p>A paragraph.</p><p>Another paragraph.</p>"
        html = self.htmloutline.format(body)
        htt = HTMLtoText()
        htt.feed(html)
        text = str(htt)
        self.assertEquals(text, "\nA paragraph.\n\nAnother paragraph.\n")
        
    def test_linebreak(self):
        html = self.htmloutline.format("One line.<br/>Two lines.")
        htt = HTMLtoText()
        htt.feed(html)
        text = str(htt)
        self.assertEquals(text, "One line.\nTwo lines.")

    
#==============================================================================#
