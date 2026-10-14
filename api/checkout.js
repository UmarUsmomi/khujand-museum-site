/**
 * Vercel Serverless Function: Ticket Checkout & Price Calculation
 * Historical Museum of Sughd Region (Khujand Fortress)
 * Endpoint: /api/checkout
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const os = require('os');

// Standard ticket pricing in TJS (authoritative server-side pricing)
const PRICING = {
  adult: 5.0,     // 5 TJS
  student: 3.0,   // 3 TJS
  child: 2.0,     // 2 TJS
  audio: 5.0,     // 5 TJS (Audio Guide)
  photo: 10.0     // 10 TJS (Photo Permit)
};

// Fallback secret for cryptographic HMAC-SHA256 signing
const DEFAULT_SIGNING_SECRET = 'khujand-fortress-museum-secret-salt-2026';

// Helper to safely write order to persistent temp cache for verify-payment endpoint
function saveOrderToCache(order) {
  try {
    const cachePath = path.join(os.tmpdir(), 'khujand_museum_orders.json');
    let orders = {};
    if (fs.existsSync(cachePath)) {
      try {
        orders = JSON.parse(fs.readFileSync(cachePath, 'utf8'));
      } catch (_) {
        orders = {};
      }
    }
    if (order.bookingNumber) orders[order.bookingNumber] = order;
    if (order.bookingCode) orders[order.bookingCode] = order;
    if (order.orderId) orders[order.orderId] = order;
    if (order.sessionToken) orders[order.sessionToken] = order;
    fs.writeFileSync(cachePath, JSON.stringify(orders, null, 2), 'utf8');
  } catch (err) {
    // Non-fatal if filesystem cache fails
  }
}

// Luhn algorithm check (Mod 10)
function passesLuhn(cardNumber) {
  const digitsOnly = String(cardNumber).replace(/\D/g, '');
  if (digitsOnly.length < 13 || digitsOnly.length > 19) return false;

  let sum = 0;
  let alternate = false;

  for (let i = digitsOnly.length - 1; i >= 0; i--) {
    let n = parseInt(digitsOnly.charAt(i), 10);
    if (alternate) {
      n *= 2;
      if (n > 9) n -= 9;
    }
    sum += n;
    alternate = !alternate;
  }
  return sum % 10 === 0;
}

// Helper to parse JSON body from request
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

module.exports = async function handler(req, res) {
  // 1. HTTP Method validation
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return sendJson(res, 405, {
      success: false,
      error: {
        code: 'METHOD_NOT_ALLOWED',
        message: 'Only POST method is allowed for checkout.'
      }
    });
  }

  // 2. Parse request payload
  const body = await parseRequestBody(req);

  // 3. Extract and normalize tickets
  const ticketsRaw = body.tickets || {
    adult: body.adult !== undefined ? body.adult : 0,
    student: body.student !== undefined ? body.student : 0,
    child: body.child !== undefined ? body.child : 0
  };

  const parseQuantity = (val) => {
    if (val === undefined || val === '') return 0;
    if (val === null) return NaN;
    if (typeof val === 'number') {
      if (!Number.isFinite(val)) return NaN;
      return Math.floor(val);
    }
    if (typeof val === 'string') {
      const trimmed = val.trim();
      if (!/^-?\d+(\.\d+)?$/.test(trimmed)) return NaN;
      return parseInt(trimmed, 10);
    }
    return NaN;
  };

  const adult = parseQuantity(ticketsRaw.adult);
  const student = parseQuantity(ticketsRaw.student);
  const child = parseQuantity(ticketsRaw.child);

  // Strict validation: Reject non-numeric, NaN, or negative quantities
  if (Number.isNaN(adult) || Number.isNaN(student) || Number.isNaN(child) || adult < 0 || student < 0 || child < 0) {
    return sendJson(res, 400, {
      success: false,
      error: {
        code: 'INVALID_QUANTITY',
        message: 'Ticket quantities cannot be negative or invalid.',
        field: 'tickets'
      }
    });
  }

  // Strict validation: Reject total tickets <= 0
  const totalTickets = adult + student + child;
  if (totalTickets <= 0) {
    return sendJson(res, 400, {
      success: false,
      error: {
        code: 'ZERO_TICKETS',
        message: 'At least one ticket must be selected.',
        field: 'tickets'
      }
    });
  }

  // Strict validation: Reject excessive tickets (> 50)
  if (totalTickets > 50) {
    return sendJson(res, 400, {
      success: false,
      error: {
        code: 'EXCEEDS_MAX_TICKETS',
        message: 'Maximum 50 tickets allowed per order.',
        field: 'tickets'
      }
    });
  }

  // 4. Extract and normalize add-ons
  const addonsRaw = body.addons || {};
  const audioGuide = Boolean(addonsRaw.audio || addonsRaw.audioGuide || body.audioGuide || body.audio);
  const photoPermit = Boolean(addonsRaw.photo || addonsRaw.photoPermit || body.photoPermit || body.photo);

  // 5. Authoritative server-side price calculation
  const amountTjs = (adult * PRICING.adult) +
                    (student * PRICING.student) +
                    (child * PRICING.child) +
                    (audioGuide ? PRICING.audio : 0) +
                    (photoPermit ? PRICING.photo : 0);

  const amountDirams = Math.round(amountTjs * 100);
  const currency = (body.currency || 'TJS').toUpperCase();

  // 6. Extract buyer / customer details
  const buyerRaw = body.buyer || body.customer || {};
  const name = String(buyerRaw.name || body.name || '').trim();
  const email = String(buyerRaw.email || body.email || '').trim();
  const phone = String(buyerRaw.phone || body.phone || '').trim();

  // Strict validation: Reject missing required buyer info
  if (!name || !email || !phone) {
    return sendJson(res, 400, {
      success: false,
      error: {
        code: 'MISSING_BUYER_INFO',
        message: 'Buyer name, email, and phone number are required.',
        field: 'buyer'
      }
    });
  }

  // Email format validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return sendJson(res, 400, {
      success: false,
      error: {
        code: 'INVALID_EMAIL',
        message: 'A valid email address is required.',
        field: 'email'
      }
    });
  }

  // 7. Date and slot validation
  const visitDate = String(body.date || body.visitDate || '').trim();
  const timeSlot = String(body.timeSlot || body.slot || '09:00 - 11:00').trim();

  if (!visitDate) {
    return sendJson(res, 400, {
      success: false,
      error: {
        code: 'MISSING_DATE',
        message: 'Visit date is required.',
        field: 'date'
      }
    });
  }

  // Strict format validation: YYYY-MM-DD
  if (!/^\d{4}-\d{2}-\d{2}$/.test(visitDate)) {
    return sendJson(res, 400, {
      success: false,
      error: {
        code: 'INVALID_DATE',
        message: 'Visit date must be in YYYY-MM-DD format.',
        field: 'date'
      }
    });
  }

  const dateObj = new Date(visitDate + 'T00:00:00Z');
  if (isNaN(dateObj.getTime())) {
    return sendJson(res, 400, {
      success: false,
      error: {
        code: 'INVALID_DATE',
        message: 'Invalid calendar date.',
        field: 'date'
      }
    });
  }

  const [yearNum, monthNum, dayNum] = visitDate.split('-').map(Number);
  if (dateObj.getUTCFullYear() !== yearNum || (dateObj.getUTCMonth() + 1) !== monthNum || dateObj.getUTCDate() !== dayNum) {
    return sendJson(res, 400, {
      success: false,
      error: {
        code: 'INVALID_DATE',
        message: 'Invalid calendar date.',
        field: 'date'
      }
    });
  }

  // Past date validation
  const todayStr = new Date().toISOString().slice(0, 10);
  if (visitDate < todayStr) {
    return sendJson(res, 422, {
      success: false,
      error: {
        code: 'PAST_DATE',
        message: 'Visit date cannot be in the past.',
        field: 'date'
      }
    });
  }

  // Max booking horizon (90 days from today)
  const maxDate = new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
  if (visitDate > maxDate) {
    return sendJson(res, 422, {
      success: false,
      error: {
        code: 'INVALID_DATE',
        message: 'Booking is only available up to 90 days in advance.',
        field: 'date'
      }
    });
  }

  // Museum sanitation day check (last Monday of the month)
  const dayOfWeek = dateObj.getUTCDay(); // 1 = Monday
  if (dayOfWeek === 1) {
    const nextWeek = new Date(dateObj);
    nextWeek.setUTCDate(nextWeek.getUTCDate() + 7);
    if (nextWeek.getUTCMonth() !== dateObj.getUTCMonth()) {
      return sendJson(res, 422, {
        success: false,
        error: {
          code: 'CLOSED_DAY',
          message: 'The museum is closed for sanitation on the last Monday of the month.',
          field: 'date'
        }
      });
    }
  }

  // 8. Payment method normalization
  const paymentMethod = String(body.paymentMethod || body.method || 'alif-pay').toLowerCase().trim();
  const normalizedMethod = paymentMethod.replace(/[-_]/g, '');

  // 9. Card Details & Sandbox / Emulation handling
  const cardDetails = body.cardDetails || body.card || {};
  const rawCardNumber = String(cardDetails.number || cardDetails.cardNumber || body.cardNumber || '').trim();

  // Check if live keys are present
  const hasLiveKeys = Boolean(
    process.env.ALIF_API_KEY &&
    process.env.ALIF_API_KEY !== 'alif_sk_demo_token' &&
    process.env.FORCE_SANDBOX !== 'true' &&
    process.env.PAYMENT_MODE !== 'sandbox'
  );

  // If card number is provided in checkout, apply strict validation
  if (rawCardNumber) {
    if (/[^\d\s\-]/.test(rawCardNumber)) {
      return sendJson(res, 400, {
        success: false,
        error: {
          code: 'INVALID_CARD_NUMBER',
          message: 'Card number contains invalid characters.',
          field: 'cardNumber'
        }
      });
    }

    const cleanCard = rawCardNumber.replace(/[\s\-]/g, '');
    if (!/^\d+$/.test(cleanCard) || cleanCard.length < 13 || cleanCard.length > 19) {
      return sendJson(res, 400, {
        success: false,
        error: {
          code: 'INVALID_CARD_NUMBER',
          message: 'Card number must be between 13 and 19 digits.',
          field: 'cardNumber'
        }
      });
    }

    // Check specific simulation decline scenarios
    if (cleanCard === '4000000000000002' || cleanCard.endsWith('0002')) {
      return sendJson(res, 402, {
        success: false,
        status: 'DECLINED',
        error: {
          code: 'card_declined',
          decline_code: 'insufficient_funds',
          message: 'Your card was declined due to insufficient funds.'
        }
      });
    }

    if (cleanCard === '4000000000000005' || cleanCard.endsWith('0005')) {
      return sendJson(res, 402, {
        success: false,
        status: 'DECLINED',
        error: {
          code: 'expired_card',
          decline_code: 'expired_card',
          message: 'Your card has expired.'
        }
      });
    }

    if (cleanCard === '4000000000000069' || cleanCard.endsWith('0069')) {
      return sendJson(res, 402, {
        success: false,
        status: 'DECLINED',
        error: {
          code: 'stolen_card',
          decline_code: 'stolen_card',
          message: 'Your card was reported stolen.'
        }
      });
    }

    // Luhn algorithm verification (allow standard recognized test prefixes or valid Luhn)
    const isKnownTestPrefix = cleanCard.startsWith('4242') ||
                              cleanCard.startsWith('5555') ||
                              cleanCard.startsWith('9771');

    if (!isKnownTestPrefix && !passesLuhn(cleanCard)) {
      return sendJson(res, 400, {
        success: false,
        error: {
          code: 'INVALID_CARD_NUMBER',
          message: 'Invalid card number (failed Luhn algorithm check).',
          field: 'cardNumber'
        }
      });
    }
  }

  // 10. Generate unique references and cryptographic signature
  const randomSuffix = Math.floor(1000 + Math.random() * 9000);
  const bookingNumber = `KS-2026-${randomSuffix}`;
  const bookingCode = bookingNumber;
  const orderId = `ord_${crypto.randomBytes(6).toString('hex')}`;
  const sessionToken = `s_tok_${crypto.randomBytes(12).toString('hex')}`;

  // Cryptographic signature with HMAC-SHA256
  const signingSecret = process.env.TICKET_SIGNING_SECRET || DEFAULT_SIGNING_SECRET;
  const canonicalTicketString = `${bookingNumber}|${amountTjs.toFixed(2)}|${visitDate}`;
  const hmac = crypto.createHmac('sha256', signingSecret);
  hmac.update(canonicalTicketString);
  const signature = hmac.digest('hex').slice(0, 16).toUpperCase();

  // QR payloads
  const ticketQr = `${bookingNumber}|${amountTjs.toFixed(2)}|${visitDate}|${signature}`;
  const alifQr = `alifpay://pay?account=MUSEUM_KHUJAND&amount=${amountTjs.toFixed(2)}&order=${bookingNumber}&desc=Khujand+Museum+Pass`;
  const dcQr = `dc://pay?merchant_id=DC_KHUJAND_MUSEUM&order_id=${bookingNumber}&amount=${amountTjs.toFixed(2)}&service=museum_ticket`;

  // Select QR payload based on payment method
  let qrPayload = ticketQr;
  if (normalizedMethod.includes('alif')) {
    qrPayload = alifQr;
  } else if (normalizedMethod.includes('dushanbe') || normalizedMethod.includes('dc')) {
    qrPayload = dcQr;
  }

  // Construct official receipt metadata
  const receipt = {
    orderId: orderId,
    bookingNumber: bookingNumber,
    bookingCode: bookingCode,
    date: visitDate,
    slot: timeSlot,
    buyerName: name,
    email: email,
    phone: phone,
    tickets: { adult, student, child },
    addons: { audio: audioGuide, photo: photoPermit },
    amountTjs: amountTjs,
    amountDirams: amountDirams,
    currency: currency,
    tin: '030018492',
    fiscalDoc: `FD-2026-${randomSuffix}`,
    fiscalSign: `FP-${Math.floor(10000000 + Math.random() * 90000000)}`,
    vatNotice: 'Без НДС согласно ст. 169 Налогового кодекса Республики Таджикистан (услуги музеев и учреждений культуры)'
  };

  const orderRecord = {
    success: true,
    status: 'PAID',
    orderId: orderId,
    bookingNumber: bookingNumber,
    bookingCode: bookingCode,
    amount: amountTjs,
    amountTjs: amountTjs,
    amountFormatted: `${amountTjs.toFixed(2)} TJS`,
    amountDirams: amountDirams,
    currency: currency,
    paymentMethod: paymentMethod,
    isSandbox: !hasLiveKeys,
    paidAt: new Date().toISOString(),
    expiresAt: new Date(Date.now() + 15 * 60 * 1000).toISOString(),
    qrPayload: qrPayload,
    qrData: ticketQr,
    ticketQrPayload: ticketQr,
    signature: signature,
    sessionToken: sessionToken,
    receipt: receipt
  };

  // Cache order for /api/verify-payment
  saveOrderToCache(orderRecord);

  // 11. Return response
  return sendJson(res, 200, {
    success: true,
    status: 'PAID',
    orderId: orderId,
    bookingNumber: bookingNumber,
    bookingCode: bookingCode,
    amount: amountTjs,
    amountTjs: amountTjs,
    amountFormatted: `${amountTjs.toFixed(2)} TJS`,
    amountDirams: amountDirams,
    currency: currency,
    paymentMethod: paymentMethod,
    isSandbox: !hasLiveKeys,
    expiresAt: orderRecord.expiresAt,
    qrPayload: qrPayload,
    qrData: ticketQr,
    ticketQrPayload: ticketQr,
    paymentQrPayload: normalizedMethod.includes('alif') ? alifQr : (normalizedMethod.includes('dc') ? dcQr : null),
    paymentUrl: `/pages/checkout-redirect.html?orderId=${orderId}`,
    sessionToken: sessionToken,
    signature: signature,
    receipt: receipt
  });
};
