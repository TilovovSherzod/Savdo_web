/**
 * SAVDO - Asosiy JavaScript fayli
 */

// DOM yuklangandan keyin ishga tushadi
document.addEventListener("DOMContentLoaded", () => {
  // Xabarlarni avtomatik yopish
  setTimeout(() => {
    const alerts = document.querySelectorAll(".alert")
    alerts.forEach((alert) => {
      const closeButton = alert.querySelector(".btn-close")
      if (closeButton) {
        closeButton.click()
      }
    })
  }, 5000)

  // Rasmlarni kattalashtirish
  const productImages = document.querySelectorAll(".product-image-container img")
  productImages.forEach((img) => {
    img.addEventListener("click", () => {
      // Kattalashtirish logikasi
    })
  })
})

// CSRF token olish funksiyasi
function getCookie(name) {
  let cookieValue = null
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";")
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim()
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue
}

// Savatga qo'shish funksiyasi
function addToCart(productId, quantity = 1) {
  fetch("/savatga-qoshish/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      // Removed CSRF token header since we're exempting the view
    },
    body: JSON.stringify({
      maxsulot_id: productId,
      miqdor: quantity,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // Savatdagi maxsulotlar sonini yangilash
        const savatSoni = document.getElementById("savat-soni")
        if (savatSoni) {
          savatSoni.textContent = data.savat_maxsulotlar_soni
        }

        // Modal xabarini yangilash va ko'rsatish
        const cartModalMessage = document.getElementById("cartModalMessage")
        if (cartModalMessage) {
          cartModalMessage.textContent = `"${data.maxsulot_nomi}" savatga qo'shildi!`
          const bootstrap = window.bootstrap // Ensure bootstrap is accessible
          const modal = document.getElementById("addToCartModal")
          if (modal && bootstrap && bootstrap.Modal) {
            new bootstrap.Modal(modal).show()
          }
        }
      }
    })
    .catch((error) => console.error("Error:", error))
}

// Savatni yangilash funksiyasi
function updateCart(productId, quantity) {
  fetch("/savat-yangilash/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      // Removed CSRF token header since we're exempting the view
    },
    body: JSON.stringify({
      maxsulot_id: productId,
      miqdor: quantity,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // Savatdagi maxsulotlar sonini yangilash
        const savatSoni = document.getElementById("savat-soni")
        if (savatSoni) {
          savatSoni.textContent = data.maxsulotlar_soni
        }

        // Jami narxni yangilash
        const cartSubtotal = document.getElementById("cart-subtotal")
        const cartTotal = document.getElementById("cart-total")
        if (cartSubtotal && cartTotal) {
          cartSubtotal.textContent = data.jami_narx + " so'm"
          cartTotal.textContent = data.jami_narx + " so'm"
        }
      }
    })
    .catch((error) => console.error("Error:", error))
}

// Savatni tozalash funksiyasi
function clearCart() {
  fetch("/savat-tozalash/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      // Removed CSRF token header since we're exempting the view
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        location.reload()
      }
    })
    .catch((error) => console.error("Error:", error))
}

// Cart item quantity update function for the cart page
function updateCartItemQuantity(productId, quantity) {
  fetch("/savat-yangilash/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      // Removed CSRF token header since we're exempting the view
    },
    body: JSON.stringify({
      maxsulot_id: productId,
      miqdor: quantity,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // Sahifani yangilash
        location.reload()
      }
    })
    .catch((error) => console.error("Error:", error))
}

