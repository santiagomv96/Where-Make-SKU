#######################################################
############## 1. IMPORTAR LIBRERIAS ##################
#######################################################

import pandas as pd
#Importar pyomo
import pyomo.environ as pyo
import re

#######################################################
####### 2. LECTURA Y PRE-PROCESAMIENTO DE DATOS #######
#######################################################
# Función que crea un diccionario para almacenar cada hoja del archivo de Excel en un dataframe
def Diccionario_dataframes_desde_excel(ruta_carpeta,nombre_archivo):
    
    """
    Función que crea un diccionario para almacenar cada hoja del archivo de Excel en un dataframe.
    
    Argumentos:
        ruta_carpeta (string): Ruta donde está ubicado el archivo de excel con los datos de entrada para la instancia o escenario que se desea modelar.
                             Ejemplo: 'C:\\Users\\Usuario1\\FolderModelo'
                             
        nombre_archivo (string):  Nombre del archivo de excel con los datos de entrada para la instancia o escenario que se desea modelar.                 
                            Ejemplo: 'Instancia1 PL.xlsx'
    
    Returns:
        dict: Diccionario con un dataframe por cada hoja del archivo de Excel.
    """           
    
    ruta_instancia=ruta_carpeta +r'\\' + nombre_archivo
    try:
        # Leer el archivo completo de Excel con todo su contenido
        excel_data = pd.read_excel(ruta_instancia, sheet_name=None)   
        
        # Crear un diccionario para almacenar cada hoja del archivo de Excel en un dataframe
        dfs = {}
        
        # Iterar sobre cada pestaña (hoja) del archivo de Excel
        for sheet_name, data in excel_data.items():
            # Crear un dataframe por cada hoja del archivo
            dfs[sheet_name] = pd.DataFrame(data)
        
        # Imprimir el nombre de cada hoja y los primeros 3 registros de cada dataframe creado (opcional)
        #for sheet_name, df in dfs.items():
        #    print(f"DataFrame for sheet: {sheet_name}")
        #    print(df.head(3))  # Print the first few rows of each DataFrame
            
        # Obtener la lista de dataframes creados
        #list_of_dfs = list(dfs.values())

        # Obtener la lista de los nombres de cada hoja del archivo de excel
        #list_of_sheet_names = list(dfs.keys())
        
        return dfs
    except Exception as e:
        print(f"Error al leer el archivo de Excel: {e}")
        return None


##########################################
########### 2.1. LEER INDICES ############
##########################################
def Leer_Indices(inputs_instancia_dfs):
    #Vehículos
    V=inputs_instancia_dfs['Vehiculos(V)']['Indice'].tolist()
    #Almacenes Regionales
    R=inputs_instancia_dfs['Destinos(R)']['Indice'].tolist()
    #Clientes
    C=inputs_instancia_dfs['Clientes(C)']['Indice'].tolist()
    #Plantas
    O=inputs_instancia_dfs['Plantas(O)']['Indice'].tolist()
    #Cedis Nacionales
    N=inputs_instancia_dfs['CedisNacionales(N)']['Indice'].tolist()
    #Periodos
    T=inputs_instancia_dfs['Periodos(T)']['Indice'].tolist()
    #Hubs
    H=inputs_instancia_dfs['Hubs(H)']['Indice'].tolist()
    #Frecuencias
    F=inputs_instancia_dfs['Frecuencias(F)']['Indice'].tolist()
    #Productos
    P=inputs_instancia_dfs['GruposProductos(P)']['Indice'].tolist()
    return V,R,C,O,N,T,H,F,P


#############################################################################################################
####### 2.2. CREACIÓN DE ARREGLOS (LISTAS DE TUPLAS) SOLO CON COMBINACIONES VIABLES Y DICCIONARIOS     ######
####### CON COSTOS DE TRANSPORTE, FLUJOS REALES (BASELINE) POR COMBINACION 'ORIGEN-DESTINO-VEHICULO'   ######
####### Y FRECUENCIAS DE VISITA ACTUALES (BASLINE)                                                     ######
#############################################################################################################


#Crear malla de combinaciones posibles de destinos y productos basados en la demanda, para un periodo específico
def Malla_P_R(df_dict,t):
    """Función que crea la malla de combinaciones posibles de destinos y productos basados los datos de entrada:':':',''' para un periodo específico.
    Argumentos:
            df_dict:
                    Descripción:   Diccionario que contiene los dataframes (un dataframe por cada pestaña del archivo de inputs) 
                                   con todos los datos de entrada de la instancia o escenario que se desea modelar.
                    Tipo de dato:  dict 
            t:      
                    Descripción:   indice númerico que indica el periodo que se desea modelar 
                    Tipo de dato:  int
    """
    D=df_dict['Demanda(D)']
    H=df_dict['Hubs(H)'][['Indice']].rename(columns={'Indice':'Indice Hub'})
    F=df_dict['Frecuencias(F)'][['Indice']].rename(columns={'Indice':'Frecuencia'})
    # Cargar el dataframe que contiene los Costos de transporte de Hub a almacenes regionales y filtrarlo por el periodo deseado 
    Costos_HR_df=df_dict['CostosTTE(H-R)'][df_dict['CostosTTE(H-R)']['Indice Periodo']==t]
     
    #Combinaciones 'Producto - Almacen Regional'
    P_R_df=D[['Indice Producto','Indice Cliente']][D['Indice Periodo']==t].drop_duplicates()
    P_R=list(P_R_df.itertuples(index=False, name=None))
    
    #Combinaciones 'Producto - Cliente'
    P_C=P_R
    P_R_C=list(P_R_df[['Indice Producto','Indice Cliente','Indice Cliente']].itertuples(index=False, name=None))
    #Combinaciones Producto-Hub-Cliente
    """ Para realizar un inner join en pandas sin usar la cláusula on, y así añadir una nueva columna a todos los registros del DataFrame, 
    puedes usar el método merge con la opción how='cross'. Este tipo de join, conocido como "cross join" o "producto cartesiano", 
    combina cada fila del primer DataFrame con cada fila del segundo DataFrame. """
    
    #P_R_H_df=pd.merge(P_R_df,H,how='cross')
    P_R_H_df=pd.merge(P_R_df,Costos_HR_df,left_on='Indice Cliente',right_on='Indice Destino', how='inner')
    P_H_R=list(P_R_H_df[['Indice Producto','Indice Hub','Indice Cliente']].drop_duplicates().itertuples(index=False, name=None))
    
    #Combinaciones producto-hub
    P_H=list(P_R_H_df[['Indice Producto','Indice Hub']].drop_duplicates().itertuples(index=False, name=None))
    #Combinaciones Producto-Almacen Regional-Frecuencia
    P_R_F_df=pd.merge(P_R_df,F,how='cross')
    P_R_F=list(P_R_F_df[['Indice Producto','Indice Cliente','Frecuencia']].itertuples(index=False, name=None))
    
    return P_R,P_C,P_R_C,P_H_R,P_R_F,P_H

#Crear malla de combinaciones posibles de plantas a Cedis Nacionales por Producto y vehiculo, para un periodo específico
def Malla_P_O_N_V(df_dict,t):
    """
    Función que crea la malla de combinaciones posibles de de plantas a Cedis Nacionales por Producto y vehiculo, para un periodo específico.
    Argumentos:
            df_dict:
                    Descripción:   Diccionario que contiene los dataframes (un dataframe por cada pestaña del archivo de inputs) 
                                   con todos los datos de entrada de la instancia o escenario que se desea modelar.
                    Tipo de dato:  dict 
            t:      
                    Descripción:   indice númerico que indica el periodo que se desea modelar 
                    Tipo de dato:  int
    """
    # Cargar el dataframe que contiene el detalle de productos fabricados en cada planta
    OrigenP_df=df_dict['OrigenProductos']
    #Crear lista de los indices de las plantas definidad en Origen Productos (es decir, las que producen por lo menos un producto)
    PlantasActivas=df_dict['OrigenProductos']['Indice Planta'].unique().tolist()
    # Cargar el dataframe que contiene los indices de las frecuencias de abastecimiento
    F=df_dict['Frecuencias(F)'][['Indice']].rename(columns={'Indice':'Frecuencia'})
    # Cargar el dataframe que contiene los indices de los hubs
    H=df_dict['Hubs(H)'][['Indice']].rename(columns={'Indice':'Indice Hub'})
    
    # Cargar el dataframe que contiene los detalles de los productos
    P=df_dict['GruposProductos(P)'].rename(columns={'Indice':'Indice Producto'})
    # Cargar el dataframe que contiene los detalles de los Cedis Nacionales
    N=df_dict['CedisNacionales(N)'].rename(columns={'Indice':'Indice Cedi Nacional'})
    
    # Cargar el dataframe que contiene los Costos de transporte de Plantas a Cedis nacionales y filtrarlo por el periodo deseado y plantas activas
    #Costos_O_N_V_df=df_dict['CostosTTE(O-N)'][df_dict['CostosTTE(O-N)']['Indice Planta'].isin(PlantasActivas) & df_dict['CostosTTE(O-N)']['Indice Periodo']==t]
    Costos_O_N_V_df=df_dict['CostosTTE(O-N)'][df_dict['CostosTTE(O-N)']['Indice Periodo']==t]
    Costos_O_N_V_df=Costos_O_N_V_df[Costos_O_N_V_df['Indice Planta'].isin(PlantasActivas)]
    
    #crear diccionario con el costo de transporte por cada combinación 'planta-cedi nacional-vehiculo'
    Costos_ON_dict={(int(row['Indice Planta']), int(row['Indice Cedi Nacional']), int(row['Indice Vehiculo'])): row['Costo Transporte Fijo'] for _, row in Costos_O_N_V_df.iterrows()}
    
    # Cargar el dataframe que contiene los Costos de transporte de Plantas a Hub y filtrarlo por el periodo deseado 
    #Costos_O_H_V_df=df_dict['CostosTTE(O-H)'][df_dict['CostosTTE(O-H)']['Indice Planta'].isin(PlantasActivas) & df_dict['CostosTTE(O-H)']['Indice Periodo']==t]
    Costos_O_H_V_df=df_dict['CostosTTE(O-H)'][df_dict['CostosTTE(O-H)']['Indice Periodo']==t]
    Costos_O_H_V_df=Costos_O_H_V_df[Costos_O_H_V_df['Indice Planta'].isin(PlantasActivas)]
    
    
    #crear diccionario con el costo de transporte por cada combinación 'planta-hub-vehiculo'
    Costos_OH_dict={(int(row['Indice Planta']), int(row['Indice Hub']), int(row['Indice Vehiculo'])): row['Costo Transporte Fijo'] for _, row in Costos_O_H_V_df.iterrows()}
    
    # Cargar el dataframe que contiene los Costos de transporte de Cedis nacionales a Hub y filtrarlo por el periodo deseado 
    Costos_N_H_V_df=df_dict['CostosTTE(N-H)'][df_dict['CostosTTE(N-H)']['Indice Periodo']==t]
    #crear diccionario con el costo de transporte por cada combinación 'cedi nacional-hub-vehiculo'
    Costos_NH_dict={(int(row['Indice Cedi Nacional']), int(row['Indice Hub']), int(row['Indice Vehiculo'])): row['Costo Transporte Fijo'] for _, row in Costos_N_H_V_df.iterrows()}
    
    # Cargar dataframe que contiene la cantidad de flujos reales (baseline) desde plantas a Cedis Nacionales por vehículo y filtrarlo por el periodo deseado 
    Flujos_ON_df=df_dict['FlujosReales(O-N)'][df_dict['FlujosReales(O-N)']['Indice Periodo']==t]
    #crear diccionario con el flujo real (baseline) cada combinación 'producto-planta-cedi nacional-vehiculo'
    Flujos_ON_dict={(int(row['Indice Producto']),int(row['Indice Planta']), int(row['Indice Cedi Nacional']), 
                     int(row['Indice Vehiculo'])): row['Cantidad (Unidades)'] for _, row in Flujos_ON_df.iterrows()}
    
    
    #Dataframe combinando Origen productos y lineas habilitadas de plantas a Cedis Nacionales por producto y vehiculo
    P_O_N_V_Aux1_df=pd.merge(OrigenP_df, Costos_O_N_V_df, on='Indice Planta', how='inner')[['Indice Producto','Indice Planta', 'Indice Cedi Nacional','Indice Vehiculo','Indice Periodo']]
    # Merge adicionales por negocio para garantizar que los productos de plantas externas vayan al Cedi Nacional adecuado
    P_O_N_V_Aux2_df=pd.merge(P_O_N_V_Aux1_df, P, on='Indice Producto', how='inner')[['Indice Producto','Negocio','Indice Planta', 'Indice Cedi Nacional','Indice Vehiculo','Indice Periodo']]
    P_O_N_V_df=pd.merge(P_O_N_V_Aux2_df, N, on=['Indice Cedi Nacional','Negocio'], how='inner')[['Indice Producto','Indice Planta', 'Indice Cedi Nacional','Indice Vehiculo','Indice Periodo']]
    
    P_O_N_V=list(P_O_N_V_df[['Indice Producto','Indice Planta', 'Indice Cedi Nacional','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None))
    
    P_O_N= list(P_O_N_V_df[['Indice Producto','Indice Planta', 'Indice Cedi Nacional']].drop_duplicates().itertuples(index=False, name=None))
    
    O_N_V=list(P_O_N_V_df[['Indice Planta', 'Indice Cedi Nacional','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None))
    
    O_V_df=P_O_N_V_df[['Indice Planta','Indice Vehiculo']].drop_duplicates()
    
    #O_H_V_df=pd.merge(O_V_df,H,how='cross')[['Indice Planta','Indice Hub','Indice Vehiculo']]
    O_H_V_df=Costos_O_H_V_df[['Indice Planta','Indice Hub','Indice Vehiculo']]
    O_H_V=list(O_H_V_df.drop_duplicates().itertuples(index=False, name=None))
    
    N_V_df=P_O_N_V_df[['Indice Cedi Nacional','Indice Vehiculo']].drop_duplicates()
    #N_H_V_df=pd.merge(N_V_df,H,how='cross')[['Indice Cedi Nacional','Indice Hub','Indice Vehiculo']]
    N_H_V_df=Costos_N_H_V_df[['Indice Cedi Nacional','Indice Hub','Indice Vehiculo']]
    N_H_V=list(N_H_V_df.drop_duplicates().itertuples(index=False, name=None))
    
    P_O_V_df=P_O_N_V_df[['Indice Producto','Indice Planta','Indice Vehiculo']].drop_duplicates()
    #P_O_H_V_df=pd.merge(P_O_V_df,H,how='cross')[['Indice Producto','Indice Planta','Indice Hub','Indice Vehiculo']]
    P_O_H_V_df=pd.merge(OrigenP_df,Costos_O_H_V_df,on='Indice Planta',how='inner')[['Indice Producto','Indice Planta','Indice Hub','Indice Vehiculo']]
    P_O_H_V=list(P_O_H_V_df.drop_duplicates().itertuples(index=False, name=None))
    
    P_N_V_df=P_O_N_V_df[['Indice Producto','Indice Cedi Nacional','Indice Vehiculo']].drop_duplicates()
    #P_N_H_V_df=pd.merge(P_N_V_df,H,how='cross')[['Indice Producto','Indice Cedi Nacional','Indice Hub','Indice Vehiculo']]
    P_N_H_V_df=pd.merge(P_N_V_df[['Indice Producto','Indice Cedi Nacional']],Costos_N_H_V_df,
                        on='Indice Cedi Nacional',how='inner')[['Indice Producto','Indice Cedi Nacional','Indice Hub','Indice Vehiculo']]
    P_N_H_V=list(P_N_H_V_df.drop_duplicates().itertuples(index=False, name=None))
    
    
    #Filtrar diccionarios de parámetros para garantizar que se carguen solo los datos de combinaciones factibles
    Costos_ON_dict={clave: valor for clave, valor in Costos_ON_dict.items() if clave in O_N_V}
    Costos_OH_dict={clave: valor for clave, valor in Costos_OH_dict.items() if clave in O_H_V}
    Costos_NH_dict={clave: valor for clave, valor in Costos_NH_dict.items() if clave in N_H_V}
    Flujos_ON_dict={clave: valor for clave, valor in Flujos_ON_dict.items() if clave in P_O_N_V}
    
    
    return P_O_N_V,P_O_N,O_N_V,O_H_V,N_H_V,P_O_H_V,P_N_H_V,Costos_ON_dict,Costos_OH_dict,Costos_NH_dict,Flujos_ON_dict,P_O_N_V_df

#Crear malla de combinaciones posibles de Cedis Nacionales y Almacenes Regionales 
#a partir de la demanda y el origen de los productos, para un periodo específico
def Malla_P_N_R_F_V(df_dict,t):
    """
    Función que crea la malla de combinaciones posibles de Cedis Nacionales y Almacenes Regionales 
        a partir de la demanda y el origen de los productos, para un periodo específico.
    Argumentos:
            df_dict:
                    Descripción:   Diccionario que contiene los dataframes (un dataframe por cada pestaña del archivo de inputs) 
                                   con todos los datos de entrada de la instancia o escenario que se desea modelar.
                    Tipo de dato:  dict 
            t:      
                    Descripción:   indice númerico que indica el periodo que se desea modelar 
                    Tipo de dato:  int
    """
    # llamar el dataframe que contiene las combinaciones 'producto-planta-cedi nacional-vehiculo' 
    P_O_N_V_df=Malla_P_O_N_V(df_dict,t)[11]
    # Cargar el dataframe que contiene los indices de las frecuencias de abastecimiento
    F=df_dict['Frecuencias(F)'][['Indice']].rename(columns={'Indice':'Frecuencia'})
    # Cargar el dataframe que contiene los indices de los hubs
    H=df_dict['Hubs(H)'][['Indice']].rename(columns={'Indice':'Indice Hub'})
    # Cargar el dataframe que contiene la demanda por producto y almacen regional
    D=df_dict['Demanda(D)'][df_dict['Demanda(D)']['Indice Periodo']==t]
    
    # Cargar el dataframe que contiene los Costos de transporte de Cedis nacionales a almacenes regionales y filtrarlo por el periodo deseado 
    Costos_NR_df=df_dict['CostosTTE(N-R)'][df_dict['CostosTTE(N-R)']['Indice Periodo']==t]
    #crear diccionario con el costo de transporte por cada combinación 'cedi nacional-almacen regional-vehiculo'
    Costos_NR_dict={(int(row['Indice Cedi Nacional']), int(row['Indice Destino']), int(row['Indice Vehiculo'])): row['Costo Transporte Fijo'] for _, row in Costos_NR_df.iterrows()}
    
    # Cargar el dataframe que contiene los Costos de transporte de Hub a almacenes regionales y filtrarlo por el periodo deseado 
    Costos_HR_df=df_dict['CostosTTE(H-R)'][df_dict['CostosTTE(H-R)']['Indice Periodo']==t]
    #crear diccionario con el costo de transporte por cada combinación 'hub-almacen regional--vehiculo'
    Costos_HR_dict={(int(row['Indice Hub']), int(row['Indice Destino']), int(row['Indice Vehiculo'])): row['Costo Transporte Fijo'] for _, row in Costos_HR_df.iterrows()}
    
    # Cargar dataframe que contiene la cantidad de flujos reales (baseline) desde Cedis Nacionales a almacenes regionales por vehículo y filtrarlo por el periodo deseado 
    Flujos_NR_df=df_dict['FlujosReales(N-R)'][df_dict['FlujosReales(N-R)']['Indice Periodo']==t]
    #crear diccionario con el flujo real (baseline) cada combinación 'producto-planta-cedi nacional-vehiculo'
    Flujos_NR_dict={(int(row['Indice Producto']), int(row['Indice Cedi Nacional']),int(row['Indice Destino']), 
                     int(row['Indice Vehiculo'])): row['Cantidad (Unidades)'] for _, row in Flujos_NR_df.iterrows()}
    
    #cargar el dataframe que contiene las frecuencias de visita directas actuales y filtrarlo por el periodo deseado
    FrecuenciasVisitaNR_df=df_dict['FrecuenciaVisitaDirecta(FV)'][df_dict['FrecuenciaVisitaDirecta(FV)']['Indice Periodo']==t]
    #crear diccionario con la frecuencia de visita real (baseline) para cada combinación 'cedi nacional-almacen regional'
    FrecuenciasVisitaNR_dict={(int(row['Indice Cedi Nacional']), int(row['Indice Destino'])): row['Frecuencia Visita'] for _, row in FrecuenciasVisitaNR_df.iterrows()}
  
    #P_N_R_V_df=pd.merge(P_O_N_V_df,D ,on=['Indice Producto','Indice Periodo'],
    #                                 how='inner')[['Indice Producto','Indice Cedi Nacional','Indice Cliente','Indice Vehiculo']].rename(columns={'Indice Cliente':'Indice Destino'})
    
    P_N_R_V_df=pd.merge(P_O_N_V_df[['Indice Producto','Indice Cedi Nacional','Indice Periodo']].drop_duplicates(),Costos_NR_df,
                        on=['Indice Cedi Nacional','Indice Periodo'],how='inner')[['Indice Producto','Indice Cedi Nacional','Indice Destino','Indice Vehiculo']]
    
    
    """ Para realizar un inner join en pandas sin usar la cláusula "on", y así añadir una nueva columna a todos los registros del DataFrame, 
    puedes usar el método merge con la opción how='cross'. Este tipo de join, conocido como "cross join" o "producto cartesiano", 
    combina cada fila del primer DataFrame con cada fila del segundo DataFrame. """
    P_N_R_F_V_df=pd.merge(P_N_R_V_df,F,how='cross')[['Indice Producto','Indice Cedi Nacional','Indice Destino','Frecuencia','Indice Vehiculo']].drop_duplicates()
    
    P_N_R_V=list(P_N_R_V_df.drop_duplicates().itertuples(index=False, name=None))
    P_N_R_F_V=list(P_N_R_F_V_df.drop_duplicates().itertuples(index=False, name=None))
    P_N_R=list(P_N_R_V_df[['Indice Producto','Indice Cedi Nacional','Indice Destino']].drop_duplicates().itertuples(index=False, name=None))
    N_R_V=list(P_N_R_V_df[['Indice Cedi Nacional','Indice Destino','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None))
    N_R=list(P_N_R_V_df[['Indice Cedi Nacional','Indice Destino']].drop_duplicates().itertuples(index=False, name=None))
    P_N=list(P_N_R_V_df[['Indice Producto','Indice Cedi Nacional']].drop_duplicates().itertuples(index=False, name=None))
    P_R_C_V=list(P_N_R_V_df[['Indice Producto','Indice Destino','Indice Destino','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None))
    
    R_V_df=P_N_R_V_df[['Indice Destino','Indice Vehiculo']].drop_duplicates()
    #H_R_V_df=pd.merge(H,R_V_df,how='cross')[['Indice Hub','Indice Destino','Indice Vehiculo']]
    H_R_V_df=Costos_HR_df[['Indice Hub','Indice Destino','Indice Vehiculo']].drop_duplicates()
    H_R_V=list(H_R_V_df.itertuples(index=False, name=None))
    
    P_R_F_V_df=P_N_R_F_V_df[['Indice Producto','Indice Destino','Frecuencia','Indice Vehiculo']].drop_duplicates()
    P_R_F_V = list(P_R_F_V_df.drop_duplicates().itertuples(index=False, name=None))
    
    #P_H_R_F_V_df=pd.merge(P_R_F_V_df,H,how='cross')[['Indice Producto','Indice Hub','Indice Destino','Frecuencia','Indice Vehiculo']]
    P_H_R_F_V_df=pd.merge(P_R_F_V_df[['Indice Producto','Indice Destino','Frecuencia']].drop_duplicates(),Costos_HR_df,on=['Indice Destino'],
                          how='inner')[['Indice Producto','Indice Hub','Indice Destino','Frecuencia','Indice Vehiculo']]
    P_H_R_F_V=list(P_H_R_F_V_df.drop_duplicates().itertuples(index=False, name=None))
    
    
    
    #Filtrar diccionarios de parámetros para garantizar que se carguen solo los datos de combinaciones factibles
    Costos_NR_dict={clave: valor for clave, valor in Costos_NR_dict.items() if clave in N_R_V}
    Costos_HR_dict={clave: valor for clave, valor in Costos_HR_dict.items() if clave in H_R_V}
    Flujos_NR_dict={clave: valor for clave, valor in Flujos_NR_dict.items() if clave in P_N_R_V}
    FrecuenciasVisitaNR_dict={clave: valor for clave, valor in FrecuenciasVisitaNR_dict.items() if clave in N_R}
      
    return P_N_R_V,P_N_R,N_R_V,N_R,P_N,P_R_C_V,P_N_R_F_V,H_R_V,P_H_R_F_V,P_R_F_V,Costos_NR_dict,Costos_HR_dict,Flujos_NR_dict,FrecuenciasVisitaNR_dict

#Crear malla de combinaciones posibles entre Almacenes Regionales 
#a partir de los costos de transporte, destinos y productos
def Malla_P_R_R_V(df_dict,t):
    """
    Función que crea la malla de combinaciones posibles entre Almacenes Regionales 
      a partir de los costos de transporte, destinos y productos.
    Argumentos:
            df_dict:
                    Descripción:   Diccionario que contiene los dataframes (un dataframe por cada pestaña del archivo de inputs) 
                                   con todos los datos de entrada de la instancia o escenario que se desea modelar.
                    Tipo de dato:  dict 
            t:      
                    Descripción:   indice númerico que indica el periodo que se desea modelar 
                    Tipo de dato:  int
    """
    # Cargar el dataframe que contiene los indices de los almacenes regionales
    R=df_dict['Destinos(R)']
    # verticalizar niveles de cada combinación 'almacen regional-negocio'
    R_melted = R.melt(id_vars=['Indice'], 
                  value_vars=['Nivel Cárnicos','Nivel Galletas','Nivel Chocolates','Nivel Café'], 
                  var_name='Negocio', value_name='Nivel Destino-Negocio')
    R_melted['Negocio'] =R_melted['Negocio'].str.replace('Nivel ', '')
    
    # Cargar el dataframe que contiene los indices de los productos
    P=df_dict['GruposProductos(P)'][['Indice','Negocio']].rename(columns={'Indice':'Indice Producto'})
    # Cargar el dataframe que contiene los indices de las frecuencias de abastecimiento
    F=df_dict['Frecuencias(F)'][['Indice']].rename(columns={'Indice':'Frecuencia'})
    
    
    # Cargar el dataframe que contiene las combinaciones posibles de multiparadas y redespachos
    Rede_Mult= df_dict['Redespachos_Multiparadas'][df_dict['Redespachos_Multiparadas']['Indice Periodo']==t].drop_duplicates()
    
    # Cargar el dataframe que contiene la demanda por producto y almacen regional, y filtar el periodo deseado
    D=df_dict['Demanda(D)'][['Indice Producto','Indice Cliente']][df_dict['Demanda(D)']['Indice Periodo']==t].drop_duplicates()
    #Demanda con detalles del producto
    D_P=pd.merge(D,P, on='Indice Producto',how='left')
    
        
    #Cargar el dataframe que contiene los Costos de transporte de almacenes regionales  y filtrarlo por el periodo deseado
    Costos_RR_df=df_dict['CostosTTE(R-R)'][['Indice Destino Nivel Previo','Indice Destino Nivel Posterior',
                                               'Indice Vehiculo','Costo Transporte Fijo']][df_dict['CostosTTE(R-R)']['Indice Periodo']==t].drop_duplicates()
    #crear diccionario con el costo de transporte por cada combinación de almacenes regionales y vehiculos
    Costos_RR_dict={(int(row['Indice Destino Nivel Previo']), int(row['Indice Destino Nivel Posterior']),
                     int(row['Indice Vehiculo'])): row['Costo Transporte Fijo'] for _, row in Costos_RR_df.iterrows()}
    
    
    # Cargar dataframe que contiene la cantidad de flujos reales (baseline) entre almacenes regionales por vehículo y filtrarlo por el periodo deseado 
    Flujos_RR_df=df_dict['FlujosReales(R-R)'][df_dict['FlujosReales(R-R)']['Indice Periodo']==t]
    #crear diccionario con el flujo real (baseline) cada combinación 'producto-almacenes regionales-vehiculo'
    Flujos_RR_dict={(int(row['Indice Producto']), int(row['Indice Destino Nivel Previo']),int(row['Indice Destino Nivel Posterior']), 
                     int(row['Indice Vehiculo'])): row['Cantidad (Unidades)'] for _, row in Flujos_RR_df.iterrows()} 
    
        
    #cargar el dataframe que contiene las frecuencias de visita indirectas actuales y filtrarlo por el periodo deseado
    FrecuenciasVisita_RR_df=df_dict['FrecuenciaVisitaIndirecta(FV)'][df_dict['FrecuenciaVisitaIndirecta(FV)']['Indice Periodo']==t]
    #crear diccionario con el la frecuencia de visita real (baseline) para cada combinación 'almacen regional nivel 1-almacen regional nivel 2'
    FrecuenciasVisita_RR_dict={(int(row['Indice Destino Nivel Previo']), int(row['Indice Destino Nivel Posterior'])): row['Frecuencia Visita'] for _, row in FrecuenciasVisita_RR_df.iterrows()}
    
    #Obtener el nivel del almacen regional de origen para cada negocio
    Niveles_Origen=pd.merge(Costos_RR_df,R_melted ,left_on='Indice Destino Nivel Previo',right_on='Indice', how='inner')
    #Obtener el nivel del almacen regional de destino para cada negocio
    Niveles_Origen_Destino=pd.merge(Niveles_Origen,R_melted ,left_on=['Indice Destino Nivel Posterior','Negocio'],
                        right_on=['Indice','Negocio'], 
                        how='inner',suffixes=['_Origen','_Destino'])[['Indice Destino Nivel Previo',
                                                           'Indice Destino Nivel Posterior','Negocio', 
                                                           'Nivel Destino-Negocio_Origen','Nivel Destino-Negocio_Destino','Indice Vehiculo']]
    
    #Lista con todos los almacenes regionales de nivel 4.   
    M_list= Niveles_Origen_Destino[Niveles_Origen_Destino['Nivel Destino-Negocio_Destino']==4]['Indice Destino Nivel Posterior'].tolist()
    #Lista con todos los almacenes regionales de nivel 3.   
    L_list= Niveles_Origen_Destino[Niveles_Origen_Destino['Nivel Destino-Negocio_Destino']==3]['Indice Destino Nivel Posterior'].tolist()
    #Lista con todos los almacenes regionales de nivel 2.   
    K_list= Niveles_Origen_Destino[Niveles_Origen_Destino['Nivel Destino-Negocio_Destino']==2]['Indice Destino Nivel Posterior'].tolist()
    
    #Dataframe con el listado de todos los productos demandados en regionales de nivel 4.   
    D_P_M_df=D_P[D_P['Indice Cliente'].isin(M_list)].drop_duplicates()
    
    #Dataframe con el listado de todos los productos que pasan por regionales de nivel 3.   
    D_P_L_df=D_P[D_P['Indice Cliente'].isin(L_list+M_list)].drop_duplicates()
    
    #Dataframe con el listado de todos los productos que pasan por regionales de nivel 2.   
    D_P_K_df=D_P[D_P['Indice Cliente'].isin(L_list+M_list+K_list)].drop_duplicates()
    
    #Dataframe con el listado de todos los productos que se abastecen directo a regionales de nivel 1.
    D_P_R_Dir_df=D_P[~D_P['Indice Cliente'].isin(L_list+M_list+K_list)].drop_duplicates()
    P_R_Dir=list(D_P_R_Dir_df[['Indice Producto','Indice Cliente']].drop_duplicates().itertuples(index=False, name=None))
        
    #############################                 
    #Obtener combinaciones de Producto-Origen_destino-Vehiculo para los arcos habilitados entre almacenes regionales nivel 1 y nivel 2 (multiparadas y redespachos)
    P_J_K_V_df=pd.merge(Niveles_Origen_Destino,D_P_K_df, left_on=['Indice Destino Nivel Posterior','Negocio'],
                        right_on=['Indice Cliente','Negocio'],how='inner')
    
    P_J_K_V_df=P_J_K_V_df[(P_J_K_V_df['Nivel Destino-Negocio_Origen']==1) &
                                      (P_J_K_V_df['Nivel Destino-Negocio_Destino']==2)]
    
    # Obtener detalle para saber si el arco corresponde a un modelo de multiparada o redespacho
    P_J_K_V_df=pd.merge(P_J_K_V_df,Rede_Mult, on = ['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior'], 
                        how='inner')[['Indice Producto','Indice Destino Nivel Previo', 'Indice Destino Nivel Posterior', 'Indice Vehiculo','Tipo Ruta']]
    
       
    ############################
    #Obtener combinaciones de Producto-Origen_destino-Vehiculo para los arcos habilitados entre almacenes regionalesnivel 2 y nivel 3 (multiparadas)
    P_K_L_V_df=pd.merge(Niveles_Origen_Destino,D_P_L_df, left_on=['Indice Destino Nivel Posterior','Negocio'],
                        right_on=['Indice Cliente','Negocio'],how='inner')
    P_K_L_V_df=P_K_L_V_df[(P_K_L_V_df['Nivel Destino-Negocio_Origen']==2) &
                                      (P_K_L_V_df['Nivel Destino-Negocio_Destino']==3)][['Indice Producto','Indice Destino Nivel Previo', 
                                                                                         'Indice Destino Nivel Posterior', 
                                                                                         'Indice Vehiculo']]
                                      
    # Obtener detalle para saber si el arco corresponde a un modelo de multiparada o redespacho
    P_K_L_V_df=pd.merge(P_K_L_V_df,Rede_Mult, on = ['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior'], 
                        how='inner')[['Indice Producto','Indice Destino Nivel Previo', 'Indice Destino Nivel Posterior', 'Indice Vehiculo','Tipo Ruta']]
    
    
    #############################
    # Obtener combinaciones de Producto-Origen_destino-Vehiculo para los arcos habilitados entre almacenes regionalesnivel 3 y nivel 4 (multiparadas)
    P_L_M_V_df=pd.merge(Niveles_Origen_Destino,D_P_M_df, left_on=['Indice Destino Nivel Posterior','Negocio'],
                        right_on=['Indice Cliente','Negocio'],how='inner')
    P_L_M_V_df=P_L_M_V_df[(P_L_M_V_df['Nivel Destino-Negocio_Origen']==3) &
                                      (P_L_M_V_df['Nivel Destino-Negocio_Destino']==4)][['Indice Producto','Indice Destino Nivel Previo', 
                                                                                         'Indice Destino Nivel Posterior', 
                                                                                         'Indice Vehiculo']]
    # Obtener detalle para saber si el arco corresponde a un modelo de multiparada o redespacho
    P_L_M_V_df=pd.merge(P_L_M_V_df,Rede_Mult, on = ['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior'], 
                        how='inner')[['Indice Producto','Indice Destino Nivel Previo', 'Indice Destino Nivel Posterior', 'Indice Vehiculo','Tipo Ruta']]
    
    
    ############################
        
    P_J_K_V= list(P_J_K_V_df[['Indice Producto','Indice Destino Nivel Previo', 'Indice Destino Nivel Posterior','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None))   
    P_K_L_V= list(P_K_L_V_df[['Indice Producto','Indice Destino Nivel Previo', 'Indice Destino Nivel Posterior','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None))  
    P_L_M_V= list(P_L_M_V_df[['Indice Producto','Indice Destino Nivel Previo', 'Indice Destino Nivel Posterior','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None))  
    
    J_K=list(P_J_K_V_df[['Indice Destino Nivel Previo', 'Indice Destino Nivel Posterior']].drop_duplicates().itertuples(index=False, name=None)) 
    K_L=list(P_K_L_V_df[['Indice Destino Nivel Previo', 'Indice Destino Nivel Posterior']].drop_duplicates().itertuples(index=False, name=None)) 
    L_M=list(P_L_M_V_df[['Indice Destino Nivel Previo', 'Indice Destino Nivel Posterior']].drop_duplicates().itertuples(index=False, name=None)) 
    
    P_J=list(P_J_K_V_df[['Indice Producto','Indice Destino Nivel Previo']].drop_duplicates().itertuples(index=False, name=None)) 
    P_K=list(P_J_K_V_df[['Indice Producto', 'Indice Destino Nivel Posterior']].drop_duplicates().itertuples(index=False, name=None)) 
    P_L=list(P_K_L_V_df[['Indice Producto','Indice Destino Nivel Posterior']].drop_duplicates().itertuples(index=False, name=None)) 
    P_M=list(P_L_M_V_df[['Indice Producto','Indice Destino Nivel Posterior']].drop_duplicates().itertuples(index=False, name=None)) 
    P_K_Rede=list(P_J_K_V_df[P_J_K_V_df['Tipo Ruta']=='Redespacho'][['Indice Producto','Indice Destino Nivel Posterior']].drop_duplicates().itertuples(index=False, name=None)) 
    P_K_Mult=list(P_J_K_V_df[P_J_K_V_df['Tipo Ruta']=='Multiparada'][['Indice Producto','Indice Destino Nivel Posterior']].drop_duplicates().itertuples(index=False, name=None))
    
    J_K_V=list(P_J_K_V_df[['Indice Destino Nivel Previo', 'Indice Destino Nivel Posterior','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None)) 
    K_L_V=list(P_K_L_V_df[['Indice Destino Nivel Previo', 'Indice Destino Nivel Posterior','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None)) 
    L_M_V=list(P_L_M_V_df[['Indice Destino Nivel Previo', 'Indice Destino Nivel Posterior','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None)) 
    
    P_J_K=list(P_J_K_V_df[['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior']].drop_duplicates().itertuples(index=False, name=None)) 
    P_K_L=list(P_K_L_V_df[['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior']].drop_duplicates().itertuples(index=False, name=None)) 
    P_L_M=list(P_L_M_V_df[['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior']].drop_duplicates().itertuples(index=False, name=None)) 
    
    P_J_V=list(P_J_K_V_df[['Indice Producto','Indice Destino Nivel Previo','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None)) 
    P_K_V=list(P_K_L_V_df[['Indice Producto','Indice Destino Nivel Previo','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None)) 
    P_L_V=list(P_L_M_V_df[['Indice Producto','Indice Destino Nivel Previo','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None)) 
    
    P_J_V_Mult=list(P_J_K_V_df[P_J_K_V_df['Tipo Ruta']=='Multiparada'][['Indice Producto','Indice Destino Nivel Previo','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None)) 
    P_K_V_Mult=list(P_K_L_V_df[P_K_L_V_df['Tipo Ruta']=='Multiparada'][['Indice Producto','Indice Destino Nivel Previo','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None)) 
    P_L_V_Mult=list(P_L_M_V_df[P_L_M_V_df['Tipo Ruta']=='Multiparada'][['Indice Producto','Indice Destino Nivel Previo','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None)) 
    
    P_J_C_V=list(P_J_K_V_df[['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Previo','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None))        
    P_K_C_V=list(P_K_L_V_df[['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Previo','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None))  \
            + list(P_J_K_V_df[P_J_K_V_df['Tipo Ruta']=='Redespacho'][['Indice Producto','Indice Destino Nivel Posterior','Indice Destino Nivel Posterior','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None)) 
    P_L_C_V=list(P_L_M_V_df[['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Previo','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None)) 
    P_M_C_V=list(P_L_M_V_df[['Indice Producto','Indice Destino Nivel Posterior','Indice Destino Nivel Posterior','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None)) 
    
    
    P_J_K_F_V_df=pd.merge(P_J_K_V_df,F,how='cross')[['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior','Frecuencia','Indice Vehiculo']]
    P_J_K_F_V_df=pd.merge(P_J_K_F_V_df,Rede_Mult, on = ['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior'], 
                        how='inner')[['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior','Frecuencia','Indice Vehiculo','Tipo Ruta']]
    
    P_J_K_F_V=list(P_J_K_F_V_df[['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior','Frecuencia','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None))   
    
    P_K_L_F_V_df=pd.merge(P_K_L_V_df,F,how='cross')[['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior','Frecuencia','Indice Vehiculo']]
    P_K_L_F_V_df=pd.merge(P_K_L_F_V_df,Rede_Mult, on = ['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior'], 
                        how='inner')[['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior','Frecuencia','Indice Vehiculo','Tipo Ruta']]
    
    
    P_K_L_F_V=list(P_K_L_F_V_df[['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior','Frecuencia','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None))   
    
    P_L_M_F_V_df=pd.merge(P_L_M_V_df,F,how='cross')[['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior','Frecuencia','Indice Vehiculo']]
    P_L_M_F_V_df=pd.merge(P_L_M_F_V_df,Rede_Mult, on = ['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior'], 
                        how='inner')[['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior','Frecuencia','Indice Vehiculo','Tipo Ruta']]
    
    
    P_L_M_F_V=list(P_L_M_F_V_df[['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior','Frecuencia','Indice Vehiculo']].drop_duplicates().itertuples(index=False, name=None))   
    
    P_J_K_L_df=pd.merge(P_J_K_V_df[['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior']],
                        P_K_L_V_df[['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior']]
                        ,left_on=['Indice Producto','Indice Destino Nivel Posterior'],right_on=['Indice Producto','Indice Destino Nivel Previo'],how='inner')
    P_J_K_L_df=P_J_K_L_df[['Indice Producto','Indice Destino Nivel Previo_x','Indice Destino Nivel Posterior_x',
                           'Indice Destino Nivel Posterior_y']].rename(columns={'Indice Destino Nivel Previo_x':'Indice Destino J',
                                                                                'Indice Destino Nivel Posterior_x':'Indice Destino K',
                                                                                'Indice Destino Nivel Posterior_y':'Indice Destino L'} )   
    
    P_J_K_L=list(P_J_K_L_df.drop_duplicates().itertuples(index=False, name=None)) 
    J_K_L=list(P_J_K_L_df[['Indice Destino J','Indice Destino K','Indice Destino L']].drop_duplicates().itertuples(index=False, name=None))
     
    P_K_L_M_df=pd.merge(P_K_L_V_df[['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior']],
                        P_L_M_V_df[['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior']],
                        left_on=['Indice Producto','Indice Destino Nivel Posterior'],right_on=['Indice Producto','Indice Destino Nivel Previo'],how='inner')
    P_K_L_M_df=P_K_L_M_df[['Indice Producto','Indice Destino Nivel Previo_x','Indice Destino Nivel Posterior_x',
                           'Indice Destino Nivel Posterior_y']].rename(columns={'Indice Destino Nivel Previo_x':'Indice Destino K',
                                                                                'Indice Destino Nivel Posterior_x':'Indice Destino L',
                                                                                'Indice Destino Nivel Posterior_y':'Indice Destino M'} )
    P_K_L_M=list(P_K_L_M_df.drop_duplicates().itertuples(index=False, name=None))   
    K_L_M=list(P_K_L_M_df[['Indice Destino K','Indice Destino L','Indice Destino M']].drop_duplicates().itertuples(index=False, name=None))
     
    P_K_F=list(P_J_K_F_V_df[['Indice Producto','Indice Destino Nivel Posterior','Frecuencia']].drop_duplicates().itertuples(index=False, name=None)) 
    P_L_F=list(P_K_L_F_V_df[['Indice Producto','Indice Destino Nivel Posterior','Frecuencia']].drop_duplicates().itertuples(index=False, name=None)) 
    P_M_F=list(P_L_M_F_V_df[['Indice Producto','Indice Destino Nivel Posterior','Frecuencia']].drop_duplicates().itertuples(index=False, name=None)) 
    
    P_J_K_F_Mult=list(P_J_K_F_V_df[P_J_K_F_V_df['Tipo Ruta']=='Multiparada'][['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior','Frecuencia']].drop_duplicates().itertuples(index=False, name=None)) 
    P_K_L_F_Mult=list(P_K_L_F_V_df[P_K_L_F_V_df['Tipo Ruta']=='Multiparada'][['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior','Frecuencia']].drop_duplicates().itertuples(index=False, name=None)) 
    P_L_M_F_Mult=list(P_L_M_F_V_df[P_L_M_F_V_df['Tipo Ruta']=='Multiparada'][['Indice Producto','Indice Destino Nivel Previo','Indice Destino Nivel Posterior','Frecuencia']].drop_duplicates().itertuples(index=False, name=None)) 
    
    #Filtrar diccionarios de parámetros para garantizar que se carguen solo los datos de combinaciones factibles
    Costos_JK_dict={clave: valor for clave, valor in Costos_RR_dict.items() if clave in J_K_V}
    Costos_KL_dict={clave: valor for clave, valor in Costos_RR_dict.items() if clave in K_L_V}
    Costos_LM_dict={clave: valor for clave, valor in Costos_RR_dict.items() if clave in L_M_V}
    Flujos_JK_dict={clave: valor for clave, valor in Flujos_RR_dict.items() if clave in P_J_K_V}
    Flujos_KL_dict={clave: valor for clave, valor in Flujos_RR_dict.items() if clave in P_K_L_V}
    Flujos_LM_dict={clave: valor for clave, valor in Flujos_RR_dict.items() if clave in P_L_M_V}
    FrecuenciasVisita_JK_dict={clave: valor for clave, valor in FrecuenciasVisita_RR_dict.items() if clave in J_K}
    FrecuenciasVisita_KL_dict={clave: valor for clave, valor in FrecuenciasVisita_RR_dict.items() if clave in K_L}
    FrecuenciasVisita_LM_dict={clave: valor for clave, valor in FrecuenciasVisita_RR_dict.items() if clave in L_M}
    
    return P_J_K_V,P_K_L_V,P_L_M_V,J_K,K_L,L_M,P_R_Dir,P_J,P_K,P_L,P_M,J_K_V,K_L_V,L_M_V,P_J_K,P_K_L,P_L_M,P_J_V,P_K_V,P_L_V,\
            P_J_K_F_V,P_K_L_F_V,P_L_M_F_V,P_J_K_L,P_K_L_M,P_K_F,P_L_F,P_M_F,J_K_L,K_L_M,P_J_C_V,P_K_C_V,P_L_C_V,P_M_C_V,P_J_K_F_Mult,P_K_L_F_Mult,P_L_M_F_Mult,\
            P_K_Rede,P_K_Mult,P_J_V_Mult,P_K_V_Mult,P_L_V_Mult, \
            Costos_JK_dict,Costos_KL_dict,Costos_LM_dict,\
            Flujos_JK_dict,Flujos_KL_dict,Flujos_LM_dict,\
            FrecuenciasVisita_JK_dict,FrecuenciasVisita_KL_dict,FrecuenciasVisita_LM_dict



##########################################
######### 2.3. LEER PARAMETROS ###########
##########################################

 
def Parametros_PR(df_dict,t):
    '''Función que lee los parametros de entrada para la malla de combinaciones posibles de destinos y productos.
    Argumentos:
            df_dict:
                    Descripción:   Diccionario que contiene los dataframes (un dataframe por cada pestaña del archivo de inputs) 
                                   con todos los datos de entrada de la instancia o escenario que se desea modelar.
                    Tipo de dato:  dict 
            t:      
                    Descripción:   indice númerico que indica el periodo que se desea modelar 
                    Tipo de dato:  int
    '''
    #cargar el dataframe que contiene la demanda por producto-cliente y filtrarlo por el periodo deseado 
    Demanda_df=df_dict['Demanda(D)'][df_dict['Demanda(D)']['Indice Periodo']==t]
    #crear diccionario con la demanda por combinación producto-cliente
    Demanda_dict={(int(row['Indice Producto']), int(row['Indice Cliente'])): row['Cantidad Mes'] for _, row in Demanda_df.iterrows()}
    
    #crear diccionario con el ADU (Consumo promedio diario) por combinación producto-cliente
    ADU_dict={(int(row['Indice Producto']), int(row['Indice Cliente'])): row['ADU'] for _, row in Demanda_df.iterrows()}
    
    #cargar el dataframe que contiene la zona roja por producto-cliente y filtrarlo por el periodo deseado 
    ZonaRoja_df=df_dict['ZonaRoja'][df_dict['ZonaRoja']['Indice Periodo']==t]
    #crear diccionario con la Zona Roja por combinación producto-cliente
    ZonaRoja_dict={(int(row['Indice Producto']), int(row['Indice Cliente'])): row['Tamaño Zona Roja'] for _, row in ZonaRoja_df.iterrows()}
    
    #cargar el dataframe que contiene el tamaño minimo de pedido  por producto-cliente y filtrarlo por el periodo deseado 
    MOQ_df=df_dict['MOQ'][df_dict['MOQ']['Indice Periodo']==t]
    #crear diccionario con el tamaño minimo de pedido por combinación producto-cliente
    MOQ_dict={(int(row['Indice Producto']), int(row['Indice Cliente'])): row['MOQ'] for _, row in MOQ_df.iterrows()}
    
    #cargar el dataframe que contiene la frecuencia actual de abastecimiento por producto y almacén regional y filtrarlo por el periodo deseado
    FrAb_df=df_dict['FrecuenciaAbastecimiento(FA)'][df_dict['FrecuenciaAbastecimiento(FA)']['Indice Periodo']==t]
    #crear diccionario con el tamaño minimo de pedido por combinación producto-cliente
    FrAb_dict={(int(row['Indice Producto']), int(row['Indice Destino'])): row['Frecuencia de abastecimiento'] for _, row in FrAb_df.iterrows()}
    
    return Demanda_dict, ADU_dict, ZonaRoja_dict, MOQ_dict,FrAb_dict

def Parametros_T(df_dict,t):
    '''Función que lee los parametros de entrada a nivel de periodo.
    Argumentos:
            df_dict:
                    Descripción:   Diccionario que contiene los dataframes (un dataframe por cada pestaña del archivo de inputs) 
                                   con todos los datos de entrada de la instancia o escenario que se desea modelar.
                    Tipo de dato:  dict 
            t:      
                    Descripción:   indice númerico que indica el periodo que se desea modelar 
                    Tipo de dato:  int
    '''
    #cargar el dataframe que contiene la tasa del costo de capital WACC y filtrarlo por el periodo deseado 
    WACC_df=df_dict['WACC'][df_dict['WACC']['Indice Periodo']==t]
    #crear variable con el valor numérico del WACC para el periodo deseado
    WACC=WACC_df['WACC'].values[0]
    return WACC

def Parametros_V(df_dict):
    '''Función que lee los parametros de entrada a nivel de vehículo.
    Argumentos:
            df_dict:
                    Descripción:   Diccionario que contiene los dataframes (un dataframe por cada pestaña del archivo de inputs) 
                                   con todos los datos de entrada de la instancia o escenario que se desea modelar.
                    Tipo de dato:  dict 
    '''
    #cargar el dataframe que contiene los parámetros del vehiculo
    Vehiculos_df=df_dict['Vehiculos(V)']
    #crear diccionario con la capacidad en peso de cada vehiculo
    Q_peso_dict={int(row['Indice']): row['CapacidadPeso(KG)'] for _, row in Vehiculos_df.iterrows()}
    #crear diccionario con la capacidad en volumen de cada vehiculo
    Q_vol_dict={int(row['Indice']): row['CapacidadVolumen(M3)'] for _, row in Vehiculos_df.iterrows()}
    return Q_peso_dict,Q_vol_dict

def Parametros_P(df_dict):
    '''Función que lee los parametros de entrada pa nivel de producto.
    Argumentos:
            df_dict:
                    Descripción:   Diccionario que contiene los dataframes (un dataframe por cada pestaña del archivo de inputs) 
                                   con todos los datos de entrada de la instancia o escenario que se desea modelar.
                    Tipo de dato:  dict 
    '''
    #cargar el dataframe que contiene los parámetros de cada producto
    Productos_df=df_dict['GruposProductos(P)']
    #crear diccionario con el peso unitario de cada producto
    PU_dict={int(row['Indice']): row['Peso Unitario (KG)'] for _, row in Productos_df.iterrows()}
    #crear diccionario con el volumen unitario de cada producto
    VOLU_dict={int(row['Indice']): row['Volumen Unitario (M3)'] for _, row in Productos_df.iterrows()}
    #crear diccionario con el Costo unitario de cada producto
    CU_dict={int(row['Indice']): row['Costo Unitario'] for _, row in Productos_df.iterrows()}
    return PU_dict,VOLU_dict,CU_dict
   
def Inicializar_conjuntos(model,V,R,C,O,N,H,F,P):
        '''Para definir una lista de Python como un índice en pyomo, puedes usar la clase Set para crear un conjunto de índices basado en la lista. 
        # Esto es útil cuando tus índices no son necesariamente consecutivos o no siguen un rango específico.'''

        #Vehículos
        model.Vehiculos = pyo.Set(initialize=V)
        #Almacenes Regionales
        model.AlmacenesRegionales = pyo.Set(initialize=R)
        #Clientes
        model.Clientes = pyo.Set(initialize=C)
        #Plantas
        model.Plantas = pyo.Set(initialize=O)
        #Cedis Nacionales
        model.CedisNacionales = pyo.Set(initialize=N)
        #Hubs
        model.Hubs = pyo.Set(initialize=H)
        #Frecuencias
        model.Frecuencias = pyo.Set(initialize=F)
        #Productos
        model.Productos = pyo.Set(initialize=P)
        
        return model
        
def Crear_combinaciones_factibles(model, P_R,P_H_R,P_R_F,P_O_N_V,O_N_V,O_H_V,N_H_V,P_O_H_V,P_N_H_V,\
        P_N_R_V,P_N_R,N_R_V,P_R_C_V,P_N_R_F_V,H_R_V,P_H_R_F_V,P_J_K_V,P_K_L_V,P_L_M_V,J_K,K_L,L_M,J_K_V,K_L_V,L_M_V,P_J_K,P_K_L,P_L_M,\
        P_J_K_F_V,P_K_L_F_V,P_L_M_F_V,P_K_C_V,P_L_C_V,P_M_C_V):
        # Conjunto de combinaciones de Indices 'producto-almacén regional'
        model.PR = pyo.Set(initialize=P_R)
        """ # Conjunto de combinaciones de Indices 'cedi nacional-almacén regional'
        model.NR = pyo.Set(initialize=N_R)
        """
        # Conjunto de combinaciones de Indices 'almacén regional nivel 1-almacén regional nivel 2'
        model.JK = pyo.Set(initialize=J_K)
        # Conjunto de combinaciones de Indices 'almacén regional nivel 2-almacén regional nivel 3'
        model.KL = pyo.Set(initialize=K_L)
        # Conjunto de combinaciones de Indices 'almacén regional nivel 3-almacén regional nivel 4'
        model.LM = pyo.Set(initialize=L_M)

        # Conjunto de combinaciones de Indices 'planta-cedi nacional-vehiculo'
        model.ONV = pyo.Set(initialize=O_N_V)
        # Conjunto de combinaciones de Indices 'planta-hub-vehiculo'
        model.OHV = pyo.Set(initialize=O_H_V)
        #Conjunto de combinaciones de Indices 'cedi nacional-hub-vehiculo' 
        model.NHV = pyo.Set(initialize=N_H_V)
        # Conjunto de combinaciones de Indices 'Cedi Nacional-almacén regional-vehiculo'
        model.NRV = pyo.Set(initialize=N_R_V)
        # Conjunto de combinaciones de Indices 'Hub-almacén regional-vehiculo'
        model.HRV = pyo.Set(initialize=H_R_V)
        # Conjunto de combinaciones de Indices 'almacén regional nivel 1-almacén regional nivel 2-vehiculo'
        model.JKV = pyo.Set(initialize=J_K_V)
        # Conjunto de combinaciones de Indices 'almacén regional nivel 2-almacén regional nivel 3-vehiculo'
        model.KLV = pyo.Set(initialize=K_L_V)
        # Conjunto de combinaciones de Indices 'almacén regional nivel 3-almacén regional nivel 4-vehiculo'
        model.LMV = pyo.Set(initialize=L_M_V)
        # Conjunto de combinaciones de Indices 'producto-hub-almacén regional'
        model.PHR = pyo.Set(initialize=P_H_R)
        # Conjunto de combinaciones de Indices 'producto-cedi nacional-almacén regional'
        model.PNR = pyo.Set(initialize=P_N_R)
        # Conjunto de combinaciones de Indices 'producto-almacén regional nivel 1-almacén regional nivel 2'
        model.PJK = pyo.Set(initialize=P_J_K)
        # Conjunto de combinaciones de Indices 'producto-almacén regional nivel 2-almacén regional nivel 3'
        model.PKL = pyo.Set(initialize=P_K_L)
        # Conjunto de combinaciones de Indices 'producto-almacén regional nivel 3-almacén regional nivel 4'
        model.PLM = pyo.Set(initialize=P_L_M)
        # Conjunto de combinaciones de Indices 'producto-almacén regional-frecuencia'
        model.PRF = pyo.Set(initialize=P_R_F)

        # Conjunto de combinaciones de Indices 'producto-planta-cedi nacional-vehiculo'
        model.PONV = pyo.Set(initialize=P_O_N_V)
        # Conjunto de combinaciones de Indices 'producto-planta-hub-vehiculo'
        model.POHV = pyo.Set(initialize=P_O_H_V)
        
        # Conjunto de combinaciones de Indices 'producto-cedi nacional-hub-vehiculo'
        model.PNHV = pyo.Set(initialize=P_N_H_V)
        # Conjunto de combinaciones de Indices 'producto-almacen regional-cliente-vehiculo'
        model.PRCV = pyo.Set(initialize=list(set(P_R_C_V+P_K_C_V+P_L_C_V+P_M_C_V)))

        # Conjunto de combinaciones de Indices 'producto-cedi nacional-almacen regional-vehiculo'
        model.PNRV = pyo.Set(initialize=P_N_R_V)
        # Conjunto de combinaciones de Indices 'producto-almacén regional nivel 1-almacén regional nivel 2-vehiculo'
        model.PJKV = pyo.Set(initialize=P_J_K_V)
        # Conjunto de combinaciones de Indices 'producto-almacén regional nivel 2-almacén regional nivel 3-vehiculo'
        model.PKLV = pyo.Set(initialize=P_K_L_V)
        # Conjunto de combinaciones de Indices 'producto-almacén regional nivel 3-almacén regional nivel 4-vehiculo'
        model.PLMV = pyo.Set(initialize=P_L_M_V)

        # Conjunto de combinaciones de Indices 'producto-cedi nacional-almacen regional-frecuencia-vehiculo'
        model.PNRFV = pyo.Set(initialize=P_N_R_F_V)
        # Conjunto de combinaciones de Indices 'producto-hub-almacen regional-frecuencia-vehiculo'
        model.PHRFV = pyo.Set(initialize=P_H_R_F_V)
        # Conjunto de combinaciones de Indices 'producto-almacen regional nivel 1-almacen regional nivel 2-frecuencia-vehiculo'
        model.PJKFV = pyo.Set(initialize=P_J_K_F_V)
        # Conjunto de combinaciones de Indices 'producto-almacen regional nivel 2-almacen regional nivel 3-frecuencia-vehiculo'
        model.PKLFV = pyo.Set(initialize=P_K_L_F_V)
        # Conjunto de combinaciones de Indices 'producto-almacen regional nivel 3-almacen regional nivel 4-frecuencia-vehiculo'
        model.PLMFV = pyo.Set(initialize=P_L_M_F_V)
        
        return model



def Inicializar_parametros(model,Demanda,ADU,ZRoja, WACC,Q_peso,Q_vol,PU,VOLU,CU,FrAb,Costos_ON,Costos_NR,Costos_HR,Costos_OH,Costos_NH,Costos_JK,Costos_KL,Costos_LM,
                           Flujos_ON,Flujos_NR,Flujos_JK,Flujos_KL,Flujos_LM):
        # 𝐷_𝑝𝑟:Demanda de producto 𝑝 en el almacén regional 𝑟
        model.D=pyo.Param(model.PR, initialize=Demanda) 
        # 𝐴𝐷𝑈_𝑝𝑟:Consumo prom. diario del producto 𝑝 en el almacén regional 𝑟
        model.ADU=pyo.Param(model.PR, initialize=ADU) 
        # 𝑅_𝑝𝑟:Zona Roja de producto 𝑝 en el almacén regional 𝑟
        model.ZRoja=pyo.Param(model.PR, initialize=ZRoja) 
        # WACC: Costo  de Capital (tasa mensual) 
        model.WACC=pyo.Param(within=pyo.NonNegativeReals, initialize=WACC)
        # 𝑄_peso_𝑣:Capacidad en peso del vehículo 𝑣
        model.Q_peso=pyo.Param(model.Vehiculos, initialize=Q_peso)
        # 𝑄_vol_𝑣:Capacidad en volumen del vehículo 𝑣
        model.Q_vol=pyo.Param(model.Vehiculos, initialize=Q_vol)
        # 𝑃U_𝑝:Peso unitario del producto 𝑝
        model.PU=pyo.Param(model.Productos, initialize=PU)
        # 𝑉𝑂𝐿U_𝑝:Volumen unitario del producto 𝑝
        model.VOLU=pyo.Param(model.Productos, initialize=VOLU)
        # 𝐶𝑈_𝑝:Costo unitario del producto 𝑝
        model.CU=pyo.Param(model.Productos, initialize=CU)
        # 𝐹𝑟𝐴𝑏_𝑝𝑟::Frecuencia actual de abastecimiento del producto 𝑝 al almacén regional 𝑟 (cada cuántos días se abastece)
        model.FrAb=pyo.Param(model.PR, initialize=FrAb)

        #Costos de transporte
        # 𝐶_𝑂𝑁_𝑜𝑛𝑣:Costo de transporte (variable 𝑜 𝑓𝑙𝑒𝑡𝑒)  desde la planta 𝑜 al Cedi Nacional 𝑛 en el vehículo 𝑣
        model.C_ON=pyo.Param(model.ONV, initialize=Costos_ON)
        # 𝐶_𝑂𝐻_𝑜ℎ𝑣:Costo de transporte (variable 𝑜 𝑓𝑙𝑒𝑡𝑒)  desde la planta 𝑜 al Hub ℎ en el vehículo 𝑣 (∀ o ∈ {5,6,7,8…..}) (Cero en el baseline)
        model.C_OH=pyo.Param(model.OHV, initialize=Costos_OH)
        # 𝐶_𝑁𝐻_𝑛ℎ𝑣:Costo de transporte (variable 𝑜 𝑓𝑙𝑒𝑡𝑒)  desde el Cedi Nacional 𝑛 al Hub ℎ en el vehículo 𝑣 (Cero en el baseline)
        model.C_NH=pyo.Param(model.NHV, initialize=Costos_NH)
        # 𝐶_𝑁𝑅_𝑛𝑟𝑣:Costo de transporte (Flete)  desde el Cedi Nacional 𝑛 al almacén regional 𝑟 en el vehículo 𝑣
        model.C_NR=pyo.Param(model.NRV, initialize=Costos_NR)
        # 𝐶_𝐻𝑅_ℎ𝑟𝑣:Costo de transporte (Flete)  desde el Hub ℎ al almacén regional 𝑟 en el vehículo 𝑣 (Cero en el baseline)
        model.C_HR=pyo.Param(model.HRV, initialize=Costos_HR)
        # 𝐶_𝐽𝐾_𝑗𝑘𝑣:Costo de transporte (Flete)  desde el almacén regional 𝑗 al almacén regional 𝑘 en el vehículo 𝑣 (k  ∈𝑅)
        model.C_JK=pyo.Param(model.JKV, initialize=Costos_JK)
        # 𝐶_𝐾𝐿_𝑘𝑙𝑣:Costo de transporte (Flete)  desde el almacén regional 𝑘 al almacén regional 𝑙 en el vehículo 𝑣 (l  ∈𝑅)
        model.C_KL=pyo.Param(model.KLV, initialize=Costos_KL)
        # 𝐶_𝐿𝑀_𝑙𝑚𝑣:Costo de transporte (Flete)  desde el almacén regional 𝑙 al almacén regional 𝑚 en el vehículo 𝑣 (m  ∈𝑅)
        model.C_LM=pyo.Param(model.LMV, initialize=Costos_LM)

        # Cantidades  reales baseline– tamaño de flujos desde plantas:
        # 𝑄_𝑂𝑁_𝑝𝑜𝑛𝑣: cantidad de producto 𝑝 enviado desde la planta 𝑜 al Cedi Nacional 𝑛 en el vehículo 𝑣
        model.Q_ON=pyo.Param(model.PONV, initialize=Flujos_ON)

        # Cantidades  reales  baseline– tamaño de flujos desde Cedis Nacionales:
        # 𝑄_𝑁𝑅_𝑝𝑛𝑟𝑣:Cantidad de producto 𝑝 enviado desde el Cedi Nacional 𝑛 al almacén regional 𝑟 en el vehículo 𝑣
        model.Q_NR=pyo.Param(model.PNRV, initialize=Flujos_NR)

        # Cantidades  reales  baseline– tamaño de flujos entre destinos:
        # 𝑄_𝐽𝐾_𝑝𝑗𝑘𝑣:Cantidad de producto 𝑝 enviado desde el almacén regional 𝑗 al almacén regional 𝑘 en el vehículo 𝑣
        model.Q_JK=pyo.Param(model.PJKV, initialize=Flujos_JK)
        # 𝑄_𝐾𝐿_𝑝𝑘𝑙𝑣:Cantidad de producto 𝑝 enviado desde el almacén regional 𝑘 al almacén regional 𝑙 en el vehículo 𝑣
        model.Q_KL=pyo.Param(model.PKLV, initialize=Flujos_KL)
        # 𝑄_𝐿𝑀_𝑝𝑙𝑚𝑣:Cantidad de producto 𝑝 enviado desde el almacén regional 𝑙 al almacén regional 𝑚 en el vehículo 𝑣
        model.Q_LM=pyo.Param(model.PLMV, initialize=Flujos_LM)
        return model



def Definir_Variables(model):
        """ Para crear variables en pyomo utilizando una lista de tuplas que contiene los índices, puedes usar la clase 'Var' junto con un conjunto Set 
        que inicializa con la lista de tuplas. Esto es útil cuando trabajas con variables indexadas por múltiples dimensiones. """

        #Cantidades – tamaño de flujos desde plantas:
        #𝑂𝑁_𝑝𝑜𝑛𝑣: Cantidad de producto 𝑝 enviado desde la planta 𝑜 al Cedi Nacional 𝑛 en el vehículo 𝑣 
        model.Flujo_ON = pyo.Var(model.PONV, domain=pyo.NonNegativeReals,initialize=0) 
        #𝑂𝐻_𝑝𝑜ℎ𝑣:Cantidad de producto 𝑝 enviado desde la planta 𝑜 al Hub ℎ en el vehículo 𝑣 ("Cero en el baseline)"
        model.Flujo_OH = pyo.Var(model.POHV, domain=pyo.NonNegativeReals,initialize=0) 

        # Cantidades – tamaño de flujos desde almacenamientos de origen (Cedis Nacionales):
        # NR_𝑝𝑛𝑟𝑓𝑣:Cantidad de producto 𝑝 enviado desde el Cedi Nacional 𝑛 al almacén regional 𝑟 en la frecuencia 𝑓 en el vehículo 𝑣 
        model.Flujo_NR = pyo.Var(model.PNRFV, domain=pyo.NonNegativeReals,initialize=0) 
        # NH_𝑝𝑛ℎ𝑣:Cantidad de producto 𝑝 enviado desde el Cedi Nacional 𝑛 al Hub ℎ en el vehículo 𝑣 (Cero en el baseline)
        model.Flujo_NH = pyo.Var(model.PNHV, domain=pyo.NonNegativeReals,initialize=0) 

        # Cantidades – tamaño de flujos desde  Hub:
        # 𝐻𝑅_𝑝ℎ𝑟𝑓𝑣:Cantidad de producto 𝑝 enviado desde el hub 𝑛 al almacén regional 𝑟 en la frecuencia 𝑓 en el vehículo 𝑣 "(Cero en el baseline)"
        model.Flujo_HR = pyo.Var(model.PHRFV, domain=pyo.NonNegativeReals,initialize=0) 

        # Cantidades – tamaño de flujos entre regionales:
        # 𝐽𝐾_𝑝𝑗𝑘𝑓𝑣:Cantidad de producto 𝑝 enviado desde el almacén regional 𝑗 al almacén regional 𝑘 en la frecuencia 𝑓 el vehículo 𝑣 (∀ 𝑗≠𝑘;  𝑗,𝑘∈𝑅)
        model.Flujo_JK = pyo.Var(model.PJKFV, domain=pyo.NonNegativeReals,initialize=0)
        # 𝐾𝐿_𝑝𝑘𝑙𝑓𝑣:Cantidad de producto 𝑝 enviado desde el almacén regional 𝑘 al almacén regional 𝑙 en la frecuencia 𝑓 en el vehículo 𝑣 (∀ 𝑘≠𝑙;  𝑘,𝑙∈𝑅)
        model.Flujo_KL = pyo.Var(model.PKLFV, domain=pyo.NonNegativeReals,initialize=0)
        # 𝐿𝑀_𝑝𝑙𝑚𝑓𝑣:Cantidad de producto 𝑝 enviado desde el almacén regional 𝑙 al almacén regional 𝑚 en la frecuencia 𝑓 en el vehículo 𝑣 (∀ 𝑙≠𝑚;  𝑙,𝑚∈𝑅)
        model.Flujo_LM = pyo.Var(model.PLMFV, domain=pyo.NonNegativeReals,initialize=0)

        # Cantidades – tamaño de flujos desde Regionales hacia clientes (Ficticio):
        # 𝑅𝐶_𝑝𝑟𝑐𝑣:Cantidad de producto 𝑝 enviado desde el almacén regional 𝑟 al cliente 𝑐 en el vehículo 𝑣
        model.Flujo_RC = pyo.Var(model.PRCV, domain=pyo.NonNegativeReals,initialize=0)

        # Dimensionamiento de flota- Cantidad de viajes:
        # 𝑉𝑂𝑁_𝑜𝑛𝑣:Cantidad de viajes desde la planta de origen 𝑜 𝑎𝑙 Cedi Nacional 𝑛 en el vehiculo 𝑣
        model.Viajes_VON = pyo.Var(model.ONV, domain=pyo.NonNegativeIntegers,initialize=0)
        # 𝑉𝑂𝐻_𝑜ℎ𝑣:Cantidad de viajes desde la planta de origen 𝑜 al hub ℎ en el vehiculo 𝑣
        model.Viajes_VOH = pyo.Var(model.OHV, domain=pyo.NonNegativeIntegers,initialize=0)
        # 𝑉𝑁𝐻_𝑛ℎ𝑣:Cantidad de viajes desde el Cedi Nacional 𝑛 al hub ℎ en el vehiculo 𝑣 
        model.Viajes_VNH = pyo.Var(model.NHV, domain=pyo.NonNegativeIntegers,initialize=0)
        # 𝑉𝑁𝑅_𝑛𝑟𝑣:Cantidad de viajes desde el Cedi Nacional 𝑛 al almacén regional 𝑟 en el vehiculo 𝑣
        model.Viajes_VNR = pyo.Var(model.NRV, domain=pyo.NonNegativeIntegers,initialize=0)
        # 𝑉𝐻𝑅_ℎ𝑟𝑣:Cantidad de viajes desde el Hub ℎ al almacén regional 𝑟 en el vehiculo 𝑣(Cero en el baseline)
        model.Viajes_VHR = pyo.Var(model.HRV, domain=pyo.NonNegativeIntegers,initialize=0)
        # 𝑉𝐽𝐾_𝑗𝑘𝑣:Cantidad de viajes desde el almacén regional 𝑗 al almacén regional 𝑘 en el vehiculo 𝑣(∀𝑗≠𝑘;  𝑗,𝑘∈R)
        model.Viajes_VJK = pyo.Var(model.JKV, domain=pyo.NonNegativeIntegers,initialize=0)
        # 𝑉𝐾𝐿_𝑘𝑙𝑣:Cantidad de viajes desde el almacén regional 𝑘 al almacén regional 𝑙 en el vehiculo 𝑣(∀𝑘≠𝑙;  𝑗,𝑘∈R)
        model.Viajes_VKL = pyo.Var(model.KLV, domain=pyo.NonNegativeIntegers,initialize=0)
        # 𝑉𝐿𝑀_𝑙𝑚𝑣:Cantidad de viajes desde el almacén regional 𝑙 al almacén regional 𝑚 en el vehiculo 𝑣(∀𝑙≠𝑚;  𝑗,𝑘∈R)
        model.Viajes_VLM = pyo.Var(model.LMV, domain=pyo.NonNegativeIntegers,initialize=0)

        # Frecuencias de abastecimiento:
        # 𝐹𝐴_𝑝𝑟: Frecuencia de abastecimiento del producto 𝑝 al almacén regional 𝑟 "(cada cuántos días se abastece)"
        model.Frecuencia_FA = pyo.Var(model.PR, domain=pyo.NonNegativeIntegers,initialize=0)

        # Inventario promedio en cada almacen regional:
        # 𝐼𝑅_𝑝𝑟:Inventario de producto 𝑝 en el almacén regional 𝑟
        model.Inventario_IR = pyo.Var(model.PR, domain=pyo.NonNegativeReals,initialize=0)


        # Definición forma de abastecimiento por producto-destino:
        # 𝐵𝐻_𝑝ℎ𝑟:(1  si el almacén de destino 𝑟 es abastecido con el producto 𝑝 a través del hub ℎ, 0 𝑒𝑛 𝑜𝑡𝑟𝑜 𝑐𝑎𝑠𝑜)
        model.BH = pyo.Var(model.PHR, domain=pyo.Binary,initialize=0)
        # 𝐵𝑁_𝑝𝑛𝑟:(1  si el almacén de destino 𝑟 es abastecido con el producto 𝑝 a través del Cedi Nacional n, 0 𝑒𝑛 𝑜𝑡𝑟𝑜 𝑐𝑎𝑠𝑜)
        model.BN = pyo.Var(model.PNR, domain=pyo.Binary,initialize=0)
        # 𝐵𝑅𝐽_𝑝𝑗𝑘:(1  si el almacén de destino 𝑘 es abastecido con el producto 𝑝 a través del almacen regional 𝑗, 0 𝑒𝑛 𝑜𝑡𝑟𝑜 𝑐𝑎𝑠𝑜)
        model.BRJ = pyo.Var(model.PJK, domain=pyo.Binary,initialize=0)
        # 𝐵𝑅𝐾_𝑝𝑘𝑙:(1  si el almacén de destino 𝑙 es abastecido con el producto 𝑝 a través del almacen regional 𝑘, 0 𝑒𝑛 𝑜𝑡𝑟𝑜 𝑐𝑎𝑠𝑜)
        model.BRK = pyo.Var(model.PKL, domain=pyo.Binary,initialize=0)
        # 𝐵𝑅𝐿_𝑝𝑙𝑚:(1  si el almacén de destino 𝑚 es abastecido con el producto 𝑝 a través del almacen regional 𝑙, 0 𝑒𝑛 𝑜𝑡𝑟𝑜 𝑐𝑎𝑠𝑜)
        model.BRL = pyo.Var(model.PLM, domain=pyo.Binary,initialize=0)

        # Definición frecuencia de abastecimiento:
        # 𝐵𝐹_𝑝𝑟𝑓:(1  si el almacén de destino 𝑟 es abastecido con el producto 𝑝  en la frecuencia 𝑓, 0 𝑒𝑛 𝑜𝑡𝑟𝑜 𝑐𝑎𝑠𝑜)
        model.BF = pyo.Var(model.PRF, domain=pyo.Binary,initialize=0)
        
        # Definición hubs a habilitar:
        # 𝐵Hub_ℎ:(1  si 𝑠𝑒 ℎ𝑎𝑏𝑖𝑙𝑖𝑡𝑎 𝑦 𝑠𝑒 𝑢𝑠𝑎 𝑒𝑙 ℎ𝑢𝑏 ℎ, 𝑒𝑛 𝑜𝑡𝑟𝑜 𝑐𝑎𝑠𝑜))
        model.BHub = pyo.Var(model.Hubs, domain=pyo.Binary,initialize=0)
                

        #DEFINICIÓN DE VARIABLES PARA CALCULAR CADA ELEMENTO DE LA FUNCIÓN OBJETIVO POR SEPARADO
        model.CostoCapital=pyo.Var(domain=pyo.NonNegativeReals,initialize=0) # Costo de capital inventario en almacenes regionales

        #******* Calcular costos por tipo de arco ************
        model.Costotte_ONV=pyo.Var(domain=pyo.NonNegativeReals,initialize=0) # Costo transportes de Plantas a Cedis nacionales
        model.Costotte_OHV=pyo.Var(domain=pyo.NonNegativeReals,initialize=0)  # Costo transportes de Plantas a Hub
        model.Costotte_NHV=pyo.Var(domain=pyo.NonNegativeReals,initialize=0)  # Costo transportes de Almacenes Origen a Hub
        model.Costotte_NRV=pyo.Var(domain=pyo.NonNegativeReals,initialize=0)  # Costo transportes de Cedis Nacionales a almacenes regionales (directos)
        model.Costotte_HRV=pyo.Var(domain=pyo.NonNegativeReals,initialize=0)  # Costo transportes de Hub a almacenes regionales
        model.Costotte_JKV=pyo.Var(domain=pyo.NonNegativeReals,initialize=0)  # Costo transportes entre almacenes regionales nivel 1 y nivel 2
        model.Costotte_KLV=pyo.Var(domain=pyo.NonNegativeReals,initialize=0)  # Costo transportes entre almacenes regionales nivel 2 y nivel 3
        model.Costotte_LMV=pyo.Var(domain=pyo.NonNegativeReals,initialize=0)  # Costo transportes entre almacenes regionales nivel 3 y nivel 4

        return model

def Crear_FO(model):
        """ Para definir una función objetivo en pyomo que incluya una sumatoria en múltiples índices basada en una lista de tuplas previamente definida,
se debe seguir un enfoque ligeramente diferente. En este caso, se debe usar la lista de tuplas para definir las variables y 
luego construir la función objetivo en base a esa lista. """

        model.obj = pyo.Objective(expr=model.WACC*sum(model.CU[p]*model.Inventario_IR[p, r] for (p, r) in model.PR) # Costo de capital inventario en almacenes regionales
                          +sum(model.C_ON[o,n,v]*model.Viajes_VON[o,n,v] for (o,n,v) in model.ONV) # Costo transportes de Plantas a Cedis nacionales
                          +sum(model.C_OH[o,h,v]*model.Viajes_VOH[o,h,v] for (o,h,v) in model.OHV) # Costo transportes de Plantas a Hub
                          +sum(model.C_NH[n,h,v]*model.Viajes_VNH[n,h,v] for (n,h,v) in model.NHV) # Costo transportes de Almacenes Origen a Hub
                          +sum(model.C_NR[n,r,v]*model.Viajes_VNR[n,r,v] for (n,r,v) in model.NRV) # Costo transportes de Cedis Nacionales a almacenes regionales (directos)
                          +sum(model.C_HR[h,r,v]*model.Viajes_VHR[h,r,v] for (h,r,v) in model.HRV) # Costo transportes de Hub a almacenes regionales
                          +sum(model.C_JK[j,k,v]*model.Viajes_VJK[j,k,v] for (j,k,v) in model.JKV) # Costo transportes entre almacenes regionales nivel 1 y nivel 2
                          +sum(model.C_KL[k,l,v]*model.Viajes_VKL[k,l,v] for (k,l,v) in model.KLV) # Costo transportes entre almacenes regionales nivel 2 y nivel 3
                          +sum(model.C_LM[l,m,v]*model.Viajes_VLM[l,m,v] for (l,m,v) in model.LMV) # Costo transportes entre almacenes regionales nivel 3 y nivel 4
                          , sense=pyo.minimize)
        
 
 
def Crear_restricciones_generales(model,P_R,P_C,P_H_R,P_R_F,P_H,O_N_V,O_H_V,N_H_V,P_N_R,N_R_V,P_N,H_R_V,P_R_Dir,P_J,P_K,P_L,
                                  P_M,J_K_V,K_L_V,L_M_V,P_J_K,P_K_L,P_L_M,P_K_F, P_L_F,P_M_F,J_K_L,K_L_M,P_J_K_F_Mult,P_K_L_F_Mult,P_L_M_F_Mult,
                                  P_K_Rede,P_K_Mult,P_J_V_Mult,P_K_V_Mult,P_L_V_Mult):
        
        # Definir el conjunto de restricciones vacío para empezar a llenarlo iterando dentro de las lista de tuplas factibles creadas previamente
        model.constraints = pyo.ConstraintList()

        #******* Calcular Costo de capital ***********
        model.constraints.add(model.CostoCapital==model.WACC*sum(model.CU[p]*model.Inventario_IR[p, r] for (p, r) in model.PR))# Costo de capital inventario en almacenes regionales

        #******* Calcular costos por tipo de arco ************
        model.constraints.add(model.Costotte_ONV==sum(model.C_ON[o,n,v]*model.Viajes_VON[o,n,v] for (o,n,v) in model.ONV)) # Costo transportes de Plantas a Cedis nacionales
        model.constraints.add(model.Costotte_OHV==sum(model.C_OH[o,h,v]*model.Viajes_VOH[o,h,v] for (o,h,v) in model.OHV)) # Costo transportes de Plantas a Hub
        model.constraints.add(model.Costotte_NHV==sum(model.C_NH[n,h,v]*model.Viajes_VNH[n,h,v] for (n,h,v) in model.NHV)) # Costo transportes de Almacenes Origen a Hub
        model.constraints.add(model.Costotte_NRV==sum(model.C_NR[n,r,v]*model.Viajes_VNR[n,r,v] for (n,r,v) in model.NRV)) # Costo transportes de Cedis Nacionales a almacenes regionales (directos)
        model.constraints.add(model.Costotte_HRV==sum(model.C_HR[h,r,v]*model.Viajes_VHR[h,r,v] for (h,r,v) in model.HRV)) # Costo transportes de Hub a almacenes regionales
        model.constraints.add(model.Costotte_JKV==sum(model.C_JK[j,k,v]*model.Viajes_VJK[j,k,v] for (j,k,v) in model.JKV)) # Costo transportes entre almacenes regionales nivel 1 y nivel 2
        model.constraints.add(model.Costotte_KLV==sum(model.C_KL[k,l,v]*model.Viajes_VKL[k,l,v] for (k,l,v) in model.KLV)) # Costo transportes entre almacenes regionales nivel 2 y nivel 3
        model.constraints.add(model.Costotte_LMV==sum(model.C_LM[l,m,v]*model.Viajes_VLM[l,m,v] for (l,m,v) in model.LMV)) # Costo transportes entre almacenes regionales nivel 3 y nivel 4


        #*************Cantidad de viajes por arco**************
        '''Definir un conjunto en Pyomo es útil cuando quieres usar ese conjunto para definir variables, restricciones, parámetros, etc.,
        de manera más estructurada y reutilizable. 

        Pyomo permite iterar directamente sobre listas y otros iterables en Python. Por lo tanto, 
        puedes usar una lista de tuplas directamente para agregar restricciones sin necesidad de definir un conjunto adicional en el modelo.'''

        #Agregar restricciones de Cantidad de viajes por arco planta-cedi nacional-vehiculo
        # for (o,n,v) in O_N_V:
        #     model.constraints.add(model.Viajes_VON[o,n,v] >= (sum(model.Flujo_ON[p,o,n,v]*model.PU[p] for p in model.Productos)/model.Q_peso[v]))
        #     model.constraints.add(model.Viajes_VON[o,n,v] >= (sum(model.Flujo_ON[p,o,n,v]*model.VOLU[p] for p in model.Productos)/model.Q_vol[v]))
        for (o,n,v) in O_N_V:
                model.constraints.add(model.Viajes_VON[o,n,v] >= 
                                        (sum(model.Flujo_ON[p,o,n,v]*model.PU[p] for p in list({tupla[0] for tupla in list(model.Flujo_ON) if tupla[1:] == (o,n,v)}))/model.Q_peso[v]))
                model.constraints.add(model.Viajes_VON[o,n,v] >=
                                        (sum(model.Flujo_ON[p,o,n,v]*model.VOLU[p] for p in list({tupla[0] for tupla in list(model.Flujo_ON) if tupla[1:] == (o,n,v)}))/model.Q_vol[v]))
                
        #Agregar restricciones de Cantidad de viajes por arco planta-hub-vehiculo
        for (o,h,v) in O_H_V:
                model.constraints.add(model.Viajes_VOH[o,h,v] >=
                                        (sum(model.Flujo_OH[p,o,h,v]*model.PU[p] for p in list({tupla[0] for tupla in list(model.Flujo_OH) if tupla[1:] == (o,h,v)}))/model.Q_peso[v]))
                model.constraints.add(model.Viajes_VOH[o,h,v] >=
                                        (sum(model.Flujo_OH[p,o,h,v]*model.VOLU[p] for p in list({tupla[0] for tupla in list(model.Flujo_OH) if tupla[1:] == (o,h,v)}))/model.Q_vol[v]))
                
        #Agregar restricciones de Cantidad de viajes por arco cedi nacional-hub-vehiculo
        for (n,h,v) in N_H_V:
                model.constraints.add(model.Viajes_VNH[n,h,v] >= 
                                        (sum(model.Flujo_NH[p,n,h,v]*model.PU[p] for p in list({tupla[0] for tupla in list(model.Flujo_NH) if tupla[1:] == (n,h,v)}))/model.Q_peso[v]))
                model.constraints.add(model.Viajes_VNH[n,h,v] >= 
                                        (sum(model.Flujo_NH[p,n,h,v]*model.VOLU[p] for p in list({tupla[0] for tupla in list(model.Flujo_NH) if tupla[1:] == (n,h,v)}))/model.Q_vol[v]))
                
        #Agregar restricciones de Cantidad de viajes por arco cedi nacional-almacen regional-vehiculo
        for (n,r,v) in N_R_V:
                model.constraints.add(model.Viajes_VNR[n,r,v] >= 
                                        (sum(model.Flujo_NR[p,n,r,f,v]*model.PU[p] for (p,f) in list({(tupla[0],tupla[3]) for tupla in list(model.Flujo_NR) if (tupla[1],tupla[2],tupla[4]) == (n,r,v)}))/model.Q_peso[v]))
                model.constraints.add(model.Viajes_VNR[n,r,v] >= 
                                        (sum(model.Flujo_NR[p,n,r,f,v]*model.VOLU[p] for (p,f) in list({(tupla[0],tupla[3]) for tupla in list(model.Flujo_NR) if (tupla[1],tupla[2],tupla[4]) == (n,r,v)}))/model.Q_vol[v]))

        #Agregar restricciones de Cantidad de viajes por arco hub-almacen regional-vehiculo
        for (h,r,v) in H_R_V:
                model.constraints.add(model.Viajes_VHR[h,r,v] >= 
                                        (sum(model.Flujo_HR[p,h,r,f,v]*model.PU[p] for (p,f) in list({(tupla[0],tupla[3]) for tupla in list(model.Flujo_HR) if (tupla[1],tupla[2],tupla[4])  == (h,r,v)}))/model.Q_peso[v]))
                model.constraints.add(model.Viajes_VHR[h,r,v] >= 
                                        (sum(model.Flujo_HR[p,h,r,f,v]*model.VOLU[p] for (p,f) in list({(tupla[0],tupla[3]) for tupla in list(model.Flujo_HR) if (tupla[1],tupla[2],tupla[4]) == (h,r,v)}))/model.Q_vol[v]))
                
        #Agregar restricciones de Cantidad de viajes por arco almacen regional nivel 1-almacen regional nivel 2-vehiculo
        for (j,k,v) in J_K_V:
                model.constraints.add(model.Viajes_VJK[j,k,v] >= 
                                        (sum(model.Flujo_JK[p,j,k,f,v]*model.PU[p] for (p,f) in list({(tupla[0],tupla[3]) for tupla in list(model.Flujo_JK) if (tupla[1],tupla[2],tupla[4]) == (j,k,v)}))/model.Q_peso[v]))
                model.constraints.add(model.Viajes_VJK[j,k,v] >=
                                        (sum(model.Flujo_JK[p,j,k,f,v]*model.VOLU[p] for (p,f) in list({(tupla[0],tupla[3]) for tupla in list(model.Flujo_JK) if (tupla[1],tupla[2],tupla[4]) == (j,k,v)}))/model.Q_vol[v]))    

        #Agregar restricciones de Cantidad de viajes por arco almacen regional nivel 2-almacen regional nivel 3-vehiculo
        for (k,l,v) in K_L_V:
                model.constraints.add(model.Viajes_VKL[k,l,v] >= 
                                        (sum(model.Flujo_KL[p,k,l,f,v]*model.PU[p] for (p,f) in list({(tupla[0],tupla[3]) for tupla in list(model.Flujo_KL) if (tupla[1],tupla[2],tupla[4]) == (k,l,v)}))/model.Q_peso[v]))
                model.constraints.add(model.Viajes_VKL[k,l,v] >= 
                                        (sum(model.Flujo_KL[p,k,l,f,v]*model.VOLU[p] for (p,f) in list({(tupla[0],tupla[3]) for tupla in list(model.Flujo_KL) if (tupla[1],tupla[2],tupla[4])  == (k,l,v)}))/model.Q_vol[v]))
                
        #Agregar restricciones de Cantidad de viajes por arco almacen regional nivel 3-almacen regional nivel 4-vehiculo
        for (l,m,v) in L_M_V:
                model.constraints.add(model.Viajes_VLM[l,m,v] >=
                                        (sum(model.Flujo_LM[p,l,m,f,v]*model.PU[p] for (p,f) in list({(tupla[0],tupla[3]) for tupla in list(model.Flujo_LM) if (tupla[1],tupla[2],tupla[4])  == (l,m,v)}))/model.Q_peso[v]))
                model.constraints.add(model.Viajes_VLM[l,m,v] >= 
                                        (sum(model.Flujo_LM[p,l,m,f,v]*model.VOLU[p] for (p,f) in list({(tupla[0],tupla[3]) for tupla in list(model.Flujo_LM) if (tupla[1],tupla[2],tupla[4]) == (l,m,v)}))/model.Q_vol[v]))    

        #*************Balance de flujos **************
        #Agregar restricciones de Balance de flujos en cedis nacionales
        
        for (p,n) in P_N:
                model.constraints.add(sum(model.Flujo_ON[p,o,n,v] for (o,v) in list({(tupla[1],tupla[3]) for tupla in list(model.Flujo_ON) if (tupla[0],tupla[2]) == (p,n)}))>=  
                                        (sum(model.Flujo_NR[p,n,r,f,v] for (r,f,v) in list({(tupla[2],tupla[3],tupla[4]) for tupla in list(model.Flujo_NR) if (tupla[0],tupla[1]) == (p,n)}))
                                        +sum(model.Flujo_NH[p,n,h,v] for (h,v) in list({(tupla[2],tupla[3]) for tupla in list(model.Flujo_NH) if (tupla[0],tupla[1]) == (p,n)}))))
                
        #Agregar restricciones de Balance de flujos en Hubs
        for (p,h) in P_H:
                model.constraints.add((sum(model.Flujo_OH[p,o,h,v] for (o,v) in list({(tupla[1],tupla[3]) for tupla in list(model.Flujo_OH) if (tupla[0],tupla[2]) == (p,h)}))
                                        +sum(model.Flujo_NH[p,n,h,v] for (n,v) in list({(tupla[1],tupla[3]) for tupla in list(model.Flujo_NH) if (tupla[0],tupla[2]) == (p,h)}))) >= 
                                        sum(model.Flujo_HR[p,h,r,f,v] for (r,f,v) in list({(tupla[2],tupla[3],tupla[4]) for tupla in list(model.Flujo_HR) if (tupla[0],tupla[1]) == (p,h)})))

        
        #Agregar restricciones de Balance de flujos en regionales de nivel 1 solo directos
        for (p,r) in P_R_Dir:
                model.constraints.add((sum(model.Flujo_NR[p,n,r,f,v] for (n,f,v) in list({(tupla[1],tupla[3],tupla[4]) for tupla in list(model.Flujo_NR) if (tupla[0],tupla[2]) == (p,r)}))
                                        +sum(model.Flujo_HR[p,h,r,f,v] for (h,f,v) in list({(tupla[1],tupla[3],tupla[4]) for tupla in list(model.Flujo_HR) if (tupla[0],tupla[2]) == (p,r)}))) 
                                        >= model.D[p,r])
                        
        #Agregar restricciones de Balance de flujos en regionales de nivel 1 de redespachos y multi-paradas
        for (p,j) in P_J:
                model.constraints.add((sum(model.Flujo_NR[p,n,j,f,v] for (n,f,v) in list({(tupla[1],tupla[3],tupla[4]) for tupla in list(model.Flujo_NR) if (tupla[0],tupla[2]) == (p,j)}))
                                        +sum(model.Flujo_HR[p,h,j,f,v] for (h,f,v) in list({(tupla[1],tupla[3],tupla[4]) for tupla in list(model.Flujo_HR) if (tupla[0],tupla[2]) == (p,j)}))) 
                                        >= model.D[p,j]+sum(model.Flujo_JK[p,j,k,f,v] for (k,f,v) in list({(tupla[2],tupla[3],tupla[4]) for tupla in list(model.Flujo_JK) if (tupla[0],tupla[1]) == (p,j)})))

        #Agregar restricciones de Balance de flujos  en regionales de nivel 2 - redespachos
        for (p,k) in P_K_Rede:
                model.constraints.add((sum(model.Flujo_NR[p,n,k,f,v] for (n,f,v) in list({(tupla[1],tupla[3],tupla[4]) for tupla in list(model.Flujo_NR) if (tupla[0],tupla[2]) == (p,k)}))
                                        +sum(model.Flujo_HR[p,h,k,f,v] for (h,f,v) in list({(tupla[1],tupla[3],tupla[4]) for tupla in list(model.Flujo_HR) if (tupla[0],tupla[2]) == (p,k)}))
                                        +sum(model.Flujo_JK[p,j,k,f,v] for (j,f,v) in list({(tupla[1],tupla[3],tupla[4]) for tupla in list(model.Flujo_JK) if (tupla[0],tupla[2]) == (p,k)})))
                                        >= model.D[p,k])

        #Agregar restricciones de Balance de flujos  en regionales de nivel 2 - multiparadas
        for (p,k) in P_K_Mult:
                model.constraints.add((sum(model.Flujo_NR[p,n,k,f,v] for (n,f,v) in list({(tupla[1],tupla[3],tupla[4]) for tupla in list(model.Flujo_NR) if (tupla[0],tupla[2]) == (p,k)}))
                                        +sum(model.Flujo_HR[p,h,k,f,v] for (h,f,v) in list({(tupla[1],tupla[3],tupla[4]) for tupla in list(model.Flujo_HR) if (tupla[0],tupla[2]) == (p,k)}))
                                        +sum(model.Flujo_JK[p,j,k,f,v] for (j,f,v) in list({(tupla[1],tupla[3],tupla[4]) for tupla in list(model.Flujo_JK) if (tupla[0],tupla[2]) == (p,k)})))
                                        >= model.D[p,k]+sum(model.Flujo_KL[p,k,l,f,v] for (l,f,v) in list({(tupla[2],tupla[3],tupla[4]) for tupla in list(model.Flujo_KL) if (tupla[0],tupla[1]) == (p,k)})))

        #Agregar restricciones de Balance de flujos  en regionales de nivel 3 - multiparadas
        for (p,l) in P_L:
                model.constraints.add((sum(model.Flujo_NR[p,n,l,f,v] for (n,f,v) in list({(tupla[1],tupla[3],tupla[4]) for tupla in list(model.Flujo_NR) if (tupla[0],tupla[2]) == (p,l)}))
                                        +sum(model.Flujo_HR[p,h,l,f,v] for (h,f,v) in list({(tupla[1],tupla[3],tupla[4]) for tupla in list(model.Flujo_HR) if (tupla[0],tupla[2]) == (p,l)}))
                                        +sum(model.Flujo_KL[p,k,l,f,v] for (k,f,v) in list({(tupla[1],tupla[3],tupla[4]) for tupla in list(model.Flujo_KL) if (tupla[0],tupla[2]) == (p,l)})))
                                        >= model.D[p,l]+sum(model.Flujo_LM[p,l,m,f,v] for (m,f,v) in list({(tupla[2],tupla[3],tupla[4]) for tupla in list(model.Flujo_LM) if (tupla[0],tupla[1]) == (p,l)})))

        #Agregar restricciones de Balance de flujos  en regionales de nivel 4 - multiparadas
        for (p,m) in P_M:
                model.constraints.add((sum(model.Flujo_NR[p,n,m,f,v] for (n,f,v) in list({(tupla[1],tupla[3],tupla[4]) for tupla in list(model.Flujo_NR) if (tupla[0],tupla[2]) == (p,m)}))
                                        +sum(model.Flujo_HR[p,h,m,f,v] for (h,f,v) in list({(tupla[1],tupla[3],tupla[4]) for tupla in list(model.Flujo_HR) if (tupla[0],tupla[2]) == (p,m)}))
                                        +sum(model.Flujo_LM[p,l,m,f,v] for (l,f,v) in list({(tupla[1],tupla[3],tupla[4]) for tupla in list(model.Flujo_LM) if (tupla[0],tupla[2]) == (p,m)})))
                                        >= model.D[p,m])


        #***************Conservación tipo vehículo en multi-paradas***************
        #Agregar restricciones de Conservación tipo vehículo en multi-paradas en regionales de nivel 1 multi-parada
        for (p,j,v) in P_J_V_Mult:
                model.constraints.add((sum(model.Flujo_NR[p,n,j,f,v] for (n,f) in list({(tupla[1],tupla[3]) for tupla in list(model.Flujo_NR) if (tupla[0],tupla[2],tupla[4]) == (p,j,v)}))
                                +sum(model.Flujo_HR[p,h,j,f,v] for (h,f) in list({(tupla[1],tupla[3]) for tupla in list(model.Flujo_HR) if (tupla[0],tupla[2],tupla[4]) == (p,j,v)})))
                                >= 
                                (sum(model.Flujo_RC[p,j,c,v] for (j,c) in list({(tupla[1],tupla[2]) for tupla in list(model.Flujo_RC) if (tupla[0],tupla[1],tupla[3]) == (p,j,v)}))
                                +sum(model.Flujo_JK[p,j,k,f,v] for (k,f) in list({(tupla[2],tupla[3]) for tupla in list(model.Flujo_JK) if (tupla[0],tupla[1],tupla[4]) == (p,j,v)}))))
                                

        #Agregar restricciones de Conservación tipo vehículo en multi-paradas en regionales de nivel 2 multi-parada
        for (p,k,v) in P_K_V_Mult:
                model.constraints.add((sum(model.Flujo_NR[p,n,k,f,v] for (n,f) in list({(tupla[1],tupla[3]) for tupla in list(model.Flujo_NR) if (tupla[0],tupla[2],tupla[4]) == (p,k,v)}))
                                +sum(model.Flujo_HR[p,h,k,f,v] for (h,f) in list({(tupla[1],tupla[3]) for tupla in list(model.Flujo_HR) if (tupla[0],tupla[2],tupla[4]) == (p,k,v)}))
                                +sum(model.Flujo_JK[p,j,k,f,v] for (j,f) in list({(tupla[1],tupla[3]) for tupla in list(model.Flujo_JK) if (tupla[0],tupla[2],tupla[4]) == (p,k,v)})))
                                >= 
                                (sum(model.Flujo_RC[p,k,c,v] for (k,c) in list({(tupla[1],tupla[2]) for tupla in list(model.Flujo_RC) if (tupla[0],tupla[1],tupla[3]) == (p,k,v)}))
                                +sum(model.Flujo_KL[p,k,l,f,v] for (l,f) in list({(tupla[2],tupla[3]) for tupla in list(model.Flujo_KL) if (tupla[0],tupla[1],tupla[4]) == (p,k,v)}))))
                                
        #Agregar restricciones de Conservación tipo vehículo en multi-paradas en regionales de nivel 3 multi-parada
        for (p,l,v) in P_L_V_Mult:
                model.constraints.add((sum(model.Flujo_NR[p,n,l,f,v] for (n,f) in list({(tupla[1],tupla[3]) for tupla in list(model.Flujo_NR) if (tupla[0],tupla[2],tupla[4]) == (p,l,v)}))
                                +sum(model.Flujo_HR[p,h,l,f,v] for (h,f) in list({(tupla[1],tupla[3]) for tupla in list(model.Flujo_HR) if (tupla[0],tupla[2],tupla[4]) == (p,l,v)}))
                                +sum(model.Flujo_KL[p,k,l,f,v] for (k,f) in list({(tupla[1],tupla[3]) for tupla in list(model.Flujo_KL) if (tupla[0],tupla[2],tupla[4]) == (p,l,v)})))
                                >= 
                                (sum(model.Flujo_RC[p,l,c,v] for (l,c) in list({(tupla[1],tupla[2]) for tupla in list(model.Flujo_RC) if (tupla[0],tupla[1],tupla[3]) == (p,l,v)}))
                                +sum(model.Flujo_LM[p,l,m,f,v] for (m,f) in list({(tupla[2],tupla[3]) for tupla in list(model.Flujo_LM) if (tupla[0],tupla[1],tupla[4]) == (p,l,v)}))))


        #***********Garantizar multi-parada completa *********************
        #Agregar restricciones para garantizar que la ruta de multi-parada completa (si es óptimo)
        # for (p,j,k,l) in P_J_K_L:
        #     model.constraints.add(model.BRJ[p,j,k]==model.BRK[p,k,l]) #Garantiza que, si se hace el arco j-k, se haga también el arco k-l
        
        # for (p,k,l,m) in P_K_L_M:
        #     model.constraints.add(model.BRK[p,k,l]==model.BRL[p,l,m]) #Garantiza que, si se hace el arco k-l, se haga también el arco l-m
        
        for (j,k,l) in J_K_L:
                model.constraints.add(sum(model.BRJ[p,j,k] for p in list({tupla[0] for tupla in list(model.BRJ) if (tupla[1],tupla[2]) == (j,k)}))
                                ==sum(model.BRK[p,k,l]for p in list({tupla[0] for tupla in list(model.BRK) if (tupla[1],tupla[2]) == (k,l)}))) #Garantiza que, si se hace el arco j-k, se haga también el arco k-l
        
        for (k,l,m) in K_L_M:
                model.constraints.add(sum(model.BRK[p,k,l] for p in list({tupla[0] for tupla in list(model.BRK) if (tupla[1],tupla[2]) == (k,l)}))
                                ==sum(model.BRL[p,l,m]for p in list({tupla[0] for tupla in list(model.BRL) if (tupla[1],tupla[2]) == (l,m)}))) #Garantiza que, si se hace el arco k-l, se haga también el arco l-m
                
        
        
        
        #************Selección de restricciones  -  Frecuencia ***********
        #defirir el valor del Parametro BigM que controlará la selección de una única frecuencia por producto-destino
        BigM_F=1000000000
        #Agregar restricciones de flujo por cada frecuencia  en regionales de nivel 1
        for (p,r,f) in P_R_F:
                model.constraints.add((sum(model.Flujo_NR[p,n,r,f,v] for (n,v) in list({(tupla[1],tupla[4]) for tupla in list(model.Flujo_NR) if (tupla[0],tupla[2],tupla[3]) == (p,r,f)}))
                                +sum(model.Flujo_HR[p,h,r,f,v] for (h,v) in list({(tupla[1],tupla[4]) for tupla in list(model.Flujo_HR) if (tupla[0],tupla[2],tupla[3]) == (p,r,f)})))
                                <=BigM_F*model.BF[p,r,f])
        #Agregar restricciones de flujo por cada frecuencia  en regionales de nivel 2
        for (p,k,f) in P_K_F:
                model.constraints.add((sum(model.Flujo_NR[p,n,k,f,v] for (n,v) in list({(tupla[1],tupla[4]) for tupla in list(model.Flujo_NR) if (tupla[0],tupla[2],tupla[3]) == (p,k,f)}))
                                +sum(model.Flujo_HR[p,h,k,f,v] for (h,v) in list({(tupla[1],tupla[4]) for tupla in list(model.Flujo_HR) if (tupla[0],tupla[2],tupla[3]) == (p,k,f)}))
                                +sum(model.Flujo_JK[p,j,k,f,v] for (j,v) in list({(tupla[1],tupla[4]) for tupla in list(model.Flujo_JK) if (tupla[0],tupla[2],tupla[3]) == (p,k,f)})))
                                <=BigM_F*model.BF[p,k,f])
        
        #Agregar restricciones de flujo por cada frecuencia  en regionales de nivel 3
        for (p,l,f) in P_L_F:
                model.constraints.add((sum(model.Flujo_NR[p,n,l,f,v] for (n,v) in list({(tupla[1],tupla[4]) for tupla in list(model.Flujo_NR) if (tupla[0],tupla[2],tupla[3]) == (p,l,f)}))
                                +sum(model.Flujo_HR[p,h,l,f,v] for (h,v) in list({(tupla[1],tupla[4]) for tupla in list(model.Flujo_HR) if (tupla[0],tupla[2],tupla[3]) == (p,l,f)}))
                                +sum(model.Flujo_KL[p,k,l,f,v] for (k,v) in list({(tupla[1],tupla[4]) for tupla in list(model.Flujo_KL) if (tupla[0],tupla[2],tupla[3]) == (p,l,f)})))
                                <=BigM_F*model.BF[p,l,f])
        #Agregar restricciones de flujo por cada frecuencia  en regionales de nivel 4
        for (p,m,f) in P_M_F:
                model.constraints.add((sum(model.Flujo_NR[p,n,m,f,v] for (n,v) in list({(tupla[1],tupla[4]) for tupla in list(model.Flujo_NR) if (tupla[0],tupla[2],tupla[3]) == (p,m,f)}))
                                +sum(model.Flujo_HR[p,h,m,f,v] for (h,v) in list({(tupla[1],tupla[4]) for tupla in list(model.Flujo_HR) if (tupla[0],tupla[2],tupla[3]) == (p,m,f)}))
                                +sum(model.Flujo_LM[p,l,m,f,v] for (l,v) in list({(tupla[1],tupla[4]) for tupla in list(model.Flujo_LM) if (tupla[0],tupla[2],tupla[3]) == (p,m,f)})))
                                <=BigM_F*model.BF[p,m,f])
        #Agregar restricciones para selección de frecuencia en regionales de todos los niveles garantizando una única frecuencia por producto-destino
        for (p,r) in P_R:
                model.constraints.add(sum(model.BF[p,r,f] for f in list({(tupla[2]) for tupla in list(model.BF) if (tupla[0],tupla[1]) == (p,r)}))==1)
        
        
        #***********Garantizar misma frecuencia por producto en multi-parada *********************
        #Agregar restricciones para garantizar igual frecuencia por producto en la multi-parada completa (si es óptimo)
        for (p,j,k,f) in P_J_K_F_Mult:
                model.constraints.add(model.BF[p,j,f]==model.BF[p,k,f]) #Garantiza que, si el producto p es abastecido al almacen regional j en la frecuencia f, se abastesca  en la misma frecuencia al almacen regional k
        
        for (p,k,l,f) in P_K_L_F_Mult:
                model.constraints.add(model.BF[p,k,f]==model.BF[p,l,f]) #Garantiza que, si el producto p es abastecido al almacen regional k en la frecuencia f, se abastesca  en la misma frecuencia al almacen regional l

        for (p,l,m,f) in P_L_M_F_Mult:
                model.constraints.add(model.BF[p,l,f]==model.BF[p,m,f]) #Garantiza que, si el producto p es abastecido al almacen regional k en la frecuencia f, se abastesca  en la misma frecuencia al almacen regional l
                                

        #************Selección de restricciones   Relación Viajes-  Frecuencia******************
        #Agregar restricciones para garantizar la relación viajes- Frecuencia por cada almacen regional (de todos los niveles) y producto
        for (p,r) in P_R_Dir:
                model.constraints.add(sum(model.Viajes_VNR[n,r,v] for (n,v) in list({(tupla[0],tupla[2]) for tupla in list(model.Viajes_VNR) if tupla[1] == r}))
                                +sum(model.Viajes_VHR[h,r,v] for (h,v) in list({(tupla[0],tupla[2]) for tupla in list(model.Viajes_VHR) if tupla[1] == r}))
                                >=
                                sum((24*model.BF[p,r,f]/f) for f in list({tupla[2] for tupla in list(model.BF) if (tupla[0],tupla[1]) == (p,r)}))) 


        #Agregar restricciones para garantizar la relación viajes- Frecuencia por cada almacen regional nivel 2 y producto
        for (p,k) in P_K:
                model.constraints.add(sum(model.Viajes_VNR[n,k,v] for (n,v) in list({(tupla[0],tupla[2]) for tupla in list(model.Viajes_VNR) if tupla[1] == k}))
                                +sum(model.Viajes_VHR[h,k,v] for (h,v) in list({(tupla[0],tupla[2]) for tupla in list(model.Viajes_VHR) if tupla[1] == k}))
                                +sum(model.Viajes_VJK[j,k,v] for (j,v) in list({(tupla[0],tupla[2]) for tupla in list(model.Viajes_VJK) if tupla[1] == k}))
                                >=
                                sum((24*model.BF[p,k,f]/f) for f in list({tupla[2] for tupla in list(model.BF) if (tupla[0],tupla[1]) == (p,k)}))) 
        
        
        #Agregar restricciones para garantizar la relación viajes- Frecuencia por cada almacen regional nivel 3 y producto
        for (p,l) in P_L:
                model.constraints.add(sum(model.Viajes_VNR[n,l,v] for (n,v) in list({(tupla[0],tupla[2]) for tupla in list(model.Viajes_VNR) if tupla[1] == l}))
                                +sum(model.Viajes_VHR[h,l,v] for (h,v) in list({(tupla[0],tupla[2]) for tupla in list(model.Viajes_VHR) if tupla[1] == l}))
                                +sum(model.Viajes_VKL[k,l,v] for (k,v) in list({(tupla[0],tupla[2]) for tupla in list(model.Viajes_VKL) if tupla[1] == l}))
                                >=
                                sum((24*model.BF[p,l,f]/f) for f in list({tupla[2] for tupla in list(model.BF) if (tupla[0],tupla[1]) == (p,l)}))) 
        
        #Agregar restricciones para garantizar la relación viajes- Frecuencia por cada almacen regional nivel 4 y producto
        for (p,m) in P_M:
                model.constraints.add(sum(model.Viajes_VNR[n,m,v] for (n,v) in list({(tupla[0],tupla[2]) for tupla in list(model.Viajes_VNR) if tupla[1] == m}))
                                +sum(model.Viajes_VHR[h,m,v] for (h,v) in list({(tupla[0],tupla[2]) for tupla in list(model.Viajes_VHR) if tupla[1] == m}))
                                +sum(model.Viajes_VLM[l,m,v] for (l,v) in list({(tupla[0],tupla[2]) for tupla in list(model.Viajes_VLM) if tupla[1] == m}))
                                >=
                                sum((24*model.BF[p,m,f]/f) for f in list({tupla[2] for tupla in list(model.BF) if (tupla[0],tupla[1]) == (p,m)}))) 
                
        
        #************Selección de restricciones: único Origen por producto-almacen regional *************
        #defirir el valor del Parametro BigM que controlará la selección de un único Origen por producto-destino
        BigM_N=1000000000
        BigM_H=1000000000
        BigM_J=1000000000
        BigM_K=1000000000
        BigM_L=1000000000
        #Agregar restricciones de flujo por cada combinación Cedi nacional-almacén regional
        for (p,n,r) in P_N_R:
                model.constraints.add(sum(model.Flujo_NR[p,n,r,f,v] for (f,v) in list({(tupla[3],tupla[4]) for tupla in list(model.Flujo_NR) if (tupla[0],tupla[1],tupla[2]) == (p,n,r)}))
                                <=BigM_N*model.BN[p,n,r])
        #Agregar restricciones de flujo por cada combinación Hub-almacén regional
        for (p,h,r) in P_H_R:
                model.constraints.add(sum(model.Flujo_HR[p,h,r,f,v] for (f,v) in list({(tupla[3],tupla[4]) for tupla in list(model.Flujo_HR) if (tupla[0],tupla[1],tupla[2]) == (p,h,r)}))
                                <=BigM_H*model.BH[p,h,r])   
        
        #Agregar restricciones de flujo por cada combinación almacén regional nivel 1 - almacén regional nivel 2 
        for (p,j,k) in P_J_K:
                model.constraints.add(sum(model.Flujo_JK[p,j,k,f,v] for (f,v) in list({(tupla[3],tupla[4]) for tupla in list(model.Flujo_JK) if (tupla[0],tupla[1],tupla[2]) == (p,j,k)}))
                                <=BigM_J*model.BRJ[p,j,k])    
        
        #Agregar restricciones de flujo por cada combinación almacén regional nivel 2 - almacén regional nivel 3 
        for (p,k,l) in P_K_L:
                model.constraints.add(sum(model.Flujo_KL[p,k,l,f,v] for (f,v) in list({(tupla[3],tupla[4]) for tupla in list(model.Flujo_KL) if (tupla[0],tupla[1],tupla[2]) == (p,k,l)}))
                                <=BigM_K*model.BRK[p,k,l])  

        #Agregar restricciones de flujo por cada combinación almacén regional nivel 3 - almacén regional nivel 4 
        for (p,l,m) in P_L_M:
                model.constraints.add(sum(model.Flujo_LM[p,l,m,f,v] for (f,v) in list({(tupla[3],tupla[4]) for tupla in list(model.Flujo_LM) if (tupla[0],tupla[1],tupla[2]) == (p,l,m)}))
                                <=BigM_L*model.BRL[p,l,m])
        
        # Agregar restricciones para selección de único origen por producto-almacén regional en regionales de nivel 1
        for (p,r) in P_R_Dir:
                model.constraints.add((sum(model.BN[p,n,r] for n in list({tupla[1] for tupla in list(model.BN) if (tupla[0],tupla[2]) == (p,r)}))
                                +sum(model.BH[p,h,r] for h in list({tupla[1] for tupla in list(model.BH) if (tupla[0],tupla[2]) == (p,r)})))
                                <=1)
        
        # Agregar restricciones para selección de único origen por producto-almacén regional en regionales de nivel 2
        for (p,k) in P_K:
                model.constraints.add((sum(model.BN[p,n,k] for n in list({tupla[1] for tupla in list(model.BN) if (tupla[0],tupla[2]) == (p,k)}))
                                +sum(model.BH[p,h,k] for h in list({tupla[1] for tupla in list(model.BH) if (tupla[0],tupla[2]) == (p,k)}))
                                +sum(model.BRJ[p,j,k] for j in list({tupla[1] for tupla in list(model.BRJ) if (tupla[0],tupla[2]) == (p,k)})))
                                <=1)

        # Agregar restricciones para selección de único origen por producto-almacén regional en regionales de nivel 3
        for (p,l) in P_L:
                model.constraints.add((sum(model.BN[p,n,l] for n in list({tupla[1] for tupla in list(model.BN) if (tupla[0],tupla[2]) == (p,l)}))
                                +sum(model.BH[p,h,l] for h in list({tupla[1] for tupla in list(model.BH) if (tupla[0],tupla[2]) == (p,l)}))
                                +sum(model.BRK[p,k,l] for k in list({tupla[1] for tupla in list(model.BRK) if (tupla[0],tupla[2]) == (p,l)})))
                                <=1) 
        
        
        # Agregar restricciones para selección de único origen por producto-almacén regional en regionales de nivel 4
        for (p,m) in P_M:
                model.constraints.add((sum(model.BN[p,n,m] for n in list({tupla[1] for tupla in list(model.BN) if (tupla[0],tupla[2]) == (p,m)}))
                                +sum(model.BH[p,h,m] for h in list({tupla[1] for tupla in list(model.BH) if (tupla[0],tupla[2]) == (p,m)}))
                                +sum(model.BRL[p,l,m] for l in list({tupla[1] for tupla in list(model.BRL) if (tupla[0],tupla[2]) == (p,m)})))
                                <=1)     
        
        
        #******************Demanda*****************
        # Agregar restricciones para garantizar el cumplimiento de la demanda en cada almacén regional
        for (p,c) in P_C:
                model.constraints.add((sum(model.Flujo_RC[p,r,c,v] for (r,v) in list({(tupla[1],tupla[3]) for tupla in list(model.Flujo_RC) if (tupla[0],tupla[2]) 
                                                                                == (p,c)}))) >=model.D[p,c])   
        
        #****************** Calcular Frecuencias de abastecimiento   *************
        for (p,r) in P_R:
                model.constraints.add(model.Frecuencia_FA[p,r]==sum(f*model.BF[p,r,f] for f in list({tupla[2] for tupla in list(model.BF) if (tupla[0],tupla[1]) == (p,r)})))

        
        #************ Calcular Inventario  promedio en cada Almacen regional por producto  *************
        for (p,r) in P_R:
                model.constraints.add(model.Inventario_IR[p,r] == 
                                (model.ZRoja[p,r]
                                +((model.Frecuencia_FA[p,r]*model.ADU[p,r])/2)))
        

             
                        
                        

        #************Selección de restricciones: Cuales hubs habilitar *************
        #defirir el valor del Parametro BigM que controlará la selección de hubs a habilitar
        BigM_Hub=1000000000
        
        # Agregar restricciones para selección de los hubs a habilitar
        for h in model.Hubs:
                model.constraints.add((sum(model.Flujo_OH[p,o,h,v] for (p,o,v) in list({(tupla[0],tupla[1],tupla[3]) for tupla in list(model.Flujo_OH) if tupla[2] == h}))
                                      +sum(model.Flujo_NH[p,n,h,v] for (p,n,v) in list({(tupla[0],tupla[1],tupla[3]) for tupla in list(model.Flujo_NH) if tupla[2] == h}))) 
                                      <=BigM_Hub*model.BHub[h])
                model.constraints.add(sum(model.Flujo_HR[p,h,r,f,v] for (p,r,f,v) in list({(tupla[0],tupla[2],tupla[3],tupla[4]) for tupla in list(model.Flujo_HR) if tupla[1] == h}))
                                      <=BigM_Hub*model.BHub[h]) 
                
                model.constraints.add((sum(model.Viajes_VOH[o,h,v] for (o,v) in list({(tupla[0],tupla[2]) for tupla in list(model.Viajes_VOH) if tupla[1] == h}))
                                      +sum(model.Viajes_VNH[n,h,v] for (n,v) in list({(tupla[0],tupla[2]) for tupla in list(model.Viajes_VNH) if tupla[1] == h}))) 
                                      <=BigM_Hub*model.BHub[h])
                model.constraints.add(sum(model.Viajes_VHR[h,r,v] for (r,v) in list({(tupla[1],tupla[2]) for tupla in list(model.Viajes_VHR) if tupla[0] == h}))
                                      <=BigM_Hub*model.BHub[h])
        
        return model    

        
def Crear_restricciones_frecuencias__libres_menores_a_6(model,P_R):
        # ********* No empeorar Frecuencias de Abastecimiento actuales   *************
        # Agregar restricciones para garantizar no empeorar Frecuencias de Abastecimiento actuales de cada producto en cada almacen regional 
        for (p,r) in P_R:
                if (p,r) in list (model.FrAb):
                        if model.FrAb[p,r]<=6:
                                model.constraints.add(model.Frecuencia_FA[p,r] <= model.FrAb[p,r])
                        else: 
                                model.constraints.add(model.Frecuencia_FA[p,r] == model.FrAb[p,r])        
                #else:
                        #model.constraints.add(model.Frecuencia_FA[p,r] == 0)
        return model

def Crear_restricciones_frecuencias_todas_libres(model,P_R):
        # ********* No empeorar Frecuencias de Abastecimiento actuales   *************
        # Agregar restricciones para garantizar no empeorar Frecuencias de Abastecimiento actuales de cada producto en cada almacen regional 
        for (p,r) in P_R:
                if (p,r) in list (model.FrAb):
                        model.constraints.add(model.Frecuencia_FA[p,r] <= model.FrAb[p,r])
 

def Crear_restricciones_baseline(model,P_R,P_O_N_V,P_N_R_V,P_J_K_V,P_K_L_V,P_L_M_V,O_H_V,N_H_V,H_R_V):

        #************ Anulación de flujos  y viajes desde y hacia hub  *************
        # Agregar restricciones para anular flujos de plantas a hubs
        for h in list(model.Hubs):
                model.constraints.add(sum(model.Flujo_OH[p,o,h,v] for (p,o,v) in list({(tupla[0],tupla[1],tupla[3]) for tupla in list(model.Flujo_OH) if tupla[2] == h}))
                                ==0)
        # Agregar restricciones para anular flujos de cedis nacionales  a hubs
        for h in list(model.Hubs):
                model.constraints.add(sum(model.Flujo_NH[p,n,h,v] for (p,n,v) in list({(tupla[0],tupla[1],tupla[3]) for tupla in list(model.Flujo_NH) if tupla[2] == h}))
                                ==0)
        # Agregar restricciones para anular flujos desde hubs  hacia almacenes regionales
        for h in list(model.Hubs):
                model.constraints.add(sum(model.Flujo_HR[p,h,r,f,v] for (p,r,f,v) in list({(tupla[0],tupla[2],tupla[3],tupla[4]) for tupla in list(model.Flujo_HR) if tupla[1] == h}))
                                ==0)
                
                   
        #Agregar restricciones para anular los viajes viajes por arco planta-hub-vehiculo
        for (o,h,v) in O_H_V:
                model.constraints.add(model.Viajes_VOH[o,h,v] ==0)
                
        #Agregar restricciones para anular los viajes por arco cedi nacional-hub-vehiculo
        for (n,h,v) in N_H_V:
                model.constraints.add(model.Viajes_VNH[n,h,v] ==0)
                
        #Agregar restricciones para anular los viajes por arco hub-almacen regional-vehiculo
        for (h,r,v) in H_R_V:
                model.constraints.add(model.Viajes_VHR[h,r,v] ==0)
              
        
        # ********* Reflejar Frecuencias de Abastecimiento actuales   *************
        # Agregar restricciones para Reflejar Frecuencias de Abastecimiento actuales de cada producto en cada almacen regional 
        for (p,r) in P_R:
                if (p,r) in list (model.FrAb):
                        model.constraints.add(model.Frecuencia_FA[p,r] == model.FrAb[p,r])
                else:
                        model.constraints.add(model.Frecuencia_FA[p,r] == 0)
                        
        
        # ********* Reflejar flujos reales de linea base   *************
        #Agregar restricciones para Reflejar flujos reales de linea base desde plantas a cedis nacionales
        for (p,o,n,v) in P_O_N_V:
                if (p,o,n,v) in list(model.Q_ON):
                        model.constraints.add(model.Flujo_ON[p,o,n,v] == model.Q_ON[p,o,n,v]) 
                else:
                        model.constraints.add(model.Flujo_ON[p,o,n,v] == 0) 

        #Agregar restricciones para Reflejar flujos reales de linea base desde cedis nacionales a almacenes regionaes (directos)
        for (p,n,r,v) in P_N_R_V:
                if (p,n,r,v) in list(model.Q_NR):
                        model.constraints.add(sum(model.Flujo_NR[p,n,r,f,v] for f in list({tupla[3] for tupla in list(model.Flujo_NR) if (tupla[0],tupla[1],tupla[2],tupla[4]) == (p,n,r,v)}))
                                        >= round(model.Q_NR[p,n,r,v],0))
                else:
                        model.constraints.add(sum(model.Flujo_NR[p,n,r,f,v] for f in list({tupla[3] for tupla in list(model.Flujo_NR) if (tupla[0],tupla[1],tupla[2],tupla[4]) == (p,n,r,v)}))
                                        == 0)  
        
        #Agregar restricciones para Reflejar flujos reales de linea base desde  almacenes regionaes nivel 1 a almacenes regionaes nivel 2
        for (p,j,k,v) in P_J_K_V:
                if (p,j,k,v) in list(model.Q_JK):
                        model.constraints.add(sum(model.Flujo_JK[p,j,k,f,v] for f in list({tupla[3] for tupla in list(model.Flujo_JK) if (tupla[0],tupla[1],tupla[2],tupla[4]) == (p,j,k,v)}))
                                        >= model.Q_JK[p,j,k,v]) 
                else:
                        model.constraints.add(sum(model.Flujo_JK[p,j,k,f,v] for f in list({tupla[3] for tupla in list(model.Flujo_JK) if (tupla[0],tupla[1],tupla[2],tupla[4]) == (p,j,k,v)}))
                                        == 0)     

        #Agregar restricciones para Reflejar flujos reales de linea base desde  almacenes regionaes nivel 2 a almacenes regionaes nivel 3
        for (p,k,l,v) in P_K_L_V:
                if (p,k,l,v) in list(model.Q_KL):
                        model.constraints.add(sum(model.Flujo_KL[p,k,l,f,v] for f in list({tupla[3] for tupla in list(model.Flujo_KL) if (tupla[0],tupla[1],tupla[2],tupla[4]) == (p,k,l,v)}))
                                        >= model.Q_KL[p,k,l,v]) 
                else:
                        model.constraints.add(sum(model.Flujo_KL[p,k,l,f,v] for f in list({tupla[3] for tupla in list(model.Flujo_KL) if (tupla[0],tupla[1],tupla[2],tupla[4]) == (p,k,l,v)}))
                                        == 0)       

        #Agregar restricciones para Reflejar flujos reales de linea base desde  almacenes regionaes nivel 3 a almacenes regionaes nivel 4
        for (p,l,m,v) in P_L_M_V:
                if (p,l,m,v) in list(model.Q_LM):
                        model.constraints.add(sum(model.Flujo_LM[p,l,m,f,v] for f in list({tupla[3] for tupla in list(model.Flujo_LM) if (tupla[0],tupla[1],tupla[2],tupla[4]) == (p,l,m,v)}))
                                        >= model.Q_LM[p,l,m,v]) 
                else:
                        model.constraints.add(sum(model.Flujo_LM[p,l,m,f,v] for f in list({tupla[3] for tupla in list(model.Flujo_LM) if (tupla[0],tupla[1],tupla[2],tupla[4]) == (p,l,m,v)}))
                                        == 0)     
        return model


### 6. IMPRIMIR RESULTADOS DEL MODELO

def Crear_dict_dataframes_outputs(model,periodo,nombre_modelo):
    #Lista de indices Por combianción
    Indices_PONV=['Producto','Planta','Cedi Nacional','Vehículo']
    Indices_POHV=['Producto','Planta','Hub','Vehículo']
    Indices_PNRFV=['Producto','Cedi Nacional','Almacén Regional','Frecuencia','Vehículo']
    Indices_PNHV=['Producto','Cedi Nacional','Hub','Vehículo']
    Indices_PHRFV=['Producto','Hub','Almacén Regional','Frecuencia','Vehículo']
    Indices_PJKFV=['Producto','Almacén Regional Nivel 1','Almacén Regional Nivel 2','Frecuencia','Vehículo']
    Indices_PKLFV=['Producto','Almacén Regional Nivel 2','Almacén Regional Nivel 3','Frecuencia','Vehículo']
    Indices_PLMFV=['Producto','Almacén Regional Nivel 3','Almacén Regional Nivel 4','Frecuencia','Vehículo']
    Indices_PRCV=['Producto','Almacén Regional','Cliente','Vehículo']
    Indices_ONV=['Planta','Cedi Nacional','Vehículo']
    Indices_OHV=['Planta','Hub','Vehículo']
    Indices_NRV=['Cedi Nacional','Almacén Regional','Vehículo']
    Indices_NHV=['Cedi Nacional','Hub','Vehículo']
    Indices_HRV=['Hub','Almacén Regional','Vehículo']
    Indices_JKV=['Almacén Regional Nivel 1','Almacén Regional Nivel 2','Vehículo']
    Indices_KLV=['Almacén Regional Nivel 2','Almacén Regional Nivel 3','Vehículo']
    Indices_LMV=['Almacén Regional Nivel 3','Almacén Regional Nivel 4','Vehículo']
    Indices_PR=['Producto','Almacén Regional']
    Indices_PHR=['Producto','Hub','Almacén Regional']
    Indices_PNR=['Producto','Cedi Nacional','Almacén Regional']
    Indices_PJK=['Producto','Almacén Regional Nivel 1','Almacén Regional Nivel 2']
    Indices_PKL=['Producto','Almacén Regional Nivel 2','Almacén Regional Nivel 3']
    Indices_PLM=['Producto','Almacén Regional Nivel 3','Almacén Regional Nivel 4']
    Indices_PRF=['Producto','Almacén Regional','Frecuencia']

    #Crear diccionario con el Nombre de cada grupo de variables y la lista de los nombres de sus respectivos indices 
    Variables_Indices_dict={'Flujo_ON':Indices_PONV,'Flujo_OH':Indices_POHV,'Flujo_NR':Indices_PNRFV,'Flujo_NH':Indices_PNHV,'Flujo_HR':Indices_PHRFV,'Flujo_JK':Indices_PJKFV,
                            'Flujo_KL':Indices_PKLFV,'Flujo_LM':Indices_PLMFV,'Flujo_RC':Indices_PRCV,'Viajes_VON':Indices_ONV,'Viajes_VOH':Indices_OHV,'Viajes_VNH':Indices_NHV,
                            'Viajes_VNR':Indices_NRV,'Viajes_VHR':Indices_HRV,'Viajes_VJK':Indices_JKV,'Viajes_VKL':Indices_KLV,'Viajes_VLM':Indices_LMV,'Frecuencia_FA':Indices_PR,
                            'Inventario_IR':Indices_PR ,'BH':Indices_PHR,'BN':Indices_PNR,'BRJ':Indices_PJK,'BRK':Indices_PKL,'BRL':Indices_PLM,'BF':Indices_PRF,'BHub':['Hub'],
                            'CostoCapital':['Total'],'Costotte_ONV':['Total'],'Costotte_OHV':['Total'],'Costotte_NHV':['Total'],
                            'Costotte_NRV':['Total'],'Costotte_HRV':['Total'],
                            'Costotte_JKV':['Total'],'Costotte_KLV':['Total'],'Costotte_LMV':['Total']}


    # Extraer valores de las variables y guardarlos en un diccionario por cada grupo de variable

    #crear un dicionario vacío para almacenar un Dataframe por cada grupo de variables
    resultados_dfs={}
    for var in model.component_objects(pyo.Var, active=True):
        varobject = getattr(model, str(var))
        #crear un diccionario vacio por cada grupo de variables para almacenar las tupas variable, valor 
        varobject_dict = {'Variable': [], 'Indices': [], 'Valor': []}
        for index in varobject:
            varobject_dict['Variable'].append(str(var))
            varobject_dict['Indices'].append(index)
            varobject_dict['Valor'].append(pyo.value(varobject[index]))
            
        if len(varobject_dict['Variable'])>0:
        # Convertir el diccionario de cada grupo de variables a un DataFrame
            grupo_var_df=pd.DataFrame(varobject_dict)
            
            #Obtener el nombre de los indices del grupo e Variables
            indices_list=Variables_Indices_dict[str(varobject)]
            
            #Separar la columna de indice en multiples columnas (una por cada indice)
            grupo_var_df[indices_list] = pd.DataFrame(grupo_var_df['Indices'].tolist(), index=grupo_var_df.index)
            
            grupo_var_df=grupo_var_df[['Variable','Indices']+indices_list+['Valor']]
            grupo_var_df['Periodo']=periodo
            grupo_var_df['Escenario']=nombre_modelo.replace(f'_period{periodo}','')
            #Almacenar el DataFrame de cada grupo de variables en el diccionario donde se consolidan todos los resultados (un dataframe por cada grupo de variables)
            resultados_dfs[str(var)] = grupo_var_df
        
        #Guardar Valor de la Función Objetivo en un dataframe
        Costo_Total_df=pd.DataFrame([['Costo Total', pyo.value(model.obj)]],columns=['Objetivo','Valor'])
        Costo_Total_df['Periodo']=periodo
        Costo_Total_df['Escenario']=nombre_modelo.replace(f'_period{periodo}','')
        #Agregar el Dataframe que contiene el valor de la función Objetivo
    
        resultados_dfs['Funcion Objetivo'] = Costo_Total_df 
    return resultados_dfs

####Tamaño del modelo
def Tamaño_modelo(model):
        # Obtener el número total de variables
        num_total_vars = sum(len(v) for v in model.component_objects(pyo.Var, active=True))
        print(f"Número total de variables: {num_total_vars}")

        # Obtener el número total de restricciones
        num_total_constraints = sum(len(c) for c in model.component_objects(pyo.Constraint, active=True))# if isinstance(c, pyo.Constraint))
        print(f"Número total de restricciones: {num_total_constraints}")
        return None

def extraer_numero_final(texto):
    # Buscar la secuencia de dígitos al final del string
    resultado = re.search(r'\d+$', texto)
    if resultado:
        return int(resultado.group())
    else:
        return None  # Retorna None si no hay números al final

# Función para reemplazar el texto después de la segunda ocurrencia de '_'
def replace_after_second_underscore(text, replacement):
    parts = text.split('_')
    if len(parts) <= 2:
        return text  # Si hay menos de dos guiones bajos, devolver el texto original
    
    # Reemplazar el texto después del segundo guion bajo
    new_text = '_'.join(parts[:2]) + replacement
    return new_text

# Función para reemplazar el texto después de la ultima ocurrencia de '_'
def replace_after_last_underscore(input_string, replacement):
    # Find the last underscore in the string
    last_underscore_index = input_string.rfind('_')
    
    # If there is no underscore, return the original string
    if last_underscore_index == -1:
        return input_string
    
    # Replace the part after the last underscore
    return input_string[:last_underscore_index] + replacement