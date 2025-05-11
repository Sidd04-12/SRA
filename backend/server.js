const express = require('express');
const cors = require('cors');
const { exec } = require('child_process');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json());

// Route: POST /api/optimize-route
app.post('/api/optimize-route', (req, res) => {
    const pythonScript = path.join(__dirname, 'ship_route_optimizer.py');

  exec(`python "${pythonScript}"`, (error, stdout, stderr) => {
    if (error) {
      console.error(`❌ Error executing script: ${error.message}`);
      return res.status(500).json({ error: 'Python script execution failed.' });
    }
    if (stderr) console.warn(`⚠️ Script stderr: ${stderr}`);
    console.log(`✅ Python Output:\n${stdout}`);
    res.json({ message: 'Route optimization completed. Open ship_routes.html to view the result.' });
  });
});

// Start server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`🚢 Ship Optimizer backend running at http://localhost:${PORT}`);
});
