/**
 * Vercel Serverless Function: Ticket & Payment Status Verification
 * Historical Museum of Sughd Region (Khujand Fortress)
 * Endpoint: /api/verify-payment
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const os = require('os');

// Fallback secret for cryptographic HMAC-SHA256 signing
const DEFAULT_SIGNING_SECRET = 'khujand-fortress-museum-secret-salt-2026';

// Helper to retrieve order from temp filesystem cache
function getOrderFromCache(identifier) {
  if (!identifier) return null;
  try {
    const cachePath = path.join(os.tmpdir(), 'khujand_museum_orders.json');
    if (fs.existsSync(cachePath)) {
      const orders = JSON.parse(fs.readFileSync(cachePath, 'utf8'));
      return orders[identifier] || null;
    }
  } catch (_) {
    // Ignore cache read errors
  }
  return null;
}

// Helper to extract query parameters
function getQueryParams(req) {
  if (req.query && Object.keys(req.query).length > 0) {
    return req.query;
  }
  try {
    const parsedUrl = new URL(req.url, 'http://localhost');
    const params = {};
    for (const [key, val] of parsedUrl.searchParams.entries()) {
      params[key] = val;
    }
    return params;
  } catch (_) {
    return {};
  }
}

// Helper to parse JSON body
async function parseRequestBody(req) {
  if (req.body) {
    if (typeof req.body === 'string') {
      try {
        return JSON.parse(req.body);
      } catch (_) {
        return {};
      }
    }
    if (Buffer.isBuffer(req.body)) {
      try {
        return JSON.parse(req.body.toString('utf8'));
      } catch (_) {
        return {};
      }
    }
    if (typeof req.body === 'object') {
      return req.body;
    }
  }

  return new Promise((resolve) => {
    let raw = '';
    req.on('data', (chunk) => {
      raw += chunk;
    });
    req.on('end', () => {
      try {
        resolve(raw ? JSON.parse(raw) : {});
      } catch (_) {
        resolve({});
      }
    });
    req.on('error', () => resolve({}));
  });
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

// Timing-safe or case-insensitive string equality check
function safeCompare(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string') return false;
  const upperA = a.toUpperCase();
  const upperB = b.toUpperCase();
  if (upperA === upperB) return true;
  // Also check if one is prefix of other (e.g. 16-char truncated hex vs 64-char full hex)
  if (upperA.length === 16 && upperB.startsWith(upperA)) return true;
  if (upperB.length === 16 && upperA.startsWith(upperB)) return true;
  return false;
}

module.exports = async function handler(req, res) {
  // Support both GET and POST
  if (req.method !== 'GET' && req.method !== 'POST') {
    res.setHeader('Allow', 'GET, POST');
    return sendJson(res, 405, {
      success: false,
      valid: false,
      error: {
        code: 'METHOD_NOT_ALLOWED',
        message: 'Only GET and POST methods are allowed.'
      }
    });
  }

  // Extract parameters from query or body
  const queryParams = getQueryParams(req);
  const bodyParams = req.method === 'POST' ? await parseRequestBody(req) : {};
  const params = { ...queryParams, ...bodyParams };

  const bookingNumber = String(params.bookingNumber || params.bookingCode || '').trim();
  const orderId = String(params.orderId || '').trim();
  const sessionToken = String(params.sessionToken || '').trim();
  const signature = String(params.signature || params.qrSignature || '').trim();
  const simulate = String(params.simulate || '').toLowerCase();

  // If no identifying parameter is provided
  if (!bookingNumber && !orderId && !sessionToken) {
    return sendJson(res, 400, {
      success: false,
      valid: false,
      error: {
        code: 'MISSING_PARAMETERS',
        message: 'bookingNumber, bookingCode, or orderId is required for verification.'
      }
    });
  }

  // Look up in order cache
  const cachedOrder = getOrderFromCache(bookingNumber) ||
                      getOrderFromCache(orderId) ||
                      getOrderFromCache(sessionToken);

  const signingSecret = process.env.TICKET_SIGNING_SECRET || DEFAULT_SIGNING_SECRET;

  // Case 1: Order found in cache
  if (cachedOrder) {
    const expectedSig1 = cachedOrder.signature;
    const expectedSig2 = crypto.createHmac('sha256', signingSecret)
      .update(`${cachedOrder.bookingNumber}|${Number(cachedOrder.amount).toFixed(2)}|${cachedOrder.receipt?.date || ''}`)
      .digest('hex').slice(0, 16).toUpperCase();
    const expectedSig3 = crypto.createHmac('sha256', signingSecret)
      .update(cachedOrder.bookingNumber)
      .digest('hex').slice(0, 16).toUpperCase();

    // If signature was provided, verify it
    if (signature) {
      const isValidSig = safeCompare(signature, expectedSig1) ||
                         safeCompare(signature, expectedSig2) ||
                         safeCompare(signature, expectedSig3);

      if (!isValidSig) {
        return sendJson(res, 400, {
          success: false,
          valid: false,
          orderId: cachedOrder.orderId,
          bookingNumber: cachedOrder.bookingNumber,
          bookingCode: cachedOrder.bookingCode,
          status: 'INVALID_SIGNATURE',
          error: {
            code: 'INVALID_SIGNATURE',
            message: 'Cryptographic ticket signature does not match.'
          }
        });
      }
    }

    return sendJson(res, 200, {
      success: true,
      valid: true,
      orderId: cachedOrder.orderId,
      bookingNumber: cachedOrder.bookingNumber,
      bookingCode: cachedOrder.bookingCode,
      status: cachedOrder.status || 'PAID',
      paidAt: cachedOrder.paidAt || new Date().toISOString(),
      amount: cachedOrder.amount,
      amountTjs: cachedOrder.amountTjs || cachedOrder.amount,
      currency: cachedOrder.currency || 'TJS',
      paymentMethod: cachedOrder.paymentMethod,
      transactionId: `txn_verified_${cachedOrder.bookingNumber}`,
      ticket: {
        bookingNumber: cachedOrder.bookingNumber,
        bookingCode: cachedOrder.bookingCode,
        buyerName: cachedOrder.receipt?.buyerName || 'Посетитель',
        date: cachedOrder.receipt?.date || new Date().toISOString().slice(0, 10),
        slot: cachedOrder.receipt?.slot || '09:00 - 11:00',
        categories: 'Взрослый/Детский',
        addons: cachedOrder.receipt?.addons?.audio ? 'Аудиогид' : 'Стандарт',
        qrSignature: cachedOrder.signature,
        qrContent: cachedOrder.qrPayload || cachedOrder.qrData
      }
    });
  }

  // Case 2: Order NOT in cache (Offline gate verification or direct HMAC validation)
  if (bookingNumber) {
    const visitDate = String(params.date || '').trim();
    const amount = params.amount !== undefined ? Number(params.amount) : null;

    // Check signature candidates
    let isValidSig = false;

    if (signature) {
      if (amount !== null && visitDate) {
        const sigCandidate1 = crypto.createHmac('sha256', signingSecret)
          .update(`${bookingNumber}|${amount.toFixed(2)}|${visitDate}`)
          .digest('hex').slice(0, 16).toUpperCase();
        if (safeCompare(signature, sigCandidate1)) isValidSig = true;
      }

      const sigCandidate2 = crypto.createHmac('sha256', signingSecret)
        .update(bookingNumber)
        .digest('hex').slice(0, 16).toUpperCase();
      if (safeCompare(signature, sigCandidate2)) isValidSig = true;
    }

    const hasLiveKeys = Boolean(
      (process.env.ALIF_API_KEY && process.env.ALIF_API_KEY !== 'alif_sk_demo_token') ||
      (process.env.STRIPE_SECRET_KEY && process.env.STRIPE_SECRET_KEY !== 'sk_test_demo') ||
      (process.env.NODE_ENV === 'production')
    );
    const allowSimulation = !hasLiveKeys && process.env.FORCE_SANDBOX === 'true';

    // Allow simulation only when explicitly in sandbox test mode with no live keys
    if (allowSimulation && simulate === 'success') {
      isValidSig = true;
    }

    if (isValidSig) {
      const generatedSig = signature || crypto.createHmac('sha256', signingSecret)
        .update(bookingNumber).digest('hex').slice(0, 16).toUpperCase();

      return sendJson(res, 200, {
        success: true,
        valid: true,
        bookingNumber: bookingNumber,
        bookingCode: bookingNumber,
        status: 'PAID',
        paidAt: new Date().toISOString(),
        amount: amount || 10.0,
        currency: 'TJS',
        verifiedOffline: true,
        ticket: {
          bookingNumber: bookingNumber,
          bookingCode: bookingNumber,
          buyerName: 'Посетитель',
          date: visitDate || new Date().toISOString().slice(0, 10),
          slot: params.slot || '09:00 - 11:00',
          qrSignature: generatedSig,
          qrContent: `${bookingNumber}|${(amount || 10.0).toFixed(2)}|${visitDate || ''}|${generatedSig}`
        }
      });
    }

    if (signature && !isValidSig) {
      return sendJson(res, 400, {
        success: false,
        valid: false,
        bookingNumber: bookingNumber,
        error: {
          code: 'INVALID_SIGNATURE',
          message: 'Cryptographic signature is invalid.'
        }
      });
    }
  }

  // Case 3: Order not found
  return sendJson(res, 404, {
    success: false,
    valid: false,
    error: {
      code: 'ORDER_NOT_FOUND',
      message: 'The requested order was not found.'
    }
  });
};
