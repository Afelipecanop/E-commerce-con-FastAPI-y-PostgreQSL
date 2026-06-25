const API_URL = "https://e-commerce-con-fastapi-y-postgreqsl-production.up.railway.app";

// ─── TOKEN ───────────────────────────────────────────────────────────────────

function getToken() {
    return localStorage.getItem("token");
}

function setToken(token) {
    localStorage.setItem("token", token);
}

function removeToken() {
    localStorage.removeItem("token");
}

function isLoggedIn() {
    return !!getToken();
}

// ─── FETCH BASE ───────────────────────────────────────────────────────────────

async function apiFetch(endpoint, options = {}) {
    const token = getToken();
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers: { ...headers, ...options.headers }
    });

    if (response.status === 401) {
        removeToken();
        window.location.href = "/frontend/login.html";
        return;
    }

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Error en la solicitud");
    }

    if (response.status === 204) return null;
    return response.json();
}

// ─── AUTH ─────────────────────────────────────────────────────────────────────

async function register(email, password, fullName) {
    return apiFetch("/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password, full_name: fullName })
    });
}

async function login(email, password) {
    const data = await apiFetch("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password })
    });
    setToken(data.access_token);
    return data;
}

async function getMe() {
    return apiFetch("/auth/me");
}

function logout() {
    removeToken();
    window.location.href = "/frontend/login.html";
}

// ─── PRODUCTOS ────────────────────────────────────────────────────────────────

async function getProducts() {
    return apiFetch("/products/");
}

async function getProduct(id) {
    return apiFetch(`/products/${id}`);
}

async function createProduct(data) {
    return apiFetch("/products/", { method: "POST", body: JSON.stringify(data) });
}

async function updateProduct(id, data) {
    return apiFetch(`/products/${id}`, { method: "PUT", body: JSON.stringify(data) });
}

async function deleteProduct(id) {
    return apiFetch(`/products/${id}`, { method: "DELETE" });
}

// ─── CARRITO ──────────────────────────────────────────────────────────────────

async function getCart() {
    return apiFetch("/cart/");
}

async function addToCart(productId, quantity = 1) {
    return apiFetch("/cart/items", {
        method: "POST",
        body: JSON.stringify({ product_id: productId, quantity })
    });
}

async function updateCartItem(itemId, quantity) {
    return apiFetch(`/cart/items/${itemId}`, {
        method: "PUT",
        body: JSON.stringify({ quantity })
    });
}

async function removeFromCart(itemId) {
    return apiFetch(`/cart/items/${itemId}`, { method: "DELETE" });
}

// ─── PAGOS Y ÓRDENES ─────────────────────────────────────────────────────────

async function checkout() {
    return apiFetch("/payments/checkout", { method: "POST" });
}

async function getOrders() {
    return apiFetch("/payments/orders");
}