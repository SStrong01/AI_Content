document.addEventListener("DOMContentLoaded", () => {
  const buyBtn = document.getElementById("buyPremiumBtn");

  if (buyBtn) {
    buyBtn.addEventListener("click", async () => {
      const niche = document.getElementById("niche").value;
      const platform = document.getElementById("platform").value;
      const stripePublicKey = buyBtn.dataset.stripeKey;

      buyBtn.disabled = true;
      buyBtn.innerText = "Processing...";

      try {
        const response = await fetch("/buy", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ niche, platform })
        });

        const data = await response.json();

        if (data.id) {
          const stripe = Stripe(stripePublicKey);
          stripe.redirectToCheckout({ sessionId: data.id });
        } else {
          alert("Error: " + (data.error || "Something went wrong."));
          console.error("Stripe session error:", data);
        }
      } catch (error) {
        alert("Network error. Please try again.");
        console.error("Fetch error:", error);
      } finally {
        buyBtn.disabled = false;
        buyBtn.innerText = "Buy Premium Ideas ($15)";
      }
    });
  }
});