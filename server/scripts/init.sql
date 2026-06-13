CREATE DATABASE IF NOT EXISTS sc_datav;
USE sc_datav;

CREATE TABLE IF NOT EXISTS revenue_table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    total DECIMAL(20,4)
);
INSERT INTO revenue_table (total) VALUES (996080000);

CREATE TABLE IF NOT EXISTS enterprise_table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cnt INT
);
INSERT INTO enterprise_table (cnt) VALUES (7792);
