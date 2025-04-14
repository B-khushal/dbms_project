// BKP Florist - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss flash messages after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            if (alert && bootstrap) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, 5000);

    // Toggle billing address form in checkout page
    const sameAsShipping = document.getElementById('same-as-shipping');
    const billingAddressForm = document.getElementById('billing-address-form');
    
    if (sameAsShipping && billingAddressForm) {
        sameAsShipping.addEventListener('change', function() {
            if (this.checked) {
                billingAddressForm.style.display = 'none';
                copyShippingToBilling();
            } else {
                billingAddressForm.style.display = 'block';
            }
        });
        
        // Copy shipping fields to billing when they change
        const shippingFields = ['address', 'city', 'state', 'postal_code', 'country'];
        shippingFields.forEach(field => {
            const shippingField = document.getElementById('shipping_' + field);
            if (shippingField) {
                shippingField.addEventListener('change', function() {
                    if (sameAsShipping.checked) {
                        document.getElementById('billing_' + field).value = this.value;
                    }
                });
            }
        });
    }
    
    // Initialize quantity buttons in cart page
    const quantityBtns = document.querySelectorAll('.quantity-form button');
    if (quantityBtns.length > 0) {
        quantityBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                setTimeout(() => {
                    this.closest('form').submit();
                }, 100);
            });
        });
    }
    
    // Initialize product image gallery in product detail page
    const productCarousel = document.getElementById('productCarousel');
    if (productCarousel) {
        const carousel = new bootstrap.Carousel(productCarousel, {
            interval: 5000
        });
        
        // Thumbnail click handler
        const thumbnails = document.querySelectorAll('[data-bs-target="#productCarousel"]');
        thumbnails.forEach(thumbnail => {
            thumbnail.addEventListener('click', function(e) {
                e.preventDefault();
            });
        });
    }
});

// Helper function to copy shipping address to billing
function copyShippingToBilling() {
    const shippingFields = ['address', 'city', 'state', 'postal_code', 'country'];
    shippingFields.forEach(field => {
        const shippingValue = document.getElementById('shipping_' + field).value;
        const billingField = document.getElementById('billing_' + field);
        if (billingField) {
            billingField.value = shippingValue;
        }
    });
} 
