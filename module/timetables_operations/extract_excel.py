from openpyxl import load_workbook

def extract():
    workbook = load_workbook(filename="./module/timetables_operations/bus_orario0.xlsx")

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




