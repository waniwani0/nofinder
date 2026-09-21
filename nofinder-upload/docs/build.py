#!/usr/bin/env python3
"""Wrap ../nofinder.html (the artifact source) into a standalone PWA page."""
import io, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, os.pardir, "nofinder.html")
OUT = os.path.join(HERE, "index.html")

src = io.open(SRC, encoding="utf-8").read()
cut = src.index("</style>") + len("</style>")
head, body = src[:cut], src[cut:]
title = re.search(r"<title>(.*?)</title>", head).group(1)

page = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
<meta name="theme-color" content="#141210">
<meta name="description" content="覗き穴しか映らないフィルムカメラ。">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="%(title)s">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="icon" href="icon-192.png">
<style>
  :root{
    box-sizing:border-box;color-scheme:dark;
    padding-top:env(safe-area-inset-top,0px);
    padding-bottom:env(safe-area-inset-bottom,0px);
  }
  html,body{margin:0}
  img{max-width:100%%}
  [hidden]{display:none!important}
</style>
%(head)s
</head>
<body>
%(body)s
<script>
if("serviceWorker" in navigator){
  window.addEventListener("load", function(){
    navigator.serviceWorker.register("sw.js").catch(function(){});
  });
}
</script>
</body>
</html>
""" % {"title": title, "head": head, "body": body.strip()}

io.open(OUT, "w", encoding="utf-8").write(page)
print("wrote", OUT, len(page), "bytes")
