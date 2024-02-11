async function getUser(place) {
    const api_url = `https://timezone.abstractapi.com/v1/current_time/?api_key=API_KEY&location=${place}`
    
    const response = await fetch(api_url);
    
    const data = await response.json();
    
    time = await data.datetime
    // arr = Array.from(time)
    // arr.splice(0, 11)
    // arr.toString()
    // timezone = (arr.splice(0, 5)).join("");
    document.getElementById("time").innerText = `${place}'s time = ${time} ${data.timezone_abbreviation}`

}

const countryContent = {
    "United-States": {
        header: "<h2>United States</h2>",
        sharpeRatio: "<h6><i>Current sharpe ratio: 1.2</i></h6>",
        stocks: "<h6 style='text-decoration: underline';>Best Stocks To Invest</h6><ul style='list-style-type: none;'><li style='font-size: 14px'>Apple(AAPL)</li><li style='font-size: 14px'>Netflix(NFLX)</li><li style='font-size: 14px'>Alphabet(GOOG)</li></ul>"
    },
    "Japan": {
        header: "<h2>Insights</h2>",
        sharpeRatio: "<h6><i>Current sharpe ratio: 0.3</i></h6>",
        stocks: "<h6 style='text-decoration: underline';>Best Stocks To Invest</h6><ul style='list-style-type: none;'><li style='font-size: 14px'>Toyota(TM)</li><li style='font-size: 14px'>Honda(HMC)</li><li style='font-size: 14px'>Sony(SONY)</li></ul>"
    }
};

document.querySelectorAll(".allPaths").forEach(e => {
e.setAttribute('class', `allPaths ${e.id}`);
e.addEventListener("mouseover", function () {

    window.onmousemove=function (j) {
        x = j.clientX
        y = j.clientY
        document.getElementById('name').style.top = y-60  + 'px'
        document.getElementById('name').style.left = x +10 + 'px'
    };

    let content = countryContent[e.id] ? countryContent[e.id].header + countryContent[e.id].sharpeRatio + countryContent[e.id].stocks : e.id;

    document.getElementById("namep").innerHTML = content;

    const classes=e.className.baseVal.replace(/ /g, '.')         
    document.querySelectorAll(`.${classes}`).forEach(country =>{
        if (country.id === "United-States") {
            country.style.fill = "rgba(0, 128, 0, 0.7)"; // Green with reduced opacity
        } else if (country.id === "Japan") {
            country.style.fill = "rgba(255, 0, 0, 0.7)"; // Red with reduced opacity
        } else {
            country.style.fill = "#ececec";
        }
    });
    document.getElementById("name").style.opacity = 1
    
})
e.addEventListener("mouseleave", function () {
    const classes=e.className.baseVal.replace(/ /g, '.');
    document.querySelectorAll(`.${classes}`).forEach(country =>{

        if (country.id === "United-States") {
            country.style.fill = "green";
        } else if(country.id === "Japan") {
            country.style.fill = "red";
        } else {
            country.style.fill = "#ececec"
        }
    })
    document.getElementById("name").style.opacity = 0
})

e.addEventListener("click",function(){
    getUser(e.id)
})

})

// document.getElementById("searchBtn").addEventListener("click", function () {
//     country = document.getElementById("search").value
//     document.querySelectorAll(`.allPaths`).forEach(e => {
//         e.style.fill = "#ececec"
//     })
//     document.querySelectorAll(`#${country}`).forEach(e => {
//         e.style.fill = "red"
//     })
// })