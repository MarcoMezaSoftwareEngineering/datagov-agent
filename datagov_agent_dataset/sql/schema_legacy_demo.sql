-- Esquema legacy simulado para DataGov Agent

CREATE TABLE clientes (
    cliente_id VARCHAR(20) PRIMARY KEY,
    nombre VARCHAR(100),
    apellido VARCHAR(100),
    dni VARCHAR(20),
    ruc VARCHAR(20),
    correo VARCHAR(150),
    telefono VARCHAR(20),
    direccion VARCHAR(200),
    distrito VARCHAR(100),
    pais VARCHAR(50),
    fecha_registro DATE,
    estado_cliente VARCHAR(30),
    segmento VARCHAR(50)
);

CREATE TABLE productos (
    producto_id VARCHAR(20) PRIMARY KEY,
    sku VARCHAR(50),
    nombre_producto VARCHAR(200),
    categoria VARCHAR(100),
    marca VARCHAR(100),
    precio DECIMAL(12,2),
    moneda VARCHAR(10),
    estado_producto VARCHAR(30),
    fecha_alta DATE,
    proveedor_id VARCHAR(20)
);

CREATE TABLE ventas (
    venta_id VARCHAR(20) PRIMARY KEY,
    cliente_id VARCHAR(20),
    producto_id VARCHAR(20),
    fecha_venta DATE,
    cantidad INTEGER,
    precio_unitario DECIMAL(12,2),
    total DECIMAL(12,2),
    canal VARCHAR(50),
    sucursal_id VARCHAR(20),
    vendedor VARCHAR(100)
);
