taskId = null;
interval = null;

function presentError(xhr) {
    let data = xhr.responseJSON;
    let errorMsg = data ? "Error: " + data['error'] : "Something went wrong, please try again."
    $("#error-msg").text(errorMsg);
    $("#error-msg").show();
    $("#start").prop("disabled", false);
}

function setProgressBar(pct) {
    $("#progress .bar").css("width", pct + "%");
    $("#pct").text(pct + "%");
}

$("#start:not(:disabled)").click(function() {
    let steamId = $("#steam-id").val();
    $(this).prop("disabled", true);
    $("#error-msg").hide();
    $.get("http://localhost:5000/steam", {steam_id: steamId, interval: $("input[name='interval']:checked").val()}, function(data) {
        taskId = data['task_id'];
        if (interval != null) {
            clearInterval(interval);
        }
        interval = window.setInterval(refreshProgress, 1000);
    }).fail(function($xhr) {
        presentError($xhr);
    });
});

function refreshProgress() {
    if (taskId == null) {
        if (interval != null) {
            clearInterval(interval);
            interval = null;
            setProgressBar(0);
        }
    } else {
        $.get("http://localhost:5000/steam/progress/" + taskId, function(data) {
            setProgressBar(data.progress);
            if (data.progress == 100 && interval != null) {
                $("#achievement-field").text(data['achievements']);
                clearInterval(interval);
                taskId = null;
                interval = null;
                $("#start").prop("disabled", false);
            }
        }).fail(function($xhr) {
            presentError($xhr);
            clearInterval(interval);
            interval = null;
            setProgressBar(0);
        });
    }
}

$(".x").click(function() {
    $(this).parent("div").hide();
});
