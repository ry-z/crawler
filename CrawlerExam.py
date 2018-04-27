import socket
from selectors import *
import re
import urllib.parse


urls_todo = set(['/'])
seen_urls = set(['/'])
selector = DefaultSelector()
stopped = False

class Fetcher:
    def __init__(self,url):
        self.response = b''#empty array of bytes
        self.url = url
        self.sock = None

    #Method on Fecher class.
    def fetch(self):
        self.sock = socket.socket()
        self.sock.setblocking(False)
        try:
            self.sock.connect(('animefansarea1.com',80))
        except BlockingIOError:
            pass

        #Register next callback
        selector.register(self.sock.fileno(),EVENT_WRITE,self.connected)


    def connected(self,key,mask):
        print('connected!')
        selector.unregister(key.fd)
        #Host 代表需要访问的Host服务器地址，self.url代表具体需要访问的链接资源
        request = 'GET {} HTTP/1.1\r\nHost: animefansarea1.com\r\n\r\n'.format(self.url)
        self.sock.send(request.encode('ascii'))

        #Regester the next callback.
        selector.register(key.fd,EVENT_READ,self.read_response)

    def read_response(self,key,mask):
        global stopped

        chunk = self.sock.recv(4096)

        if chunk:
            self.response += chunk
        else:
            selector.unregister(key.fd) #Done reading
            links = self.parse_links()
            #python set-logic:
            #just in links not in seen-urls
            for link in links.difference(seen_urls):
                urls_todo.add(link)
                Fetcher(link).fetch()


            seen_urls.update(links)
            urls_todo.remove(self.url)
            if not urls_todo:
                stopped = True
            print(self.url)

    def body(self):
        body = self.response.split(b'\r\n\r\n',1)[1]
        return body.decode('utf-8')

    def parse_links(self):
        if not self.response:
            print('error:{}'.format(self.url))
            return set()
        if not self._is_html():
            return set()
        urls = set(re.findall(r'''(?i)href=["']?([^\s"'<>]+)'''
                            ,self.body()))

        links = set()
        for url in urls:
            normalized = urllib.parse.urljoin(self.url,url)
            parts = urllib.parse.urlparse(normalized)
            if parts.scheme not in ('','http','https'):
                continue
            host,port = urllib.parse.splitport(parts.netloc)
            if host and host.lower() not in ('animefansarea1.com'):
                continue
            defragmented,frag = urllib.parse.urldefrag(parts.path)
            links.add(defragmented)
        print(links)

        return links

    def _is_html(self):
        head,body = self.response.split(b'\r\n\r\n',1)
        headers = dict(h.split(': ')for h in head.decode().split('\r\n')[1:])
        return headers.get('Content-Type','').startswith('text/html')





#文件描述符（file descriptor）来访问文件。文件描述符是非负整数。fileno
#打开现存文件或新建文件时，内核会返回一个文件描述符。
#读写文件也需要使用文件描述符来指定待读写的文件
fetcher = Fetcher('/')
fetcher.fetch()

while not stopped:
    events = selector.select()
    for event_key,event_mask in events:
        callback = event_key.data
        callback(event_key,event_mask)
print('have get:')
for n in seen_urls:
    print(n)
