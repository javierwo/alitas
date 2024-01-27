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

#def pg_connect():
#  connection = psycopg2.connect(
#    #host='db',
#    host='localhost',
#    database='mr_alitas',
#    user='postgres',
#    password='000111'
#  )
#  return connection

def pg_connect():
  connection = psycopg2.connect(
    host='monorail.proxy.rlwy.net',
    database='railway',
    user='postgres',
    password='4EAFBd5-5da2D-6gd4EGg2f1G2B32df3',
    port=15770
  )
  return connection

def connect_database():
  #print('checking connection')
  if 'is_db_connected' in st.session_state:
    #print('db connection exists')
    alchemyEngine = st.session_state['alchemyEngine']
  else:
    #print('connecting to db...')
    #alchemyEngine = create_engine('postgresql+psycopg2://postgres:000111@db:5432/mr_alitas', pool_recycle=3600);
    #alchemyEngine = create_engine('postgresql+psycopg2://postgres:000111@localhost:5432/mr_alitas', pool_recycle=3600);
    alchemyEngine = create_engine('postgresql+psycopg2://postgres:4EAFBd5-5da2D-6gd4EGg2f1G2B32df3@monorail.proxy.rlwy.net:15770/railway', pool_recycle=3600);
    st.session_state['is_db_connected'] = True
    st.session_state['alchemyEngine'] = alchemyEngine
    #print('connected to db')
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
        "SELECT id_producto, nombre, precio FROM productos",
        dbConnection
      )
    if len(PRODUCTOS) == 0:
      st.error('No se ha realizado ninguna venta.')
      st.stop()
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
      PAGA_CON = st.number_input("Paga con (en dólares):", value=None, placeholder="$")

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

  if len(VENTAS) == 0:
    st.error('No se ha realizado ninguna venta.')
    st.stop()
    
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

def highlight_total(row):
  if row.name == 'Total':
    return ['background-color: #f8f9fb']*len(row)
  return ['']*len(row)

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

  with st.expander("Filtros", expanded=True):

    with st.form("my_form", border=True):
      if 'data_loaded' in st.session_state:
        ALL_USERS = st.session_state['ALL_USERS']
        ALL_PRODUCTS = st.session_state['ALL_PRODUCTS']
        ALL_USERS_LIST = ALL_USERS['name_user'].unique().tolist() 
        ALL_PRODUCTS_LIST = ALL_PRODUCTS['nombre'].unique().tolist() 
      else: 
        with alchemyEngine.connect() as dbConnection:
          ALL_USERS = pd.read_sql(
            "select id_usuario, name_user from usuarios",# where name_user not like 'Ximena García'
            dbConnection,
          )
          ALL_PRODUCTS = pd.read_sql(
            "select id_producto, nombre, precio from productos p",
            dbConnection,
          )
          ALL_USERS_LIST = ALL_USERS['name_user'].unique().tolist() 
          ALL_PRODUCTS_LIST = ALL_PRODUCTS['nombre'].unique().tolist() 

          st.session_state['data_loaded'] = True
          st.session_state['ALL_USERS'] = ALL_USERS
          st.session_state['ALL_PRODUCTS'] = ALL_PRODUCTS

      options_usuarios = st.multiselect(
        'Usuarios',
        ALL_USERS_LIST,
        help='Al dejar este campo vacío se incluirán todos los Usuarios.',
        placeholder="Seleccione los usuarios",
      )

      options_productos = st.multiselect(
        'Productos',
        ALL_PRODUCTS_LIST,
        help='Al dejar este campo vacío se incluirán todos los Productos.',
        placeholder="Seleccione los productos",
      )

      col1_date, col2_date = st.columns(2)
      with col1_date:
        date_desde = st.date_input("Fecha de Inicio", datetime.date.today()-datetime.timedelta(days=30), max_value=datetime.date.today(), format="DD-MM-YYYY")
      with col2_date:
        date_hasta = st.date_input("Fecha de Fin", datetime.date.today(), max_value=datetime.date.today(), format="DD-MM-YYYY")

      st.divider()

      col1_sub, col2_sub = st.columns(2)
      with col1_sub:
        submitted = st.form_submit_button("Cargar Datos", use_container_width=True)

      with col2_sub:
        if submitted:

          with st.spinner('Cargando los datos...'):

            if len(options_usuarios)==0:
              ALL_USERS_IDS = ALL_USERS_LIST
            else:
              ALL_USERS_IDS = ALL_USERS[ALL_USERS['name_user'].isin(options_usuarios)]['id_usuario'].unique().tolist()

            if len(options_productos)==0:
              ALL_PRODUCTS_IDS = ALL_PRODUCTS['id_producto'].unique().tolist()
            else:
              ALL_PRODUCTS_IDS = ALL_PRODUCTS[ALL_PRODUCTS['nombre'].isin(options_productos)]['id_producto'].unique().tolist()

            date_desde_str = "'"+str(date_desde)+"'"
            date_hasta_str = "'"+str(date_hasta)+"'"

            if len(ALL_USERS_IDS)==0 or len(ALL_USERS_LIST)==len(ALL_USERS_IDS):
              SQL_VENTAS = "select * from ventas v left join usuarios u on u.id_usuario = v.id_usuario_fk where DATE(v.fecha_creacion) between "+date_desde_str+" and "+date_hasta_str+";"
            else:
              SQL_VENTAS = "select * from ventas v left join usuarios u on u.id_usuario = v.id_usuario_fk where DATE(v.fecha_creacion) between "+date_desde_str+" and "+date_hasta_str+" and v.id_usuario_fk in ("+str(ALL_USERS_IDS)[1:-1]+")"
            
            with alchemyEngine.connect() as dbConnection:
              VENTAS_GENERAL = pd.read_sql(
                SQL_VENTAS,
                dbConnection,
              )

              if len(VENTAS_GENERAL)==0:
                # ESTOS PARÁMETROS SE AÑADEN SOLO PARA MOSTRAR EL MENSAJE DE QUE NO EXISTEN VENTAS
                # DEBIDO A LA CONDICIÓN DE if len(VENTAS_PRODUCTOS)==0: 
                st.session_state['VENTAS'] = True
                st.session_state['VENTAS_PRODUCTOS'] = []

              else:
                id_venta_list = VENTAS_GENERAL['id_venta'].tolist()
                with alchemyEngine.connect() as dbConnection:
                  VENTAS_PRODUCTOS = pd.read_sql(
                    "select pv.id_venta_fk, pv.id_producto_fk, pv.cantidad, pv.total, p.nombre, p.precio, u.name_user, v.fecha_creacion from productos_ventas pv left join productos p on p.id_producto = pv.id_producto_fk left join ventas v on pv.id_venta_fk  = v.id_venta left join usuarios u on v.id_usuario_fk = u.id_usuario where id_venta_fk in ("+str(id_venta_list)[1:-1]+")",
                    dbConnection,
                  )

                VENTAS_PRODUCTOS = VENTAS_PRODUCTOS[VENTAS_PRODUCTOS['id_producto_fk'].isin(ALL_PRODUCTS_IDS)]
                del VENTAS_PRODUCTOS['id_venta_fk']
                del VENTAS_PRODUCTOS['id_producto_fk']
                st.session_state['VENTAS'] = True
                st.session_state['VENTAS_PRODUCTOS'] = VENTAS_PRODUCTOS

  if 'VENTAS' not in st.session_state:
    st.info('Busque datos aplicando los filtros.', icon="ℹ️")
  else:
    VENTAS_PRODUCTOS = st.session_state['VENTAS_PRODUCTOS']

    if len(VENTAS_PRODUCTOS)==0: 
      st.info('No se han registrado ventas con esos parámetros.', icon="ℹ️")
      st.stop()

    VENTAS_PRODUCTOS = st.session_state['VENTAS_PRODUCTOS']

    VENTAS_PRODUCTOS = VENTAS_PRODUCTOS[[
      'fecha_creacion',
      'name_user',
      'nombre',
      'precio',
      'cantidad',
      'total',
      ]]
    
    VENTAS_PRODUCTOS.rename(columns = {
        'fecha_creacion':'Fecha de Creación',
        'name_user':'Usuario',
        'nombre':'Producto',
        'precio':'Precio Unitario',
        'cantidad':'Cantidad',
        'total':'Precio Total',
      }, inplace = True)

    # FILA TOTAL
    row_sum = VENTAS_PRODUCTOS.iloc[:,3:6].sum()
    row_sum['Usuario'] = int(len(VENTAS_PRODUCTOS['Usuario'].unique()))
    row_sum['Producto'] = int(len(VENTAS_PRODUCTOS))

    VENTAS_PRODUCTOS.loc['Total'] = row_sum
    VENTAS_PRODUCTOS_EXCEL = VENTAS_PRODUCTOS.copy()

    VENTAS_PRODUCTOS['Precio Unitario'] = VENTAS_PRODUCTOS['Precio Unitario'].apply(lambda x: f'$ {x:,.2f}')
    VENTAS_PRODUCTOS['Precio Total'] = VENTAS_PRODUCTOS['Precio Total'].apply(lambda x: f'$ {x:,.2f}')

    VENTAS_PRODUCTOS['Usuario'] = VENTAS_PRODUCTOS['Usuario'].astype(str)
    VENTAS_PRODUCTOS['Usuario'] = VENTAS_PRODUCTOS['Usuario'].str.replace('.0', '')
    VENTAS_PRODUCTOS['Producto'] = VENTAS_PRODUCTOS['Producto'].astype(str)
    VENTAS_PRODUCTOS['Producto'] = VENTAS_PRODUCTOS['Producto'].str.replace('.0', '')

    VENTAS_PRODUCTOS['Fecha de Creación'] = VENTAS_PRODUCTOS['Fecha de Creación'].dt.strftime("%d-%m-%Y %H:%M:%S")

    VENTAS_PRODUCTOS = VENTAS_PRODUCTOS.fillna('')

    VENTAS_PRODUCTOS.fillna('', inplace=True)

    tab = sac.tabs([
      #sac.TabsItem(label='Ventas por Usuario', icon='person-fill-check'),
      #sac.TabsItem(label='Ventas Totales', icon='currency-dollar'),
      sac.TabsItem(label='Detalle de Ventas', icon='table'),
    ], align='start', variant='default', use_container_width=False, size='sm')

    if tab == 'Detalle de Ventas':



      st.dataframe(VENTAS_PRODUCTOS, use_container_width=True)

      NOMBRE_ARCHIVO = 'REPORTE DE VENTAS' + '_ DEL ' + str(date_desde) + ' AL ' + str(date_hasta) + '.xlsx'
      df_xlsx = to_excel(VENTAS_PRODUCTOS_EXCEL, True)
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
