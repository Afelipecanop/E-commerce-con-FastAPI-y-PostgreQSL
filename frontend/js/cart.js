// ─── CARRITO LOCAL (invitados y usuarios) ──────────────────────────────────────
// El carrito vive en localStorage para que cualquiera pueda explorarlo y llenarlo
// sin necesidad de iniciar sesión. El login solo se pide al momento de pagar.

const CART_KEY = "velonox_cart";

// Devuelve el carrito como array de { product_id, quantity }
function getLocalCart() {
    try {
        const raw = localStorage.getItem(CART_KEY);
        const items = raw ? JSON.parse(raw) : [];
        return Array.isArray(items) ? items : [];
    } catch (e) {
        return [];
    }
}

function saveLocalCart(items) {
    localStorage.setItem(CART_KEY, JSON.stringify(items));
    updateCartBadge();
}

// Cantidad total de unidades en el carrito
function cartCount() {
    return getLocalCart().reduce((sum, i) => sum + (i.quantity || 0), 0);
}

function addToLocalCart(productId, quantity = 1) {
    const items = getLocalCart();
    const existing = items.find(i => i.product_id === productId);
    if (existing) {
        existing.quantity += quantity;
    } else {
        items.push({ product_id: productId, quantity });
    }
    saveLocalCart(items);
}

function setLocalQty(productId, quantity) {
    let items = getLocalCart();
    if (quantity <= 0) {
        items = items.filter(i => i.product_id !== productId);
    } else {
        const item = items.find(i => i.product_id === productId);
        if (item) item.quantity = quantity;
    }
    saveLocalCart(items);
}

function removeLocalItem(productId) {
    saveLocalCart(getLocalCart().filter(i => i.product_id !== productId));
}

function clearLocalCart() {
    localStorage.removeItem(CART_KEY);
    updateCartBadge();
}

// Actualiza el globo del carrito en la barra de navegación (si existe)
function updateCartBadge() {
    const badge = document.getElementById("cart-badge");
    if (!badge) return;
    const n = cartCount();
    badge.textContent = n;
    badge.style.display = n > 0 ? "flex" : "none";
}

// Sincroniza el carrito local con el carrito del backend del usuario autenticado.
// Vacía el carrito del backend y lo rellena con lo que hay en localStorage, de modo
// que queden idénticos antes de crear la sesión de pago. Requiere estar logueado.
async function syncLocalCartToBackend() {
    // 1. Vaciar el carrito actual del backend (si tiene items)
    try {
        const backendCart = await getCart();
        for (const item of backendCart.items) {
            await removeFromCart(item.id);
        }
    } catch (e) {
        // 404 = el carrito aún no existe / está vacío; no es un error real aquí
    }

    // 2. Subir los items del carrito local
    const local = getLocalCart();
    for (const item of local) {
        await addToCart(item.product_id, item.quantity);
    }
}
