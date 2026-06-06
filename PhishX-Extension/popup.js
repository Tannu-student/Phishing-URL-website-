chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
    let url = tabs[0].url;

    fetch("http://127.0.0.1:5000/predict", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({url: url})
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("result").innerText =
            data.prediction + " (" + data.confidence + "%)";

        let reasons = document.getElementById("reasons");
        reasons.innerHTML = "";

        data.reasons.forEach(r => {
            let li = document.createElement("li");
            li.innerText = r;
            reasons.appendChild(li);
        });
    });
});