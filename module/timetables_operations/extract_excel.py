from openpyxl import load_workbook
from module.timetables_operations.times_op import isTimeFormat,isTimeFormatH

#convertire pdf in excel

def extract(s:str):
    if s=='bus':
        workbook = load_workbook(filename="./module/timetables_operations/bus_orario0.xlsx")
    elif s=='littorina':
        workbook = load_workbook(filename="./module/timetables_operations/littorina_orario0.xlsx")

    sheet = workbook.active

    matrix=[]
    n_righe=0
    for row in sheet.iter_rows():
        n_righe+=1

    matrix=[[] for i in range(n_righe)]

    i=0
    for row in sheet.iter_rows(values_only=True):
        for j in row:
            matrix[i].append(j)    
        i+=1
    
    return matrix

def dimensions(matr,table:int):
    h=True
    count_table=0
    for i in range(len(matr)):
        if str(matr[i][0])=="CATANIA (S.Sofia)":
            count_table+=1
        if count_table==1 and table==0 and h:
            start=i
            h=False
        elif count_table==2 and table==0 and h==False:
            rows=i+1
            h=True
        elif count_table==3 and table==1 and h:
            start=i
            h=False
        elif count_table==4 and table==1 and h==False:
            rows=i+1
            break
    dim=[start,rows]
    return dim

def all_replacing(s:str):
    s=s.upper().replace(' ','').replace("P.ZZA","PIAZZA").replace("Ù","U'").replace("'",'').replace('°','').replace('.','').replace('(','').replace(')','').replace('METRO','')
    return s


def locations_to_file(s:str):
    matrix=extract(s)
    dim1=dimensions(matrix,0)
    dim2=dimensions(matrix,1)
    
    different_types=[[],[]] #bus, train

    toadd=[]
    start=dim1[0]
    toadd.append(str(matrix[dim1[0]][0]))
    different_types[0].append(str(matrix[dim1[0]][0]))
    for i in range(start+1,dim1[1]):
        h=True
        for element in toadd:
            if all_replacing(str(matrix[i][0]))==all_replacing(str(element)):
                h=False
        if h:
            toadd.append(str(matrix[i][0]))
            b=False
            t=False
            for j in range(len(matrix[i])):
                if(isTimeFormat(str(matrix[i][j])) or isTimeFormatH(str(matrix[i][j]))):
                    if str(matrix[start-2][j])=="BUS":
                        b=True
                    elif str(matrix[start-2][j]).replace('.','')=="TR":
                        t=True
            if b and not t:
                different_types[0].append(str(matrix[i][0]))
            elif t and not b:
                different_types[1].append(str(matrix[i][0]))
            if t and b:
                different_types[0].append(str(matrix[i][0]))
                different_types[1].append(str(matrix[i][0]))

    start=dim2[0]
    dim1[1]=dim2[1]
    for i in range(start+1,dim1[1]):
        h=True
        for element in toadd:
            if all_replacing(str(matrix[i][0]))==all_replacing(str(element)):
                h=False
        if h:
            toadd.append(str(matrix[i][0]))
            b=False
            t=False
            for j in range(len(matrix[i])):
                if(isTimeFormat(str(matrix[i][j])) or isTimeFormatH(str(matrix[i][j]))):
                    if str(matrix[start-2][j])=="BUS":
                        b=True
                    elif str(matrix[start-2][j]).replace('.','')=="TR":
                        t=True
            if t and b:
                different_types[2].append(str(matrix[i][0]))
            elif b:
                different_types[0].append(str(matrix[i][0]))
            elif t:
                different_types[1].append(str(matrix[i][0]))
    
    different_types[0].sort()
    different_types[1].sort()
    with open("./module/timetables_operations/locations"+s+".txt","w") as f:
        for element in different_types[0]:
            f.write(element+"\n")
        f.write("TR\n")
        for element in different_types[1]:
            f.write(element+"\n")


#locations_to_file("bus")

