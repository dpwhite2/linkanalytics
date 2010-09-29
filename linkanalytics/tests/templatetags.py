"""
    Tests on custom template tags and filters.
"""
import textwrap

from django.template import Template, Context

import helpers
import base

#==============================================================================#
class Track_TemplateTag_TestCase(base.LinkAnalytics_TestCaseBase):
    def test_trail(self):
        templtxt = """\
            {% load tracked_links %}
            {% track 'trail' 'path/to/file.ext' %}
            """
        templtxt = textwrap.dedent(templtxt)
        t = Template(templtxt)
        c = Context({})
        s = t.render(c)
        self.assertEquals(s, '\n{% trackedurl linkid "path/to/file.ext" %}\n')
        
    def test_url(self):
        templtxt = """\
            {% load tracked_links %}
            {% track 'url' 'http://www.domain.org/path/to/file.html' %}
            """
        templtxt = textwrap.dedent(templtxt)
        t = Template(templtxt)
        c = Context({})
        s = t.render(c)
        self.assertEquals(s, '\n{% trackedurl linkid "http/www.domain.org/path/to/file.html" %}\n')
        
    def test_pixel(self):
        templtxt = """\
            {% load tracked_links %}
            {% track 'pixel' 'gif' %}
            {% track 'pixel' 'png' %}
            """
        templtxt = textwrap.dedent(templtxt)
        t = Template(templtxt)
        c = Context({})
        s = t.render(c)
        a = '{% if not ignore_pixelimages %}'
        b = '{% endif %}'
        gpx = '{% trackedurl linkid "gpx" %}'
        ppx = '{% trackedurl linkid "ppx" %}'
        self.assertEquals(s, '\n{a}{gpx}{b}\n{a}{ppx}{b}\n'.format(a=a,b=b,gpx=gpx,ppx=ppx))
        

class TrackedUrl_TemplateTag_TestCase(base.LinkAnalytics_TestCaseBase):
    def test_basic(self):
        templtxt = """\
            {% load tracked_links %}
            {% trackedurl linkid "r/path/to/file.ext" %}
            """
        templtxt = textwrap.dedent(templtxt)
        t = Template(templtxt)
        uuid = '0'*32
        urlbase = 'http://example.com'
        c = Context({'linkid':uuid, 'urlbase':urlbase})
        s = t.render(c)
        url = helpers.urlreverse_redirect_local(uuid=uuid, filepath='path/to/file.ext')
        self.assertEquals(s, '\n{0}{1}\n'.format(urlbase,url))
        
    def test_url(self):
        templtxt = """\
            {% load tracked_links %}
            {% trackedurl linkid "http/www.example.com/path/file.html" %}
            """
        templtxt = textwrap.dedent(templtxt)
        t = Template(templtxt)
        uuid = '0'*32
        urlbase = 'http://example.com'
        c = Context({'linkid':uuid, 'urlbase':urlbase})
        s = t.render(c)
        url = helpers.urlreverse_redirect_http(uuid=uuid, domain='www.example.com', filepath='path/file.html')
        self.assertEquals(s, '\n{0}{1}\n'.format(urlbase,url))
        
    
#==============================================================================#
    



