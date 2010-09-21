from django import template
import urlparse

register = template.Library()


def create_trackedurl_tag(trailpath):
    return '{{% trackedurl {linkidvar} "{tp}" %}}'.format(linkidvar='linkid',tp=trailpath)

class TrackNode(template.Node):
    pass
    
class TrackTrailNode(TrackNode):
    def __init__(self, trailpath):
        self.text = create_trackedurl_tag(trailpath)
    def render(self, context):
        return self.text

class TrackUrlNode(TrackNode):
    def __init__(self, url):
        p = urlparse.urlsplit(url)
        scheme, netloc, path, query, fragment = p
        u = '{s}/{n}{f}'.format(s=scheme, n=netloc, f=path)
        self.text = create_trackedurl_tag(u)
    def render(self, context):
        return self.text

class TrackPixelNode(TrackNode):
    def __init__(self, type):
        trailpath = 'gpx'
        if type=='gif':
            trailpath = 'gpx'
        elif type=='png':
            trailpath = 'ppx'
        self.text = create_trackedurl_tag(trailpath)
    def render(self, context):
        return self.text


def track(parser, token):
    try:
        tagname,category,arg = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires two arguments" % token.contents.split()[0]
    if not (category[0] == category[-1] and category[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's first argument should be in quotes" % tagname
    if not (arg[0] == arg[-1] and arg[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's second argument should be in quotes" % tagname
    
    category = category[1:-1]
    arg = arg[1:-1]
    
    if category=='trail':
        return TrackTrailNode(arg)
    elif category=='url':
        return TrackUrlNode(arg)
    elif category=='pixel':
        return TrackPixelNode(arg)
    else:
        raise template.TemplateSyntaxError, "%r tag's first argument, '%s', was not recognized" % (tagname,category)

register.tag('track',track)
    
    
class TrackedurlNode(template.Node):
    def __init__(self, urlbase, linkid, trailpath):
        self.urlbase = template.Variable(urlbase)
        self.linkid = template.Variable(linkid)
        self.trailpath = trailpath
        
    def render(self, context):
        try:
            urlbase = self.urlbase.resolve(context)
            linkid = self.linkid.resolve(linkid)
            return '{u}/{id}/{p}'.format(u=urlbase, id=linkid, p=self.trailpath)
        except:
            return ''
    

def trackedurl(parser, token):
    try:
        tagname,urlbase,linkid,trailpath = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires three arguments" % token.contents.split()[0]
    for v in (urlbase, linkid, trailpath):
        if not (v[0] == v[-1] and v[0] in ('"', "'")):
            raise template.TemplateSyntaxError, "%r tag's arguments should be in quotes" % tagname
    
    urlbase = urlbase[1:-1]
    linkid = linkid[1:-1]
    trailpath = trailpath[1:-1]
    
    return TrackedurlNode(urlbase, linkid, trailpath)

register.tag('trackedurl',trackedurl)


