<?php
require 'session.php';

$message = ""; // Variable to store error/success messages

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $target = $_POST['target'];
    // Run the ping command and capture the output
    $output = shell_exec("ping -c 3 " . $target);

    // If the output is empty or contains any errors, show the error message
    if ($output === null || $output === "" || strpos($output, 'unknown host') !== false || strpos($output, '100% packet loss') !== false) {
        // If there's an error, show the "Cannot ping" message
        $message = "Cannot ping $target";
    } else {
        // Otherwise, show the ping results
        $message = "Ping results for $target:<br><pre>" . htmlspecialchars($output) . "</pre>";
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ENSIBS Corp Router - Diagnostics</title>
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
            text-align: center;
        }
        h1 {
            color: #4CAF50;
        }
        form {
            margin-top: 20px;
        }
        input[type="text"] {
            padding: 8px;
            width: 60%;
            margin-bottom: 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        button {
            padding: 10px 15px;
            font-size: 16px;
            color: white;
            background-color: #4CAF50;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        pre {
            background-color: #eee;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            max-width: 90%;
            margin: auto;
            text-align: left;
        }
        .error {
            color: red;
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
        <h1>Diagnostics</h1>
        <p>Enter an IP address or hostname to check connectivity.</p>

        <form action="diagnostics.php" method="POST">
            <input type="text" name="target" placeholder="Enter IP or hostname" required>
            <button type="submit">Run Diagnostics</button>
        </form>

        <?php if (isset($message)): ?>
            <h2>Output:</h2>
            <?php if (strpos($message, 'Cannot ping') !== false): ?>
                <p class="error"><?php echo htmlspecialchars($message); ?></p>
            <?php else: ?>
                <div><?php echo $message; ?></div>
            <?php endif; ?>
        <?php endif; ?>
    </div>
</body>
</html>
