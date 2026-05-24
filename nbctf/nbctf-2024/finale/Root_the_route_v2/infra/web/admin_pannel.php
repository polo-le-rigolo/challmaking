<?php
require 'session.php';

$uptime = "5 days, 3 hours, 22 minutes";
$firmware_version = "1.2.3";
$connected_devices = 12;
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ENSIBS Corp Router - Admin Panel</title>
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
            max-width: 800px;
            margin: auto;
            text-align: left;
        }
        h1 {
            color: #4CAF50;
            text-align: center;
        }
        .section {
            margin-top: 20px;
            padding: 20px;
            background-color: #fff;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        .section h2 {
            color: #4CAF50;
            margin-top: 0;
        }
        .quick-links {
            display: flex;
            justify-content: space-around;
            margin-top: 20px;
        }
        .quick-links button {
            padding: 10px 15px;
            font-size: 16px;
            color: white;
            background-color: #4CAF50;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .quick-links button:hover {
            background-color: #45a049;
        }
        .info {
            display: flex;
            justify-content: space-between;
        }
        .info div {
            text-align: center;
        }
    </style>
</head>
<body>
    <nav>
        <a href="admin_pannel.php">Admin Panel</a>
        <a href="network_settings.php">Network Settings</a>
        <a href="diagnostics.php">Diagnostics</a>
        <a href="logout.php">Logout</a>

    </nav>
    
    <div class="content">
        <h1>Admin Panel</h1>
        <p>Welcome to the ENSIBS Corp Router Administration Panel!</p>
        
        <div class="section">
            <h2>Router Status</h2>
            <div class="info">
                <div>
                    <strong>Uptime:</strong>
                    <p><?php echo $uptime; ?></p>
                </div>
                <div>
                    <strong>Firmware Version:</strong>
                    <p><?php echo $firmware_version; ?></p>
                </div>
                <div>
                    <strong>Connected Devices:</strong>
                    <p><?php echo $connected_devices; ?></p>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Quick Actions</h2>
            <div class="quick-links">
                <button onclick="alert('Router is restarting...');">Restart Router</button>
                <button onclick="alert('Logs downloaded');">Download Logs</button>
                <button onclick="alert('Firmware update check...');">Check for Updates</button>
            </div>
        </div>
    </div>
</body>
</html>

