chrome.tabs.onUpdated.addListener(function(tabId, changeInfo, tab) {

    // Run only when page fully loads
    if (changeInfo.status === "complete" && tab.url) {

        let url = tab.url;

        // Ignore Chrome internal pages
        if (url.startsWith("chrome://") || url.startsWith("edge://")) {
            return;
        }

        // 🔥 Call your Flask API
        fetch("http://127.0.0.1:5000/predict", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ url: url })
        })
        .then(res => res.json())
        .then(data => {

            console.log("Scan Result:", data);

            // 🚨 If phishing → show alert
            if (data.prediction === "Phishing") {

                chrome.scripting.executeScript({
                    target: { tabId: tabId },
                    func: showWarning,
                    args: [data]
                });

            }

        })
        .catch(err => console.error(err));
    }
});


// 🔴 This runs inside the webpage
function showWarning(data) {
    alert(
        "⚠️ PHISHING ALERT!\n\n" +
        "Type: " + data.attack_type + "\n" +
        "Confidence: " + data.confidence + "%\n\n" +
        "Be careful!"
    );
}