# M-Pesa Payment Integration Guide

## 🎯 Overview

Your CyberTech Security Scanner now includes full M-Pesa payment integration powered by Safaricom's Daraja API. This enables:

- **Pay-per-Report**: 100 KSH per PDF report download
- **Monthly Subscription**: 2,000 KSH/month for unlimited access
- **Premium Features**: Advanced scans (SQL Injection, XSS, Directory Enum)

---

## 💰 Payment Models

### **1. Pay-Per-Report (100 KSH)**
- One-time payment for each report download
- Perfect for occasional users
- Access to specific scan report
- No commitment

### **2. Professional Subscription (2,000 KSH/month)**
- Unlimited scans
- Unlimited report downloads
- SQL Injection scanning
- XSS detection
- Directory enumeration
- Trend analysis
- Priority support
- API access
- 30-day subscription period

---

## 🚀 Setup Instructions

### **Step 1: Get Daraja API Credentials**

1. **Go to Daraja Portal**:
   - Visit: https://developer.safaricom.co.ke
   - Sign up / Log in

2. **Create an App**:
   - Click "My Apps" → "Add a new app"
   - Select "Lipa Na M-Pesa Online"
   - Fill in app details
   - Submit for approval

3. **Get Credentials**:
   After approval, you'll receive:
   - Consumer Key
   - Consumer Secret
   - Business Short Code (Paybill/Till Number)
   - Passkey

4. **Start with Sandbox** (for testing):
   - Use sandbox credentials initially
   - Test Short Code: `174379`
   - Switch to production when ready

---

### **Step 2: Configure Environment Variables**

Update your `.env` file:

```bash
# M-Pesa Configuration
MPESA_ENVIRONMENT=sandbox  # Change to 'production' when going live
MPESA_CONSUMER_KEY=your_consumer_key_here
MPESA_CONSUMER_SECRET=your_consumer_secret_here
MPESA_SHORTCODE=174379  # Sandbox: 174379, Production: Your paybill
MPESA_PASSKEY=your_passkey_here
MPESA_CALLBACK_URL=https://cybertech-security-scanner.fly.dev/api/payment/callback

# MongoDB (Required for payments)
USE_MONGODB=true
MONGODB_URI=mongodb+srv://rigzadmin:2794HSZxT6VTZZe@cluster0.9em0pjh.mongodb.net/cybertech-ecommerce?retryWrites=true&w=majority&appName=Cluster0
```

---

### **Step 3: Set Secrets on Fly.dev**

```bash
# M-Pesa credentials
fly secrets set MPESA_ENVIRONMENT=sandbox
fly secrets set MPESA_CONSUMER_KEY=your_consumer_key
fly secrets set MPESA_CONSUMER_SECRET=your_consumer_secret
fly secrets set MPESA_SHORTCODE=174379
fly secrets set MPESA_PASSKEY=your_passkey
fly secrets set MPESA_CALLBACK_URL=https://cybertech-security-scanner.fly.dev/api/payment/callback

# MongoDB
fly secrets set USE_MONGODB=true
fly secrets set MONGODB_URI=your_mongodb_uri
```

---

### **Step 4: Configure Callback URL in Daraja**

1. Go to your app in Daraja Portal
2. Set Validation URL: `https://cybertech-security-scanner.fly.dev/api/payment/callback`
3. Set Confirmation URL: `https://cybertech-security-scanner.fly.dev/api/payment/callback`

---

### **Step 5: Test in Sandbox**

Use these sandbox test numbers:
- **Test Number**: `254708374149`
- **Test PIN**: `1234` (in sandbox)

---

## 📱 How Payments Work

### **Pay-Per-Report Flow:**

1. User completes a scan
2. Clicks "Download PDF Report"
3. Payment modal appears
4. User enters M-Pesa phone number
5. Clicks "Pay 100 KSH Now"
6. User receives STK Push on phone
7. User enters M-Pesa PIN
8. Payment confirmed via callback
9. Report downloads automatically
10. Payment tracked in MongoDB

### **Subscription Flow:**

1. User visits `/pricing`
2. Clicks "Subscribe Now" on Professional plan
3. Enters M-Pesa phone number
4. Clicks "Pay 2,000 KSH via M-Pesa"
5. Receives STK Push
6. Enters M-Pesa PIN
7. Subscription activated for 30 days
8. All premium features unlocked
9. Unlimited report downloads

---

## 🔗 API Endpoints

### **1. Initiate Report Payment**
```
POST /api/payment/initiate-report
```
**Request:**
```json
{
  "phone_number": "254712345678",
  "scan_id": "abc123"
}
```

**Response:**
```json
{
  "status": "success",
  "checkout_request_id": "ws_CO_13102025...",
  "message": "Payment request sent to your phone"
}
```

---

### **2. Initiate Subscription**
```
POST /api/payment/initiate-subscription
```
**Request:**
```json
{
  "phone_number": "254712345678",
  "plan": "pro"
}
```

**Response:**
```json
{
  "status": "success",
  "checkout_request_id": "ws_CO_13102025...",
  "message": "Payment request sent to your phone"
}
```

---

### **3. Check Payment Status**
```
GET /api/payment/status/{checkout_request_id}
```

**Response:**
```json
{
  "status": "success",
  "payment": {
    "found": true,
    "status": "completed",
    "amount": 100,
    "mpesa_receipt": "QJK1234ABC",
    "scan_id": "abc123"
  }
}
```

---

### **4. Check Subscription**
```
POST /api/subscription/check
```
**Request:**
```json
{
  "phone_number": "254712345678"
}
```

**Response:**
```json
{
  "status": "success",
  "has_subscription": true,
  "subscription": {
    "phone_number": "254712345678",
    "plan": "pro",
    "status": "active",
    "expires_at": "2025-11-13T10:00:00",
    "features": [...]
  }
}
```

---

### **5. M-Pesa Callback** (Automated)
```
POST /api/payment/callback
```
Receives payment confirmation from Safaricom automatically.

---

## 💾 Database Structure

### **Payments Collection**
```json
{
  "checkout_request_id": "ws_CO_13102025...",
  "merchant_request_id": "123456...",
  "phone_number": "254712345678",
  "amount": 100,
  "payment_type": "report_download",
  "scan_id": "abc123",
  "status": "completed",
  "mpesa_receipt": "QJK1234ABC",
  "transaction_date": "20251013190000",
  "created_at": ISODate("2025-10-13T19:00:00Z"),
  "updated_at": ISODate("2025-10-13T19:01:00Z")
}
```

### **Subscriptions Collection**
```json
{
  "phone_number": "254712345678",
  "plan": "pro",
  "amount_paid": 2000,
  "payment_id": "...",
  "checkout_request_id": "ws_CO_...",
  "status": "active",
  "created_at": ISODate("2025-10-13T19:00:00Z"),
  "expires_at": ISODate("2025-11-13T19:00:00Z"),
  "features": [...]
}
```

---

## 🔐 Premium Feature Gating

### **Free Users Can:**
- ✅ Run basic scans (SSL, Headers)
- ✅ View results online
- ✅ Quick wins scanner
- ❌ Download PDF reports (requires payment)
- ❌ Email reports (requires payment)
- ❌ SQL Injection scanning (requires subscription)
- ❌ XSS detection (requires subscription)
- ❌ Directory enumeration (requires subscription)

### **Paid Report (100 KSH) Unlocks:**
- ✅ Download PDF for that specific scan
- ✅ Email report to inbox

### **Pro Subscription (2,000 KSH/month) Unlocks:**
- ✅ All free features
- ✅ SQL Injection scanning
- ✅ XSS detection
- ✅ Directory enumeration
- ✅ Unlimited report downloads
- ✅ Email all reports
- ✅ Trend analysis
- ✅ API access
- ✅ Priority support

---

## 🧪 Testing

### **Test in Sandbox:**

1. **Set sandbox environment:**
   ```bash
   export MPESA_ENVIRONMENT=sandbox
   ```

2. **Use test credentials:**
   - Consumer Key: From Daraja sandbox app
   - Consumer Secret: From Daraja sandbox app
   - Short Code: `174379`
   - Passkey: From Daraja sandbox

3. **Test phone number:** `254708374149`
4. **Test PIN:** `1234`

5. **Test flow:**
   - Run a scan
   - Click download
   - Enter test number
   - STK push appears
   - Enter PIN
   - Payment confirmed
   - Report downloads

---

## 🚀 Production Deployment

### **When Ready for Live Payments:**

1. **Get Prod Credentials:**
   - Apply for production access in Daraja
   - Get your real paybill/till number
   - Get production Consumer Key/Secret
   - Get production Passkey

2. **Update Environment:**
   ```bash
   fly secrets set MPESA_ENVIRONMENT=production
   fly secrets set MPESA_CONSUMER_KEY=prod_consumer_key
   fly secrets set MPESA_CONSUMER_SECRET=prod_consumer_secret
   fly secrets set MPESA_SHORTCODE=your_paybill_number
   fly secrets set MPESA_PASSKEY=prod_passkey
   ```

3. **Update Callback URL:**
   - Set in Daraja to your production URL

4. **Deploy:**
   ```bash
   fly deploy
   ```

---

## 💡 Revenue Potential

### **Monthly Revenue Example:**

**Scenario 1: Pay-Per-Report**
- 100 reports/month × 100 KSH = **10,000 KSH/month**

**Scenario 2: Mixed**
- 50 reports × 100 KSH = 5,000 KSH
- 10 subscriptions × 2,000 KSH = 20,000 KSH
- **Total: 25,000 KSH/month**

**Scenario 3: Subscription Focus**
- 50 subscribers × 2,000 KSH = **100,000 KSH/month**

---

## 🔧 Troubleshooting

### **Issue: STK Push Not Received**

**Check:**
1. Phone number format (254XXXXXXXXX)
2. M-Pesa credentials are correct
3. Callback URL is accessible
4. User has active Safaricom line

**Debug:**
```bash
fly logs | grep -i mpesa
```

---

### **Issue: Callback Not Working**

**Verify:**
1. Callback URL is publicly accessible
2. URL is registered in Daraja
3. Endpoint returns 200 status
4. MongoDB is connected

**Test callback manually:**
```bash
curl -X POST https://cybertech-security-scanner.fly.dev/api/payment/callback \
  -H "Content-Type: application/json" \
  -d '{"Body": {"stkCallback": {"ResultCode": 0}}}'
```

---

### **Issue: Payment Status Not Updating**

**Check:**
1. MongoDB connection
2. Callback endpoint receiving data
3. CheckoutRequestID matches

**Query MongoDB:**
```javascript
db.payments.find({checkout_request_id: "ws_CO_..."})
```

---

## 📊 Monitoring Payments

### **View All Payments:**
```javascript
// In MongoDB
db.payments.find().sort({created_at: -1}).limit(10)
```

### **View Active Subscriptions:**
```javascript
db.subscriptions.find({
  status: 'active',
  expires_at: {$gt: new Date()}
})
```

### **Payment Statistics:**
```javascript
// Total revenue
db.payments.aggregate([
  {$match: {status: 'completed'}},
  {$group: {_id: null, total: {$sum: '$amount'}}}
])

// Monthly revenue
db.payments.aggregate([
  {$match: {
    status: 'completed',
    created_at: {$gte: new Date('2025-10-01')}
  }},
  {$group: {_id: null, total: {$sum: '$amount'}}}
])
```

---

## 🎓 Next Steps

### **Immediate:**
1. ✅ Get Daraja API credentials
2. ✅ Set up sandbox environment
3. ✅ Test payment flow
4. ✅ Verify callbacks working
5. ✅ Test subscription activation

### **Before Production:**
1. Apply for production API access
2. Get real paybill/till number
3. Update production credentials
4. Test with real payments (small amounts)
5. Monitor for 24-48 hours
6. Go fully live

### **Marketing:**
1. Announce pricing on website
2. Offer launch discount (e.g., 1,500 KSH first month)
3. Create demo video
4. Share on social media
5. Target web developers/agencies

---

## 📝 Important Notes

### **Compliance:**
- ✅ Keep payment records for auditing
- ✅ Provide receipts (M-Pesa receipt number)
- ✅ Clear refund policy
- ✅ Terms of service
- ✅ Privacy policy

### **Security:**
- ✅ Never log sensitive data (M-Pesa PINs)
- ✅ Use HTTPS only
- ✅ Validate all inputs
- ✅ Implement rate limiting
- ✅ Monitor for fraud

### **Customer Support:**
- Provide clear payment instructions
- Handle failed payments gracefully
- Offer refunds for issues
- Monitor payment success rate
- Track user feedback

---

## 🎉 What You Now Have

A **complete payment system** with:
- ✅ M-Pesa STK Push integration
- ✅ Payment tracking in MongoDB
- ✅ Subscription management
- ✅ Premium feature gating
- ✅ Beautiful pricing page
- ✅ Payment modals
- ✅ Status checking
- ✅ Automatic activation
- ✅ Revenue tracking
- ✅ Production-ready code

**Ready to monetize your security scanner!** 💰🚀

