<?php
// CONFIGURATION
$DB_HOST = '31.11.39.114';
$DB_USER = 'Sql1705615';
$DB_PASS = 'Benellitrk502x!';
$DB_NAME = 'Sql1705615_3';

header('Content-Type: application/json');

// Connect to Database
$conn = new mysqli($DB_HOST, $DB_USER, $DB_PASS, $DB_NAME);
if ($conn->connect_error) {
    die(json_encode(["status" => "ERROR", "message" => "Database Connection Failed: " . $conn->connect_error]));
}

// FIX: Check both GET and POST for action
$action = $_REQUEST['action'] ?? '';
$key = $_REQUEST['key'] ?? '';
$hwid = $_REQUEST['hwid'] ?? '';
$secret = $_REQUEST['admin_secret'] ?? '';

// 1. CHECK LICENSE (Called by App on Startup)
if ($action === 'check') {
    if (!$key || !$hwid) {
        echo json_encode(["status" => "INVALID", "message" => "Missing parameters"]);
        exit;
    }

    $stmt = $conn->prepare("SELECT status, machine_id FROM licenses WHERE license_key = ?");
    $stmt->bind_param("s", $key);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result->num_rows > 0) {
        $row = $result->fetch_assoc();

        // Check Status
        if ($row['status'] !== 'ACTIVE') {
            echo json_encode(["status" => "REVOKED"]);
            exit;
        }

        // Check Machine ID Binding
        if (empty($row['machine_id'])) {
            // First use, bind it
            $update = $conn->prepare("UPDATE licenses SET machine_id = ?, last_check = NOW(), ip_address = ? WHERE license_key = ?");
            $ip = $_SERVER['REMOTE_ADDR'];
            $update->bind_param("sss", $hwid, $ip, $key);
            $update->execute();
            echo json_encode(["status" => "VALID"]);
        } elseif ($row['machine_id'] === $hwid) {
            // Match
            $update = $conn->prepare("UPDATE licenses SET last_check = NOW(), ip_address = ? WHERE license_key = ?");
            $ip = $_SERVER['REMOTE_ADDR'];
            $update->bind_param("ss", $ip, $key);
            $update->execute();
            echo json_encode(["status" => "VALID"]);
        } else {
            // Mismatch
            echo json_encode(["status" => "INVALID", "message" => "HWID Mismatch"]);
        }
    } else {
        echo json_encode(["status" => "INVALID", "message" => "Key not found"]);
    }
}

// 2. ADD LICENSE (Called by KeyGen/Admin)
elseif ($action === 'add') {
    if ($secret !== 'YOUR_ADMIN_SECRET_123') {
        die(json_encode(["status" => "ERROR", "message" => "Unauthorized"]));
    }

    $owner = $_POST['owner'] ?? '';

    $stmt = $conn->prepare("INSERT INTO licenses (license_key, machine_id, owner_name) VALUES (?, ?, ?)");
    $stmt->bind_param("sss", $key, $hwid, $owner);
    if ($stmt->execute()) {
        echo json_encode(["status" => "SUCCESS"]);
    } else {
        echo json_encode(["status" => "ERROR", "message" => $conn->error]);
    }
}

// 3. REVOKE LICENSE
elseif ($action === 'revoke') {
    if ($secret !== 'YOUR_ADMIN_SECRET_123') {
        die(json_encode(["status" => "ERROR", "message" => "Unauthorized"]));
    }

    $stmt = $conn->prepare("UPDATE licenses SET status = 'REVOKED' WHERE license_key = ?");
    $stmt->bind_param("s", $key);
    $stmt->execute();
    echo json_encode(["status" => "SUCCESS"]);
}

// 4. LIST ALL (For Syncing KeyGen Manager)
elseif ($action === 'list_all') {
    if ($secret !== 'YOUR_ADMIN_SECRET_123') {
        die(json_encode(["status" => "ERROR", "message" => "Unauthorized"]));
    }

    $result = $conn->query("SELECT * FROM licenses");
    $licenses = [];
    while ($row = $result->fetch_assoc()) {
        $licenses[] = $row;
    }
    echo json_encode(["status" => "SUCCESS", "data" => $licenses]);
}

// 5. DELETE LICENSE (New Feature)
elseif ($action === 'delete') {
    if ($secret !== 'YOUR_ADMIN_SECRET_123') {
        die(json_encode(["status" => "ERROR", "message" => "Unauthorized"]));
    }

    $stmt = $conn->prepare("DELETE FROM licenses WHERE license_key = ?");
    $stmt->bind_param("s", $key);
    $stmt->execute();
    echo json_encode(["status" => "SUCCESS"]);
} else {
    echo json_encode(["status" => "ERROR", "message" => "Unknown Action: " . htmlspecialchars($action)]);
}

$conn->close();
?>