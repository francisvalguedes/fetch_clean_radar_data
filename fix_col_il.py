import pandas as pd
import os
import re

def is_valid_date(date_str):
    # Define a expressão regular para formato de data (dd/mm/yyyy ou dd-mm-yyyy)
    date_pattern = r'^(0[1-9]|[12][0-9]|3[01])[/\-](0[1-9]|1[0-2])[/\-](\d{4})$'
    
    if re.match(date_pattern, date_str):
        return True
    else:
        return False

def fix_csv(file_path, fixed_file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    # para Ajustar todas as linhas para ter o mesmo número de colunas
    num_cols = len(lines[0].split(','))
    fixed_lines = []
    
    for line in lines:
        # Remove espaços em excesso e ignora linhas vazias
        line = re.sub(' +', ' ', line.strip())
        if not line:
            continue
        
        cols = line.split(',')

        # se for top
        if len(cols) > 0 and is_valid_date(cols[0]):
            cols.insert(0, '') # insere uma coluna pra não dá erro
                        
        if len(cols) != num_cols:
            # Ajustar o comprimento da linha adicionando/removendo vírgulas
            if len(cols) < num_cols:
                cols += [''] * (num_cols - len(cols))
            else:
                cols = cols[:num_cols]
        
        fixed_lines.append(','.join(cols))
    
    # Salva as linhas ajustadas em um novo arquivo
    # fixed_file_path = 'fixed_' + file_path
    with open(fixed_file_path, 'w') as file:
        file.write('\n'.join(fixed_lines))
    
    return 

import glob
txt_files = glob.glob('input_raw_data_il/*.d')

for file in txt_files:
    fixed_path = 'input_raw_data'+ os.path.sep + file.split(os.path.sep)[-1] 
    fix_csv(file, fixed_path )
    print('processado o arquivo: '+ file + ', salvo em: '+fixed_path )