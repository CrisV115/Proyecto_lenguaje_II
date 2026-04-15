CREATE DATABASE IF NOT EXISTS proyecto_prog2
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'proyecto_user'@'localhost' IDENTIFIED WITH mysql_native_password BY 'proyecto123';
CREATE USER IF NOT EXISTS 'proyecto_user'@'127.0.0.1' IDENTIFIED WITH mysql_native_password BY 'proyecto123';
CREATE USER IF NOT EXISTS 'proyecto_user'@'%' IDENTIFIED WITH mysql_native_password BY 'proyecto123';

ALTER USER 'proyecto_user'@'localhost' IDENTIFIED WITH mysql_native_password BY 'proyecto123';
ALTER USER 'proyecto_user'@'127.0.0.1' IDENTIFIED WITH mysql_native_password BY 'proyecto123';
ALTER USER 'proyecto_user'@'%' IDENTIFIED WITH mysql_native_password BY 'proyecto123';

GRANT ALL PRIVILEGES ON proyecto_prog2.* TO 'proyecto_user'@'localhost';
GRANT ALL PRIVILEGES ON proyecto_prog2.* TO 'proyecto_user'@'127.0.0.1';
GRANT ALL PRIVILEGES ON proyecto_prog2.* TO 'proyecto_user'@'%';

FLUSH PRIVILEGES;
