
import streamlit as st
import pandas as pd

# Lista de productos con sus precios
productos = {
"SOLANO 2 ALITAS + PAPAS": 2.00,
    "TU Y YO 4 ALITAS + PAPAS": 3.75,
    "GOLOSO  6 ALITAS + PAPAS Y JUGO COCO": 5.50,
    "JORGA 9 ALITAS + PAPAS Y COLA 1LT": 7.50,
    "FIESTERO 13 ALITAS + PAPAS + COLA 1LT": 11.00,
    "ALITAS X UNIDAD": 0.70,
    "PAPI POLLO  1 PRESA + PAPAS": 2.25,
    "PRESAS X UNIDAD": 1.50,
    "DEDOS DE PECHUGA (4 tiras de pechuga)": 3.50,
    "ARROZ MIX": 1.50,
    "ARROZ CON POLLO": 2.75,
    "Mr. BROASTER  3 PRESAS  + PAPAS": 6.50,
    "PORC PAPAS": 1.00,
    "SALCHI pequeña": 1.25,
    "SALCHI grande": 1.50,
    "SALCHI MIX  400cc": 1.80,
    "MR. PAPA STRIPS": 1.75,
    "CHORIPAPA 400cc": 2.00,
    "HAMB POLLO": 1.50,
    "CHESS BURGER": 1.75,
    "MR. BURGER": 2.50,
    "CHORIPAN peq": 1.50,
    "CHORIPAN gr": 2.50,
    "PERNIL + VASO JUGO": 2.00,
    "CUBANO": 1.50,
    "HOT DOG ": 1.25,
    "HOT DOG JUMBO": 2.00,
    "NACHOS CON QUESO": 2.00,
    "EMPANADA POLLO": 1.50,
    "CAFÉ": 0.75,
    "JUGO DE COCO": 0.75,
    "JUGO DE JAMAICA": 0.50,
    "COLA 1 LITRO": 1.00,
    "COLA PERSONAL": 0.75,
    "COLA MINI ": 0.50,
    "AGUA": 0.50,
    "HELADO pequeño": 0.90,
    "HELADO grande": 1.00,
    "CERVEZA ": 1.50,
    "CIGARRILLOS": 0.50,
}


def format_precio(precio):
  precio_str = str(precio)

  if len(precio_str.split('.')[1]) == 2:
    precio_str = '$ '+str(precio)
  elif len(precio_str.split('.')[1]) == 1:
    precio_str = '$ '+str(precio) + '0'

  return precio_str



# Crear una tabla para mostrar los productos y sus precios
df_productos = pd.DataFrame.from_dict(productos, orient='index', columns=['Precio'])

# Crear una sección para agregar productos al carrito
st.title('MR. ALITAS')

st.divider()
st.subheader('Menú')

col1, col2, col3 = st.columns([2,1,1])

with col1:
  producto = st.selectbox('Selecciona un producto', list(productos.keys()))

with col2:
  cantidad = st.number_input('Cantidad', min_value=1, max_value=200, value=1)

with col3:
  title = st.text_input('Precio', format_precio(productos[producto]), disabled=True)

with col4:
    vendedor = st.selectbox('Selecciona un vendedor', ['VENDEDOR 1', 'VENDEDOR 2', 'VENDEDOR 3'])




if st.button('Agregar al carrito'):
  st.write(f'Agregaste {cantidad} {producto} al carrito.')

    # Initialization
  if 'list_carrito' not in st.session_state:
    list_carrito = [{
      "Producto":producto,
      "Cantidad":cantidad,
      "Precio Unitario":productos[producto],
      "Total":cantidad*productos[producto]
      }]
    st.session_state['list_carrito'] = list_carrito

  else:
    list_carrito = st.session_state['list_carrito']
    list_carrito.append({
      "Producto":producto,
      "Cantidad":cantidad,
      "Precio Unitario":productos[producto],
      "Total":cantidad*productos[producto]
      })
    
  #st.write(list_carrito)


st.divider()
st.subheader('Carrito de Compras')


if 'list_carrito' not in st.session_state:
  st.write('No hay productos en el carrito.')

else: 

  list_carrito = st.session_state['list_carrito']

  df = pd.DataFrame(
    list_carrito
  )

  columns = df.columns
  column_config = {column: st.column_config.Column(disabled=True) for column in columns}

  df["Borrar Producto"] = False
  edited_df = st.data_editor(df, use_container_width = True, hide_index = True, column_config=column_config)
  #st.write(edited_df)

  df = pd.DataFrame(
    [
      {"Cantidad de Productos": edited_df['Cantidad'].sum(),"Total del Pedido":  edited_df['Total'].sum()},
    ]
  )

  st.dataframe(df, use_container_width = True, hide_index = True)


  if st.button('PAGAR'):
    st.session_state['pago'] = True
    st.session_state['df'] = df


if 'pago' in st.session_state:
  df = st.session_state['df']
  number = st.number_input("Paga con", value=None, placeholder="Ingrese el valor.")
  #st.write('Total: ', df['Total del Pedido'][0])

  cambio = round((number-df['Total del Pedido'][0]), 2)

  st.write('Cambio: ', cambio)




  if st.button('Guardar Pedido'):
    st.write('Pedido Guardado')
