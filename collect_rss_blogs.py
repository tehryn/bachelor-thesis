#!/usr/bin/env python3
import urllib.request
import sys
import re

def find_urls(string):
    idx1 = 0
    idx2 = 0
    urls = list()
    N = len(string)
    while idx2 < N and idx2 >= 0 and idx1 >= 0:
        idx1 = string.find('"http://', idx2, N)
        idx2 = string.find('"', idx1 + 1, N)
        if idx1 >= 0:
            url = string[idx1+1:idx2]
            if url.endswith(".blog.cz/"):
                urls.append(url)
            elif re.match("http[:][/][/][a-z|A-Z|0-9]+[.]blog[.]cz[/][0-9]+", url):
                spl = url.split('/')
                url = spl[0] + "//" + spl[2] + "/"
                urls.append(url)
    return urls

blogcz_new = urllib.request.urlopen("http://blog.cz/zebricky/nejnovejsi").read().decode()
blogcz_best = urllib.request.urlopen("http://blog.cz/zebricky/nejlepe-hodnocene").read().decode()
blogcz_most_visited = urllib.request.urlopen("http://blog.cz/zebricky/nejnavstevovanejsi/den").read().decode()
blogs = find_urls(blogcz_new) + find_urls(blogcz_best) + find_urls(blogcz_most_visited)
blogs = set(blogs)
dedup = list()
for url in blogs:
    dedup.append(url+"rss-kanal/prehled-clanku/\n")
    dedup.append(url+"rss-kanal/cele-clanky/\n")
    dedup.append(url+"rss-kanal/komentare/\n")
dedup_file = open("/mnt/minerva1/nlp/projects/cs_media/run_crawling/rss_sources/blogs_rss_cz.txt", "r")
dedup_data = dedup_file.readlines()
new_rss = [x for x in dedup if not(x in dedup_data)]
dedup_file.close()
output_file = open("/mnt/minerva1/nlp/projects/cs_media/run_crawling/rss_sources/blogs_rss_cz.txt", "a")
for url in new_rss:
    output_file.write(url)
output_file.close()
