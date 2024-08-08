CREATE DATABASE exit_management;

USE exit_management;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE exit_queue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    queue_number INT,
    zone VARCHAR(10),
    status ENUM('waiting', 'exited') DEFAULT 'waiting',
    FOREIGN KEY (user_id) REFERENCES users(id)
);
