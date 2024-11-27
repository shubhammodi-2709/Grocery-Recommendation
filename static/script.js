// Function to add a product to the cart
function addToCart(productId) {
    // Get the product details from the UI (for example, product name and price)
    const productElement = document.getElementById(`product-${productId}`);
    const productName = productElement.querySelector('.product-name').innerText;
    const productPrice = parseFloat(productElement.querySelector('.product-price').innerText);
    
    // Create a cart item object
    const cartItem = {
        id: productId,
        name: productName,
        price: productPrice,
        quantity: 1 // Default quantity
    };

    // Retrieve the current cart from local storage or initialize a new one
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    
    // Check if the item is already in the cart
    const existingItemIndex = cart.findIndex(item => item.id === productId);
    
    if (existingItemIndex > -1) {
        // If it exists, update the quantity
        cart[existingItemIndex].quantity += 1;
    } else {
        // If not, add it to the cart
        cart.push(cartItem);
    }
    
    // Save the updated cart back to local storage
    localStorage.setItem('cart', JSON.stringify(cart));
    
    // Update the cart UI
    updateCartUI();

    // Request product recommendations after adding the item to the cart
    fetchRecommendations();
}

// Function to update the cart UI
function updateCartUI() {
    // Get cart data from local storage
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    
    const cartContainer = document.getElementById('cart-container');
    cartContainer.innerHTML = ''; // Clear existing items
    
    let totalPrice = 0; // Initialize total price

    // Loop through the cart items and display them
    cart.forEach(item => {
        const itemTotalPrice = item.price * item.quantity;
        totalPrice += itemTotalPrice; // Accumulate total price

        const cartItemElement = document.createElement('div');
        cartItemElement.classList.add('cart-item');
        cartItemElement.innerHTML = `  
            <span class="cart-item-name">${item.name}</span>
            <span class="cart-item-price">$${item.price.toFixed(2)}</span>
            <input type="number" class="cart-item-quantity" value="${item.quantity}" min="1" onchange="updateQuantity('${item.id}', this.value)">
            <span class="cart-item-total">$${itemTotalPrice.toFixed(2)}</span>
            <button onclick="removeFromCart('${item.id}')">Remove</button>
        `;
        cartContainer.appendChild(cartItemElement);
    });

    // Display total price
    const totalElement = document.getElementById('total-price');
    totalElement.innerText = `Total: $${totalPrice.toFixed(2)}`;
}

// Function to update the quantity of an item in the cart
function updateQuantity(productId, newQuantity) {
    // Get the current cart
    let cart = JSON.parse(localStorage.getItem('cart')) || [];

    // Find the item in the cart
    const itemIndex = cart.findIndex(item => item.id === productId);

    // Update quantity if item is found
    if (itemIndex > -1) {
        cart[itemIndex].quantity = parseInt(newQuantity);
        // Save the updated cart
        localStorage.setItem('cart', JSON.stringify(cart));
        // Update the cart UI
        updateCartUI();
    }
}

// Function to remove an item from the cart
function removeFromCart(productId) {
    // Get the current cart
    let cart = JSON.parse(localStorage.getItem('cart')) || [];

    // Filter out the item to be removed
    cart = cart.filter(item => item.id !== productId);

    // Save the updated cart
    localStorage.setItem('cart', JSON.stringify(cart));
    // Update the cart UI
    updateCartUI();
}

// Function to handle checkout
function checkout() {
    // Get cart data
    let cart = JSON.parse(localStorage.getItem('cart')) || [];

    // Prepare order data to be sent to the server
    const orderData = cart.map(item => ({
        productId: item.id,
        quantity: item.quantity
    }));

    // Send order data to the server (example with fetch API)
    fetch('/checkout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData)
    })
    .then(response => response.json())
    .then(data => {
        alert('Order placed successfully!');
        localStorage.removeItem('cart'); // Clear the cart after successful checkout
        updateCartUI(); // Update UI after clearing cart
    })
    .catch(error => {
        alert('Error placing order');
        console.error('Error:', error);
    });
}

// Function to fetch recommendations based on cart contents
function fetchRecommendations() {
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    let cartIds = cart.map(item => item.id); // Extract product IDs

    // Send product IDs to the server to get recommendations
    fetch('/get_recommendations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ productIds: cartIds })
    })
    .then(response => response.json())
    .then(data => {
        displayRecommendations(data); // Function to display recommended products
    })
    .catch(error => {
        console.error('Error fetching recommendations:', error);
    });
}

// Function to display recommendations
function displayRecommendations(products) {
    const recommendationsContainer = document.getElementById('recommendations-container');
    recommendationsContainer.innerHTML = ''; // Clear existing recommendations

    products.forEach(product => {
        const productElement = document.createElement('div');
        productElement.classList.add('recommendation-item');
        productElement.innerHTML = `
            <p>${product.name}</p>
            <button onclick="addToCart(${product.id})">Add to Cart</button>
        `;
        recommendationsContainer.appendChild(productElement);
    });
}

// Initial UI Update when the page loads
document.addEventListener('DOMContentLoaded', () => {
    updateCartUI(); // Update the cart UI on page load
    fetchRecommendations(); // Fetch and display product recommendations
});
