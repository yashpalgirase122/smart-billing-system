function pieChart(labels, values) {
    new Chart(document.getElementById("pieChart"), {
        type: "pie",
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    "#ff6f91", "#ffc75f", "#845ec2", "#4d96ff"
                ]
            }]
        }
    });
}

function lineChart(months, trend) {
    new Chart(document.getElementById("lineChart"), {
        type: "line",
        data: {
            labels: months,
            datasets: [{
                label: "Future Sales",
                data: trend,
                borderColor: "#4d96ff",
                tension: 0.4
            }]
        }
    });
}
