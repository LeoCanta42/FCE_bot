from openpyxl import load_workbook
import openpyxl
from module.timetables_operations.times_op import isTimeFormat,isTimeFormatH
import os
import asyncio

path="./module/timetables_operations/"

def find_files(tipo:str):
    arr=[]
    if (tipo=="bus"):
        arr=os.listdir(path+"bus/")
    elif (tipo=="littorina"):
        arr=os.listdir(path+"littorina/")
    try:
        arr.remove("locations.txt")
    except:
        arr
    return arr


bus_workbooks=[]
train_workbooks=[]

def load(tipo:str):
    for fname in find_files(tipo):
        if tipo=="bus":
            bus_workbooks.append(load_workbook(filename=path+tipo+'/'+fname))
        elif tipo=="littorina":
            train_workbooks.append(load_workbook(filename=path+tipo+'/'+fname))

async def extract(tipo:str,work_index:int):
    workbook=openpyxl.Workbook
    if tipo=="bus":
        workbook=bus_workbooks[work_index]
        
    elif tipo=="littorina":
        workbook=train_workbooks[work_index]

    matrix=[]
    n=0
    for sheet_name in workbook.sheetnames:
        sheet=workbook[sheet_name]
        n_righe=0
        matrix.append([])
        for row in sheet.iter_rows():
            n_righe+=1

        matrix[n]=[[] for i in range(n_righe)]

        i=0
        for row in sheet.iter_rows(values_only=True):
            for j in row:
                matrix[n][i].append(j)    
            i+=1
        n+=1
    
    return matrix #array di matrici

async def dimensions(matr):
    rows=len(matr)
    start=0
    for i in range(rows):
        if str(matr[i][0])=="CATANIA (S.Sofia)": #la stringa deve essere un identificativo per l'indice di partenza
            start=i
            break
    dim=[start,rows]
    return dim

async def all_replacing(s:str):
    s=s.upper().replace(' ','').replace("P.ZZA","PIAZZA").replace("Ù","U'").replace("'",'').replace('°','').replace('.','').replace('(','').replace(')','').replace('METRO','')
    return s


def locations_to_file(tipo:str):
    file_to_check=asyncio.run(find_files(tipo))
    different_loc=[]
    for file in file_to_check:
        m_table=asyncio.run(extract(file,tipo))
        for matrix in m_table:
            dim1=asyncio.run(dimensions(matrix))

        toadd=[]
        start=dim1[0]
        toadd.append(str(matrix[start][0]))
        different_loc.append(str(matrix[start][0]))
        for i in range(start+1,dim1[1]-3): #alla fine c'e' un campo LEGENDA che occupa circa 3 spazi
            h=True
            for element in toadd:
                if asyncio.run(all_replacing(str(matrix[i][0])))==asyncio.run(all_replacing(str(element))): #se l'elemento della matrice che sto controllato esiste gia' , non deve fare nulla
                    h=False
            if h:
                toadd.append(str(matrix[i][0]))
                b=False
                t=False
                for j in range(len(matrix[i])):
                    if(asyncio.run(isTimeFormat(str(matrix[i][j]))) or asyncio.run(isTimeFormatH(str(matrix[i][j])))):
                        if tipo=="bus" and str(matrix[start-2][j])=="BUS":
                            b=True
                        elif tipo=="littorina" and str(matrix[start-2][j]).replace('.','')=="TR":
                            t=True
                if tipo=="bus" and b:
                    different_loc.append(str(matrix[i][0]))
                elif tipo=="littorina" and t:
                    different_loc.append(str(matrix[i][0]))
    
    different_loc.sort()
    with open(path+tipo+"/locations.txt","w") as f:
        for element in different_loc:
            f.write(element+"\n")