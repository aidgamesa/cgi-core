
import os, jinja2, re
from urllib.parse  import parse_qsl


class DotDict:
        base={}
        def __init__(self, base={}):
                object.__setattr__(self, "base", base)
        def __getattr__(self, name):
                return object.__getattribute__(self, "base").get(name, None)
        def __setattr__(self, name, value):

                base=object.__getattribute__(self, "base")
                base=[name]=value
                object.__setattr__(self, "base", base)
        
        def raw(self):
                return object.__getattribute__(self, "base")
        
        def __repr__(self):
                return object.__getattribute__(self, "base").__repr__()
        
        def get(self, name, default=None):
                return object.__getattribute__(self, "base").get(name, default)


def render_template(template, **kwargs):
        jenv=jinja2.Environment(
                loader=jinja2.FileSystemLoader("templates"),
                autoescape=jinja2.select_autoescape()
        )
        template=jenv.get_template(template)
        return template.render(**kwargs)

def magic_url(url):
        if url.endswith("/"):
                url=url[:-1]
        if not url.startswith("/"):
                url="/"+url
        if "?" in url:
                url=url.split("?")[0]
        return url

def parse_query(url):
        a=url.split("?")
        if len(a)<2:
                return {}
        b=a[1]
        c=parse_qsl(b)
        d=DotDict(dict(c))
        return d

class request:
        @property
        def query(self):
                return parse_query(os.environ.get("REQUEST_URI", ""))

class CGI_HTTP:
        routes={}
        request=request()
        converters={}

        def __init__(self):
                @self.converter
                class CGI_CONVERTERS:
                        def String_conv():
                                return "\/(\w+)"
                        def int_conv():
                                return "\/(\d+)"
                        def float_conv():
                                return "\/(\d+.\d+)"
                        def path_conv():
                                return "\/([\w\/\.]+)"

        def converter(self, convclass):
                for method in dir(convclass):
                        if method.endswith("_conv"):
                                self.converters[method[:-5]]=object.__getattribute__(convclass,method)

        def fn404(self):
                return "404 Not found"
        
        def fn405(self):
                return "405 Method not allowed"
        
        def httperror(self, code):
                print(self.routes.get(f"_{code}",
                        DotDict({"fn": object.__getattribute__(self, f"fn{code}")})
                ).fn())
        
        def genregex(self, url):
                regex="^"
                regex_matcher=re.compile(r"^<(\w*):(\w*)>$")
                url_a=url.split("/")[1:]
                for i in url_a:
                        a=regex_matcher.match(i)
                        if a!=None:
                                #TODO: generate regex by converter
                                conv=a.groups()[0]
                                if conv not in self.converters:
                                        raise Exception(f"{url}: Invalid convertor {conv}")
                                #regex+=f"\/(\w*)"
                                regex+=self.converters[conv]()
                        else:
                                regex+=f"\/{i}"
                regex+="$"
                return regex

        def route(self, path, methods={"GET"}):
                regex=self.genregex(path)
                if magic_url(path)!=path and not path.startswith("_"):
                        raise Exception(f"{path}: cgi url != route url, please use {magic_url(path)}")
                elif regex in self.routes:
                        raise Exception(f"{path}: url exists in routes")
                def __wrapper__(fn):
                        self.routes[regex]=DotDict({
                                "fn":fn,
                                "methods":methods,
                        })
                return __wrapper__

        def run(self):
                print("Content-Type: text/html\r\nCache-Control: no-cache\r\n\r\n", end="")
                url=magic_url(os.environ.get("REQUEST_URI", ""))
                route=None
                match=None
                for _route in self.routes:
                        match=re.match(_route, url)
                        if match!=None:
                                route=self.routes.get(_route)
                                break

                #print(url)
                if route==None:
                        return self.httperror(404)
                elif os.environ.get("REQUEST_METHOD", "GET") not in route.methods:
                        return self.httperror(405)
                print(route.fn(*match.groups()))

