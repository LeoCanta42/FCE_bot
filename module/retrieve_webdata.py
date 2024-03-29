import requests
from bs4 import BeautifulSoup

async def getdownload_urls(type_transport: int) -> list:
    url='https://www.circumetnea.it/le-nostre-linee/'

    strpage=(requests.get(url)).text
    #estraggo parti interresate della pagina
    metro=strpage[strpage.find('<h2>Metropolitana</h2>'):strpage.find('<h2>Ferrovia</h2>')]
    ferrovia=strpage[strpage.find('<h2>Ferrovia</h2>'):strpage.find('<h2>Autolinee</h2>')]
    autolinee=strpage[strpage.find('<h2>Autolinee</h2>'):]

    metro_urls=[]
    ferrovia_urls=[]
    autolinee_urls=[]

    for n in range(3):
        if(n==0): x=metro
        elif(n==1): x=ferrovia
        elif(n==2): x=autolinee

        tmp_packages=[line for line in x.splitlines() if 'class="package-title"' in line]
        for i in range(len(tmp_packages)):
            finder=BeautifulSoup(tmp_packages[i],'html.parser')
            if(n==0): metro_urls.append((finder.find('a')).get('href'))
            elif(n==1): ferrovia_urls.append((finder.find('a')).get('href'))
            elif(n==2): autolinee_urls.append((finder.find('a')).get('href'))
    
    #[0] metro, [1] ferrovia, [2] autolinee
    if(type_transport==0): return metro_urls
    if(type_transport==1): return ferrovia_urls
    if(type_transport==2): return autolinee_urls
    #prendo url in base alla tipologia passata


