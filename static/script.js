document.addEventListener("DOMContentLoaded", () => {
    const buyButton = document.getElementById("buy-premium");

    buyButton.addEventListener("click", () => {
        const niche = document.getElementById("niche").value.trim();
        const platform = document.getElementById("platform").value.trim();
        const email = document.getElementById("email").value.trim();

        if (!niche || !platform || !email) {
            alert("Please fill in all fields.");
            return;
        }

        fetch("/create-checkout-session", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ niche, platform, email })
        })
        .then(res => res.json())
        .then(data => {
            if (data.checkout_url) {
                window.location.href = data.checkout_url;
            } else {
                alert(data.error || "Failed to start checkout session.");
            }
        })
        .catch(err => {
            console.error("Checkout error:", err);
            alert("An error occurred. Please try again.");
        });
    });
});