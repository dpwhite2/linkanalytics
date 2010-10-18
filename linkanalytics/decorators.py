from django.http import Http404

#==============================================================================#
def targetview(allow_all=False):
    """Wraps a target view function so """
    
    def targetview_decorator(viewfunc):
        def wrapper(request, *args, **kwargs):
            is_linkanalytics = kwargs.pop('linkanalytics_flag', False)
            uuid = kwargs.pop('linkanalytics_uuid', None)
                
            if not allow_all and not is_linkanalytics:
                raise Http404
                
            return viewfunc(request, uuid, *args, **kwargs)
            wrapper.__name__ = viewfunc.__name__
        return wrapper
    
    return targetview_decorator
    
#==============================================================================#
