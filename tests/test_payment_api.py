"""
Opaque-Box E2E Tests for Vercel Serverless Payment API & Sandbox Architecture
Khujand Fortress Museum (Исторический музей Согдийской области)

Endpoints Tested:
- /api/checkout.js
- /api/verify-payment.js
- /api/webhook.js
- /api/send-ticket.js
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

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Shared JavaScript runner to invoke Vercel serverless functions in Node.js
NODE_RUNNER_SCRIPT = r"""
const path = require('node:path');
const fs = require('node:fs');

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

  const req = {
    method: input.method || 'GET',
    url: input.url || '/',
    headers: input.headers || {},
    query: input.query || {},
    body: input.body !== undefined ? input.body : null
  };

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

def invoke_api(endpoint_filename: str, method: str = "POST", body=None, query=None, headers=None, env_vars=None):
    """Invoke a Node.js serverless endpoint and return (status, headers, body)."""
    endpoint_path = str(PROJECT_ROOT / "api" / endpoint_filename)
    payload = {
        "method": method,
        "url": f"/api/{endpoint_filename}",
        "headers": headers or {},
        "query": query or {},
        "body": body
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
        raise RuntimeError(f"Node execution failed with code {proc.returncode}:\n{proc.stderr}")

    out_text = proc.stdout.strip()
    # Find last JSON line from output
    last_line = out_text.splitlines()[-1] if out_text.splitlines() else "{}"
    result = json.loads(last_line)
    return result["status"], result.get("headers", {}), result.get("body", {})


class TestCheckoutPricingAndCalculation(unittest.TestCase):
    """Test authoritative server-side pricing in /api/checkout.js."""

    def setUp(self):
        self.default_order = {
            "date": "2026-10-25",
            "slot": "11:00 - 13:00",
            "tickets": {"adult": 1, "student": 0, "child": 0},
            "addons": {"audio": False, "photo": False},
            "buyer": {"name": "Усмон Каримов", "email": "usmon@example.tj", "phone": "+992921234567"},
            "paymentMethod": "korti-milli",
            "currency": "TJS"
        }

    def test_adult_pricing_only(self):
        """Adult tickets are 5 TJS each: 3 adults = 15 TJS."""
        order = dict(self.default_order)
        order["tickets"] = {"adult": 3, "student": 0, "child": 0}
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 200)
        self.assertEqual(body.get("amount"), 15)
        self.assertEqual(body.get("currency"), "TJS")
        self.assertTrue(body.get("success"))

    def test_student_and_child_pricing(self):
        """Student is 3 TJS, Child is 2 TJS: 2 students + 3 children = 6 + 6 = 12 TJS."""
        order = dict(self.default_order)
        order["tickets"] = {"adult": 0, "student": 2, "child": 3}
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 200)
        self.assertEqual(body.get("amount"), 12)

    def test_mixed_tickets_all_categories(self):
        """1 adult (5) + 2 students (6) + 1 child (2) = 13 TJS."""
        order = dict(self.default_order)
        order["tickets"] = {"adult": 1, "student": 2, "child": 1}
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 200)
        self.assertEqual(body.get("amount"), 13)

    def test_audio_guide_addon_pricing(self):
        """Audio guide is +5 TJS: 1 adult (5) + audio (5) = 10 TJS."""
        order = dict(self.default_order)
        order["tickets"] = {"adult": 1, "student": 0, "child": 0}
        order["addons"] = {"audio": True, "photo": False}
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 200)
        self.assertEqual(body.get("amount"), 10)

    def test_photo_permit_addon_pricing(self):
        """Photo permit is +10 TJS: 1 adult (5) + photo (10) = 15 TJS."""
        order = dict(self.default_order)
        order["tickets"] = {"adult": 1, "student": 0, "child": 0}
        order["addons"] = {"audio": False, "photo": True}
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 200)
        self.assertEqual(body.get("amount"), 15)

    def test_all_addons_combined(self):
        """2 adults (10) + audio (5) + photo (10) = 25 TJS."""
        order = dict(self.default_order)
        order["tickets"] = {"adult": 2, "student": 0, "child": 0}
        order["addons"] = {"audio": True, "photo": True}
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 200)
        self.assertEqual(body.get("amount"), 25)
        self.assertEqual(body.get("amountDirams"), 2500)

    def test_server_side_price_tamper_defense(self):
        """Client-submitted price total is ignored; authoritative calculation prevails."""
        order = dict(self.default_order)
        order["tickets"] = {"adult": 2, "student": 1, "child": 0}  # 2*5 + 3 = 13 TJS
        order["amount"] = 0  # Tampered total
        order["total"] = -100  # Tampered total
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 200)
        self.assertEqual(body.get("amount"), 13, "Server must enforce authoritative pricing against client tampering")


class TestCheckoutValidationAndNegativeCases(unittest.TestCase):
    """Test boundary validation, negative values, and security defense in /api/checkout.js."""

    def setUp(self):
        self.base_order = {
            "date": "2026-10-25",
            "slot": "11:00 - 13:00",
            "tickets": {"adult": 1, "student": 0, "child": 0},
            "buyer": {"name": "Фарогат Исмоилова", "email": "farogat@example.tj", "phone": "+992925556677"},
            "paymentMethod": "alif-pay"
        }

    def test_zero_tickets_rejected(self):
        """Zero tickets selected must return HTTP 400 Bad Request."""
        order = dict(self.base_order)
        order["tickets"] = {"adult": 0, "student": 0, "child": 0}
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 400)
        self.assertFalse(body.get("success"))
        self.assertEqual(body.get("error", {}).get("code"), "ZERO_TICKETS")

    def test_negative_adult_quantity_rejected(self):
        """Negative adult ticket count must return HTTP 400."""
        order = dict(self.base_order)
        order["tickets"] = {"adult": -2, "student": 1, "child": 0}
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("error", {}).get("code"), "INVALID_QUANTITY")

    def test_negative_student_quantity_rejected(self):
        """Negative student ticket count must return HTTP 400."""
        order = dict(self.base_order)
        order["tickets"] = {"adult": 1, "student": -1, "child": 0}
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("error", {}).get("code"), "INVALID_QUANTITY")

    def test_negative_child_quantity_rejected(self):
        """Negative child ticket count must return HTTP 400."""
        order = dict(self.base_order)
        order["tickets"] = {"adult": 1, "student": 0, "child": -3}
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("error", {}).get("code"), "INVALID_QUANTITY")

    def test_exceeds_max_tickets_rejected(self):
        """Orders exceeding 50 tickets must return HTTP 400 EXCEEDS_MAX_TICKETS."""
        order = dict(self.base_order)
        order["tickets"] = {"adult": 51, "student": 0, "child": 0}
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("error", {}).get("code"), "EXCEEDS_MAX_TICKETS")

    def test_missing_buyer_name_rejected(self):
        """Missing buyer name must return HTTP 400."""
        order = dict(self.base_order)
        order["buyer"] = {"name": "", "email": "valid@example.com", "phone": "+992921234567"}
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("error", {}).get("code"), "MISSING_BUYER_INFO")

    def test_missing_buyer_email_rejected(self):
        """Missing buyer email must return HTTP 400."""
        order = dict(self.base_order)
        order["buyer"] = {"name": "Усмон", "email": "", "phone": "+992921234567"}
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("error", {}).get("code"), "MISSING_BUYER_INFO")

    def test_invalid_email_format_rejected(self):
        """Malformed email format must return HTTP 400 INVALID_EMAIL."""
        order = dict(self.base_order)
        order["buyer"] = {"name": "Усмон", "email": "not-an-email", "phone": "+992921234567"}
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("error", {}).get("code"), "INVALID_EMAIL")

    def test_past_visit_date_rejected(self):
        """Visit date in the past must return HTTP 422 PAST_DATE."""
        order = dict(self.base_order)
        order["date"] = "2020-01-01"
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 422)
        self.assertEqual(body.get("error", {}).get("code"), "PAST_DATE")

    def test_disallowed_http_method_rejected(self):
        """GET request to /api/checkout.js must return HTTP 405 Method Not Allowed."""
        status, headers, body = invoke_api("checkout.js", method="GET")
        self.assertEqual(status, 405)
        self.assertEqual(body.get("error", {}).get("code"), "METHOD_NOT_ALLOWED")
        self.assertIn("post", headers.get("allow", "").lower())


class TestSandboxCardProcessingAndGatewayEmulation(unittest.TestCase):
    """Test sandbox card emulation, decline triggers, and zero-key fallback."""

    def setUp(self):
        self.base_order = {
            "date": "2026-10-25",
            "slot": "11:00 - 13:00",
            "tickets": {"adult": 1, "student": 0, "child": 0},
            "buyer": {"name": "Комрон Солиев", "email": "komron@example.tj", "phone": "+992927778899"},
            "paymentMethod": "stripe"
        }

    def test_visa_sandbox_success(self):
        """Card 4242 4242 4242 4242 succeeds with status PAID and booking code KS-2026-."""
        order = dict(self.base_order)
        order["cardNumber"] = "4242 4242 4242 4242"
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 200)
        self.assertEqual(body.get("status"), "PAID")
        self.assertTrue(body.get("bookingCode", "").startswith("KS-2026-"))
        self.assertTrue(body.get("isSandbox"))

    def test_korti_milli_sandbox_success(self):
        """National card Korti Milli starting with 9771 succeeds with status PAID."""
        order = dict(self.base_order)
        order["paymentMethod"] = "korti-milli"
        order["cardNumber"] = "9771 0000 0000 1234"
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 200)
        self.assertEqual(body.get("status"), "PAID")
        self.assertTrue(body.get("bookingCode", "").startswith("KS-2026-"))

    def test_mastercard_sandbox_success(self):
        """MasterCard test card 5555 5555 5555 4444 succeeds with status PAID."""
        order = dict(self.base_order)
        order["paymentMethod"] = "mastercard"
        order["cardNumber"] = "5555 5555 5555 4444"
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 200)
        self.assertEqual(body.get("status"), "PAID")

    def test_sandbox_decline_card_insufficient_funds(self):
        """Card ending with 0002 returns HTTP 402 card_declined / insufficient_funds."""
        order = dict(self.base_order)
        order["cardNumber"] = "4000 0000 0000 0002"
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 402)
        self.assertEqual(body.get("status"), "DECLINED")
        self.assertEqual(body.get("error", {}).get("code"), "card_declined")
        self.assertEqual(body.get("error", {}).get("decline_code"), "insufficient_funds")

    def test_sandbox_decline_card_expired(self):
        """Card ending with 0005 returns HTTP 402 expired_card."""
        order = dict(self.base_order)
        order["cardNumber"] = "4000 0000 0000 0005"
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 402)
        self.assertEqual(body.get("status"), "DECLINED")
        self.assertEqual(body.get("error", {}).get("code"), "expired_card")

    def test_invalid_luhn_card_rejected(self):
        """Arbitrary card failing Luhn algorithm must return HTTP 400 INVALID_CARD_NUMBER."""
        order = dict(self.base_order)
        order["cardNumber"] = "4111 1111 1111 1112"  # Invalid Luhn checksum
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("error", {}).get("code"), "INVALID_CARD_NUMBER")

    def test_alif_qr_payload_generation(self):
        """Alif Pay payment method generates dynamic alifpay:// QR payload."""
        order = dict(self.base_order)
        order["paymentMethod"] = "alif-pay"
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 200)
        self.assertTrue(body.get("qrPayload", "").startswith("alifpay://pay"))

    def test_dc_qr_payload_generation(self):
        """Dushanbe City payment method generates dynamic dc:// QR payload."""
        order = dict(self.base_order)
        order["paymentMethod"] = "dushanbe-city"
        status, _, body = invoke_api("checkout.js", method="POST", body=order)
        self.assertEqual(status, 200)
        self.assertTrue(body.get("qrPayload", "").startswith("dc://pay"))

    def test_zero_key_sandbox_fallback_safety(self):
        """Under unpopulated or sandbox .env, system operates in safe mode without leaking secret keys."""
        order = dict(self.base_order)
        order["paymentMethod"] = "stripe"
        status, _, body = invoke_api("checkout.js", method="POST", body=order, env_vars={"FORCE_SANDBOX": "true"})
        self.assertEqual(status, 200)
        self.assertTrue(body.get("isSandbox"))
        # Security invariant: Secret keys never leak to client
        raw_body_str = json.dumps(body)
        self.assertNotIn("sk_live", raw_body_str)
        self.assertNotIn("STRIPE_SECRET_KEY", raw_body_str)
        self.assertNotIn("ALIF_API_KEY", raw_body_str)


class TestVerifyPaymentAPI(unittest.TestCase):
    """Test /api/verify-payment.js for order status and cryptographic HMAC verification."""

    def test_verify_payment_for_cached_order(self):
        """Order created via checkout can be verified with its bookingNumber and signature."""
        # 1. Create order
        checkout_order = {
            "date": "2026-10-25",
            "slot": "09:00 - 11:00",
            "tickets": {"adult": 2, "student": 0, "child": 0},
            "buyer": {"name": "Ситора Рахимова", "email": "sitora@example.tj", "phone": "+992923334455"},
            "paymentMethod": "korti-milli"
        }
        status, _, checkout_body = invoke_api("checkout.js", method="POST", body=checkout_order)
        self.assertEqual(status, 200)
        booking_number = checkout_body.get("bookingNumber")
        sig = checkout_body.get("signature")

        # 2. Verify order
        status, _, verify_body = invoke_api(
            "verify-payment.js",
            method="GET",
            query={"bookingNumber": booking_number, "signature": sig}
        )
        self.assertEqual(status, 200)
        self.assertTrue(verify_body.get("valid"))
        self.assertEqual(verify_body.get("status"), "PAID")
        self.assertIn("ticket", verify_body)
        self.assertEqual(verify_body.get("ticket", {}).get("bookingNumber"), booking_number)

    def test_verify_payment_tampered_signature_rejected(self):
        """Valid bookingNumber with tampered signature must return HTTP 400 INVALID_SIGNATURE."""
        # 1. Create order
        checkout_order = {
            "date": "2026-10-25",
            "slot": "09:00 - 11:00",
            "tickets": {"adult": 1, "student": 0, "child": 0},
            "buyer": {"name": "Хуршед", "email": "kh@example.tj", "phone": "+992921112233"}
        }
        status, _, checkout_body = invoke_api("checkout.js", method="POST", body=checkout_order)
        booking_number = checkout_body.get("bookingNumber")

        # 2. Verify with forged signature
        status, _, verify_body = invoke_api(
            "verify-payment.js",
            method="GET",
            query={"bookingNumber": booking_number, "signature": "BAD_FORGED_SIG"}
        )
        self.assertEqual(status, 400)
        self.assertFalse(verify_body.get("valid"))
        self.assertEqual(verify_body.get("error", {}).get("code"), "INVALID_SIGNATURE")

    def test_verify_payment_missing_params(self):
        """Verification request missing bookingNumber/orderId returns HTTP 400."""
        status, _, body = invoke_api("verify-payment.js", method="GET", query={})
        self.assertEqual(status, 400)
        self.assertEqual(body.get("error", {}).get("code"), "MISSING_PARAMETERS")

    def test_verify_payment_nonexistent_order_not_found(self):
        """Unknown bookingNumber returns HTTP 404 ORDER_NOT_FOUND."""
        status, _, body = invoke_api(
            "verify-payment.js",
            method="GET",
            query={"bookingNumber": "KS-2026-0000"}
        )
        self.assertEqual(status, 404)
        self.assertEqual(body.get("error", {}).get("code"), "ORDER_NOT_FOUND")

    def test_verify_payment_disallowed_method(self):
        """PUT /api/verify-payment.js returns HTTP 405 Method Not Allowed."""
        status, _, body = invoke_api("verify-payment.js", method="PUT")
        self.assertEqual(status, 405)


class TestWebhookAPI(unittest.TestCase):
    """Test /api/webhook.js for HMAC-SHA256 signature verification and replay prevention."""

    SECRET = "whsec_khujand_museum_mock_webhook_key_9981"

    def compute_signature(self, payload_dict: dict, secret: str = SECRET) -> str:
        raw_body = json.dumps(payload_dict, separators=(',', ':'))
        return hmac.new(secret.encode("utf-8"), raw_body.encode("utf-8"), hashlib.sha256).hexdigest()

    def test_webhook_valid_hmac_signature_approved(self):
        """Valid HMAC-SHA256 signature returns HTTP 200 with received: true."""
        event_payload = {
            "event": "payment.succeeded",
            "orderId": "ord_test_webhook_123",
            "bookingCode": "KS-2026-7788",
            "amount": 10
        }
        sig = self.compute_signature(event_payload)
        headers = {
            "x-webhook-signature": sig,
            "x-webhook-timestamp": str(int(time.time() * 1000))
        }
        status, _, body = invoke_api("webhook.js", method="POST", body=event_payload, headers=headers)
        self.assertEqual(status, 200)
        self.assertTrue(body.get("received"))
        self.assertEqual(body.get("status"), "PROCESSED")

    def test_webhook_invalid_hmac_signature_rejected(self):
        """Tampered or invalid signature returns HTTP 400 INVALID_SIGNATURE."""
        event_payload = {"event": "payment.succeeded", "orderId": "ord_fake"}
        headers = {
            "x-webhook-signature": "bogus_hex_signature_1234567890abcdef",
            "x-webhook-timestamp": str(int(time.time() * 1000))
        }
        status, _, body = invoke_api("webhook.js", method="POST", body=event_payload, headers=headers)
        self.assertEqual(status, 400)
        self.assertFalse(body.get("received"))
        self.assertEqual(body.get("code"), "INVALID_SIGNATURE")

    def test_webhook_replay_attack_protection_beyond_300s(self):
        """Payload timestamp older than 300 seconds is rejected with TIMESTAMP_EXPIRED."""
        event_payload = {"event": "payment.succeeded", "orderId": "ord_replay"}
        sig = self.compute_signature(event_payload)
        expired_timestamp = int((time.time() - 360) * 1000)  # 360 seconds ago (>300s)
        headers = {
            "x-webhook-signature": sig,
            "x-webhook-timestamp": str(expired_timestamp)
        }
        status, _, body = invoke_api("webhook.js", method="POST", body=event_payload, headers=headers)
        self.assertEqual(status, 400)
        self.assertEqual(body.get("code"), "TIMESTAMP_EXPIRED")

    def test_webhook_replay_tolerance_within_300s_accepted(self):
        """Payload timestamp within 300 seconds (e.g. 60s ago) is accepted."""
        event_payload = {"event": "payment.succeeded", "orderId": "ord_valid_time"}
        sig = self.compute_signature(event_payload)
        recent_timestamp = int((time.time() - 60) * 1000)  # 60s ago
        headers = {
            "x-webhook-signature": sig,
            "x-webhook-timestamp": str(recent_timestamp)
        }
        status, _, body = invoke_api("webhook.js", method="POST", body=event_payload, headers=headers)
        self.assertEqual(status, 200)
        self.assertTrue(body.get("received"))

    def test_webhook_idempotency_duplicate_calls(self):
        """Re-submitting the same webhook event is idempotent and acknowledges receipt."""
        event_payload = {"event": "payment.succeeded", "orderId": "ord_idempotent_999"}
        sig = self.compute_signature(event_payload)
        headers = {
            "x-webhook-signature": sig,
            "x-webhook-timestamp": str(int(time.time() * 1000))
        }
        status1, _, body1 = invoke_api("webhook.js", method="POST", body=event_payload, headers=headers)
        status2, _, body2 = invoke_api("webhook.js", method="POST", body=event_payload, headers=headers)
        self.assertEqual(status1, 200)
        self.assertEqual(status2, 200)
        self.assertTrue(body2.get("idempotent"))

    def test_webhook_disallowed_method_rejected(self):
        """GET /api/webhook.js returns HTTP 405 Method Not Allowed."""
        status, _, body = invoke_api("webhook.js", method="GET")
        self.assertEqual(status, 405)


class TestSendTicketAPI(unittest.TestCase):
    """Test /api/send-ticket.js for email receipt dispatch and fallback mock delivery."""

    def test_send_ticket_mock_success(self):
        """Valid ticket dispatch request returns HTTP 200 with sent: true and mock adapter."""
        payload = {
            "orderId": "ord_mock_123",
            "bookingNumber": "KS-2026-9999",
            "email": "buyer@example.tj",
            "buyerName": "Шерзод Шарипов",
            "date": "2026-10-25",
            "slot": "09:00 - 11:00",
            "amount": 10.0
        }
        status, _, body = invoke_api("send-ticket.js", method="POST", body=payload)
        self.assertEqual(status, 200)
        self.assertTrue(body.get("sent"))
        self.assertEqual(body.get("recipient"), "buyer@example.tj")
        self.assertTrue(body.get("messageId", "").startswith("msg_mock_"))

    def test_send_ticket_invalid_email_rejected(self):
        """Malformed recipient email returns HTTP 400 INVALID_EMAIL."""
        payload = {
            "bookingNumber": "KS-2026-9999",
            "email": "invalid-email-address",
            "buyerName": "Тест"
        }
        status, _, body = invoke_api("send-ticket.js", method="POST", body=payload)
        self.assertEqual(status, 400)
        self.assertFalse(body.get("sent"))
        self.assertEqual(body.get("error", {}).get("code"), "INVALID_EMAIL")

    def test_send_ticket_disallowed_method(self):
        """GET /api/send-ticket.js returns HTTP 405 Method Not Allowed."""
        status, _, body = invoke_api("send-ticket.js", method="GET")
        self.assertEqual(status, 405)


if __name__ == "__main__":
    unittest.main()
