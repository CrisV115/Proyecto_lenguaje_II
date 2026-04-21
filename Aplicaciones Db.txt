CREATE DATABASE IF NOT EXISTS contabilidad CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE contabilidad;

CREATE TABLE IF NOT EXISTS usuarios (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(150) NOT NULL UNIQUE,
  email VARCHAR(255) NOT NULL UNIQUE,
  telefono VARCHAR(10) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  pregunta_seguridad ENUM('mascota','madre','ciudad') NOT NULL,
  respuesta_seguridad VARCHAR(100) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS empleados (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  apellidos_nombres VARCHAR(200) NOT NULL,
  cedula_pasaporte VARCHAR(20) NOT NULL UNIQUE,
  cargo VARCHAR(120) NOT NULL,
  fecha_ingreso DATE NOT NULL,
  sueldo DECIMAL(10,2) NOT NULL,
  decimo_tercer_sueldo_modalidad ENUM('anual','mensual') NOT NULL DEFAULT 'anual',
  decimo_cuarto_sueldo_modalidad ENUM('anual','mensual') NOT NULL DEFAULT 'anual'
);

CREATE TABLE IF NOT EXISTS rol_pagos (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  datos JSON NOT NULL
);

CREATE TABLE IF NOT EXISTS facturas (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  numero_factura VARCHAR(17) NOT NULL UNIQUE,
  razon_social VARCHAR(255) NOT NULL,
  ruc VARCHAR(13) NOT NULL,
  direccion VARCHAR(255) NOT NULL,
  establecimiento VARCHAR(3) NOT NULL DEFAULT '001',
  punto_emision VARCHAR(3) NOT NULL DEFAULT '001',
  secuencial VARCHAR(9) NOT NULL,
  cliente_nombre VARCHAR(255) NOT NULL,
  cliente_identificacion VARCHAR(13) NOT NULL,
  tipo_identificacion ENUM('04','05','06','07') NOT NULL DEFAULT '05',
  cliente_direccion VARCHAR(255) NOT NULL,
  subtotal_0 DECIMAL(12,2) NOT NULL DEFAULT 0,
  subtotal_12 DECIMAL(12,2) NOT NULL DEFAULT 0,
  iva DECIMAL(12,2) NOT NULL DEFAULT 0,
  total_descuento DECIMAL(12,2) NOT NULL DEFAULT 0,
  total DECIMAL(12,2) NOT NULL DEFAULT 0,
  forma_pago VARCHAR(100) NOT NULL,
  tiempo_pago VARCHAR(100) NULL,
  correo VARCHAR(255) NULL,
  telefono VARCHAR(15) NULL,
  clave_acceso VARCHAR(49) NOT NULL,
  numero_autorizacion VARCHAR(49) NULL,
  fecha_emision DATE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS detalle_facturas (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  factura_id INT UNSIGNED NOT NULL,
  codigo VARCHAR(50) NOT NULL,
  descripcion VARCHAR(255) NOT NULL,
  cantidad DECIMAL(12,2) NOT NULL,
  precio_unitario DECIMAL(12,2) NOT NULL,
  descuento DECIMAL(12,2) NOT NULL DEFAULT 0,
  total_sin_impuestos DECIMAL(12,2) NOT NULL,
  CONSTRAINT fk_detalle_factura FOREIGN KEY (factura_id) REFERENCES facturas(id) ON DELETE CASCADE
);
