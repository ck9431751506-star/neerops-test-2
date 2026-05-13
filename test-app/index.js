#!/usr/bin/env node

// Simple dummy application for testing NeerOps CI/CD pipeline
// This is a minimal HTTP server to verify deployment pipeline

const http = require('http');
const os = require('os');

const PORT = process.env.PORT || 8080;
const ENVIRONMENT = process.env.ENVIRONMENT || 'development';
const SERVICE_NAME = process.env.SERVICE_NAME || 'neerops-test-service';

const server = http.createServer((req, res) => {
  const currentTime = new Date().toISOString();
  const uptime = Math.floor(process.uptime());
  
  // Health check endpoint
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'healthy',
      service: SERVICE_NAME,
      environment: ENVIRONMENT,
      timestamp: currentTime,
      uptime_seconds: uptime,
      hostname: os.hostname(),
      memory: {
        used_mb: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
        total_mb: Math.round(process.memoryUsage().heapTotal / 1024 / 1024)
      }
    }));
    return;
  }

  // Ready check endpoint
  if (req.url === '/ready') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      ready: true,
      service: SERVICE_NAME,
      timestamp: currentTime
    }));
    return;
  }

  // Main endpoint
  if (req.url === '/' || req.url === '') {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(`
<!DOCTYPE html>
<html>
<head>
  <title>NeerOps Test Service</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
    .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    h1 { color: #2c3e50; }
    .badge { display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: bold; margin: 5px 0; }
    .badge.healthy { background: #27ae60; color: white; }
    .badge.environment { background: #3498db; color: white; }
    .info-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    .info-table td { padding: 10px; border-bottom: 1px solid #ecf0f1; }
    .info-table td:first-child { font-weight: bold; width: 30%; color: #2c3e50; }
    .endpoints { margin-top: 30px; }
    .endpoint { padding: 10px; background: #ecf0f1; margin: 5px 0; border-radius: 4px; font-family: monospace; }
    .footer { margin-top: 40px; color: #7f8c8d; font-size: 12px; }
  </style>
</head>
<body>
  <div class="container">
    <h1>🚀 NeerOps Test Service</h1>
    
    <p>
      <span class="badge healthy">✓ Healthy</span>
      <span class="badge environment">${ENVIRONMENT}</span>
    </p>
    
    <table class="info-table">
      <tr>
        <td>Service Name</td>
        <td>${SERVICE_NAME}</td>
      </tr>
      <tr>
        <td>Environment</td>
        <td>${ENVIRONMENT}</td>
      </tr>
      <tr>
        <td>Uptime</td>
        <td>${uptime} seconds</td>
      </tr>
      <tr>
        <td>Timestamp</td>
        <td>${currentTime}</td>
      </tr>
      <tr>
        <td>Hostname</td>
        <td>${os.hostname()}</td>
      </tr>
      <tr>
        <td>Memory Used</td>
        <td>${Math.round(process.memoryUsage().heapUsed / 1024 / 1024)} MB</td>
      </tr>
    </table>
    
    <div class="endpoints">
      <h3>API Endpoints</h3>
      <div class="endpoint">GET / - This page</div>
      <div class="endpoint">GET /health - Health check (JSON)</div>
      <div class="endpoint">GET /ready - Readiness check (JSON)</div>
    </div>
    
    <div class="footer">
      <p>This is a test application for NeerOps v9 CI/CD pipeline validation.</p>
      <p>NeerOps v9 - Goal-Centric Autonomous DevOps</p>
    </div>
  </div>
</body>
</html>
    `);
    return;
  }

  // 404 response
  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({
    error: 'Not Found',
    path: req.url,
    service: SERVICE_NAME
  }));
});

server.listen(PORT, () => {
  console.log(`✅ NeerOps Test Service running on port ${PORT}`);
  console.log(`📍 Environment: ${ENVIRONMENT}`);
  console.log(`🔗 HTTP://localhost:${PORT}`);
  console.log(`❤️  Health: HTTP://localhost:${PORT}/health`);
  console.log(`✓ Ready: HTTP://localhost:${PORT}/ready`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully...');
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down gracefully...');
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});
