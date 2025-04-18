window.addEventListener('load', function () {
    fetch('/console/api/channel/wx/config?url='+location.href)
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        wx.ready(function () {
            console.log("wx ready")
        });
        wx.error(function (res) {
            alert("错误"+res.errMsg);
        })
        wx.config(data.data);
    }).catch(error => {
        console.error('There was a problem with the fetch operation:', error);
    });
});