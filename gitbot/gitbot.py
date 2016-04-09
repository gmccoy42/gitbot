from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from subprocess import call
import subprocess
import threading
import socketserver
import logging
import cgi
import json
import sys
import os
import html

class myHandler(BaseHTTPRequestHandler):
    # Handler for the GET requests
    def do_GET(self):
        self.protocol_version='HTTP/1.1'
        self.send_response(200, 'OK')
        self.send_header('Content-type','text/html')
        self.end_headers()
        host = ""
        with open("/home/canadabot/canadabot2.0/gitdiff.txt") as f:
            data = f.readlines()
            for line in data:
                escape = html.escape(line)
                if line.startswith("+"):
                    escape = "<font color='green'>" + escape + "</font>"
                elif line.startswith("-"):
                    escape = "<font color='red'>" + escape + "</font>"
                escape =  escape + "<br>"
                host += escape
        # Send the html message
        self.wfile.write(bytes(host, "UTF-8"))

    def do_POST(self):
        content_len = int(self.headers['Content-Length'])
        content = bytes("OK", "UTF-8")
        self.send_response(200)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()

        post_body = self.rfile.read(content_len)
        parse = json.loads(post_body.decode('utf-8'))
        print("Received push event for - " + parse["repository"]["name"])

        commits = parse["commits"]
        filestr = ""
        for commit in commits:
            added = commit["added"]
            modified = commit["modified"]
            if len(modified) > 0:
                added = added + modified
            elif len(added) > 0:
                added = modified
            else:
                print("No changes")
                return 0
            for item in added:
                filestr += "," + str(item)
        with open("/home/canadabot/canadabot2.0/hooks/gitpost.txt", "w") as f:
            f.write(filestr)
        print(filestr)

class Gitbot(object):
    def __init__(self, repo, branch, remote, webhooks, port=8000, default_msg="Gitbot auto commit"):
        self.repo = repo
        self.branch = branch
        self.remote = remote
        self.port = port
        self.default_msg = default_msg
        if webhooks:
            t = threading.Thread(target=self.runserver)
            t.start()

    def runserver(self):
        self.webhooks = HTTPServer(('', self.port), myHandler)
        print ('Started httpserver on port ' , self.port)
        try:
            self.webhooks.serve_forever()
        except KeyboardInterrupt:
            print ('^C received, shutting down the web server')
            self.webhooks.socket.close()

    def pull(self):
        result = ""
        try:
            os.chdir(self.repo)
            p = subprocess.Popen(["git", "checkout", self.branch], stdout=subprocess.PIPE)
            result = p.communicate()[0].decode("unicode_escape")

            p = subprocess.Popen(["git", "pull", self.remote, self.branch], stdout=subprocess.PIPE)
            result += p.communicate()[0].decode("unicode_escape")
        except:
            return "Error Pulling"
        return result

    def push(self):
        os.chdir(self.repo)
        p = subprocess.Popen(["git", "push", self.remote, self.branch])
        result = p.communicate()[0].decode("unicode_escape")
        return result

    def add(self, files):
        os.chdir(self.repo)
        output = ""
        for f in files:
            p = subprocess.Popen(["git", "add", f])
            result = p.communicate()[0].decode("unicode_escape")
            output = output + result
        return output

    def commit(self, msg):
        os.chdir(self.repo)
        if not msg:
            msg = self.default_msg
        call(["git", "commit", "-m", msg])

    def checkout(self, path):
        os.chdir(self.repo)
        if not path:
            return "You need to enter a path"
        call(["git", "checkout", self.branch, path])

    def diff(self, f=None):
        os.chdir(self.repo)
        if f == None:
            p = subprocess.Popen(["git", "diff", self.repo], stdout=subprocess.PIPE)
        else:
            p = subprocess.Popen(["git", "diff", f], stdout=subprocess.PIPE)
        try:
            output = p.communicate()[0].decode("unicode_escape")
        except:
            output = ""
        return output

    def host(self, msg):
        with open("/home/canadabot/canadabot2.0/gitdiff.txt", "w") as f:
            f.write(msg)

    def webhook_file(self):
        with open("/home/canadabot/canadabot2.0/hooks/gitpost.txt") as f:
            data = f.read()
        return data

