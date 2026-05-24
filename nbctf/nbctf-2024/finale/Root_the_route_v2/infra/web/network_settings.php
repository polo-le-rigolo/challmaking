<?php
require 'session.php';

// Fake device information to display
$ssid = "ENSIBS_Network";
$ip_address = "192.168.1.1";
$subnet_mask = "255.255.255.0";
$dns_server = "8.8.8.8";
$connected_devices = [
    ["Device" => "Laptop", "IP" => "192.168.1.10"],
    ["Device" => "Smartphone", "IP" => "192.168.1.11"],
    ["Device" => "Tablet", "IP" => "192.168.1.12"]
];
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ENSIBS Corp Router - Network Settings</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
            color: #333;
            margin: 0;
        }
        nav {
            background-color: #333;
            padding: 15px;
            text-align: center;
        }
        nav a {
            color: #4CAF50;
            margin: 0 10px;
            text-decoration: none;
            font-weight: bold;
        }
        nav a:hover {
            text-decoration: underline;
        }
        .content {
            padding: 20px;
            text-align: center;
        }
        h1 {
            color: #4CAF50;
        }
        .info-section {
            max-width: 400px;
            margin: auto;
            text-align: left;
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        .info-section h2 {
            color: #4CAF50;
        }
        .info-item {
            margin: 10px 0;
            font-size: 16px;
        }
        .device-list {
            list-style-type: none;
            padding: 0;
        }
        .device-list li {
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }
        .device-list li:last-child {
            border-bottom: none;
        }
    </style>
</head>
<body>
    <nav>
        <a href="admin_pannel.php">Admin Panel</a>
        <a href="network_settings.php">Network Settings</a>
		<a href="diagnostics.php">Diagnotics</a>
        <a href="logout.php">Logout</a>
    </nav>
    
    <div class="content">
        <h1>Network Settings</h1>
        
        <!-- Network Info Section -->
        <div class="info-section">
            <h2>Network Information</h2>
            <div class="info-item"><strong>SSID:</strong> <?php echo $ssid; ?></div>
            <div class="info-item"><strong>Router IP Address:</strong> <?php echo $ip_address; ?></div>
            <div class="info-item"><strong>Subnet Mask:</strong> <?php echo $subnet_mask; ?></div>
            <div class="info-item"><strong>DNS Server:</strong> <?php echo $dns_server; ?></div>
        </div>

        <!-- Connected Devices Section -->
        <div class="info-section" style="margin-top: 20px;">
            <h2>Connected Devices</h2>
            <ul class="device-list">
                <?php foreach ($connected_devices as $device): ?>
                    <li><strong><?php echo $device["Device"]; ?>:</strong> <?php echo $device["IP"]; ?></li>
                <?php endforeach; ?>
            </ul>
        </div>
    </div>
</body>
</html>

