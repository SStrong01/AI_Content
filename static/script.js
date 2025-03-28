document.addEventListener("DOMContentLoaded", function () {
    const generateButton = document.getElementById("generate-button");

    generateButton.addEventListener("click", function () {
        const niche = document.getElementById("niche").value;
        const platform = document.getElementById("platform").value;

        if (!niche || !platform) {
            alert("Please enter a niche and choose a platform.");
            return;
        }

        fetch("/checkout", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ niche: niche, platform: platform })
        })
        .then(res => res.json())
        .then(data => {
            if (data.checkout_url) {
                window.location.href = data.checkout_url;
            } else {
                alert("Something went wrong during checkout.");
                console.error(data);
            }
        })
        .catch(err => {
            console.error("Error:", err);
            alert("Server error, please try again.");
        });
    });
});