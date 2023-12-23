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


# Sidebar
def sidebar_info(name, authenticator):
  st.sidebar.subheader(name)

  st.sidebar.caption('Usuario')
  st.sidebar.markdown('---')

  st.sidebar.title('Sesión')

  # CURRENTLY IF NOT WORKIING
  if authenticator.logout('Cerrar Sesión', 'sidebar'):
    print('cerrar sesion')

  st.sidebar.markdown('---')

  with st.sidebar.expander("Versión: 1.0"):
    st.write('23/12/2023 - Versión Inicial.')
    
  st.sidebar.caption('Copyright © 2023. Todos los derechos reservados.')


# FUNCIONES
def format_precio(precio):
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
    host='localhost',
    database='mr_alitas',
    user='postgres',
    password='000111'
  )
  return connection

# Función para cargar datos
def cargar_datos(id_usuario, engine):
  query = f"""
  SELECT v.fecha_creacion, pv.total, pv.cantidad, p.nombre
  FROM ventas v
  JOIN productos_ventas pv ON v.id_venta = pv.id_venta_fk
  JOIN productos p ON p.id_producto = pv.id_producto_fk
  WHERE v.id_usuario_fk = {id_usuario}
  """
  return pd.read_sql(query, engine)


def cargar_ventas(id_usuario_fk, engine):
  if 'ventas_usuario' in st.session_state:
    ventas_usuario = st.session_state['ventas_usuario']
  else:
    with engine.connect() as dbConnection:
      ventas_usuario = pd.read_sql(
        "SELECT * FROM ventas where id_usuario_fk = %s",
        dbConnection,
        params=(id_usuario_fk,)
      )
    ventas_usuario['valor_pagado'] = ventas_usuario['valor_pagado'].apply(format_precio)
    ventas_usuario['total'] = ventas_usuario['total'].apply(format_precio)
    ventas_usuario['cambio'] = ventas_usuario['cambio'].apply(format_precio)

    ventas_usuario.rename(columns = {
      'id_venta':'Venta',
      'num_productos':'Número de Productos',
      'total':'Total',
      'valor_pagado':'Valor Cancelado',
      'cambio':'Cambio',
      'fecha_creacion':'Fecha de Creación',
    }, inplace = True)
    del ventas_usuario['id_usuario_fk']



    st.session_state['ventas_usuario'] = ventas_usuario


  return ventas_usuario


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
    #config['preauthorized']
  )
  name, authentication_status, username = authenticator.login('Iniciar Sesión', 'main')

  if authentication_status:

    # SIDEBAR INFO
    sidebar_info(name, authenticator)


    # DATABASE CONNECTION
    print('checking connection')
    if 'is_db_connected' in st.session_state:
      print('db connection exists')
      alchemyEngine = st.session_state['alchemyEngine']
    else:
      print('connecting to db...')
      alchemyEngine = create_engine('postgresql+psycopg2://postgres:000111@localhost:5432/mr_alitas', pool_recycle=3600);
      st.session_state['is_db_connected'] = True
      st.session_state['alchemyEngine'] = alchemyEngine
      print('connected to db')


    # LEER LOS PRODUCTOS
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
      #t.write(id_usuario_fk)


    # TITLES
    st.title('MR. ALITAS')

    tab1, tab2 = st.tabs(["VENTA", "DASHBOARD"])

    with tab1:
      st.subheader('Menú')
      # ADDING PRODUCTS
      col1, col2 = st.columns([2,1])

      with col1:
        producto = st.selectbox('Seleccione un producto.', PRODUCTOS_NOMBRE_LIST)

      with col2:
        cantidad = st.number_input('Cantidad', min_value=1, max_value=200, value=1)

      list_carrito_adding = [{
        "Precio Unitario":find_precio(producto, 1, True, PRODUCTOS_NOMBRE_LIST, PRODUCTOS_PRECIO_LIST),
        "Precio Total":find_precio(producto, cantidad, True, PRODUCTOS_NOMBRE_LIST, PRODUCTOS_PRECIO_LIST)
        }]

      df_carrito_adding = pd.DataFrame(
        list_carrito_adding
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

        # st.dataframe(df_list_carrito_formatted, use_container_width=True, hide_index=True)
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

          with st.spinner(text="Guardando...", cache=False):

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


    with tab2:
  
      # Cargar datos
      datos = cargar_datos( id_usuario_fk, alchemyEngine)
      #datos['fecha_creacion'] = datos['fecha_creacion'].dt.date

      # Procesar datos para el gráfico
      ventas_diarias = datos.groupby(datos['fecha_creacion'].dt.date).agg({'total': 'sum'}).reset_index().head()
      ventas_diarias['total_formato_moneda'] = ['$' + '{:,.2f}'.format(x) for x in ventas_diarias['total']]  # Formatear como moneda

      # Crear el gráfico de barras
      fig_ventas_diarias = px.bar(
        ventas_diarias,
        x='fecha_creacion',
        y='total',
        text='total_formato_moneda',
        labels={'x': 'Fecha', 'total': 'Total de Ventas'}
      )

      fig_ventas_diarias.update_xaxes(
        dtick="1D",
        tickformat="%x"
        )

      fig_ventas_diarias.update_traces(texttemplate='%{text}', textposition='outside')
      fig_ventas_diarias.update_layout(uniformtext_minsize=13, uniformtext_mode='hide')

      fig_ventas_diarias.update_layout(
        xaxis_title="Fecha",  # Cambiar el nombre del eje X
        hovermode=False  # Desactivar el hover
      )

      # Mostrar el gráfico en Streamlit



      # Procesar datos para ventas mensuales
      ventas_mensuales = datos.groupby(datos['fecha_creacion'].dt.to_period('M')).agg({'total': 'sum'})

      # Convertir el índice PeriodIndex a DateTimeIndex para Plotly
      ventas_mensuales.index = ventas_mensuales.index.to_timestamp()

      # Formatear las fechas y los valores de las ventas para el gráfico
      ventas_mensuales.index = ventas_mensuales.index.strftime('%Y-%m')  # Formatear solo con año y mes
      ventas_mensuales['total_formato_moneda'] = ['$' + '{:,.2f}'.format(x) for x in ventas_mensuales['total']]  # Formatear como moneda

      # Crear el gráfico de barras para ventas mensuales
      fig_ventas_mensuales = px.bar(
          ventas_mensuales,
          x=ventas_mensuales.index,
          y='total',
          text='total_formato_moneda',
          labels={'x': 'Mes de Venta', 'total': 'Total de Ventas'}
      )

      fig_ventas_mensuales.update_xaxes(
      dtick="M1",
      tickformat="%b\n%Y")

      # Actualizar el gráfico con las modificaciones
      fig_ventas_mensuales.update_traces(texttemplate='%{text}', textposition='outside', width=0.5)  # Ajustar el ancho de las barras
      fig_ventas_mensuales.update_layout(
          xaxis_title="Mes",
          hovermode=False  # Desactivar el hover
      )



      col1_plot, col2_plot = st.columns(2)

      with col1_plot:
        st.subheader("Ventas Diarias")
        st.plotly_chart(fig_ventas_diarias, theme="streamlit", use_container_width=True)

      with col2_plot:
        st.subheader("Ventas Mensuales")
        st.plotly_chart(fig_ventas_mensuales, theme="streamlit", use_container_width=True)


      ventas_usuario = cargar_ventas(id_usuario_fk, alchemyEngine)

      st.subheader("Ventas")
      st.dataframe(ventas_usuario, use_container_width=True, hide_index=True)

# MAIN STATEMENT
if __name__ == '__main__':
  main()
