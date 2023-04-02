import requests

path="./module/news_check/"

def download_page():
    #scarico pagina e salvo in un file
    page=requests.get("https://www.circumetnea.it/category/news/")
    page=page.text[page.text.find('class="entry-title"'):]
    with open(path+"updated_news.txt","w") as f:
        f.write(page)

def check_news():
    #faccio get della pagina e confronto con quella scaricata 
    #(se ci sono news sostituisco vecchia pagina con questa)
    #cerco news, invio agli utenti/canale
    new_page=requests.get("https://www.circumetnea.it/category/news/")
    if new_page.text != open(path+"updated_news.txt","r"):
        print("Nuova")

download_page()

