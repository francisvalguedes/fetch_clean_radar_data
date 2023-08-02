import pandas as pd
import numpy as np
from datetime import timedelta
import glob
from datetime import datetime
import os
# import pymap3d as pm

# Funções
# ****************************************************
def dellfiles(file):
    py_files = glob.glob(file)
    err = 0
    for py_file in py_files:
        try:
            os.remove(py_file)
        except OSError as e:
            print(f"Error:{e.strerror}")
            err = e.strerror
    return err


def split_data(file_names, sensor_sel):
    # raw_data_ls = []
    df_list = []
    for line in file_names:
        df = pd.read_csv(line,
                    skipinitialspace=True,
                    # skiprows=range(10),
                    dtype = str,
                    delimiter=','
                    )
        
        # raw_data_ls.append(df)

        df.columns = df.columns.str.replace(' ', '') # Retira espaços nos nomes de colunas
        for col in df.columns: # Retira espaços em todas as celulas das colunas
            df[col].str.strip()


        time_format = '%d/%m/%Y,%H:%M:%S:%f'
        # time_format = '%H:%M:%S:%f'

        time = pd.to_datetime(df['Data']+ ',' +df['Hora'], format=time_format)# .dt.time

        end_idx = []
        period = []
        for idx in range(1,len(time)):
            period.append(time[idx]-time[idx-1])
            if time[idx]-time[idx-1]>timedelta(seconds=10):
                end_idx.append(idx)

        top_index_list = df[df['Sensor']=='TOPDEC-LIG'].index.values
                
        for idx in range(len(top_index_list)):
            if not (idx>=len(end_idx)):
                df_split = df.iloc[top_index_list[idx]+1:end_idx[idx],:]
                df_list.append(df_split)
            else:
                df_split = df.iloc[top_index_list[idx]+1:,:]
                df_list.append(df_split)

            top_dec = df.loc[top_index_list[idx], 'Hora']

            df_split = df_split[df_split['Sensor'].str.contains(sensor_sel)]
            raw_file_name = output_folder + os.path.sep + 'file_' + line.split(os.path.sep)[-1]+ '_tr_' +str(idx)+'.csv'
            df_split.to_csv(raw_file_name, index = False)

            df_clear = pd.read_csv(raw_file_name,
                        # skipinitialspace=True,
                        # skiprows=range(10),
                        # dtype = str,
                        delimiter=','
                        )

            df_clear['TR'] = np.round(np.arange(0,df_clear.shape[0])*sample_time, decimals=2)

            df_clear['S'] = df_clear['SAGADA'].str[1]
            df_clear['G'] = df_clear['SAGADA'].str[3]
            df_clear['D'] = df_clear['SAGADA'].str[5]


            # lat, lon, alt = pm.enu2geodetic(df_clear['X_Rampa'], df_clear['Y_Rampa'], df_clear['Z_Rampa'],
            #                                 Ramp['lat'], Ramp['lon'], Ramp['height'],
            #                                 ell=pm.Ellipsoid(model='wgs72'),
            #                                 deg=True)

            # raw_data_split_ls.append(df_clear)

            # df_clear = df_clear[df_clear['Z_Rampa']>0]
            columns = ['Hora','TR','S','G','D','Snl_Rdo','Modo','Elev','Azim','Dist','X_Rampa','Y_Rampa','Z_Rampa']
            header = ['Tempo Universal','Tempo Relativo','S','G','D','Snl_Rdo','Modo','Elev','Azim','Dist','X_Rampa','Y_Rampa','Z_Rampa']
            df_clear.to_csv(raw_file_name,
                        columns = columns, 
                        header= header,
                        # float_format='%.3f',
                        index = False
                        )        


            dic = { 'TOP': [top_dec],
                    'Z_max': [df_clear['Z_Rampa'].max()],
                    'TR_Z_max': [df_clear.loc[df_clear['Z_Rampa'].idxmax(), 'TR']],
                    'Data': [df_clear.loc[0, 'Data']],
                    'Período:' : [str(df_clear.loc[0, 'Hora']) + ' a ' + str(df_clear.loc[len(df_clear.index)-1, 'Hora'])]
                    }
            df_resume = pd.DataFrame(dic)

            df_resume.to_csv( raw_file_name + '_resume.csv',
                    index = False
                    )

# Inicialização
# ******************************************

sample_time = 0.01
sensor_sel = 'Bearn-CLBI'
# -5.922037, -35.161362, 45
Ramp = {'lat': -5.922037 ,'lon': -35.161362,'height': 45}

output_folder = 'output_clear_data'

dellfiles(output_folder + os.path.sep + '*.csv' )

txt_files = glob.glob('input_raw_data/*.d')
print(txt_files)

split_data(txt_files, sensor_sel)


# raw_data_split_ls = []

# # Loop
# # ******************************************
# for line in txt_files:
#     df = pd.read_csv(line,
#                 # skipinitialspace=True,
#                 # skiprows=range(10),
#                 # dtype = str,
#                 delimiter=','
#                 )

#     df['TR'] = np.round(np.arange(0,df.shape[0])*sample_time, decimals=2)

#     df['S'] = df['SAGADA'].str[1]
#     df['G'] = df['SAGADA'].str[3]
#     df['D'] = df['SAGADA'].str[5]

#     raw_data_split_ls.append(df)

#     # df = df[df['Z_Rampa']>0]
#     columns = ['Hora','TR','S','G','D','Snl_Rdo','Modo','Elev','Azim','Dist','X_Rampa','Y_Rampa','Z_Rampa']
#     header = ['Tempo Universal','Tempo Relativo','S','G','D','Snl_Rdo','Modo','Elev','Azim','Dist','X_Rampa','Y_Rampa','Z_Rampa']
#     df.to_csv('clear_data' + os.path.sep + 'file_' + line.split(os.path.sep)[-1]+ '_clear.csv',
#                 columns = columns, 
#                 header= header,
#                 # float_format='%.3f',
#                 index = False
#                 )
    
#     # lat, lon, alt = pm.enu2geodetic(df['X_Rampa'], df['Y_Rampa'], df['Z_Rampa'],
#     #                                 -5.922037, -35.161362, 45,
#     #                                 ell=pm.Ellipsoid(model='wgs72'),
#     #                                 deg=True)

#     dic = { 'Z_max': [df['Z_Rampa'].max()],
#             'TR_Z_max': [df.loc[df['Z_Rampa'].idxmax(), 'TR']],
#             'Data': [df.loc[0, 'Data']],
#             'Período:' : [str(df.loc[0, 'Hora']) + ' a ' + str(df.loc[len(df.index)-1, 'Hora'])]
#             }
#     df_resume = pd.DataFrame(dic)

#     df_resume.to_csv('clear_data' + os.path.sep + 'file_' + line.split(os.path.sep)[-1]+ '_clear_resume.csv',
#             index = False
#             )
    
# print(raw_data_split_ls[0].dtypes)
# print(np.max(raw_data_split_ls[0]['Z_Rampa']))


#df[df['Valido']=='Valido']

# df=df.round(2)
# df['TR']=df['TR'].astype(str)

# df.to_csv('clear_data' + os.path.sep + 'bruto.csv',
#         columns = ['TR', 'X', 'Y', 'Z'],
#         header= None,
#         # float_format='%.3f',
#         index = False
#         )