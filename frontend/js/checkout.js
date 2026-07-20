// department_name (select) y city_name (input de texto libre) ya vienen
// poblados/servidos desde checkout.html — no se tocan aquí.

// Mostrar campos de invitado si no hay sesión
if (!isLoggedIn()) {
  document.getElementById("guest-fields").style.display = "block";
  document.getElementById("guest_nombre").setAttribute("required", "required");
  document.getElementById("guest_email").setAttribute("required", "required");
}

// ── Estado de carga del SDK de Bold (integración personalizada) ────────────────
let boldLoadFailed = false;
let boldCheckout = null; // instancia reutilizable una vez creada la orden

window.addEventListener("boldCheckoutLoadFailed", () => { boldLoadFailed = true; });

// ── Perfil del usuario logueado (para prellenar customerData en Bold) ──────────
let currentUser = null;
if (isLoggedIn()) {
  getMe().then((u) => { currentUser = u; }).catch(() => {});
}

document.getElementById("checkout-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const submitBtn = document.getElementById("submit-order-btn");

  // Si ya se creó la orden y se abrió Bold antes (usuario cerró el modal sin pagar),
  // solo reabrimos el mismo checkout en vez de crear una orden nueva.
  if (boldCheckout) {
    boldCheckout.open();
    return;
  }

  const paymentMethod = document.querySelector('input[name="payment_method"]:checked').value;
  submitBtn.disabled = true;
  submitBtn.textContent = "Procesando...";

  try {
    let data;

    if (isLoggedIn()) {
      // ── Flujo usuario logueado: carrito ya vive en el backend ──
      const body = {
        customer_phone: document.getElementById("customer_phone").value,
        document_type: document.getElementById("document_type").value || null,
        document_number: document.getElementById("document_number").value || null,
        shipping_address: document.getElementById("shipping_address").value,
        shipping_notes: document.getElementById("shipping_notes").value || null,
        department_name: document.getElementById("department_name").value,
        city_name: document.getElementById("city_name").value,
        payment_method: paymentMethod,
      };
      data = await checkout(body);

    } else {
      // ── Flujo invitado: carrito viene de localStorage (velonox_cart) ──
      const guestCart = getGuestCart();
      if (guestCart.length === 0) {
        alert("Tu carrito está vacío.");
        submitBtn.disabled = false;
        submitBtn.textContent = "Confirmar pedido";
        return;
      }

      const body = {
        email: document.getElementById("guest_email").value,
        nombre: document.getElementById("guest_nombre").value,
        document_type: document.getElementById("document_type").value || null,
        document_number: document.getElementById("document_number").value || null,
        payment_method: paymentMethod,
        shipping_address: {
          direccion: document.getElementById("shipping_address").value,
          ciudad: document.getElementById("city_name").value,
          departamento: document.getElementById("department_name").value,
          telefono: document.getElementById("customer_phone").value,
          indicaciones: document.getElementById("shipping_notes").value || null,
        },
        items: guestCart.map(i => ({ product_id: i.id, quantity: i.quantity })),
      };
      data = await guestCheckout(body);
    }

    if (data.flow === "bold") {
      const opened = openBoldCheckout(data);
      submitBtn.disabled = false;
      submitBtn.textContent = "Confirmar pedido";
      if (!opened) submitBtn.disabled = true; // orden quedó creada pero Bold no cargó; evita reintento duplicado
    } else {
      if (!isLoggedIn()) clearGuestCart();
      window.location.href = `/pedido-confirmado.html?order_id=${data.order_id}`;
    }
  } catch (err) {
    alert(err.message || "Hubo un problema con tu pedido. Intenta de nuevo.");
    submitBtn.disabled = false;
    submitBtn.textContent = "Confirmar pedido";
  }
});

// ── Integración personalizada de Bold: botón propio + checkout.open() ──────────
function openBoldCheckout(data) {
  if (boldLoadFailed || window.__boldScriptFailed || typeof window.BoldCheckout === "undefined") {
    showFormAlert("No pudimos cargar la pasarela de pago de Bold. Verifica tu conexión a internet y vuelve a intentarlo en unos segundos.");
    return false;
  }

  const config = {
    orderId: data.bold_order_id,
    currency: data.currency,
    amount: String(data.amount),
    apiKey: data.api_key,
    integritySignature: data.signature,
    description: "Compra Velonox",
    redirectionUrl: data.redirection_url,
  };

  const customerData = buildCustomerData();
  if (customerData) config.customerData = customerData;

  const billingAddress = buildBillingAddress();
  if (billingAddress) config.billingAddress = billingAddress;

  boldCheckout = new window.BoldCheckout(config);
  boldCheckout.open();
  return true;
}

function buildCustomerData() {
  const { dialCode, phone } = splitPhone(document.getElementById("customer_phone").value);
  const documentType = document.getElementById("document_type").value || "";
  const documentNumber = document.getElementById("document_number").value || "";

  const customer = { phone, dialCode, documentType, documentNumber };

  if (isLoggedIn()) {
    if (currentUser) {
      customer.email = currentUser.email || "";
      customer.fullName = currentUser.full_name || "";
    }
  } else {
    customer.email = document.getElementById("guest_email").value || "";
    customer.fullName = document.getElementById("guest_nombre").value || "";
  }

  return JSON.stringify(customer);
}

function buildBillingAddress() {
  const address = document.getElementById("shipping_address").value || "";
  const city = document.getElementById("city_name").value || "";
  const state = document.getElementById("department_name").value || "";
  if (!address || !city || !state) return null;

  return JSON.stringify({ address, zipCode: "", city, state, country: "CO" });
}

// Separa un teléfono tipo "+57 300 000 0000" en indicativo y número local.
// Si no trae indicativo, asume Colombia (+57) por ser el mercado principal de la tienda.
function splitPhone(raw) {
  const cleaned = (raw || "").trim();
  if (cleaned.startsWith("+")) {
    const match = cleaned.match(/^\+(\d{1,3})[\s-]?(.*)$/);
    if (match) return { dialCode: match[1], phone: match[2].replace(/\D/g, "") };
  }
  return { dialCode: "57", phone: cleaned.replace(/\D/g, "") };
}

function showFormAlert(message) {
  const alertEl = document.getElementById("form-alert");
  if (!alertEl) { alert(message); return; }
  alertEl.textContent = message;
  alertEl.className = "alert show alert-err";
}
