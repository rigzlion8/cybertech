// CyberTech Pricing & Subscription JavaScript

const API_BASE_URL = window.location.origin;
let currentCheckoutId = null;
let statusCheckInterval = null;

function selectSubPaymentMethod(method) {
    // Hide all forms
    document.getElementById('mpesaSubForm').style.display = 'none';
    document.getElementById('paystackSubForm').style.display = 'none';
    
    // Show selected form
    if (method === 'mpesa') {
        document.getElementById('mpesaSubForm').style.display = 'block';
        setTimeout(() => document.getElementById('phoneNumber').focus(), 100);
    } else if (method === 'paystack') {
        document.getElementById('paystackSubForm').style.display = 'block';
        setTimeout(() => document.getElementById('subEmail').focus(), 100);
    }
}

async function processSubscription(method) {
    const statusDiv = document.getElementById('paymentStatus');
    let payBtn, identifier;
    
    if (method === 'mpesa') {
        identifier = document.getElementById('phoneNumber').value;
        payBtn = document.getElementById('mpesaSubBtn');
        
        if (!identifier) {
            alert('Please enter your M-Pesa phone number');
            return;
        }
    } else if (method === 'paystack') {
        identifier = document.getElementById('subEmail').value;
        payBtn = document.getElementById('paystackSubBtn');
        
        if (!identifier) {
            alert('Please enter your email address');
            return;
        }
    }
    
    // Show pending status
    statusDiv.style.display = 'block';
    statusDiv.className = 'payment-status pending';
    statusDiv.textContent = 'Initiating payment...';
    payBtn.disabled = true;
    
    try {
        let response;
        
        if (method === 'mpesa') {
            response = await fetch(`${API_BASE_URL}/api/payment/initiate-subscription`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    phone_number: identifier,
                    plan: 'pro'
                })
            });
        } else if (method === 'paystack') {
            // For Paystack subscriptions, use Paystack endpoint
            response = await fetch(`${API_BASE_URL}/api/payment/paystack/initialize`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: identifier,
                    amount: 2000,
                    type: 'subscription'
                })
            });
        }
        
        const data = await response.json();
        
        if (data.status === 'success') {
            if (data.already_paid) {
                statusDiv.className = 'payment-status success';
                statusDiv.innerHTML = '✓ You already have an active subscription!';
                
                setTimeout(() => {
                    window.location.href = '/';
                }, 2000);
                return;
            }
            
            if (method === 'mpesa') {
                // M-Pesa: Wait for STK Push confirmation
                currentCheckoutId = data.checkout_request_id;
                
                statusDiv.className = 'payment-status pending';
                statusDiv.innerHTML = `
                    <div>📱 Check your phone for M-Pesa prompt</div>
                    <div style="margin-top: 0.5rem; font-size: 0.9rem;">Enter your PIN to complete payment</div>
                    <div class="loading-spinner" style="margin: 1rem auto;"></div>
                `;
                
                // Start checking payment status
                startStatusCheck(currentCheckoutId);
                
            } else if (method === 'paystack') {
                // Paystack: Redirect to payment page
                statusDiv.className = 'payment-status pending';
                statusDiv.textContent = 'Redirecting to secure payment page...';
                
                setTimeout(() => {
                    window.location.href = data.authorization_url;
                }, 1000);
            }
            
        } else {
            statusDiv.className = 'payment-status error';
            statusDiv.textContent = `Error: ${data.error || 'Failed to initiate payment'}`;
            payBtn.disabled = false;
        }
        
    } catch (error) {
        console.error('Payment error:', error);
        statusDiv.className = 'payment-status error';
        statusDiv.textContent = 'Network error. Please try again.';
        payBtn.disabled = false;
    }
}

function startStatusCheck(checkoutId) {
    let attempts = 0;
    const maxAttempts = 60; // Check for 1 minute (60 * 1 second)
    
    statusCheckInterval = setInterval(async () => {
        attempts++;
        
        if (attempts > maxAttempts) {
            clearInterval(statusCheckInterval);
            const statusDiv = document.getElementById('paymentStatus');
            statusDiv.className = 'payment-status error';
            statusDiv.textContent = 'Payment timeout. Please try again or contact support.';
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/payment/status/${checkoutId}`);
            const data = await response.json();
            
            if (data.status === 'success' && data.payment.found) {
                const paymentStatus = data.payment.status;
                
                if (paymentStatus === 'completed') {
                    clearInterval(statusCheckInterval);
                    const statusDiv = document.getElementById('paymentStatus');
                    statusDiv.className = 'payment-status success';
                    statusDiv.innerHTML = `
                        <div>✓ Payment Successful!</div>
                        <div style="margin-top: 0.5rem;">Receipt: ${data.payment.mpesa_receipt || 'Processing'}</div>
                        <div style="margin-top: 0.5rem; font-size: 0.9rem;">Redirecting...</div>
                    `;
                    
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 3000);
                    
                } else if (paymentStatus === 'failed') {
                    clearInterval(statusCheckInterval);
                    const statusDiv = document.getElementById('paymentStatus');
                    statusDiv.className = 'payment-status error';
                    statusDiv.textContent = 'Payment failed or was cancelled. Please try again.';
                }
            }
            
        } catch (error) {
            console.error('Status check error:', error);
        }
        
    }, 2000); // Check every 2 seconds
}

function openSubscriptionModal() {
    document.getElementById('subscriptionModal').classList.add('active');
    
    // Reset form
    document.getElementById('subscriptionForm').reset();
    document.getElementById('paymentStatus').style.display = 'none';
    
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
        statusCheckInterval = null;
    }
}

function closeSubscriptionModal() {
    document.getElementById('subscriptionModal').classList.remove('active');
    
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
        statusCheckInterval = null;
    }
}

// Close modal on outside click
document.getElementById('subscriptionModal').addEventListener('click', (e) => {
    if (e.target.id === 'subscriptionModal') {
        closeSubscriptionModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeSubscriptionModal();
    }
});

