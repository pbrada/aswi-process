# -*- coding: utf-8 -*-
"""
    Simple server providing ability to add comments in your pages
    Author: Matej Berka
    Date: 27.12.2017
    Resources:
        https://wiki.postgresql.org/wiki/Using_psycopg2_with_PostgreSQL
        https://www.acmesystems.it/python_http
        https://stackoverflow.com/questions/3788897/how-to-parse-basehttprequesthandler-path
"""
# IMPORTS
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi
from urlparse import parse_qsl
import psycopg2
from psycopg2.extensions import AsIs
import re
import lxml
import urllib
from lxml.html.clean import Cleaner
new_pattern = '\s*(?:javascript:|jscript:|livescript:|vbscript:|data:[^(?:image/.+;base64)]+|about:|mocha:)'
lxml.html.clean._javascript_scheme_re = re.compile(new_pattern, re.I)
# Cleaner configuration
cleaner = Cleaner()
cleaner.javascript = True  # This is True because we want to activate the javascript filter

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

text = "Autor: %s\n URL: %s"
html = """\
<html>
  <head></head>
  <body>
    <p>Autor <strong>%s</strong> přidal nový komentář na <a href="%s" title="%s" alt="%s">stranu</a>.<br>Obsah komentáře:</p>
    %s
  </body>
</html>
"""

# CONFIGURATION
#-----------------------------------------------
# PORT NUMBER
PORT_NUMBER = 8080
# DB CONNECTION
HOST = "localhost"
DB_NAME = "aswi_comments"
DB_USER = "aswi_admin"
DB_PASSWORD = "aswi_admin"
# EMAIL CONFIGURATION
# SMTP_SERVER = "smtp.gmail.com:587"
# EMAIL_FROM = "no-replay@email.com"
# EMAIL_TO = ['some_email@gmail.com', 'some_email_2@gmail.com']
# EMAIL_SER_LOGIN_NAME = "some_email@gmail.com"
# EMAIL_SER_LOGIN_PASSWORD = "xxxxx"
#-----------------------------------------------

class DatabaseService:
    """
        This class is responsible for connecting and providing operations related to data storage
    """
    def __init__(self):
        # get a connection, if a connect cannot be made an exception will be raised here
        self.__con = psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (HOST, DB_NAME, DB_USER, DB_PASSWORD))
        self.__cursor = self.__con.cursor()

    def postgres_escape_string(self, s):
        if not isinstance(s, basestring):
            raise TypeError("%r must be a str or unicode" % (s, ))
        escaped = repr(s)
        if isinstance(s, unicode):
            assert escaped[:1] == 'u'
            escaped = escaped[1:]
        if escaped[:1] == '"':
            escaped = escaped.replace("'", "\\'")
        elif escaped[:1] != "'":
            raise AssertionError("unexpected repr: %s", escaped)
        return "E'%s'" %(escaped[1:-1], )

    def add_commnet(self, name, comment, page_id):
        comment = self.postgres_escape_string(comment.encode('utf-8'))
        name = self.postgres_escape_string(name)
        page_id = self.postgres_escape_string(page_id)
        self.__cursor.execute("INSERT INTO comments (author, comment, page_id, create_time) VALUES (%s, %s, %s, NOW())" % (name, comment, page_id))
        self.__con.commit()
        return True
    
    def get_page_commnets(self, page_id):
        # execute our Query
        self.__cursor.execute("SELECT author, comment, create_time FROM comments WHERE page_id = %s ORDER BY create_time" % self.postgres_escape_string(page_id))
        # retrieve the records from the database
        records = self.__cursor.fetchall()
        return records


class CommentBoxService:
    """
        This class provides Comments box service to the web service
    """
    def __init__(self, databaseService):
        self.__database_service = databaseService
        with open('comments-form.html', 'r') as comments_form:
            self.__form_data = comments_form.read().replace('\n', '')

    def __generate_comments(self, page_id):
        comments = self.__database_service.get_page_commnets(page_id)
        html = ''
        for comment in comments:
            html += '<div class="comment">' \
                        '<div class="comment-header">' \
                        '<span class="comment-author">' + comment[0] + '</span>' \
                        '<span class="comment-time">' + comment[2].strftime("%d.%m.%Y %H:%M:%S") + '</span>' \
                        '</div>' \
                        '<div class="comment-body ql-editor"><p>' + comment[1] + '</p></div>' \
                    '</div>'
        return html, len(comments)

    #def __send_email(self, author, comment, page_url):
     #   mailserver = smtplib.SMTP(SMTP_SERVER)
        # identify ourselves to smtp gmail client
     #   mailserver.ehlo()
        # secure our email with tls encryption
     #   mailserver.starttls()
        # re-identify ourselves as an encrypted connection
     #   mailserver.ehlo()
     #   mailserver.login(EMAIL_SER_LOGIN_NAME, EMAIL_SER_LOGIN_PASSWORD)
        # Create the message
     #   text_cont = text % (author, page_url)
     #   text_conent = MIMEText(text_cont, 'plain', 'utf-8')
     #   html_cont = html % (author, page_url, page_url, page_url, comment)
     #   html_content = MIMEText(html_cont, 'html', 'utf-8')
     #   msg = MIMEMultipart('alternative')
     #   msg['To'] = ", ".join(EMAIL_TO)
     #   msg['From'] = EMAIL_FROM
     #   msg['Subject'] = 'KIV/ASWI - Nový komentář'
     #   msg.attach(html_content)
     #   msg.attach(text_conent)
     #   mailserver.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
     #   mailserver.quit()
     #   return True

    def __generate_comment_box(self, page_id, page_url):
        return self.__form_data % (page_id, page_url)

    def update_page(self, author, comment, page_id, page_url):
        author = cgi.escape(author)
        comment = cleaner.clean_html(comment.decode('utf-8')).encode('utf-8')
        self.__database_service.add_commnet(author, comment, page_id)
        # self.__send_email(author, comment, page_url)
        return self.get_page(page_id, page_url)

    def get_page(self, page_id, page_url):
        html = '<!DOCTYPE html><html>' \
        '<head>' \
        '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">' \
        '<link rel="stylesheet" type="text/css" href="comments-form.css">' \
        '<script src="quill.min.js"></script>' \
        '<link href="quill.snow.css" rel="stylesheet">' \
        '</head><body>'

        comments_html, comments_count = self.__generate_comments(page_id)
        html += "<div id='comments-box'>"
        html += self.__generate_comment_box(page_id, page_url)
        html += '<h5>Komentáře (%s)</h5><div id="comments" class="ql-snow">' % comments_count
        html += comments_html
        html += "</div></div></body></html>"
        return html


class RequestsHandler(BaseHTTPRequestHandler):
    """
        Handler for incoming requests
    """
    def __init__(self, request, client_address, server):
        self.__view_service = CommentBoxService(DatabaseService())
        # load comments-form.css file
        with open('quill.min.js', 'r') as quill_js:
            self.__quill_js = quill_js.read().replace('\n', '')
        # load comments-form.css file
        with open('quill.snow.css', 'r') as quill_css:
            self.__quill_css = quill_css.read().replace('\n', '')
            # load comments-form.css file
        with open('comments-form.css', 'r') as comments_form:
            self.__form_css = comments_form.read().replace('\n', '')
        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    def __send_headers(self, type):
        self.send_response(200)
        self.send_header('Content-type', type)
        self.end_headers()

    def __access_forbidden(self):
        self.send_response(403)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

    def do_GET(self):
        if self.path == '/comments-form.css':
            self.__send_headers('text/css')
            self.end_headers()
            self.wfile.write(self.__form_css)
        elif self.path == '/quill.snow.css':
            self.__send_headers('text/css')
            self.end_headers()
            self.wfile.write(self.__quill_css)
        elif self.path == '/quill.min.js':
            self.__send_headers('text/javascript')
            self.end_headers()
            self.wfile.write(self.__quill_js)
        else:
            params = parse_qsl(self.path[2:])
            page_id = ''
            page_url = ''
            for key, value in params:
                if key == 'page_id':
                    page_id = value
                elif key == 'page_url':
                    page_url = value

            if page_id == '' or page_url == '':  # some random request
                self.__access_forbidden()
            else:
                page_url = urllib.unquote(page_url)
                page = self.__view_service.get_page(page_id, page_url)
                self.__send_headers('text/html')
                self.wfile.write(page)
        return

    def do_POST(self):
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        page = ''
        if ctype == 'multipart/form-data':  # this is currently unused but prepared for future updates
            postvars = cgi.parse_multipart(self.rfile, pdict)
            if 'cmb-author' in postvars and 'cmb-comment' in postvars and 'cmb-page_id' in postvars:
                page = self.__view_service.update_page(postvars['cmb-author'][0], postvars['cmb-comment'][0], postvars['cmb-page_id'][0], postvars['cmb-page_url'][0])
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers.getheader('content-length'))
            postvars = dict(parse_qsl(self.rfile.read(length)))
            if 'cmb-author' in postvars \
                and len(postvars['cmb-author']) > 0 \
                and 'cmb-comment' in postvars \
                and len(postvars['cmb-comment']) > 0 \
                and 'cmb-page_id' in postvars:
                page = self.__view_service.update_page(postvars['cmb-author'], postvars['cmb-comment'], postvars['cmb-page_id'], postvars['cmb-page_url'])
        else:
            self.__access_forbidden()
            return

        self.__send_headers('text/html')
        self.wfile.write(page)
        return

# APPLICATION STARTING POINT
# ---------------------------------
try:
    server = HTTPServer(('', PORT_NUMBER), RequestsHandler)
    print 'HTTP server started on port ' , PORT_NUMBER
    # Wait forever for incoming htto requests
    server.serve_forever()
except KeyboardInterrupt:
    print '^C received, shutting down the web server'
    server.socket.close()