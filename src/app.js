import express from 'express';
import { config } from './config.js';
import { isValidVin, decodeVin } from './lib/vin.js';
import { summarizeVehicle } from './lib/openai.js';

const app = express();

app.use(express.json({ limit: '1mb' }));

app.get('/health', (req, res) => {
  res.json({
    ok: true,
    service: 'vin-bridge',
    status: 'healthy',
    openaiConfigured: Boolean(config.openAIKey)
  });
});

app.get('/', (req, res) => {
  res.type('html').send(`<!doctype html>
    <html>
      <head>
        <title>VIN Bridge</title>
        <style>
          body { font-family: Arial, sans-serif; max-width: 700px; margin: 50px auto; padding: 20px; }
          input, button { font-size: 1rem; padding: 10px; margin-top: 8px; }
          input { width: 100%; box-sizing: border-box; }
          button { cursor: pointer; }
          pre { background: #f4f4f4; padding: 16px; overflow: auto; }
        </style>
      </head>
      <body>
        <h1>VIN Bridge</h1>
        <p>Enter a VIN to decode it and summarize the vehicle details.</p>
        <form id="vinForm">
          <input id="vinInput" name="vin" placeholder="e.g. 1HGBH41JXMN109186" maxlength="17" required />
          <button type="submit">Analyze VIN</button>
        </form>
        <pre id="result">Waiting for input...</pre>
        <script>
          const form = document.getElementById('vinForm');
          const result = document.getElementById('result');
          form.addEventListener('submit', async (event) => {
            event.preventDefault();
            const vin = document.getElementById('vinInput').value.trim();
            result.textContent = 'Loading...';
            try {
              const response = await fetch('/api/vin/lookup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ vin })
              });
              const data = await response.json();
              result.textContent = JSON.stringify(data, null, 2);
            } catch (error) {
              result.textContent = 'Error: ' + error.message;
            }
          });
        </script>
      </body>
    </html>`);
});

app.post('/api/vin/lookup', async (req, res, next) => {
  try {
    const vin = (req.body?.vin || '').trim().toUpperCase();

    if (!vin) {
      return res.status(400).json({ error: 'VIN is required.' });
    }

    if (!isValidVin(vin)) {
      return res.status(400).json({
        error: 'Invalid VIN format.',
        vin,
        expected: '17-character VIN using letters/numbers except I, O, Q.'
      });
    }

    const decoded = await decodeVin(vin);
    const ai = await summarizeVehicle(vin, decoded.data, req.body?.prompt || 'Provide a concise summary of this vehicle.');

    return res.json({
      vin,
      valid: true,
      nhtsa: decoded,
      ai
    });
  } catch (error) {
    next(error);
  }
});

app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).json({
    error: 'Internal server error',
    details: err.message
  });
});

export default app;
