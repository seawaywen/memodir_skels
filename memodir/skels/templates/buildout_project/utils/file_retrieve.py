from HTMLParser import HTMLParser
import os
from sgmllib import SGMLParser
import urlparse

__author__ = 'Kelvin'

import urllib2


class FileDownloader(object):
    def __init__(self, file_url, save_path='./', min_size=0):
        self.url = file_url
        self.save_path = save_path
        self.min_size = min_size

    def download(self):
        file_name = os.path.join(self.save_path, self.url.split('/')[-1])
        url_obj = urllib2.urlopen(self.url)
        download_file = open(file_name, 'wb')
        meta_data = url_obj.info()
        file_size = int(meta_data.getheaders("Content-Length")[0])
        if self.min_size > 0 and file_size < min_size:
            print 'file is too small to download'
            return
        #print "Downloading: %s Bytes: %s" % (file_name, file_size)

        else:
            file_size_dl = 0
            block_sz = 8192

            while True:
                _buffer = url_obj.read(block_sz)
                if not _buffer:
                    break

                file_size_dl += len(_buffer)
                download_file.write(_buffer)
                status = r"=[downloading %s] [%10d / %s ] [%3.2f%%]" % (file_name,
                                                                        file_size_dl,
                                                                        file_size,
                                                                        file_size_dl * 100. / file_size)
                status += chr(8) * (len(status) + 1)
                print status,

        download_file.close()


class URLLister(HTMLParser):
    def reset(self):
        SGMLParser.reset(self)
        self.urls = []
        self.imgs = []
        self.gzs = []
        
    def handle_starttag(self, tag, attrs):
        pass

    def start_a(self, attrs):
        href = [v for k, v in attrs if k == "href" and v.startswith("http")]
        if href:
            print
            self.urls.extend(href)

    def start_img(self, attrs):
        src = [v for k, v in attrs if k == "src" and v.startswith("http")]
        if src:
            self.imgs.extend(src)

    def start_gz(self, attrs):
        href = [v for k, v in attrs if k == "href" and v.endswith("gz")]
        if href:
            self.gzs.extend(href)


files_list = []


def get_url_of_page(url, if_img=False, if_gz=False):
    urls = []
    try:
        f = urllib2.urlopen(url, timeout=1).read()
        print f
        url_listen = URLLister()
        url_listen.feed(f)
        if if_img:
            urls.extend(url_listen.imgs)
        if if_gz:
            urls.extend(url_listen.gzs)
        else:
            urls.extend(url_listen.urls)
    except urllib2.URLError, e:
        print e.reason
    return urls


def get_page_html(begin_url, depth, ignore_outer, main_site_domain):
    if ignore_outer:
        if not main_site_domain in begin_url:
            return

    if depth == 1:
        urls = get_url_of_page(begin_url, False, True)
        files_list.extend(urls)
    else:
        urls = get_url_of_page(begin_url)
        if urls:
            for url in urls:
                get_page_html(url, depth - 1)


def download_file(save_path, min_size):
    print 'start downloading...'
    for _file in files_list:
        print _file
        downloader = FileDownloader(_file, save_path, min_size)
        downloader.download()
    print 'finish download.'

if __name__ == "__main__":
    #url = "http://localhost:9200/pycharm-124.253.dmg"
    #url = "http://localhost:9200"
    url = "http://172.22.2.225:9000"

    #_file = FileDownloader(url)
    #_file.download()

    save_path = "/tmp/kelvin"
    if not os.path.exists(save_path):
        os.mkdir(save_path)

    min_size = 80
    max_depth = 1
    ignore_outer = True
    main_site_domain = urlparse.urlsplit(url).netloc

    get_page_html(url, max_depth, ignore_outer, main_site_domain)

    download_file(save_path, min_size)