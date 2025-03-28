document.addEventListener("DOMContentLoaded", function () {
  const button = document.getElementById("generate-button");

  button.addEventListener("click", function () {
    const niche = document.getElementById("niche").value.trim();
    const platform = document.getElementById("platform").value;
    const email = document.getElementById("email").value.trim();

    if (!niche || !email) {
      alert("Please enter your niche and email.");
      return;
    }

    fetch("/checkout", {
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
        alert("Server error, please try again.");
      }
    })
    .catch(err => {
      console.error("Checkout Error:", err);
      alert("Something went wrong. Try again.");
    });
  });
});