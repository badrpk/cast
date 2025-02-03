const express = require("express");
const http = require("http");
const WebSocket = require("ws");
const os = require("os");

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Get the IP address of the server
const getLocalIP = () => {
  const interfaces = os.networkInterfaces();
  for (const iface of Object.values(interfaces)) {
    for (const config of iface) {
      if (config.family === "IPv4" && !config.internal) {
        return config.address;
      }
    }
  }
  return "Unknown IP";
};

// Serve the homepage
app.get("/", (req, res) => {
  const ipAddress = getLocalIP();
  res.send(`
    <html>
      <head>
        <title>CastApp Server</title>
        <style>
          body { font-family: Arial, sans-serif; text-align: center; padding: 20px; }
          h1 { color: #333; }
          .info { margin-top: 20px; font-size: 18px; }
          .permissions { margin-top: 20px; font-size: 16px; }
          .status { margin-top: 20px; font-size: 18px; color: green; }
        </style>
      </head>
      <body>
        <h1>Welcome to CastApp</h1>
        <p>CastApp allows you to cast media from your device to others on the same network.</p>
        
        <div class="info">
          <strong>Server IP Address:</strong> <span id="server-ip">${ipAddress}:8080</span>
        </div>

        <div class="permissions">
          <h2>Permissions Required</h2>
          <ul>
            <li><a href="intent://camera/#Intent;scheme=android-app;end;">Grant Camera Access</a></li>
            <li><a href="intent://storage/#Intent;scheme=android-app;end;">Grant Storage Access</a></li>
            <li><a href="intent://location/#Intent;scheme=android-app;end;">Grant Location Access</a></li>
            <li><a href="intent://microphone/#Intent;scheme=android-app;end;">Grant Microphone Access</a></li>
          </ul>
        </div>

        <div class="status">
          WebSocket Server is Running!
        </div>
      </body>
    </html>
  `);
});

// WebSocket functionality
wss.on("connection", (ws) => {
  console.log("New client connected");
  ws.send("Connected to CastApp Server");

  ws.on("message", (message) => {
    console.log(`Received: ${message}`);
  });

  ws.on("close", () => {
    console.log("Client disconnected");
  });
});

// Start server
server.listen(8080, () => {
  console.log(`Server running at http://${getLocalIP()}:8080`);
});
