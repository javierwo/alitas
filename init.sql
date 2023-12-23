CREATE TABLE productos (
	id_producto SERIAL PRIMARY KEY,
	nombre varchar(300),
	precio real,
	fecha TIMESTAMP default now()
);

insert into productos (nombre, precio) values
	('SOLANO 2 ALITAS + PAPAS', 2.00),
  ('TU Y YO 4 ALITAS + PAPAS', 3.75),
  ('GOLOSO  6 ALITAS + PAPAS Y JUGO COCO', 5.50),
  ('JORGA 9 ALITAS + PAPAS Y COLA 1LT', 7.50),
  ('FIESTERO 13 ALITAS + PAPAS + COLA 1LT', 11.00),
  ('ALITAS X UNIDAD', 0.70),
  ('PAPI POLLO  1 PRESA + PAPAS', 2.25),
  ('PRESAS X UNIDAD', 1.50),
  ('DEDOS DE PECHUGA (4 tiras de pechuga)', 3.50),
  ('ARROZ MIX', 1.50),
  ('ARROZ CON POLLO', 2.75),
  ('Mr. BROASTER  3 PRESAS  + PAPAS', 6.50),
  ('PORC PAPAS', 1.00),
  ('SALCHI pequeña', 1.25),
  ('SALCHI grande', 1.50),
  ('SALCHI MIX  400cc', 1.80),
  ('MR. PAPA STRIPS', 1.75),
  ('CHORIPAPA 400cc', 2.00),
  ('HAMB POLLO', 1.50),
  ('CHESS BURGER', 1.75),
  ('MR. BURGER', 2.50),
  ('CHORIPAN peq', 1.50),
  ('CHORIPAN gr', 2.50),
  ('PERNIL + VASO JUGO', 2.00),
  ('CUBANO', 1.50),
  ('HOT DOG ', 1.25),
  ('HOT DOG JUMBO', 2.00),
  ('NACHOS CON QUESO', 2.00),
  ('EMPANADA POLLO', 1.50),
  ('CAFÉ', 0.75),
  ('JUGO DE COCO', 0.75),
  ('JUGO DE JAMAICA', 0.50),
  ('COLA 1 LITRO', 1.00),
  ('COLA PERSONAL', 0.75),
  ('COLA MINI ', 0.50),
  ('AGUA', 0.50),
  ('HELADO pequeño', 0.90),
  ('HELADO grande', 1.00),
  ('CERVEZA ', 1.50),
  ('CIGARRILLOS', 0.50);

CREATE TABLE usuarios (
	id_usuario SERIAL PRIMARY KEY,
	username varchar(50),
	name_user varchar(200)
);

insert into usuarios (username, name_user) values 
  ('asinche', 'Alexandra Sinche'),
  ('sanchezd', 'Deisy Sanchez'),
  ('tenecorat', 'Tatiana Tenecora');

CREATE TABLE productos_ventas (
	id_producto_venta SERIAL PRIMARY KEY,
	id_venta_fk integer REFERENCES ventas(id_venta),
	id_producto_fk integer REFERENCES productos(id_producto),
	cantidad smallint,
	total real
);

create table ventas (
	id_venta SERIAL PRIMARY KEY,
	num_productos smallint,
	total real,
	valor_pagado real,
	cambio real,
	id_usuario_fk integer REFERENCES usuarios(id_usuario)
	fecha_creacion TIMESTAMP default now(),
	
);