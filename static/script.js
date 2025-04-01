document.addEventListener("DOMContentLoaded", function () {
    const checkoutButton = document.getElementById("checkout-button");
    const statusDiv = document.getElementById("status");

    checkoutButton.addEventListener("click", async () => {
        const niche = document.getElementById("niche").value;
        const platform = document.getElementById("platform").value;

        if (!niche || !platform) {
            alert("Please enter a niche and select a platform.");
            return;
        }

        checkoutButton.disabled = true;
        statusDiv.innerHTML = "<p style='color: yellow;'>Redirecting to payment...</p>";

        try {
            const response = await fetch("/create-checkout-session", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ niche, platform })
            });

            const result = await response.json();

            if (result.id) {
                const stripe = Stripe(document.getElementById("checkout-button").dataset.stripePublicKey);
                stripe.redirectToCheckout({ sessionId: result.id });
            } else {
                throw new Error(result.error || "Unknown error");
            }
        } catch (err) {
            statusDiv.innerHTML = `<p style='color: red;'>Error: ${err.message}</p>`;
            checkoutButton.disabled = false;
        }
    });
});