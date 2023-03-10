import requests
from bs4 import BeautifulSoup
import re

def getdownload_urls():
    url='https://www.circumetnea.it/le-nostre-linee/'

    strpage=(requests.get(url)).text
#estraggo parti interresate della pagina
    metro=strpage[strpage.find('<h2>Metropolitana</h2>'):strpage.find('<h2>Ferrovia</h2>')]
    ferrovia=strpage[strpage.find('<h2>Ferrovia</h2>'):strpage.find('<h2>Autolinee</h2>')]
    autolinee=strpage[strpage.find('<h2>Autolinee</h2>'):]

    download_urls={}

    for n in range(3):
        if(n==0): x=metro
        elif(n==1): x=ferrovia
        elif(n==2): x=autolinee

        tmp_packages=[line for line in x.splitlines() if 'class="package-title"' in line]
        #creo un dizionario in cui inserisco la chiave che indica la tipologia e il valore sono tutti gli url collegati a quella tipologia(pdf da scaricare)
        for i in range(len(tmp_packages)):
            finder=BeautifulSoup(tmp_packages[i],'html.parser')
            download_urls.update({n:(finder.find('a')).get('href')})
    
    return download_urls
    #[0] metro, [1] ferrovia, [2] autolinee

def filter_urls(n: int):
    tmpurl = [value for key,value in getdownload_urls().items() if key==n]
    #prendo url in base alla tipologia passata
    return tmpurl

def download_package(n: int):
    with open('orario.pdf', 'wb') as f:
        tmpurl=filter_urls(n)
        for i in tmpurl:
            response = requests.get(i)
            f.write(response.content)

#download_package(2)
print(filter_urls(1))
