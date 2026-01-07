CREATE TABLE `licenses` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `license_key` varchar(50) NOT NULL,
  `machine_id` varchar(50) NOT NULL,
  `owner_name` varchar(100) DEFAULT NULL,
  `owner_email` varchar(100) DEFAULT NULL,
  `status` enum('ACTIVE','REVOKED','BANNED') DEFAULT 'ACTIVE',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `last_check` timestamp NULL DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `license_key` (`license_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
