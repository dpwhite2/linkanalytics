from django import template
import urlparse
from django.core.urlresolvers import reverse as urlreverse

from linkanalytics.models import generate_hash

register = template.Library()


def create_trackedurl_tag(trailpath):
    s = '{{% trackedurl {linkidvar} "{tp}" %}}'
    return s.format(linkidvar='linkid', tp=trailpath)

def create_trackedurlhash_tag(trailpath):
    s = '{{% trackedurlhash {linkidvar} "{hash}" "{tp}" %}}'
    hash = generate_hash(trailpath)
    return s.format(linkidvar='linkid', hash=hash, tp=trailpath)

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
        u = '{s}/{n}{f}'.format(s=scheme, n=netloc, f=path)
        self.text = create_trackedurl_tag(u)
    def render(self, context):
        return self.text

class TrackPixelNode(TrackNode):
    def __init__(self, type):
        TrackNode.__init__(self)
        trailpath = 'gpx'
        if type == 'gif':
            trailpath = 'gpx'
        elif type == 'png':
            trailpath = 'ppx'
        self.text = create_trackedurl_tag(trailpath)
    def render(self, context):
        # Note: double braces are needed for 'format()' call.
        a = '{% if not ignore_pixelimages %}'
        b = '{% endif %}'
        return '{0}{1}{2}'.format(a, self.text, b)


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
    else:
        fmt = (tagname, category)
        msg = "%r tag's first argument, '%s', was not recognized" % fmt
        raise template.TemplateSyntaxError(msg)

register.tag('track', track)
    
    
class TrackedurlNode(template.Node):
    def __init__(self, linkid, trailpath):
        template.Node.__init__(self)
        self.urlbase = template.Variable('urlbase')
        self.linkid = template.Variable(linkid)
        self.trailpath = trailpath
        
    def render(self, context):
        try:
            urlbase = self.urlbase.resolve(context)
            linkid = self.linkid.resolve(context)
            urlpart = urlreverse('linkanalytics-accessview', 
                            kwargs={'uuid': linkid, 'tailpath':self.trailpath}
                            )
            return '{base}{p}'.format(base=urlbase, p=urlpart)
        except Exception:
            return ''
    

def trackedurl(parser, token):
    # TODO: token may contain two *or* three arguments
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


