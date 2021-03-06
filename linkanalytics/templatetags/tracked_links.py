from django import template
import urlparse
from django.core.urlresolvers import reverse as urlreverse

from linkanalytics import urlex, app_settings

register = template.Library()


def create_trackedurl_tag(trailpath):
    s = '{{% trackedurl {linkidvar} "{tp}" %}}'
    return s.format(linkidvar=app_settings.LINKID_VARNAME, tp=trailpath)

class TrackNode(template.Node):
    pass
    
class TrackTrailNode(TrackNode):
    def __init__(self, trailpath):
        TrackNode.__init__(self)
        self.text = create_trackedurl_tag(trailpath)
    def render(self, context):
        return self.text

class TrackUrlNode(TrackNode):
    def __init__(self, url):
        TrackNode.__init__(self)
        p = urlparse.urlsplit(url)
        scheme, netloc, path, query, fragment = p
        path = path[1:] # trim leading slash
        if scheme=='http':
            url = urlex.urltail_redirect_http(domain=netloc, filepath=path)[1:]
        elif scheme=='https':
            url = urlex.urltail_redirect_https(domain=netloc, filepath=path)[1:]
        else:
            raise RuntimeError('Unknown scheme')
        self.text = create_trackedurl_tag(url)
    def render(self, context):
        return self.text

class TrackPixelNode(TrackNode):
    def __init__(self, type):
        TrackNode.__init__(self)
        if type == 'gif':
            trailpath = urlex.urltail_pixelgif()[1:]
        elif type == 'png':
            trailpath = urlex.urltail_pixelpng()[1:]
        else:
            raise RuntimeError('Unknown pixelimage type')
        self.text = create_trackedurl_tag(trailpath)
    def render(self, context):
        a = '{% if not ignore_pixelimages %}'
        b = '{% endif %}'
        return '{0}{1}{2}'.format(a, self.text, b)
        
class TrackEmailNode(TrackNode):
    def __init__(self, option):
        TrackNode.__init__(self)
        if option=='render':
            url = urlreverse('targetview-email-render')
        elif option=='acknowledge':
            url = urlreverse('targetview-email-acknowledge')
        else:
            raise RuntimeError('Unknown email option')
        self.text = create_trackedurl_tag(url)
    def render(self, context):
        return self.text


def track(parser, token):
    try:
        tagname, category, arg = token.split_contents()
    except ValueError:
        msg = "%r tag requires two arguments" % token.contents.split()[0]
        raise template.TemplateSyntaxError(msg)
    if not (category[0] == category[-1] and category[0] in ('"', "'")):
        msg = "%r tag's first argument should be in quotes" % tagname
        raise template.TemplateSyntaxError(msg)
    if not (arg[0] == arg[-1] and arg[0] in ('"', "'")):
        msg = "%r tag's second argument should be in quotes" % tagname
        raise template.TemplateSyntaxError(msg)
    
    category = category[1:-1]
    arg = arg[1:-1]
    
    if category == 'trail':
        return TrackTrailNode(arg)
    elif category == 'url':
        return TrackUrlNode(arg)
    elif category == 'pixel':
        return TrackPixelNode(arg)
    elif category == 'email':
        return TrackEmailNode(arg)
    else:
        fmt = (tagname, category)
        msg = "%r tag's first argument, '%s', was not recognized" % fmt
        raise template.TemplateSyntaxError(msg)

register.tag('track', track)
    
    
class TrackedurlNode(template.Node):
    def __init__(self, linkid, trailpath):
        template.Node.__init__(self)
        self.urlbase = template.Variable(app_settings.URLBASE_VARNAME)
        self.linkid = template.Variable(linkid)
        self.trailpath = trailpath
        
    def render(self, context):
        try:
            linkid = self.linkid.resolve(context)
            urlpart = urlex.create_hashedurl(linkid, self.trailpath)
            urlbase = self.urlbase.resolve(context)
            return '{base}{p}'.format(base=urlbase, p=urlpart)
        except Exception:
            return ''
    

def trackedurl(parser, token):
    try:
        tagname, linkid, trailpath = token.split_contents()
    except ValueError:
        msg = "%r tag requires two arguments" % token.contents.split()[0]
        raise template.TemplateSyntaxError(msg)
    if not (trailpath[0] == trailpath[-1] and trailpath[0] in ('"', "'")):
        msg = "%r tag's second argument should be in quotes" % tagname
        raise template.TemplateSyntaxError(msg)
    
    trailpath = trailpath[1:-1]
    
    return TrackedurlNode(linkid, trailpath)

register.tag('trackedurl', trackedurl)


