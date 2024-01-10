

  # LOAD DATA
  with st.status("ESTADO"):
    st.caption("Cargando datos...")
    with alchemyEngine.connect() as dbConnection:
      VENTAS_GENERAL = pd.read_sql(
        "select * from ventas v left join usuarios u on u.id_usuario = v.id_usuario_fk",
        dbConnection,
      )

      ALL_PRODUCTS = pd.read_sql(
        "select id_producto, nombre, precio from productos p",
        dbConnection,
      )

    st.caption("Actualización: "+str(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))

  if len(VENTAS_GENERAL) == 0:
    st.error('No se ha registrado ninguna venta.')
    st.stop()

  # FILTROS
  ALL_USERS = VENTAS_GENERAL['name_user'].unique().tolist()


  with st.expander("FILTROS", expanded=True):


    options_producto = st.multiselect(
      'Productos:',
      ALL_PRODUCTS['nombre'].tolist(),
    )

    ALL_PRODUCTS_IDS = ALL_PRODUCTS[ALL_PRODUCTS['nombre'].isin(options_producto)]['id_producto'].tolist()
    ALL_PRODUCTS_IDS


    col1_date, col2_date = st.columns(2)
    with col1_date:
      date_desde = st.date_input("Desde:", datetime.date.today()-datetime.timedelta(days=30), max_value=datetime.date.today())
    with col2_date:
      date_hasta = st.date_input("Hasta:", datetime.date.today(), max_value=datetime.date.today())




  # FILTROS APLICADOS
  if not (len(options_usuario) == 0 ) or (len(options_usuario) == len(ALL_USERS)):
    VENTAS_GENERAL = VENTAS_GENERAL[VENTAS_GENERAL['name_user'].isin(options_usuario)]

  






  VENTAS_GENERAL = VENTAS_GENERAL[(VENTAS_GENERAL['fecha_creacion'].dt.date >= date_desde) & (VENTAS_GENERAL['fecha_creacion'].dt.date <= date_hasta)]

  if len(VENTAS_GENERAL) == 0:
    st.error('No existen ventas disponibles con ese filtro.')
    st.stop()

  # VENTAS DIARIAS POR USUARIOS
  daily_user_sales = VENTAS_GENERAL.groupby([VENTAS_GENERAL['fecha_creacion'].dt.to_period('D'), 'name_user'])['total'].sum().reset_index()
  daily_user_sales = daily_user_sales.sort_values(by=['fecha_creacion'])
  daily_user_sales['fecha_creacion'] = daily_user_sales['fecha_creacion'].dt.strftime("%d-%m-%Y")
  daily_user_sales_pivot = daily_user_sales.pivot(
    index='name_user',
    columns='fecha_creacion',
    values='total')
  daily_user_sales_pivot = daily_user_sales_pivot.reset_index()
  daily_user_sales_pivot = daily_user_sales_pivot.fillna(0)
  daily_user_sales_unpivot = daily_user_sales_pivot.melt(id_vars=['name_user'], var_name='fecha_creacion', value_name='total')
  
  # Convierte la columna 'fecha_string' a objetos de fecha para ordenar
  daily_user_sales_unpivot['fecha_creacion'] = pd.to_datetime(daily_user_sales_unpivot['fecha_creacion'], format='%d-%m-%Y')
  daily_user_sales_unpivot = daily_user_sales_unpivot.sort_values(by='fecha_creacion')
  daily_user_sales_unpivot['fecha_creacion'] = daily_user_sales_unpivot['fecha_creacion'].dt.strftime("%d-%m-%Y")
  

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
  daily_general_sales = daily_general_sales.sort_values(by=['fecha_creacion'])
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
  # Convierte la columna 'fecha_string' a objetos de fecha para ordenar
  monthly_user_sales_unpivot['fecha_creacion'] = pd.to_datetime(monthly_user_sales_unpivot['fecha_creacion'], format='%m-%Y')
  monthly_user_sales_unpivot = monthly_user_sales_unpivot.sort_values(by='fecha_creacion')
  monthly_user_sales_unpivot['fecha_creacion'] = monthly_user_sales_unpivot['fecha_creacion'].dt.strftime("%m-%Y")
  

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
  monthly_general_sales = monthly_general_sales.sort_values(by=['fecha_creacion'])
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
    sac.TabsItem(label='Ventas Totales', icon='currency-dollar'),
    sac.TabsItem(label='Detalle de Ventas', icon='table'),
  ], align='center', variant='default', use_container_width=True, size='sm')

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

  elif tab == 'Ventas Totales':
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

  elif tab == 'Detalle de Ventas':
    id_venta_list = VENTAS_GENERAL['id_venta'].tolist()

    with alchemyEngine.connect() as dbConnection:
      VENTAS_PRODUCTOS = pd.read_sql(
        "select pv.id_producto_fk, pv.cantidad, pv.total, u.name_user, v.fecha_creacion from productos_ventas pv left join productos p on p.id_producto = pv.id_producto_fk left join ventas v on pv.id_venta_fk  = v.id_venta left join usuarios u on v.id_usuario_fk = u.id_usuario where id_venta_fk in ("+str(id_venta_list)[1:-1]+")",
        dbConnection,
      )

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

    # Cast Venta ID a entero
    ventas_generales_show['Venta ID'] = ventas_generales_show['Venta ID'].astype(int)

    # FILA TOTAL
    row_sum = ventas_generales_show.iloc[:,1:3].sum()
    row_sum['Venta ID'] = int(len(ventas_generales_show))

    ventas_generales_show.loc['Total'] = row_sum
    ventas_generales_show_format = ventas_generales_show.copy()


    # Formatear la columnas con precios en formato de dólares
    ventas_generales_show_format['Total'] = ventas_generales_show_format['Total'].apply(lambda x: f'$ {x:,.2f}')
    ventas_generales_show_format['Valor Cancelado'] = ventas_generales_show_format['Valor Cancelado'].apply(lambda x: f'$ {x:,.2f}')
    ventas_generales_show_format['Cambio'] = ventas_generales_show_format['Cambio'].apply(lambda x: f'$ {x:,.2f}')
    ventas_generales_show_format['Cambio'] = ventas_generales_show_format['Cambio'].replace('$ nan', '')
    ventas_generales_show_format['Valor Cancelado'] = ventas_generales_show_format['Valor Cancelado'].replace('$ nan', '')

    # Formatear la columna de fecha
    ventas_generales_show_format['Fecha de Creación'] = ventas_generales_show_format['Fecha de Creación'].dt.strftime("%d-%m-%Y %H:%M:%S")

    print(ventas_generales_show_format.info())

    # Eliminar las filas con valores nulos
    ventas_generales_show_format = ventas_generales_show_format.fillna('')

    st.subheader('Todas las Ventas')
    st.dataframe(ventas_generales_show_format, use_container_width=True)
    NOMBRE_ARCHIVO = 'MR ALITAS - VENTAS TOTALES.xlsx'
    df_xlsx = to_excel(ventas_generales_show, True)
    st.download_button(label='Descargar Excel', data=df_xlsx, file_name=NOMBRE_ARCHIVO)

    st.divider()

    st.subheader('Productos Vendidos')

    daily_user_sales = VENTAS_PRODUCTOS.groupby([VENTAS_PRODUCTOS['fecha_creacion'].dt.to_period('D'), 'name_user','id_producto_fk']).agg(
      {
        'cantidad': 'sum',
        'total': 'sum'}
      ).reset_index()
    
    MERGE_VENTAS = pd.merge(daily_user_sales, ALL_PRODUCTS, left_on='id_producto_fk', right_on='id_producto', how='left')

    MERGE_VENTAS = MERGE_VENTAS[[
      'fecha_creacion',
      'name_user',
      'nombre',
      'precio',
      'cantidad',
      'total'
      ]]
    
    MERGE_VENTAS.rename(columns = {
      'fecha_creacion':'Fecha de Venta',
      'name_user':'Usuario',
      'nombre':'Producto',
      'precio':'Precio Unitario',
      'cantidad':'Cantidad',
      'total':'Total',
    }, inplace = True)

    MERGE_VENTAS_show = MERGE_VENTAS.copy()
    MERGE_VENTAS_show['Precio Unitario'] = MERGE_VENTAS_show['Precio Unitario'].apply(lambda x: f'$ {x:,.2f}')
    MERGE_VENTAS_show['Total'] = MERGE_VENTAS_show['Total'].apply(lambda x: f'$ {x:,.2f}')

    st.dataframe(MERGE_VENTAS_show, use_container_width=True, hide_index=True)

    NOMBRE_ARCHIVO = 'MR ALITAS - PRODUCTOS VENDIDOS.xlsx'
    df_xlsx = to_excel(MERGE_VENTAS, False)
    st.download_button(label='Descargar Excel', data=df_xlsx, file_name=NOMBRE_ARCHIVO)


  

