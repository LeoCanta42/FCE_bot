import requests
from bs4 import BeautifulSoup

path="./module/news_check/"

def indexes(page) -> list:
    arr=[]
    arr.append(page.text.find('class="entry-title"')) #inizio info news
    arr.append(page.text.find('class="page-numbers')) #fine info news
    return arr

def download_page() -> None:
    #scarico pagina e salvo in un file
    page=requests.get("https://www.circumetnea.it/category/news/")
    ind=indexes(page)
    page=page.text[ind[0]:ind[1]]
    with open(path+"updated_news.html","w") as f:
        f.write(page)

def scraping_news(soup:BeautifulSoup) -> list: #ritorna una matrice
    # [i][j] i=indice notizia | j=[0,1,2]=titolo,descrizione,link
    notizie=[]
    i=0
    for title in soup.find_all("h5"):
        notizie.append(["","",""])
        notizie[i][0]=title.text
        i+=1
    
    i=0
    for description in soup.find_all("p"):
        notizie[i][1]=description.text
        i+=1

    i=0
    all_links=[]
    for _ in soup.find_all("a"):
        all_links.append(_.get('href'))

    i=0
    for link in all_links:
        if notizie[len(notizie)-1][2]!='': break #se ho gia' riempito l'ultimo elemento

        if link!="https://www.circumetnea.it/category/news/":
            h=False
            for j in range(len(notizie)): 
                if(link==notizie[j][2]):#se notizia gia' esistente non inserisco
                    h=True
                    break
                elif(notizie[j][2]==''):#se trovo vuoto mentre scorro vuol dire che ancora non ci sono arrivato quindi posso gia' fermarmi (gli altri saranno vuoti)
                    break
            if not h:
                notizie[i][2]=link
                i+=1
    return notizie


def check_news() -> list:
    #faccio get della pagina e confronto con quella scaricata 
    #(se ci sono news sostituisco vecchia pagina con questa)
    #cerco news, invio agli utenti/canale
    new_page=requests.get("https://www.circumetnea.it/category/news/")
    ind=indexes(new_page)
    new_page=new_page.text[ind[0]:ind[1]]
    
    old_page=open(path+"updated_news.html","r").read()
    if new_page != old_page:
        to_send=[]
        print("News disponibili !\n")
        new_soup=BeautifulSoup(new_page,'html.parser')
        old_soup=BeautifulSoup(old_page,'html.parser')
        nuove=scraping_news(new_soup)
        vecchie=scraping_news(old_soup)

        for i in range(len(nuove)):
            h=False
            for j in range(len(vecchie)):
                if nuove[i][0]==vecchie[j][0]: #se e' uguale almeno ad uno allora e' notizia vecchia
                    h=True
                    break #posso fermarmi, non devo considerarla
            if not h:
                stringa=str(nuove[i][0])+"\n\n"+str(nuove[i][1])+"\n\n"+str(nuove[i][2])
                to_send.append(stringa)
        with open(path+"updated_news.html","w") as f: #aggiorno la pagina con le nuove notizie
            f.write(new_page)
        
        return to_send
