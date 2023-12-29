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
from pygwalker.api.streamlit import StreamlitRenderer, init_streamlit_comm

# ROLEs FOR EACH USER
ROLES = {
  'ximena': 'user',
  'asinche': 'user',
  'sanchezd': 'user',
  'tenecorat': 'user',
  'admin': 'admin',
}


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
def show_ventas_user(alchemyEngine, username):

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

def show_dashboard_user(alchemyEngine, username):
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

  st.subheader('Ventas por Día')
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
      "left": "5%", 
      "right": "2%", 
    },
    "series": [{
      "data": sales,
      "type": 'line',
      "label": {
        "show": True,
        "position": 'top',
        "formatter": '$ {c}'
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
  NOMBRE_ARCHIVO = 'REPORTE DE VENTAS_'+username.upper()+'_'+str(current_month) + '-' + str(current_year)+'.xlsx'
  df_xlsx = to_excel(VENTAS, False)
  st.download_button(label='Descargar Excel', data=df_xlsx, file_name=NOMBRE_ARCHIVO)


def paint_user(name, authenticator, username):
  # SIDEBAR INFO
  sidebar_info(name, authenticator)
  MENU_ITEM = st.session_state['MENU_ITEM']

  # DATABASE CONNECTION
  alchemyEngine = connect_database()

  if MENU_ITEM == 'ventas':
    show_ventas_user(alchemyEngine, username)
  else:
    show_dashboard_user(alchemyEngine, username)


# SIDEBAR
def sidebar_info_admin(name, authenticator):

  # TITLE
  st.sidebar.title('MR. ALITAS')
  with st.sidebar:
    st.success('Usuario: '+name)
  st.sidebar.divider()

  # MENU
  st.sidebar.subheader('Menú')
  with st.sidebar:
    MENU_ITEM = sac.menu([
      sac.MenuItem('dashboard', icon='clipboard2-data-fill'),
      #sac.MenuItem('análisis visual', icon='tools'),
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

def show_dashboard_admin(alchemyEngine, username):
  # LOAD DATA
  with st.status("ESTADO"):
    st.caption("Cargando datos...")
    with alchemyEngine.connect() as dbConnection:
      VENTAS_GENERAL = pd.read_sql(
        "select * from ventas v left join usuarios u on u.id_usuario = v.id_usuario_fk",
        dbConnection,
      )

    with alchemyEngine.connect() as dbConnection:
      VENTAS_PRODUCTOS = pd.read_sql(
        "select * from productos_ventas pv left join productos p on p.id_producto = pv.id_producto_fk",
        dbConnection,
      )

    st.caption("Actualización: "+str(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))



  # FILTROS
  ALL_USERS = VENTAS_GENERAL['name_user'].unique().tolist()
  with st.expander("FILTROS", expanded=True):
    options_usuario = st.multiselect(
      'Usuarios:',
      ALL_USERS,
      ALL_USERS
    )

    col1_date, col2_date = st.columns(2)
    with col1_date:
      date_desde = st.date_input("Desde:", datetime.date.today()-datetime.timedelta(days=30), max_value=datetime.date.today())
    with col2_date:
      date_hasta = st.date_input("Hasta:", datetime.date.today(), max_value=datetime.date.today())

  # FILTROS APLICADOS
  if not (len(options_usuario) == 0 ) or (len(options_usuario) == len(ALL_USERS)):
    VENTAS_GENERAL = VENTAS_GENERAL[VENTAS_GENERAL['name_user'].isin(options_usuario)]

  VENTAS_GENERAL = VENTAS_GENERAL[(VENTAS_GENERAL['fecha_creacion'].dt.date >= date_desde) & (VENTAS_GENERAL['fecha_creacion'].dt.date <= date_hasta)]


  # VENTAS DIARIAS POR USUARIOS
  daily_user_sales = VENTAS_GENERAL.groupby([VENTAS_GENERAL['fecha_creacion'].dt.to_period('D'), 'name_user'])['total'].sum().reset_index()
  daily_user_sales['fecha_creacion'] = daily_user_sales['fecha_creacion'].dt.strftime("%d-%m-%Y")

  daily_user_sales_pivot = daily_user_sales.pivot(
    index='name_user',
    columns='fecha_creacion',
    values='total')
  daily_user_sales_pivot = daily_user_sales_pivot.reset_index()
  daily_user_sales_pivot = daily_user_sales_pivot.fillna(0)
  daily_user_sales_unpivot = daily_user_sales_pivot.melt(id_vars=['name_user'], var_name='fecha_creacion', value_name='total')

  daily_data = []
  for user in daily_user_sales_unpivot['name_user'].unique():
    user_data = daily_user_sales_unpivot[daily_user_sales_unpivot['name_user'] == user]
    daily_data.append({
      "name": f"{user}",
      "type": 'line',
      "data": user_data['total'].tolist(),
      "label": {
        "show": True,
        "position": 'top',
        "formatter": '$ {c}'
      }
    })

  days = daily_user_sales_unpivot['fecha_creacion'].unique().tolist()

  options_ventas_diarias_usuarios = {
    "tooltip": {
      "trigger": 'axis'
    },
    "legend": {
      "data": [f"{user}" for user in daily_user_sales_unpivot['name_user'].unique()]
    },
    "grid": {
      "left": "10%", 
      "right": "10%", 
    },
    "xAxis": {
      "type": 'category',
      "data": days
    },
    "yAxis": {
      "type": 'value',
      "axisLabel": {
        "formatter": '${value}'
      }
    },
    "series": daily_data
  }
  
  # VENTAS DIARIAS TOTALES
  daily_general_sales = VENTAS_GENERAL.groupby([VENTAS_GENERAL['fecha_creacion'].dt.to_period('D')])['total'].sum().reset_index()
  dates = [date.strftime("%d-%m-%Y") for date in daily_general_sales['fecha_creacion'].to_list()]
  sales = daily_general_sales['total'].tolist()

  options_ventas_diarias_totales = {
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
      "left": "10%", 
      "right": "10%", 
    },
    "series": [{
      "data": sales,
      "type": 'line',
      "label": {
          "show": True,
          "position": 'top',
          "formatter": '$ {c}'
        },
        "itemStyle": {
          "color": 'blue'
        },
        "emphasis": {
            "focus": 'series'
        }
    }]
  }


  # VENTAS MENSUALES POR USUARIO
  monthly_user_sales = VENTAS_GENERAL.groupby([VENTAS_GENERAL['fecha_creacion'].dt.to_period('M'), 'name_user'])['total'].sum().reset_index()
  monthly_user_sales['fecha_creacion'] = monthly_user_sales['fecha_creacion'].dt.strftime("%m-%Y")

  monthly_user_sales_pivot = monthly_user_sales.pivot(
    index='name_user',
    columns='fecha_creacion',
    values='total')
  monthly_user_sales_pivot = monthly_user_sales_pivot.reset_index()
  monthly_user_sales_pivot = monthly_user_sales_pivot.fillna(0)

  monthly_user_sales_unpivot = monthly_user_sales_pivot.melt(id_vars=['name_user'], var_name='fecha_creacion', value_name='total')

  monthly_data = []
  for user in monthly_user_sales_unpivot['name_user'].unique():
    user_data = monthly_user_sales_unpivot[monthly_user_sales_unpivot['name_user'] == user]
    monthly_data.append({
      "name": f"{user}",
      "type": 'line',
      "data": user_data['total'].tolist(),
      "label": {
        "show": True,
        "position": 'top',
        "formatter": '$ {c}'
      }
    })

  months = monthly_user_sales_unpivot['fecha_creacion'].unique().tolist()

  options_ventas_mensuales_usuarios = {
    "tooltip": {
      "trigger": 'axis'
    },
    "legend": {
      "data": [f"{user}" for user in monthly_user_sales_unpivot['name_user'].unique()]
    },
    "grid": {
      "left": "10%", 
      "right": "10%", 
    },
    "xAxis": {
      "type": 'category',
      "data": months
    },
    "yAxis": {
      "type": 'value',
      "axisLabel": {
        "formatter": '${value}'
      }
    },
    "series": monthly_data
  }



  # VENTAS MENSUALES TOTALES
  monthly_general_sales = VENTAS_GENERAL.groupby([VENTAS_GENERAL['fecha_creacion'].dt.to_period('M')])['total'].sum().reset_index()
  monthly_general_sales['fecha_creacion'] = monthly_general_sales['fecha_creacion'].dt.strftime("%m-%Y")

  dates = monthly_general_sales['fecha_creacion'].to_list()
  sales = monthly_general_sales['total'].tolist()

  options_ventas_mensuales_totales = {
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
      "left": "10%", 
      "right": "10%", 
    },
    "series": [{
      "data": sales,
      "type": 'line',
      "label": {
          "show": True,
          "position": 'top',
          "formatter": '$ {c}'
        },
        "itemStyle": {
          "color": 'blue'
        },
        "emphasis": {
            "focus": 'series'
        }
    }]
  }

  st.divider()

  # PAINTING
  tab = sac.tabs([
    sac.TabsItem(label='Ventas por Usuario', icon='person-fill-check'),
    sac.TabsItem(label='Ventas totales', icon='currency-dollar'),
    sac.TabsItem(label='detalle de ventas', icon='table'),
  ], format_func='title', align='start', grow=True)

  if tab == 'Ventas por Usuario':
    st.subheader('Ventas Diarias')
    st_echarts(options=options_ventas_diarias_usuarios, height="400px")

    daily_user_sales_show = daily_user_sales.copy()
    daily_user_sales_show_rename = daily_user_sales_show.rename(columns = {
      'fecha_creacion':'Fecha',
      'name_user':'Usuario',
      'total':'Total',
    })
    daily_user_sales_show_rename['Total'] = daily_user_sales_show_rename['Total'].apply(format_precio)
    st.dataframe(daily_user_sales_show_rename, use_container_width=True, hide_index=True)
    NOMBRE_ARCHIVO = 'REPORTE DE VENTAS DIARIAS POR USUARIO' + '_ DEL ' + str(date_desde) + ' AL ' + str(date_hasta) + '.xlsx'
    df_xlsx = to_excel(daily_user_sales_show, False)
    st.download_button(label='Descargar Excel', data=df_xlsx, file_name=NOMBRE_ARCHIVO)

    st.divider()

    st.subheader('Ventas Mensuales')
    st_echarts(options=options_ventas_mensuales_usuarios, height="400px")

    monthly_user_sales_show = monthly_user_sales.copy()
    monthly_user_sales_show_rename = monthly_user_sales_show.rename(columns = {
      'fecha_creacion':'Mes',
      'name_user':'Usuario',
      'total':'Total',
    })
    monthly_user_sales_show_rename['Total'] = monthly_user_sales_show_rename['Total'].apply(format_precio)
    st.dataframe(monthly_user_sales_show_rename, use_container_width=True, hide_index=True)
    NOMBRE_ARCHIVO = 'REPORTE DE VENTAS MENSUALES POR USUARIO' + '_ DEL ' + str(date_desde) + ' AL ' + str(date_hasta) + '.xlsx'
    df_xlsx = to_excel(monthly_user_sales_show, False)
    st.download_button(label='Descargar Excel', data=df_xlsx, file_name=NOMBRE_ARCHIVO)

  elif tab == 'Ventas totales':
    st.subheader('Ventas Diarias')
    st_echarts(options=options_ventas_diarias_totales, height="400px")

    daily_general_sales_show = daily_general_sales.copy()
    daily_general_sales_show_rename = daily_general_sales_show.rename(columns = {
      'fecha_creacion':'Fecha',
      'total':'Total',
    })
    daily_general_sales_show_rename['Total'] = daily_general_sales_show_rename['Total'].apply(format_precio)
    st.dataframe(daily_general_sales_show_rename, use_container_width=True, hide_index=True)
    NOMBRE_ARCHIVO = 'REPORTE DE VENTAS TOTALES DIARIAS' + '_ DEL ' + str(date_desde) + ' AL ' + str(date_hasta) + '.xlsx'
    df_xlsx = to_excel(daily_general_sales_show, False)
    st.download_button(label='Descargar Excel', data=df_xlsx, file_name=NOMBRE_ARCHIVO)

    st.divider()

    st.subheader('Ventas Mensuales')
    st_echarts(options=options_ventas_mensuales_totales, height="400px")

    monthly_general_sales_show = monthly_general_sales.copy()
    monthly_general_sales_show_rename = monthly_general_sales_show.rename(columns = {
      'fecha_creacion':'Mes',
      'total':'Total',
    })
    monthly_general_sales_show_rename['Total'] = monthly_general_sales_show_rename['Total'].apply(format_precio)
    st.dataframe(monthly_general_sales_show_rename, use_container_width=True, hide_index=True)
    NOMBRE_ARCHIVO = 'REPORTE DE VENTAS TOTALES MENSUALES' + '_ DEL ' + str(date_desde) + ' AL ' + str(date_hasta) + '.xlsx'
    df_xlsx = to_excel(monthly_general_sales_show, False)
    st.download_button(label='Descargar Excel', data=df_xlsx, file_name=NOMBRE_ARCHIVO)

  elif tab == 'detalle de ventas':
    ventas_generales_show = VENTAS_GENERAL.copy()
    ventas_generales_show.rename(columns = {
      'id_venta':'Venta ID',
      'num_productos':'Número de Productos',
      'total':'Total',
      'valor_pagado':'Valor Cancelado',
      'cambio':'Cambio',
      'fecha_creacion':'Fecha de Creación',
      'name_user':'Usuario',
    }, inplace = True)
    del ventas_generales_show['id_usuario_fk']
    del ventas_generales_show['username']
    del ventas_generales_show['id_usuario']
    ventas_generales_show_format = ventas_generales_show.copy()
    ventas_generales_show_format['Total'] = ventas_generales_show_format['Total'].apply(format_precio)
    ventas_generales_show_format['Valor Cancelado'] = ventas_generales_show_format['Valor Cancelado'].apply(format_precio)
    ventas_generales_show_format['Cambio'] = ventas_generales_show_format['Cambio'].apply(format_precio)

    st.subheader('Todas las Ventas')
    st.dataframe(ventas_generales_show_format, use_container_width=True, hide_index=True)
    NOMBRE_ARCHIVO = 'MR ALITAS - VENTAS TOTALES.xlsx'
    df_xlsx = to_excel(ventas_generales_show, False)
    st.download_button(label='Descargar Excel', data=df_xlsx, file_name=NOMBRE_ARCHIVO)

    st.divider()

    st.subheader('Productos de la Venta')
    option_venta_id = st.selectbox(
    'Seleccione una venta', 
    ventas_generales_show_format['Venta ID'].unique().tolist())

    ventas_productos_show = VENTAS_PRODUCTOS.copy()
    ventas_productos_show = ventas_productos_show[ventas_productos_show['id_venta_fk'] == option_venta_id]
    del ventas_productos_show['id_producto']
    del ventas_productos_show['id_producto_venta']
    del ventas_productos_show['id_venta_fk']
    del ventas_productos_show['id_producto_fk']
    del ventas_productos_show['fecha_ingreso']

    ventas_productos_show.rename(columns = {
      'cantidad':'Cantidad',
      'total':'Total',
      'nombre':'Producto',
      'precio':'Precio',
    }, inplace = True)
    ventas_productos_show['Venta ID'] = option_venta_id

    ventas_productos_show_format = ventas_productos_show.copy()
    ventas_productos_show_format['Total'] = ventas_productos_show_format['Total'].apply(format_precio)
    ventas_productos_show_format['Precio'] = ventas_productos_show_format['Precio'].apply(format_precio)
    ventas_productos_show_format = ventas_productos_show_format[['Venta ID', 'Producto', 'Cantidad', 'Precio', 'Total']]

    st.dataframe(ventas_productos_show_format, use_container_width=True, hide_index=True)

    NOMBRE_ARCHIVO = 'MR ALITAS - VENTAS ID '+str(option_venta_id)+'.xlsx'
    df_xlsx = to_excel(ventas_productos_show, False)
    st.download_button(label='Descargar Excel', data=df_xlsx, file_name=NOMBRE_ARCHIVO)


  


# Get an instance of pygwalker's renderer. You should cache this instance to effectively prevent the growth of in-process memory.
@st.cache_resource
def get_data_admin(_alchemyEngine) -> "StreamlitRenderer":
  with st.status("Cargando..."):
    st.write("Cargando datos...")
    with _alchemyEngine.connect() as dbConnection:
      VENTAS_GENERAL = pd.read_sql(
        "select * from ventas v left join usuarios u on u.id_usuario = v.id_usuario_fk",
        dbConnection,
      )
    st.write("Actualización: "+str(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
  return StreamlitRenderer(VENTAS_GENERAL, spec="./gw_config.json", debug=False)


def show_analisis_admin(alchemyEngine, username):

  # Establish communication between pygwalker and streamlit
  init_streamlit_comm()
  
  renderer = get_data_admin(alchemyEngine)
  
  # Render your data exploration interface. Developers can use it to build charts by drag and drop.
  renderer.render_explore()


def paint_admin(name, authenticator, username):
  # SIDEBAR INFO
  sidebar_info_admin(name, authenticator)
  MENU_ITEM = st.session_state['MENU_ITEM']

  # DATABASE CONNECTION
  alchemyEngine = connect_database()

  if MENU_ITEM == "dashboard":
    show_dashboard_admin(alchemyEngine, username)
  #elif MENU_ITEM == "análisis visual":
  #  show_analisis_admin(alchemyEngine, username)









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
    if ROLES[username] == 'user':
      paint_user(name, authenticator, username)
    elif ROLES[username] == 'admin':
      paint_admin(name, authenticator, username)
  elif authentication_status == False:
    st.error('Usuario o contraseña incorrecta.')
  elif authentication_status == None:
    st.warning('Ingrese su usuario y contraseña.')


# MAIN STATEMENT
if __name__ == '__main__':
  main()
