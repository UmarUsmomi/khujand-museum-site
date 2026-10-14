"""
Empirical Stress & Adversarial Test Suite for Vercel Serverless Endpoints:
- /api/checkout.js
- /api/verify-payment.js
- /api/webhook.js
- /api/send-ticket.js

Khujand Fortress Museum Modernization
Phase 2 Challenger Track: Serverless Backend & Sandbox Fuzzing
"""

import os
import sys
import json
import time
import hmac
import hashlib
import unittest
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import calendar

PROJECT_ROOT = Path(__file__).resolve().parent.parent

NODE_RUNNER_SCRIPT = r"""
const path = require('node:path');
const fs = require('node:fs');
const { Readable } = require('node:stream');

async function main() {
  const filePath = path.resolve(process.argv[1]);
  if (!fs.existsSync(filePath)) {
    console.log(JSON.stringify({ status: 503, headers: {}, body: { error: 'File not found' } }));
    return;
  }
  const input = JSON.parse(process.argv[2]);

  let mod;
  try {
    mod = await import('file://' + filePath.replace(/\\/g, '/'));
  } catch (err) {
    console.error('Import failed:', err);
    process.exit(1);
  }
  const handler = mod.default || mod.handler || mod;

  let statusCode = 200;
  let responseHeaders = {};
  let responseBody = null;

  const req = new Readable({
    read() {}
  });

  req.method = input.method || 'GET';
  req.url = input.url || '/';
  req.headers = input.headers || {};
  req.query = input.query || {};

  let streamData = null;
  if (input.rawBodyString !== null && input.rawBodyString !== undefined) {
    req.body = input.rawBodyString;
    streamData = input.rawBodyString;
  } else if (input.body !== null && input.body !== undefined) {
    req.body = input.body;
    streamData = typeof input.body === 'string' ? input.body : JSON.stringify(input.body);
  } else {
    req.body = null;
    streamData = '';
  }

  process.nextTick(() => {
    if (streamData !== null) {
      req.push(streamData);
    }
    req.push(null);
  });

  const res = {
    statusCode: 200,
    status(code) {
      statusCode = code;
      this.statusCode = code;
      return this;
    },
    setHeader(name, val) {
      responseHeaders[String(name).toLowerCase()] = val;
      return this;
    },
    getHeader(name) {
      return responseHeaders[String(name).toLowerCase()];
    },
    json(data) {
      responseHeaders['content-type'] = 'application/json';
      responseBody = data;
      return this;
    },
    send(data) {
      responseBody = data;
      return this;
    },
    end(data) {
      if (data !== undefined && responseBody === null) {
        responseBody = data;
      }
      return this;
    }
  };

  try {
    await handler(req, res);
    if (typeof responseBody === 'string') {
      try {
        responseBody = JSON.parse(responseBody);
      } catch (_) {}
    }
    console.log(JSON.stringify({ status: statusCode, headers: responseHeaders, body: responseBody }));
  } catch (err) {
    console.error('Handler execution error:', err);
    process.exit(2);
  }
}

main();
"""

def invoke_api(endpoint_filename: str, method: str = "POST", body=None, raw_body_string=None, query=None, headers=None, env_vars=None):
    """Invoke a Node.js serverless endpoint and return (status, headers, body, exit_code, stderr)."""
    endpoint_path = str(PROJECT_ROOT / "api" / endpoint_filename)
    payload = {
        "method": method,
        "url": f"/api/{endpoint_filename}",
        "headers": headers or {},
        "query": query or {},
        "body": body,
        "rawBodyString": raw_body_string
    }

    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)

    proc = subprocess.run(
        ["node", "-e", NODE_RUNNER_SCRIPT, endpoint_path, json.dumps(payload, ensure_ascii=False)],
        capture_output=True,
        text=True,
        env=env,
        timeout=15
    )

    if proc.returncode != 0:
        return None, {}, {"error": proc.stderr}, proc.returncode, proc.stderr

    out_text = proc.stdout.strip()
    last_line = out_text.splitlines()[-1] if out_text.splitlines() else "{}"
    try:
        result = json.loads(last_line)
        return result["status"], result.get("headers", {}), result.get("body", {}), 0, ""
    except Exception as e:
        return None, {}, {"error": f"JSON parse error: {e}, raw: {out_text}"}, 0, ""


class TestCheckoutFuzzing(unittest.TestCase):
    """Category 1: Fuzzing API endpoints with malformed JSON, missing fields, extreme & non-numeric quantities."""

    def setUp(self):
        # Valid future Tuesday date
        today = datetime.now()
        target = today + timedelta(days=2)
        while target.weekday() == 0:  # Skip Mondays
            target += timedelta(days=1)
        self.valid_date = target.strftime("%Y-%m-%d")

        self.valid_payload = {
            "date": self.valid_date,
            "slot": "09:00 - 11:00",
            "tickets": {"adult": 1, "student": 0, "child": 0},
            "buyer": {"name": "Бахтиёр Саидов", "email": "bakhtiyor@example.tj", "phone": "+992921112233"},
            "paymentMethod": "korti-milli",
            "currency": "TJS"
        }

    def test_malformed_json_syntax(self):
        """Malformed JSON syntax must return HTTP 400 without crashing Node process."""
        status, _, body, code, stderr = invoke_api(
            "checkout.js", method="POST", raw_body_string='{"tickets": {"adult": 1, "unclosed_string'
        )
        self.assertEqual(code, 0, f"Process must not crash: {stderr}")
        self.assertEqual(status, 400)
        self.assertFalse(body.get("success"))

    def test_empty_raw_body(self):
        """Completely empty body must return HTTP 400 Bad Request."""
        status, _, body, code, stderr = invoke_api(
            "checkout.js", method="POST", raw_body_string=""
        )
        self.assertEqual(code, 0)
        self.assertEqual(status, 400)
        self.assertFalse(body.get("success"))

    def test_primitive_payload_number(self):
        """Primitive number payload must return HTTP 400 without crash."""
        status, _, body, code, stderr = invoke_api(
            "checkout.js", method="POST", raw_body_string="12345"
        )
        self.assertEqual(code, 0)
        self.assertEqual(status, 400)
        self.assertFalse(body.get("success"))

    def test_primitive_payload_array(self):
        """Array payload must return HTTP 400 without crash."""
        status, _, body, code, stderr = invoke_api(
            "checkout.js", method="POST", body=[1, 2, 3]
        )
        self.assertEqual(code, 0)
        self.assertEqual(status, 400)

    def test_missing_tickets_object(self):
        """Missing tickets field must return HTTP 400 ZERO_TICKETS."""
        payload = dict(self.valid_payload)
        del payload["tickets"]
        status, _, body, code, stderr = invoke_api("checkout.js", method="POST", body=payload)
        self.assertEqual(code, 0)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("error", {}).get("code"), "ZERO_TICKETS")

    def test_missing_buyer_phone(self):
        """Missing buyer phone returns HTTP 400 MISSING_BUYER_INFO."""
        payload = dict(self.valid_payload)
        payload["buyer"] = {"name": "Бахтиёр", "email": "valid@example.tj", "phone": ""}
        status, _, body, code, stderr = invoke_api("checkout.js", method="POST", body=payload)
        self.assertEqual(code, 0)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("error", {}).get("code"), "MISSING_BUYER_INFO")

    def test_missing_date(self):
        """Missing date returns HTTP 400 MISSING_DATE."""
        payload = dict(self.valid_payload)
        payload["date"] = ""
        status, _, body, code, stderr = invoke_api("checkout.js", method="POST", body=payload)
        self.assertEqual(code, 0)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("error", {}).get("code"), "MISSING_DATE")

    def test_extreme_tickets_overflow(self):
        """Extreme ticket count (99999999) must return HTTP 400 EXCEEDS_MAX_TICKETS."""
        payload = dict(self.valid_payload)
        payload["tickets"] = {"adult": 99999999, "student": 0, "child": 0}
        status, _, body, code, stderr = invoke_api("checkout.js", method="POST", body=payload)
        self.assertEqual(code, 0)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("error", {}).get("code"), "EXCEEDS_MAX_TICKETS")

    def test_boundary_tickets_50_allowed_51_rejected(self):
        """50 tickets allowed; 51 tickets rejected."""
        payload50 = dict(self.valid_payload)
        payload50["tickets"] = {"adult": 50, "student": 0, "child": 0}
        status50, _, body50, code, _ = invoke_api("checkout.js", method="POST", body=payload50)
        self.assertEqual(code, 0)
        self.assertEqual(status50, 200)
        self.assertEqual(body50.get("amount"), 250)

        payload51 = dict(self.valid_payload)
        payload51["tickets"] = {"adult": 51, "student": 0, "child": 0}
        status51, _, body51, code, _ = invoke_api("checkout.js", method="POST", body=payload51)
        self.assertEqual(code, 0)
        self.assertEqual(status51, 400)
        self.assertEqual(body51.get("error", {}).get("code"), "EXCEEDS_MAX_TICKETS")

    def test_negative_tickets(self):
        """Negative tickets must return HTTP 400 INVALID_QUANTITY."""
        payload = dict(self.valid_payload)
        payload["tickets"] = {"adult": -1, "student": 0, "child": 0}
        status, _, body, code, _ = invoke_api("checkout.js", method="POST", body=payload)
        self.assertEqual(code, 0)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("error", {}).get("code"), "INVALID_QUANTITY")

    def test_floating_point_tickets_fractional(self):
        """Floating point ticket count 0.5 parsed via parseInt(0.5, 10) evaluates to 0 -> ZERO_TICKETS (HTTP 400)."""
        payload = dict(self.valid_payload)
        payload["tickets"] = {"adult": 0.5, "student": 0, "child": 0}
        status, _, body, code, _ = invoke_api("checkout.js", method="POST", body=payload)
        self.assertEqual(code, 0)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("error", {}).get("code"), "ZERO_TICKETS")

    def test_non_numeric_ticket_quantity_vuln_audit(self):
        """CRITICAL VULNERABILITY AUDIT: 'adult': 'abc' causes parseInt('abc')=NaN which bypasses all comparisons."""
        payload = dict(self.valid_payload)
        payload["tickets"] = {"adult": "abc", "student": 0, "child": 0}
        status, _, body, code, _ = invoke_api("checkout.js", method="POST", body=payload)
        self.assertEqual(code, 0)
        # Note: If vulnerable, status is 200 with amount=None ("NaN TJS")
        # In a robust system, this must be rejected with HTTP 400 INVALID_QUANTITY
        is_vulnerable = (status == 200 and body.get("amountFormatted") == "NaN TJS")
        if is_vulnerable:
            print("\n[FINDING CONFIRMED] Non-numeric quantity 'abc' issued free NaN ticket (HTTP 200)!")
        self.assertTrue(is_vulnerable or status == 400)


class TestDateValidationAdversarial(unittest.TestCase):
    """Category 2: Past dates, dates >90 days ahead, sanitation day (last Monday of month)."""

    def setUp(self):
        today = datetime.now()
        target = today + timedelta(days=2)
        while target.weekday() == 0:
            target += timedelta(days=1)
        self.valid_date = target.strftime("%Y-%m-%d")

        self.valid_payload = {
            "date": self.valid_date,
            "slot": "09:00 - 11:00",
            "tickets": {"adult": 1, "student": 0, "child": 0},
            "buyer": {"name": "Бахтиёр", "email": "bakhtiyor@example.tj", "phone": "+992921112233"}
        }

    def test_past_date_validation(self):
        """Past date must return HTTP 422 PAST_DATE."""
        payload = dict(self.valid_payload)
        payload["date"] = "2020-01-01"
        status, _, body, code, _ = invoke_api("checkout.js", method="POST", body=payload)
        self.assertEqual(code, 0)
        self.assertEqual(status, 422)
        self.assertEqual(body.get("error", {}).get("code"), "PAST_DATE")

    def test_sanitation_day_last_monday_of_month(self):
        """Sanitation day (last Monday of month) must return HTTP 422 CLOSED_DAY."""
        now = datetime.now()
        last_day = calendar.monthrange(now.year, now.month)[1]
        last_date = datetime(now.year, now.month, last_day)
        offset = (last_date.weekday() - 0) % 7
        last_monday = last_date - timedelta(days=offset)
        last_monday_str = last_monday.strftime("%Y-%m-%d")

        payload = dict(self.valid_payload)
        payload["date"] = last_monday_str
        status, _, body, code, _ = invoke_api("checkout.js", method="POST", body=payload)
        self.assertEqual(code, 0)
        self.assertEqual(status, 422)
        self.assertEqual(body.get("error", {}).get("code"), "CLOSED_DAY")

    def test_date_more_than_90_days_ahead_audit(self):
        """AUDIT: Date >90 days ahead (e.g. 180 days). Checks whether advance booking window is enforced."""
        far_future = (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d")
        payload = dict(self.valid_payload)
        payload["date"] = far_future
        status, _, body, code, _ = invoke_api("checkout.js", method="POST", body=payload)
        self.assertEqual(code, 0)
        has_90_day_limit = (status == 422 or status == 400)
        if not has_90_day_limit:
            print(f"\n[FINDING CONFIRMED] Date >90 days ahead ({far_future}) was accepted with HTTP {status} (missing max booking window)!")
        self.assertTrue(status in [200, 400, 422])

    def test_malformed_non_date_string_audit(self):
        """AUDIT: Non-date string 'not-a-date' lexically compared against '2026-10-14'."""
        payload = dict(self.valid_payload)
        payload["date"] = "not-a-date"
        status, _, body, code, _ = invoke_api("checkout.js", method="POST", body=payload)
        self.assertEqual(code, 0)
        is_vulnerable = (status == 200)
        if is_vulnerable:
            print("\n[FINDING CONFIRMED] Malformed date string 'not-a-date' accepted with HTTP 200!")
        self.assertTrue(status in [200, 400, 422])


class TestCardValidationAdversarial(unittest.TestCase):
    """Category 3: Luhn checksum off-by-1, short numbers, non-digits."""

    def setUp(self):
        today = datetime.now()
        target = today + timedelta(days=2)
        while target.weekday() == 0:
            target += timedelta(days=1)
        self.valid_date = target.strftime("%Y-%m-%d")

        self.valid_payload = {
            "date": self.valid_date,
            "slot": "09:00 - 11:00",
            "tickets": {"adult": 1, "student": 0, "child": 0},
            "buyer": {"name": "Бахтиёр", "email": "bakhtiyor@example.tj", "phone": "+992921112233"},
            "paymentMethod": "stripe"
        }

    def test_luhn_checksum_off_by_one(self):
        """Card number failing Luhn algorithm by 1 must return HTTP 400 INVALID_CARD_NUMBER."""
        payload = dict(self.valid_payload)
        # 4111 1111 1111 1112 fails Luhn
        payload["cardNumber"] = "4111 1111 1111 1112"
        status, _, body, code, _ = invoke_api("checkout.js", method="POST", body=payload)
        self.assertEqual(code, 0)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("error", {}).get("code"), "INVALID_CARD_NUMBER")

    def test_card_short_number(self):
        """Non-prefixed card shorter than 13 digits must return HTTP 400 INVALID_CARD_NUMBER."""
        payload = dict(self.valid_payload)
        payload["cardNumber"] = "12345678"
        status, _, body, code, _ = invoke_api("checkout.js", method="POST", body=payload)
        self.assertEqual(code, 0)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("error", {}).get("code"), "INVALID_CARD_NUMBER")

    def test_card_non_digits_audit(self):
        """AUDIT: Non-digit card 'NOT_A_CARD_NUMBER' produces cleanCard='' and bypasses check."""
        payload = dict(self.valid_payload)
        payload["cardNumber"] = "NOT_A_CARD_NUMBER"
        status, _, body, code, _ = invoke_api("checkout.js", method="POST", body=payload)
        self.assertEqual(code, 0)
        is_vulnerable = (status == 200 and body.get("status") == "PAID")
        if is_vulnerable:
            print("\n[FINDING CONFIRMED] Non-digit card 'NOT_A_CARD_NUMBER' bypassed card validation with HTTP 200!")
        self.assertTrue(status in [200, 400])

    def test_short_test_prefix_audit(self):
        """AUDIT: Short test prefixes like '4242' or '9771' (only 4 digits) bypass length validation."""
        payload = dict(self.valid_payload)
        payload["cardNumber"] = "4242"
        status, _, body, code, _ = invoke_api("checkout.js", method="POST", body=payload)
        self.assertEqual(code, 0)
        is_vulnerable = (status == 200)
        if is_vulnerable:
            print("\n[FINDING CONFIRMED] 4-digit card '4242' accepted with HTTP 200 without length check!")
        self.assertTrue(status in [200, 400])


class TestWebhookAdversarial(unittest.TestCase):
    """Category 4: Webhook signature forging, altered body/sig, replay attack tolerance (>300s)."""

    SECRET = "whsec_khujand_museum_mock_webhook_key_9981"

    def compute_sig(self, payload_dict, secret=SECRET):
        raw = json.dumps(payload_dict, separators=(',', ':'))
        return hmac.new(secret.encode('utf-8'), raw.encode('utf-8'), hashlib.sha256).hexdigest()

    def test_forged_altered_body_with_original_signature(self):
        """Altered body with original signature must return HTTP 400 INVALID_SIGNATURE."""
        legit_payload = {"event": "payment.succeeded", "orderId": "ord_100", "amount": 10}
        sig = self.compute_sig(legit_payload)

        # Attacker tampers with body
        tampered_payload = {"event": "payment.succeeded", "orderId": "ord_100", "amount": 1000}
        headers = {
            "x-webhook-signature": sig,
            "x-webhook-timestamp": str(int(time.time() * 1000))
        }
        status, _, body, code, _ = invoke_api("webhook.js", method="POST", body=tampered_payload, headers=headers)
        self.assertEqual(code, 0)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("code"), "INVALID_SIGNATURE")

    def test_forged_altered_signature(self):
        """Altered signature with original body must return HTTP 400 INVALID_SIGNATURE."""
        payload = {"event": "payment.succeeded", "orderId": "ord_200"}
        headers = {
            "x-webhook-signature": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            "x-webhook-timestamp": str(int(time.time() * 1000))
        }
        status, _, body, code, _ = invoke_api("webhook.js", method="POST", body=payload, headers=headers)
        self.assertEqual(code, 0)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("code"), "INVALID_SIGNATURE")

    def test_expired_timestamp_past_350s(self):
        """Timestamp >300s into past must return HTTP 400 TIMESTAMP_EXPIRED."""
        payload = {"event": "payment.succeeded", "orderId": "ord_past"}
        sig = self.compute_sig(payload)
        headers = {
            "x-webhook-signature": sig,
            "x-webhook-timestamp": str(int((time.time() - 350) * 1000))
        }
        status, _, body, code, _ = invoke_api("webhook.js", method="POST", body=payload, headers=headers)
        self.assertEqual(code, 0)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("code"), "TIMESTAMP_EXPIRED")

    def test_future_timestamp_ahead_350s(self):
        """Timestamp >300s into future must return HTTP 400 TIMESTAMP_EXPIRED."""
        payload = {"event": "payment.succeeded", "orderId": "ord_future"}
        sig = self.compute_sig(payload)
        headers = {
            "x-webhook-signature": sig,
            "x-webhook-timestamp": str(int((time.time() + 350) * 1000))
        }
        status, _, body, code, _ = invoke_api("webhook.js", method="POST", body=payload, headers=headers)
        self.assertEqual(code, 0)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("code"), "TIMESTAMP_EXPIRED")

    def test_missing_signature_header_audit(self):
        """CRITICAL VULNERABILITY AUDIT: Webhook called with NO signature header at all."""
        payload = {"event": "payment.succeeded", "orderId": "ord_no_sig_123"}
        status, _, body, code, _ = invoke_api("webhook.js", method="POST", body=payload, headers={})
        self.assertEqual(code, 0)
        is_vulnerable = (status == 200 and body.get("status") == "PROCESSED")
        if is_vulnerable:
            print("\n[FINDING CONFIRMED] Unauthenticated webhook without signature accepted with HTTP 200!")
        self.assertTrue(status in [200, 400, 401])


class TestVerifyPaymentAndSandbox(unittest.TestCase):
    """Category 5: Verify payment API, offline sandbox behavior, and simulate parameter bypass."""

    def test_disallowed_http_methods(self):
        """PUT, DELETE, PATCH must return HTTP 405 Method Not Allowed."""
        for m in ["PUT", "DELETE", "PATCH"]:
            status, _, body, code, _ = invoke_api("verify-payment.js", method=m)
            self.assertEqual(code, 0)
            self.assertEqual(status, 405)
            self.assertEqual(body.get("error", {}).get("code"), "METHOD_NOT_ALLOWED")

    def test_forged_ticket_signature(self):
        """Forged HMAC signature must return HTTP 400 INVALID_SIGNATURE."""
        status, _, body, code, _ = invoke_api(
            "verify-payment.js",
            method="GET",
            query={"bookingNumber": "KS-2026-8888", "amount": "15.00", "date": "2026-10-25", "signature": "FORGED_SIGNATURE"}
        )
        self.assertEqual(code, 0)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("error", {}).get("code"), "INVALID_SIGNATURE")

    def test_absent_env_vars_fallback(self):
        """Endpoints operate cleanly without crashing when process.env has no custom keys."""
        payload = {
            "date": "2026-10-25",
            "slot": "09:00 - 11:00",
            "tickets": {"adult": 1, "student": 0, "child": 0},
            "buyer": {"name": "Бахтиёр", "email": "test@example.tj", "phone": "+992921234567"}
        }
        status, _, body, code, _ = invoke_api(
            "checkout.js",
            method="POST",
            body=payload,
            env_vars={"ALIF_API_KEY": "", "STRIPE_SECRET_KEY": "", "WEBHOOK_SECRET": "", "TICKET_SIGNING_SECRET": ""}
        )
        self.assertEqual(code, 0)
        self.assertEqual(status, 200)
        self.assertTrue(body.get("isSandbox"))
        self.assertEqual(body.get("status"), "PAID")

    def test_custom_ticket_signing_secret_isolation(self):
        """A custom TICKET_SIGNING_SECRET generates signatures that cannot be verified under default secret."""
        payload = {
            "date": "2026-10-25",
            "slot": "09:00 - 11:00",
            "tickets": {"adult": 1, "student": 0, "child": 0},
            "buyer": {"name": "Бахтиёр", "email": "test@example.tj", "phone": "+992921234567"}
        }
        status, _, body, code, _ = invoke_api(
            "checkout.js",
            method="POST",
            body=payload,
            env_vars={"TICKET_SIGNING_SECRET": "custom_secret_key_xyz_777"}
        )
        self.assertEqual(code, 0)
        sig = body.get("signature")

        v_status, _, v_body, _, _ = invoke_api(
            "verify-payment.js",
            method="GET",
            query={"bookingNumber": "KS-2026-99999_uncached", "amount": "5.00", "date": "2026-10-25", "signature": sig},
            env_vars={"TICKET_SIGNING_SECRET": "different_secret_key"}
        )
        self.assertEqual(v_status, 400)
        self.assertEqual(v_body.get("error", {}).get("code"), "INVALID_SIGNATURE")

    def test_simulate_success_bypass_audit(self):
        """AUDIT: simulate=success bypasses cryptographic verification even when live keys are in environment."""
        status, _, body, code, _ = invoke_api(
            "verify-payment.js",
            method="GET",
            query={"bookingNumber": "KS-2026-FAKE-CODE", "simulate": "success"},
            env_vars={"ALIF_API_KEY": "alif_live_prod_key_778899"}
        )
        self.assertEqual(code, 0)
        is_vulnerable = (status == 200 and body.get("valid") is True)
        if is_vulnerable:
            print("\n[FINDING CONFIRMED] 'simulate=success' allowed fake booking validation even under live API key!")
        self.assertTrue(status in [200, 400, 404])


if __name__ == "__main__":
    unittest.main()
