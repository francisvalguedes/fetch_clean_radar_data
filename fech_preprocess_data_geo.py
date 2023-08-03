import pandas as pd
import numpy as np
from datetime import timedelta
import glob
from datetime import datetime
import os
import pymap3d as pm
import re
import sys
import matplotlib.pyplot as plt

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

def gms_to_decimal(s):
    angle_gms = re.split('[°\' "]+', s)
    dd = 0
    for i in range(3):
        dd+= np.sign(float(angle_gms[0]))*abs(float(angle_gms[i])/(60**i))
    return dd

def fit_coord(coord_ref):
    for index, row in coord_ref.iterrows():
        if not isinstance(coord_ref.loc[index]['lat'], float):
            try:
                coord_ref.at[index,'lat'] = gms_to_decimal(coord_ref.loc[index]['lat'])
            except:
                print("error: coord_ref.csv file is not in proper angle format")
                sys. exit()
            try:
                coord_ref.at[index,'lon'] = gms_to_decimal(coord_ref.loc[index]['lon'])
            except:
                print("error: coord_ref.csv file is not in proper angle format")
                sys. exit()
        if coord_ref.loc[index]['ellipsoid'] not in ['wgs72','wgs84']:
            print("error: coord_ref.csv ellipsoid: wgs72' or 'wgs84")
            sys. exit()
        if  not isinstance(coord_ref.loc[index]['height'], float):
            print("error: coord_ref.csv height must be float")
            sys. exit()
    return coord_ref


def split_data(file_names):
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
            raw_file_name = output_folder + os.path.sep + 'file_' + line.split(os.path.sep)[-1]+ '_tr_' +str(idx)
            df_split.to_csv(raw_file_name + '_bruto.csv', index = False)

            df_clear = pd.read_csv(raw_file_name + '_bruto.csv',
                        # skipinitialspace=True,
                        # skiprows=range(10),
                        # dtype = str,
                        delimiter=','
                        )                       

            df_clear['TR'] = np.round(np.arange(0,df_clear.shape[0])*sample_time, decimals=2)

            df_clear['S'] = df_clear['SAGADA'].str[1]
            df_clear['G'] = df_clear['SAGADA'].str[3]
            df_clear['D'] = df_clear['SAGADA'].str[5]   

            # Elev	Azim	Dist
            enu_x,enu_y,enu_z = pm.aer2enu(df_clear['Azim'], df_clear['Elev'], 1000*df_clear['Dist'], deg=False)
            df_clear['sens_enu_x'] = enu_x
            df_clear['sens_enu_y'] = enu_y
            df_clear['sens_enu_z'] = enu_z 

            ecef_x,ecef_y,ecef_z = pm.enu2ecef(enu_x, enu_y, enu_z,
                                                c_ref.loc['SENS']['lat'], c_ref.loc['SENS']['lon'], c_ref.loc['SENS']['height'],
                                                ell=pm.Ellipsoid(model= ellipsoid),
                                                deg=True)
            
            ramp_enu_x,ramp_enu_y,ramp_enu_z= pm.ecef2enu(ecef_x, ecef_y, ecef_z,
                                                          c_ref.loc['RAMP']['lat'], c_ref.loc['RAMP']['lon'], c_ref.loc['RAMP']['height'],
                                                          ell=pm.Ellipsoid(model= ellipsoid),
                                                          deg=True)
            
            df_clear['ramp_enu_x'] = ramp_enu_x
            df_clear['ramp_enu_y'] = ramp_enu_y
            df_clear['ramp_enu_z'] = ramp_enu_z

            lat, lon, alt = pm.enu2geodetic(df_clear['ramp_enu_x'], df_clear['ramp_enu_y'], df_clear['ramp_enu_z'],
                                            c_ref.loc['RAMP']['lat'], c_ref.loc['RAMP']['lon'], c_ref.loc['RAMP']['height'],
                                            ell=pm.Ellipsoid(model= ellipsoid), 
                                            deg=True)
            
            df_clear['lat'] = lat
            df_clear['lon'] = lon
            df_clear['height'] = alt

            if truncar_elev:
                df_clear = df_clear[df_clear['height']>altitude_perda_radar]

            # Salva dataframe completo
            df_clear.to_csv( raw_file_name + '_completo.csv',index = True)

            # raw_data_split_ls.append(df_clear)

            
            columns = ['Hora','TR','S','G','D','Snl_Rdo','Modo','Elev','Azim','Dist','X_Rampa','Y_Rampa','Z_Rampa']
            header = ['Tempo Universal','Tempo Relativo','S','G','D','S/R(dB)','Modo','Elev(rad)','Azim(rad)','Dist(km)','X_Rampa(km)','Y_Rampa(km)','Z_Rampa(Km)']
            df_clear.to_csv(raw_file_name + '_limpo.csv',
                        columns = columns, 
                        header= header,
                        # float_format='%.3f',
                        index = False
                        )  

            # ****************************************************
            # Informações Importantes do Rastreio                      

            # remove outliers do radar (ultrapassagem do km 0)
            outliers = df_clear[df_clear['Dist']>4000]
            if len(outliers.index)>0:
                print('Presença de ' +str(len(outliers.index))+ ' outliers d>4000km em tr ' + str(idx))
            df_clear = df_clear[df_clear['Dist']<4000]
            
            # df_clear = df_clear[df_clear['height']>0]
            df_clear = df_clear[df_clear['Valido']=='Valido'] # Apenas válidos
            # print('len(df_clear.index)')
            # print(len(df_clear.index))
            # print('max')
            # print(df_clear['Z_Rampa'].max())

            df_clear.reset_index(drop=True, inplace=True)

            dic = { 'TOP': [top_dec],
                    'height_max': [0.001*df_clear['height'].max()],
                    'TR_height_max': [df_clear.loc[df_clear['height'].idxmax(), 'TR']],
                    'ramp_z_max': [0.001*df_clear['ramp_enu_z'].max()],
                    'TR_z_max': [df_clear.loc[df_clear['Z_Rampa'].idxmax(), 'TR']],
                    'Data': [df_clear.loc[0, 'Data']],
                    'Período:' : [str(df_clear.loc[0, 'Hora']) + ' a ' + str(df_clear.loc[len(df_clear.index)-1, 'Hora'])],
                    'n_outliers>4000' : len(outliers.index)
                    }
            df_resume = pd.DataFrame(dic)

            df_resume.to_csv( raw_file_name + '_resumo.csv',
                    index = False,
                    float_format='%.5f'
                    )
            
            print('trajetória ' + str(idx) + ' concluída')

            # GRÁFICOS
            if plot:
                fig1 = plt.figure()
                ax1 = fig1.subplots()
                ax1.plot(df_clear['TR'],df_clear['height'], '.', label='Sensor')
                ax1.set_xlabel('t(s)')
                ax1.set_ylabel('height(m)')
                ax1.legend()

                plt.xlim(0)

                # ax1 = fig1.add_subplot(111, projection='3d')
                # ax1.plot3D(df_clear['ramp_enu_x'],df_clear['ramp_enu_y'],df_clear['ramp_enu_z'] , '.', label=sensor_sel)
                # ax1.set_xlabel('X(m)')
                # ax1.set_ylabel('Y(m)')
                # ax1.set_zlabel('Z(m)')
                # ax1.legend()

                plt.show()

            

# Inicialização
# ******************************************

sample_time = 0.01 # Periodo de amostragem
sensor_sel = 'Bearn-CLBI' # Sensor
ellipsoid = 'wgs72' # Ellipsoid

truncar_elev = False
altitude_perda_radar =  0.0  # altitude geodesica de perda radar

# plota grafico a cada trajetória
plot = True

# Arquivo de configuração de localização do Sensor e da Rampa
c_ref = pd.read_csv( 'config/coord_ref_mr.txt')

# Execução do script
print('\n')
print('coord_ref FILE:')
print(c_ref)
c_ref = fit_coord(c_ref)
print(c_ref)
print('\n')

output_folder = 'output_clear_data'

dellfiles(output_folder + os.path.sep + '*.csv' )

txt_files = glob.glob('input_raw_data/*.d')
print(txt_files)

# Função principal
split_data(txt_files)

print('processamento concluído')
print('\n')

# Fim