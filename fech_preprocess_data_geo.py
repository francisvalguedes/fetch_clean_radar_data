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
# import geopy.distance
import pymap3d.vincenty as pmv
from io import StringIO

# ****************************************************
# Desenvolvido em agosto de 2023 por Francisval Guedes
# Email: francisvalg@gmail.com
# ****************************************************

# Funções
# ****************************************************
def search_timeout(t, timout_t):
    timeout = {'time': [], 'idx':[], 'timeout': [] }
    sp = []
    sp.append(0)
    for idx in range(1,len(t)):
        sp.append((t[idx]-t[idx-1]).total_seconds())      
        if sp[-1]>timout_t:
            timeout['time'].append(t[idx-1])
            timeout['idx'].append(idx-1)
            timeout['timeout'].append((t[idx]-t[idx-1]).total_seconds())
    df = pd.DataFrame(timeout)
    return df, sp

def plot_traj(df_graf, titulo = 'Título'):    
    df = df_graf[df_graf['Dist']<4000]
    df_val = df[df['Valido']=='Valido']
    df_nval = df[df['Valido']!='Valido']
    fig1 = plt.figure()
    ax1 = fig1.subplots()
    ax1.plot(df_val['TR'],df_val['height'], '.', label='Válidos')
    ax1.plot(df_nval['TR'],df_nval['height'], '.', label='Não válidos')
    #ax1.plot(df['TR'],df['ramp_enu_z'], '.', label='z')
    ax1.set_xlabel('t(s)')
    ax1.set_ylabel('height(Km)')
    ax1.legend()
    plt.title(titulo)
    plt.xlim(0)

    plt.show()

def dellfiles(file):
    """
    Apaga arquivos em um determinado caminho.
    Parameters
    ----------
    file - caminho do arquivo
    """
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
    """
    Converte angulos em graus, minutos e segundos para float
    Parameters
    ----------
    s - string ex: -5°55'00.000
    Returns
    -------
    angulo : float
    """
    angle_gms = re.split('[°\' "]+', s)
    dd = 0
    for i in range(3):
        dd+= np.sign(float(angle_gms[0]))*abs(float(angle_gms[i])/(60**i))
    return dd

def fit_coord(coord_ref):
    """
    Função ajustar e converter arquivo de configuração dos pontos de referência
    """
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
    """
    Função principal, divide o arquivo e trata os dados
    Parameters
    ----------
    coord_ref - lista de strings - nomes dos arquivos
    """
    for line in file_names:  # varre a lista de arquivos
        print('Aguarde: Processando o arquivo: ' + line)
        df = pd.read_csv(line, skipinitialspace=True,
                    # skiprows=range(10),
                    dtype = str, delimiter=',' )
        
        # df é um pandas dataframe com o conteudo do primeiro arquivo .d
        df.columns = df.columns.str.replace(' ', '') # Retira espaços nos nomes de colunas
        for col in df.columns: # Retira espaços em todas as linha de todas as colunas
            df[col].str.strip()

        time_col_tmp = pd.to_datetime(df['Data']+ ',' +df['Hora'], format=time_format) # cria um vetor datetime

        end_idx = [] # inicializa lista
        # varre o dataframe a procura de pontos de descontinuidade
        # do tempo como marcador do fim da trajetória
        for idx in range(1,len(time_col_tmp)):  
            if time_col_tmp[idx]-time_col_tmp[idx-1]>timedelta(seconds=10):
                end_idx.append(idx)

        # verifica tops occoridos
        top_index_list = df[df['Sensor']=='TOPDEC-LIG'].index.values
                
        # varre os tops para dividir as trajetórias
        # *************************************************************
        for idx in range(len(top_index_list)):
            if not (idx>=len(end_idx)): # verifica se é o ultimo top do arquivo
                df_split = df.iloc[top_index_list[idx]+1:end_idx[idx],:] # trajetória vai até o final do arquivo
            else:
                df_split = df.iloc[top_index_list[idx]+1:,:] # trajetória termina com a descontinuidade de tempo 

            top_dec = df.loc[top_index_list[idx], 'Hora'] # salva a hora do top

            df_split = df_split.dropna(subset=['Sensor']) # remove linhas nulas
            df_split.reset_index(drop=True) # reseta o indice

            df_split = df_split[df_split['Sensor'].str.contains(sensor_sel)] # salva apenas o radar selecionado
            raw_file_name = output_folder + os.path.sep + 'file_' + line.split(os.path.sep)[-1]+ '_tr_' +str(idx) 

            csv_buffer = StringIO() # salva arquivo bruto dividido em buffer
            df_split.to_csv(csv_buffer, index = False)
            # *************************************************************            
            # Ler o arquivo salvo no buffer
            csv_buffer.seek(0) # Aponta para o inicio do buffer
            df_clear = pd.read_csv(csv_buffer, delimiter=',')            

            time_col_tmp = pd.to_datetime(df_clear['Data']+ ',' +df_clear['Hora'], format=time_format)  
            df_clear['datetime'] = time_col_tmp  # Cria coluna datetime

            df_clear['TR'] = (time_col_tmp - time_col_tmp[0]).dt.total_seconds() # Cria coluna de tempo relativo ao top

            # verifica timout de amostragem
            _ , sp = search_timeout(df_clear['datetime'], timout_det)
            df_clear['SP(s)'] = sp # cria coluna de tempo entre amostras            
            # np.round(np.arange(0,df_clear.shape[0])*sample_time, decimals=2) # Cria coluna tempo relativo ao top

            df_clear['S'] = df_clear['SAGADA'].str[1]
            df_clear['G'] = df_clear['SAGADA'].str[3]
            df_clear['D'] = df_clear['SAGADA'].str[5]   

            # Conversão ref sensor
            enu_x,enu_y,enu_z = pm.aer2enu(df_clear['Azim'], df_clear['Elev'], 1000*df_clear['Dist'], deg=False)
            df_clear['sens_enu_x'] = 0.001*enu_x
            df_clear['sens_enu_y'] = 0.001*enu_y
            df_clear['sens_enu_z'] = 0.001*enu_z

            # se o sensor for também a rampa não necessita de paralaxagem
            if c_ref.loc['SENS']['name']==c_ref.loc['RAMP']['name']:
                df_clear['ramp_enu_x'] = 0.001*enu_x
                df_clear['ramp_enu_y'] = 0.001*enu_y
                df_clear['ramp_enu_z'] = 0.001*enu_z
            else:
                # paralaxagem
                # Conversão para o ref ecef
                ecef_x,ecef_y,ecef_z = pm.enu2ecef(enu_x, enu_y, enu_z,
                                                    c_ref.loc['SENS']['lat'], c_ref.loc['SENS']['lon'], c_ref.loc['SENS']['height'],
                                                    ell=pm.Ellipsoid(model= ellipsoid),
                                                    deg=True)
                # Conversão para ref RAMPA
                ramp_enu_x,ramp_enu_y,ramp_enu_z= pm.ecef2enu(ecef_x, ecef_y, ecef_z,
                                                            c_ref.loc['RAMP']['lat'], c_ref.loc['RAMP']['lon'], c_ref.loc['RAMP']['height'],
                                                            ell=pm.Ellipsoid(model= ellipsoid),
                                                            deg=True)                                
                df_clear['ramp_enu_x'] = 0.001*ramp_enu_x
                df_clear['ramp_enu_y'] = 0.001*ramp_enu_y
                df_clear['ramp_enu_z'] = 0.001*ramp_enu_z

            # cria coluna do erro e norma do erro em comparação ao X Y Z do arquivo bruto
            df_clear['error_x'] = df_clear['ramp_enu_x']-df_clear['X_Rampa']
            df_clear['error_y'] = df_clear['ramp_enu_y']-df_clear['Y_Rampa']
            df_clear['error_z'] = df_clear['ramp_enu_z']-df_clear['Z_Rampa']
            df_clear['norm_error'] = np.linalg.norm(df_clear[['error_x','error_y','error_z']].values,axis=1)

            # Conversão coordenadas geodésicas
            lat, lon, alt = pm.enu2geodetic(1000*df_clear['ramp_enu_x'], 1000*df_clear['ramp_enu_y'], 1000*df_clear['ramp_enu_z'],
                                            c_ref.loc['RAMP']['lat'], c_ref.loc['RAMP']['lon'], c_ref.loc['RAMP']['height'],
                                            ell=pm.Ellipsoid(model= ellipsoid), 
                                            deg=True)
            
            # lat, lon, alt = pm.ecef2geodetic(ecef_x, ecef_y, ecef_z,
            #                                 ell=pm.Ellipsoid(model= ellipsoid),
            #                                 deg=True)
            
            df_clear['lat'] = lat
            df_clear['lon'] = lon
            df_clear['height'] = 0.001*alt            

            # calcula a distancia geodésica
            # preciso
            df_clear['DC'] = 0.001*pmv.vdist(c_ref.loc['RAMP']['lat'], c_ref.loc['RAMP']['lon'], lat, lon, ell=pm.Ellipsoid(model= ellipsoid))[0]

            # Salva dataframe completo
            df_clear.to_csv( raw_file_name + '_completo.csv',index = True)

            print('trajetória ' + str(idx) + ' extraída, analíze o arquivo de saída e o gráfico para determinar o TR de corte, após feche o gráfico')

            # gráfico para escolher ponto de truncar o final da trajetória
            # *************************************************************
            if plot:
                titulo = 'Completo: identifique TR de corte e feche'
                plot_traj(df_clear, titulo)

            # trunca trajetória no TR digitado
            tr_end = 0.0
            if truncar_traj:
                tr_end = input('Digite o TR(s) para truncar a trajetória ' + str(idx) + ':')
                try:
                    tr_end = float(tr_end)
                    try:
                        df_clear = df_clear[df_clear['TR']<=tr_end]
                        print("trajetória truncada em TR = " + str(tr_end) + ' feche o gráfico para continuar')
                        # gráfico após truncado
                        # *************************************************************
                        if plot:
                            titulo = 'Truncado no TR escolhido, feche para continuar'
                            plot_traj(df_clear,titulo)
                    except ValueError:
                        print("trajetória não truncada: valor digitado não está em TR")
                except ValueError:
                    print("trajetória não truncada: valor digitado não é um float")
            periodo_tr = str(df_clear.loc[0, 'Hora']) + ' a ' + str(df_clear.loc[len(df_clear.index)-1, 'Hora']) 


            # verifica timout de amostragem
            timout_o, sp = search_timeout(df_clear['datetime'], timout_det)
            if len(timout_o.index)>0: timout_o.to_csv(raw_file_name + '_timeout.csv')

            # faz a amostragem dos dados conforme selecionado
            # df_clear.reset_index(drop=True)
            df_clear = df_clear.iloc[::sample_step]

            # dataframe de relatório:
            # Colunas de origem 
            columns = ['Hora','TR','S','G','D','Snl_Rdo','Modo','Elev','Azim','Dist','ramp_enu_x','ramp_enu_y','ramp_enu_z', 'DC', 'height']

            # colunas de destino
            header = ['Tempo Universal','Tempo Relativo','S','G','D','S/R(dB)','Modo','Elev(rad)','Azim(rad)','Dist(km)','X_Rampa(Km)','Y_Rampa(Km)','Z_Rampa(Km)', 'DC_Rampa(Km)', 'Altitude(Km)']
            # salva csv
            df_clear.to_csv(raw_file_name + '_limpo.csv',
                        columns = columns, 
                        header= header,
                        float_format='%.5f',
                        index = False
                        )  

            # ****************************************************
            # Informações Importantes do Rastreio   resumo                  

            # remove outliers do radar (ultrapassagem do km 0)
            outliers = df_clear[df_clear['Dist']>4000]
            if len(outliers.index)>0:
                print('Presença de ' +str(len(outliers.index))+ ' outliers d>4000km em tr ' + str(idx))
            df_clear = df_clear[df_clear['Dist']<4000]
            
            # df_clear = df_clear[df_clear['height']>0]
            df_clear = df_clear[df_clear['Valido']=='Valido'] # Apenas válidos

            # df_clear.to_csv(raw_file_name + '_filter_brt.csv',
            #         columns = ['TR', 'ramp_enu_x', 'ramp_enu_y', 'ramp_enu_z'],
            #         header= None,
            #         float_format='%.2f',
            #         index = False
            #         )

            df_clear.reset_index(drop=True, inplace=True)

            dic = { 'TOP': [top_dec],
                    'height_max': [df_clear['height'].max()],
                    'TR_height_max': [df_clear.loc[df_clear['height'].idxmax(), 'TR']],
                    'ramp_z_max': [df_clear['ramp_enu_z'].max()],
                    'TR_z_max': [df_clear.loc[df_clear['Z_Rampa'].idxmax(), 'TR']],
                    'Data': [df_clear.loc[0, 'Data']],
                    'Período:' : [periodo_tr],
                    'n_outliers>4000' : len(outliers.index),
                    'DC_max' : [df_clear['DC'].max()],
                    'TR_end' : [tr_end],
                    'Ramp': [c_ref.loc['RAMP']['name']],
                    'Sens': [c_ref.loc['SENS']['name']],
                    'Timouts': [len(timout_o.index)]
                    }
            df_resume = pd.DataFrame(dic)

            df_resume.to_csv( raw_file_name + '_resumo.csv',
                    index = False,
                    float_format='%.5f'
                    )
            
            print('trajetória ' + str(idx) + ' concluída')

            

# Configurações
# ******************************************
# find -iname '*.d' -exec cp {} ~/Downloads/out/ \;
sample_time = 0.01 # Periodo de amostragem do arquivo .d

# passo para amostragem dos dados
sample_step = 1  # para amostragem de 10ms (sample_time = 0.01):
                                            # sample_step=1 para 10ms,
                                            # sample_step=10 para 100ms,
                                            # sample_step=100 para 1s

sensor_sel = 'Bearn-CLBI' # Sensor
ramp_sel = 'MRL-CLBI' # 'UNIVERSAL-CLBI' # 'LMU-CLBI-2' # MRL-CLBI # Rampa

ellipsoid = 'wgs72' # Ellipsoid

# Habilita a função de Truncar ou não a trajetória
truncar_traj = True

# Habilita plotar grafico a cada trajetória
plot = True

# Detecção de timout
timout_det = 0.012 # tempo em s a partir do qual é considerado para detecção de timout

# Arquivo de configuração de localização dos Sensores e das Rampas
c_ref = pd.read_csv( 'config/coord_ref.txt')

# Fim das configurações
# ******************************************

time_format = '%d/%m/%Y,%H:%M:%S:%f'

# Execução do script
print('\n')
print('arquivo coord_ref:')
print(c_ref)
c_ref = fit_coord(c_ref)
print('\n')
print('coordenadas em decimal:')
print(c_ref)
print('\n')

# filtra sensor e rampa selecionados
if len(c_ref[c_ref['name'].str.contains(ramp_sel)].index):
    if len(c_ref[c_ref['name'].str.contains(sensor_sel)].index):
        # c_ref = c_ref[c_ref['name'].str.contains(ramp_sel) + c_ref['name'].str.contains(sensor_sel)] 
        c_ref = pd.concat([c_ref[c_ref['name'].str.contains(ramp_sel)],
                           c_ref[c_ref['name'].str.contains(sensor_sel)]])
        c_ref.set_index([pd.Index(['RAMP', 'SENS'])], inplace=True)
    else:
        print('não existe no arquivo o sensor ' + sensor_sel )
        sys.exit()
else:
    print('não existe no arquivo a rampa ' + ramp_sel )
    sys.exit()


print('rampa e sensor selecionados:')
print(c_ref)
print('\n')

output_folder = 'output_clear_data'

dellfiles(output_folder + os.path.sep + '*.csv' )
# dellfiles(output_folder + os.path.sep + '*.dat' )

txt_files = glob.glob('input_raw_data/*.d')

# Função principal
split_data(txt_files)

print('processamento concluído')
print('\n')

# Fim