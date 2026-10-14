/**
 * Vercel Serverless Function: Payment Webhook Handler
 * Historical Museum of Sughd Region (Khujand Fortress)
 * Endpoint: /api/webhook
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const os = require('os');

// Default fallback secret for webhook signature verification
const DEFAULT_WEBHOOK_SECRET = 'whsec_khujand_museum_mock_webhook_key_9981';

// Tolerance for replay attacks: 300 seconds (5 minutes)
const REPLAY_TOLERANCE_MS = 300 * 1000;

// Helper to update cached order status upon webhook receipt
function updateOrderStatusInCache(orderIdOrBooking, status) {
  if (!orderIdOrBooking) return;
  try {
    const cachePath = path.join(os.tmpdir(), 'khujand_museum_orders.json');
    if (fs.existsSync(cachePath)) {
      const orders = JSON.parse(fs.readFileSync(cachePath, 'utf8'));
      if (orders[orderIdOrBooking]) {
        orders[orderIdOrBooking].status = status;
        orders[orderIdOrBooking].paidAt = new Date().toISOString();
        fs.writeFileSync(cachePath, JSON.stringify(orders, null, 2), 'utf8');
      }
    }
  } catch (_) {
    // Ignore cache update errors
  }
}

// Helper to send JSON response
function sendJson(res, statusCode, payload) {
  if (typeof res.status === 'function' && typeof res.json === 'function') {
    return res.status(statusCode).json(payload);
  }
  res.statusCode = statusCode;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.end(JSON.stringify(payload));
}

// Constant-time string comparison to prevent timing attacks
function timingSafeCompare(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string') return false;
  const bufA = Buffer.from(a.toLowerCase());
  const bufB = Buffer.from(b.toLowerCase());
  if (bufA.length !== bufB.length) return false;
  try {
    return crypto.timingSafeEqual(bufA, bufB);
  } catch (_) {
    return false;
  }
}

module.exports = async function handler(req, res) {
  // 1. Enforce POST method
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return sendJson(res, 405, {
      received: false,
      error: 'Only POST method is allowed for webhook notifications.'
    });
  }

  // 2. Read raw request body
  let rawBody = '';
  if (typeof req.body === 'string') {
    rawBody = req.body;
  } else if (Buffer.isBuffer(req.body)) {
    rawBody = req.body.toString('utf8');
  } else if (req.body && typeof req.body === 'object') {
    rawBody = JSON.stringify(req.body);
  } else {
    rawBody = await new Promise((resolve) => {
      let data = '';
      req.on('data', (chunk) => {
        data += chunk;
      });
      req.on('end', () => resolve(data));
      req.on('error', () => resolve(''));
    });
  }

  // 3. Extract signature & timestamp from headers
  const headers = req.headers || {};
  const sigHeader = headers['x-webhook-signature'] ||
                    headers['stripe-signature'] ||
                    headers['x-alif-signature'] ||
                    headers['x-signature'] ||
                    '';

  const timestampHeader = headers['x-webhook-timestamp'] ||
                          headers['x-timestamp'] ||
                          '';

  let timestampMs = null;
  let receivedSignature = String(sigHeader).trim();

  // If Stripe signature format: t=1234567890,v1=abc...
  if (receivedSignature.includes('t=') && receivedSignature.includes('v1=')) {
    const parts = receivedSignature.split(',');
    for (const part of parts) {
      const [key, val] = part.split('=');
      if (key && key.trim() === 't') {
        const parsedT = parseInt(val.trim(), 10);
        if (!isNaN(parsedT)) {
          timestampMs = parsedT < 10000000000 ? parsedT * 1000 : parsedT;
        }
      }
      if (key && key.trim() === 'v1') {
        receivedSignature = val.trim();
      }
    }
  } else if (timestampHeader) {
    const parsedT = parseInt(String(timestampHeader).trim(), 10);
    if (!isNaN(parsedT)) {
      timestampMs = parsedT < 10000000000 ? parsedT * 1000 : parsedT;
    }
  }

  // 4. Verify timestamp for replay attack prevention (300 seconds tolerance)
  if (timestampMs !== null) {
    const now = Date.now();
    const diff = Math.abs(now - timestampMs);
    if (diff > REPLAY_TOLERANCE_MS) {
      return sendJson(res, 400, {
        received: false,
        code: 'TIMESTAMP_EXPIRED',
        error: 'Payload timestamp expired. Replay tolerance exceeded.'
      });
    }
  }

  // 5. Verify mandatory HMAC-SHA256 signature
  if (!receivedSignature) {
    return sendJson(res, 400, {
      received: false,
      code: 'MISSING_SIGNATURE',
      error: 'Webhook signature header is required.'
    });
  }

  const webhookSecret = process.env.WEBHOOK_SECRET || DEFAULT_WEBHOOK_SECRET;
  let expectedSig = '';

    // If Stripe signature scheme (timestamped)
    if (timestampMs !== null) {
      const timestampSec = Math.floor(timestampMs / 1000);
      const hmacWithTime = crypto.createHmac('sha256', webhookSecret)
        .update(`${timestampSec}.${rawBody}`)
        .digest('hex');
      const hmacPlain = crypto.createHmac('sha256', webhookSecret)
        .update(rawBody)
        .digest('hex');

      if (!timingSafeCompare(receivedSignature, hmacWithTime) &&
          !timingSafeCompare(receivedSignature, hmacPlain)) {
        return sendJson(res, 400, {
          received: false,
          code: 'INVALID_SIGNATURE',
          error: 'Invalid webhook signature.'
        });
      }
    } else {
      expectedSig = crypto.createHmac('sha256', webhookSecret)
        .update(rawBody)
        .digest('hex');

      if (!timingSafeCompare(receivedSignature, expectedSig)) {
        return sendJson(res, 400, {
          received: false,
          code: 'INVALID_SIGNATURE',
          error: 'Invalid webhook signature.'
        });
      }
    }

  // 6. Parse JSON payload and update order state
  let parsedPayload = {};
  try {
    parsedPayload = rawBody ? JSON.parse(rawBody) : {};
  } catch (_) {
    parsedPayload = {};
  }

  const orderId = parsedPayload.orderId || (parsedPayload.data && parsedPayload.data.orderId) || null;
  const bookingCode = parsedPayload.bookingCode ||
                      parsedPayload.bookingNumber ||
                      (parsedPayload.data && parsedPayload.data.bookingCode) ||
                      null;

  if (orderId) updateOrderStatusInCache(orderId, 'PAID');
  if (bookingCode) updateOrderStatusInCache(bookingCode, 'PAID');

  // 7. Acknowledge webhook delivery
  return sendJson(res, 200, {
    received: true,
    status: 'PROCESSED',
    orderId: orderId,
    bookingCode: bookingCode,
    idempotent: true
  });
};
