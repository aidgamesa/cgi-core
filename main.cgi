#!/usr/bin/env python3

import os
from core import CGI_HTTP, render_template

app=CGI_HTTP()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/debug/:eqw/:eqwe")
def index2(a,b):
    return "a={}<br>b={}".format(a,b)
    #"<br>".join(["{} = {}".format(a,b) for a,b in os.environ.items()])

app.start()