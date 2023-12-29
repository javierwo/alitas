import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import psycopg2
from streamlit_js_eval import streamlit_js_eval
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader
import yaml
import plotly.express as px
import datetime
import streamlit_antd_components as sac
from streamlit_echarts import st_echarts
from io import BytesIO
from pyxlsb import open_workbook as open_xlsb


# LOGIN CONFIGURATION
def load_config():
  with open('config.yaml') as file:
    return yaml.load(file, Loader=SafeLoader)

def authenticate_user(credentials, cookie_config):
  authenticator = stauth.Authenticate(
    credentials,
    cookie_config['name'],
    cookie_config['key'],
    cookie_config['expiry_days'],
  )
  return authenticator.login('Iniciar Sesión', 'main')


# SIDEBAR
def sidebar_info(name, authenticator):

  # TITLE
  st.sidebar.title('MR. ALITAS')
  with st.sidebar:
    st.success('Usuario: '+name)
  st.sidebar.divider()

  # MENU
  st.sidebar.subheader('Menú')
  with st.sidebar:
    MENU_ITEM = sac.menu([
      sac.MenuItem('ventas', icon='currency-dollar'),
      sac.MenuItem('dashboard', icon='bar-chart-fill'),
    ], format_func='title', open_all=True)
  st.sidebar.divider()

  # SESSION
  st.sidebar.subheader('Sesión')
  if authenticator.logout('Cerrar Sesión', 'sidebar'):
    print('cerrar sesion')
  st.sidebar.divider()

  # VERSION
  st.sidebar.subheader('Versión')
  with st.sidebar.expander("Versión: 1.0"):
    st.write('23/12/2023 - Versión Inicial.')
    
  st.sidebar.caption('Copyright © 2023. Todos los derechos reservados.')

  st.session_state['MENU_ITEM'] = MENU_ITEM


# FUNCIONES
def format_precio(precio):
  precio = round(precio, 2)
  precio_str = str(precio)
  if len(precio_str.split('.')[1]) == 2:
    precio_str = '$ '+str(precio)
  elif len(precio_str.split('.')[1]) == 1:
    precio_str = '$ '+str(precio) + '0'
  return precio_str

def find_precio(item, units, format, PRODUCTOS_NOMBRE_LIST, PRODUCTOS_PRECIO_LIST):
  product_index = PRODUCTOS_NOMBRE_LIST.index(item)
  product_precio = PRODUCTOS_PRECIO_LIST[product_index]*units
  if format:
    return format_precio(product_precio)
  else:
    return product_precio

def pg_connect():
  connection = psycopg2.connect(
    #host='db',
    host='localhost',
    database='mr_alitas',
    user='postgres',
    password='000111'
  )
  return connection

def connect_database():
  print('checking connection')
  if 'is_db_connected' in st.session_state:
    print('db connection exists')
    alchemyEngine = st.session_state['alchemyEngine']
  else:
    print('connecting to db...')
    #alchemyEngine = create_engine('postgresql+psycopg2://postgres:000111@db:5432/mr_alitas', pool_recycle=3600);
    alchemyEngine = create_engine('postgresql+psycopg2://postgres:000111@localhost:5432/mr_alitas', pool_recycle=3600);
    st.session_state['is_db_connected'] = True
    st.session_state['alchemyEngine'] = alchemyEngine
    print('connected to db')
  return alchemyEngine

def to_excel(df, MULTIINDEX):
  output = BytesIO()
  writer = pd.ExcelWriter(output, engine='xlsxwriter')
  df.to_excel(writer, index=MULTIINDEX, sheet_name='Ventas')
  workbook = writer.book
  worksheet = writer.sheets['Ventas']
  #format1 = workbook.add_format({'num_format': '0.00'}) 
  #worksheet.set_column('A:A', None, format1)  
  worksheet.set_column('A:A', None, None)  
  writer.close()
  processed_data = output.getvalue()
  return processed_data


# VIEWS
def show_ventas(alchemyEngine, username):

  # LEER PRODUCTOS
  if 'productos' in st.session_state:
    PRODUCTOS = st.session_state['productos']
  else:
    with alchemyEngine.connect() as dbConnection:
      PRODUCTOS = pd.read_sql(
        "SELECT id_producto, nombre, precio FROM productos order by nombre asc",
        dbConnection
      )
    st.session_state['productos'] = PRODUCTOS

  # CARGANDO LOS DATOS
  if 'values_list' in st.session_state:
    PRODUCTOS_NOMBRE_LIST = st.session_state['PRODUCTOS_NOMBRE_LIST']
    PRODUCTOS_PRECIO_LIST = st.session_state['PRODUCTOS_PRECIO_LIST']
    PRODUCTOS_ID_LIST = st.session_state['PRODUCTOS_ID_LIST']
  else:
    PRODUCTOS_NOMBRE_LIST = PRODUCTOS['nombre'].tolist()
    PRODUCTOS_PRECIO_LIST = PRODUCTOS['precio'].tolist()
    PRODUCTOS_ID_LIST = PRODUCTOS['id_producto'].tolist()
    st.session_state['PRODUCTOS_NOMBRE_LIST'] = PRODUCTOS_NOMBRE_LIST
    st.session_state['PRODUCTOS_PRECIO_LIST'] = PRODUCTOS_PRECIO_LIST
    st.session_state['PRODUCTOS_ID_LIST'] = PRODUCTOS_ID_LIST
    st.session_state['values_list'] = True

  # VERIFICAR EL ID
  if 'user_id' not in st.session_state:
    with alchemyEngine.connect() as dbConnection:
      id_usuario_fk = pd.read_sql(
        "SELECT id_usuario FROM usuarios where username = %s",
        dbConnection,
        params=(username,)
      )
    id_usuario_fk = id_usuario_fk['id_usuario'].tolist()[0]
    st.session_state['user_id'] = id_usuario_fk
  else:
    id_usuario_fk = st.session_state['user_id']

  # MOSTRAR MENÚ
  st.subheader('Menú')
  col1, col2 = st.columns([2,1])
  with col1:
    producto = st.selectbox('Seleccione un producto', PRODUCTOS_NOMBRE_LIST)

  with col2:
    cantidad = st.number_input('Cantidad', min_value=1, max_value=200, value=1)

  df_carrito_adding = pd.DataFrame(
    [{
      "Precio Unitario":find_precio(producto, 1, True, PRODUCTOS_NOMBRE_LIST, PRODUCTOS_PRECIO_LIST),
      "Precio Total":find_precio(producto, cantidad, True, PRODUCTOS_NOMBRE_LIST, PRODUCTOS_PRECIO_LIST)
    }]
  )
  st.dataframe(df_carrito_adding, use_container_width=True, hide_index=True)


  # ADDING TO CART
  if st.button('Agregar al carrito'):
    if 'list_carrito' not in st.session_state:
      list_carrito = [{
        "Producto":producto,
        "Cantidad":cantidad,
        "Precio Unitario":find_precio(producto, 1, False, PRODUCTOS_NOMBRE_LIST, PRODUCTOS_PRECIO_LIST),
        "Precio Total":find_precio(producto, cantidad, False, PRODUCTOS_NOMBRE_LIST, PRODUCTOS_PRECIO_LIST)
        }]
      st.session_state['list_carrito'] = list_carrito
    else:
      list_carrito = st.session_state['list_carrito']
      list_carrito.append({
        "Producto":producto,
        "Cantidad":cantidad,
        "Precio Unitario":find_precio(producto, 1, False, PRODUCTOS_NOMBRE_LIST, PRODUCTOS_PRECIO_LIST),
        "Precio Total":find_precio(producto, cantidad, False, PRODUCTOS_NOMBRE_LIST, PRODUCTOS_PRECIO_LIST)
        })
    st.toast('Producto Añadido al Carrito', icon='✅')


  # CART VIEW
  st.divider()
  st.subheader('Carrito de Compras')

  if 'list_carrito' not in st.session_state:
    st.write('No hay productos en el carrito.')
  else:   
    list_carrito = st.session_state['list_carrito']

    df_list_carrito = pd.DataFrame(
      list_carrito
    )

    df_list_carrito_formatted = df_list_carrito.copy()
    df_list_carrito_formatted['Precio Unitario'] = df_list_carrito_formatted['Precio Unitario'].apply(format_precio)
    df_list_carrito_formatted['Precio Total'] = df_list_carrito_formatted['Precio Total'].apply(format_precio)
    df_list_carrito_formatted['Seleccionar'] = st.checkbox("Seleccionar", value=False)

    edited_df = st.data_editor(df_list_carrito_formatted, use_container_width=True, hide_index=True)

    TOTAL_DEL_PEDIDO = df_list_carrito['Precio Total'].sum()

    df_list_total = pd.DataFrame(
      [
        {
          "Cantidad de Productos": df_list_carrito['Cantidad'].sum(),
          "Precio Total del Pedido": TOTAL_DEL_PEDIDO
        },
      ]
    )
    df_list_total_formatted = df_list_total.copy()
    df_list_total_formatted['Precio Total del Pedido'] = df_list_total_formatted['Precio Total del Pedido'].apply(format_precio)


    # ADDING PRODUCTS
    col1_cart, col2_cart = st.columns([2,1])
    with col1_cart:
      st.dataframe(df_list_total_formatted, use_container_width=True, hide_index=True)

    with col2_cart:
      PAGA_CON = st.number_input("Paga con:", value=None, placeholder="$")

    col1_buttons, col2_buttons, col3_buttons= st.columns(3)

    with col2_buttons:
      if edited_df['Seleccionar'].any():
        NUM_SELECTED_ITEMS = len(edited_df[edited_df['Seleccionar']== True])
        if st.button('Eliminar Seleccionados ('+str(NUM_SELECTED_ITEMS)+')', use_container_width=True):
          indices_seleccionados = edited_df.index[edited_df['Seleccionar'] == True].tolist()
          # Eliminar las filas seleccionadas
          df = df_list_carrito.drop(indices_seleccionados)
          if df.empty:
            del st.session_state['list_carrito']
          else:
            st.session_state['list_carrito'] = df_list_carrito.drop(indices_seleccionados).to_dict('records')
            st.toast('Productos Eliminados', icon='✅')

          if 'resumen' in st.session_state:
            del st.session_state['resumen']
          st.rerun()
        
    with col1_buttons:
      BOTON_PAGAR = st.button('Pagar', use_container_width=True)


    if BOTON_PAGAR:
      if (PAGA_CON):
        if (TOTAL_DEL_PEDIDO>PAGA_CON):
          st.error('Error: El valor ingresado es menor al valor del pedido.')
          if 'resumen' in st.session_state:
            del st.session_state['resumen']
        else:
          st.toast('Pago Verificado', icon='✅')
          st.session_state['resumen'] = True
          st.session_state['df'] = df_list_total
          st.session_state['PAGA_CON'] = PAGA_CON
      else: 
        st.error('Error: Debe ingresar el valor con el que paga.')
        if 'resumen' in st.session_state:
          #st.write('borrando resumen')
          del st.session_state['resumen']


  # RESUMEN VIEW
  if 'resumen' in st.session_state:
    # PAGAR VIEW
    st.divider()
    st.subheader('Resumen')

    df = st.session_state['df']
    PAGA_CON = st.session_state['PAGA_CON']
    df["Cambio"] = PAGA_CON - df["Precio Total del Pedido"]

    df_formatted = df.copy()
    df_formatted['Precio Total del Pedido'] = df_formatted['Precio Total del Pedido'].apply(format_precio)
    df_formatted['Cambio'] = df_formatted['Cambio'].apply(format_precio)

    st.dataframe(df_formatted, use_container_width=True, hide_index=True)

    if st.button('GUARDAR PEDIDO', type='primary'):

      with st.status("Guardando..."):

        try:

          df['valor_pagado'] = PAGA_CON

          df.rename(columns = {
            'Cantidad de Productos':'num_productos',
            'Precio Total del Pedido':'total',
            'Cambio':'cambio',
          }, inplace = True)
          #st.dataframe(df)
          df_dict = df.to_dict('records')[0]
          #st.write(df_dict)

          df_merge_productos = pd.merge(
            df_list_carrito, 
            PRODUCTOS, 
            how="left",
            left_on='Producto', 
            right_on='nombre'
          )
          df_merge_productos_drop = df_merge_productos[['id_producto', 'Cantidad', 'Precio Total']]
          df_merge_productos_drop.rename(columns = {
            'Cantidad':'cantidad',
            'Precio Total':'total',
            'id_producto':'id_producto_fk',
          }, inplace = True)

          insert_venta = """
            INSERT INTO ventas (num_productos, total, valor_pagado, cambio, id_usuario_fk) 
            VALUES ("""+str(df_dict['num_productos'])+""", """+str(df_dict['total'])+""", """+str(df_dict['valor_pagado'])+""", """+str(df_dict['cambio'])+""", """+str(id_usuario_fk)+""") RETURNING id_venta;
          """

          conn = pg_connect()
          cursor = conn.cursor()
          cursor.execute(insert_venta)
          inserted_id_venta = cursor.fetchone()[0]
          conn.commit()
          conn.close()

          df_merge_productos_drop['id_venta_fk'] = inserted_id_venta
          #st.dataframe(df_merge_productos_drop)

          df_merge_productos_drop.to_sql('productos_ventas', alchemyEngine, if_exists='append', index=False)

          st.session_state['finished'] = True

        except Exception as e:
          print(f"An error occurred: {e}")
          st.session_state['finished'] = False


  # FINISHED VIEW
  if 'finished' in st.session_state:

    if 'resumen' in st.session_state:
      del st.session_state['resumen']
      st.rerun()

    if 'list_carrito' in st.session_state:
      del st.session_state['list_carrito']
      st.rerun()

    st.divider()
    st.subheader('Pedido Finalizado')
    FINISHED = st.session_state['finished']
    if FINISHED:
      st.success('Pedido Guardado Correctamente')
    else: 
      st.error('Error al guardar el pedido')

    if st.button("NUEVO PEDIDO", type='primary'):
      streamlit_js_eval(js_expressions="parent.window.location.reload()")

def show_dashboard(alchemyEngine, username):
  with st.status("Cargando..."):
    st.write("Cargando datos...")
    if 'user_id' not in st.session_state:
      with alchemyEngine.connect() as dbConnection:
        id_usuario_fk = pd.read_sql(
          "SELECT id_usuario FROM usuarios where username = %s",
          dbConnection,
          params=(username,)
        )
      id_usuario_fk = id_usuario_fk['id_usuario'].tolist()[0]
      st.session_state['user_id'] = id_usuario_fk
    else:
      id_usuario_fk = st.session_state['user_id']

    with alchemyEngine.connect() as dbConnection:
      VENTAS = pd.read_sql(
        "SELECT * FROM ventas where id_usuario_fk = %s",
        dbConnection,
        params=(id_usuario_fk,)
      )
    st.write("Actualización: "+str(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    
  current_year = VENTAS['fecha_creacion'].dt.year.max()
  current_month = VENTAS['fecha_creacion'].dt.month.max()
  current_month_data = VENTAS[(VENTAS['fecha_creacion'].dt.year == current_year) & (VENTAS['fecha_creacion'].dt.month == current_month)]
  current_month_sales = current_month_data.groupby(current_month_data['fecha_creacion'].dt.date)['total'].sum().reset_index()
  
  # Preparar los datos para ECharts
  dates = [date.strftime("%d-%m-%Y") for date in current_month_sales['fecha_creacion'].to_list()]
  sales = current_month_sales['total'].tolist()

  st.subheader('Ventas por Día (en dólares)')
  options = {
    "xAxis": {
      "type": "category",
      "data": dates
    },
    "tooltip": {
      "trigger": 'axis',
      #"formatter": lambda params: f'{params[0].axisValueLabel}: ${params[0].data:.2f}'
    },
    "yAxis": {
      "type": 'value',
      "axisLabel": {
        "formatter": '${value}'
      }
    },
    "grid": {
      "left": "2%", 
      "right": "2%", 
    },
    "series": [{
      "data": sales,
      "type": 'line',
      "label": {
          "show": True,
          "position": 'top',
          #"formatter": '${c:.2f}'
        },
        "itemStyle": {
          "color": 'blue'
        },
        "emphasis": {
            "focus": 'series'
        }
    }]
  }
  st_echarts(options=options, height="400px")

  st.subheader('Resumen')
  VENTAS_RESUMEN = VENTAS.copy()
  del VENTAS_RESUMEN['id_usuario_fk']
  VENTAS_RESUMEN.rename(columns = {
    'id_venta':'Venta ID',
    'num_productos':'Número de Productos',
    'total':'Total',
    'valor_pagado':'Valor Cancelado',
    'cambio':'Cambio',
    'fecha_creacion':'Fecha de Creación',
  }, inplace = True)
  VENTAS_RESUMEN['Total'] = VENTAS_RESUMEN['Total'].apply(format_precio)
  VENTAS_RESUMEN['Valor Cancelado'] = VENTAS_RESUMEN['Valor Cancelado'].apply(format_precio)
  VENTAS_RESUMEN['Cambio'] = VENTAS_RESUMEN['Cambio'].apply(format_precio)
  st.dataframe(VENTAS_RESUMEN, use_container_width=True, hide_index=True)

  NOMBRE_ARCHIVO = 'REPORTE DE VENTAS_'+username.upper()+'_'+str(current_month) + '-' + str(current_year)+'.xlsx'
  
  VENTAS.rename(columns = {
    'id_venta':'Venta ID',
    'num_productos':'Número de Productos',
    'total':'Total',
    'valor_pagado':'Valor Cancelado',
    'cambio':'Cambio',
    'fecha_creacion':'Fecha de Creación',
  }, inplace = True)
  del VENTAS['id_usuario_fk']
  VENTAS['Venta ID'] = VENTAS['Venta ID'].astype(int)
  #VENTAS = VENTAS.reset_index()
  df_xlsx = to_excel(VENTAS, False)
  st.download_button(label='Descargar Excel', data=df_xlsx, file_name=NOMBRE_ARCHIVO)



# MAIN FUNCTION
def main(): 

  # PAGE CONFIGURATION
  st.set_page_config(
    page_title="Mr. Alitas",
  )

  # Load configuration
  config = load_config()

  # Authenticate user
  authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
  )
  name, authentication_status, username = authenticator.login('Iniciar Sesión', 'main')

  if authentication_status:

    # SIDEBAR INFO
    sidebar_info(name, authenticator)
    MENU_ITEM = st.session_state['MENU_ITEM']

    # DATABASE CONNECTION
    alchemyEngine = connect_database()

    if MENU_ITEM == 'ventas':
      show_ventas(alchemyEngine, username)
    else:
      show_dashboard(alchemyEngine, username)



# MAIN STATEMENT
if __name__ == '__main__':
  main()
