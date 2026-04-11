CREATE DATABASE IF NOT EXISTS proyecto_prog2
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'proyecto_user'@'localhost' IDENTIFIED BY 'change_me';
GRANT ALL PRIVILEGES ON proyecto_prog2.* TO 'proyecto_user'@'localhost';

CREATE USER IF NOT EXISTS 'proyecto_user'@'127.0.0.1' IDENTIFIED BY 'change_me';
GRANT ALL PRIVILEGES ON proyecto_prog2.* TO 'proyecto_user'@'127.0.0.1';

FLUSH PRIVILEGES;
