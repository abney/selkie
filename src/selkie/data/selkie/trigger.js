
(function () {

    var form = document.querySelector("form");
    var triggerField = document.createElement("input");
    triggerField.type = "hidden";
    triggerField.name = "trigger";
    triggerField.value = "None";    
    form.appendChild(triggerField);

    function setTrigger (event) {
        var id = this.id;
        triggerField.value = id;
        console.log("Set trigger: " + id);
    }

    var boxes = document.querySelectorAll("input");
    for (var i = 0; i < boxes.length; ++i) {
        var box = boxes[i];
        if (box.type === "text") {
            box.addEventListener("focus", setTrigger, false);
        }
    }

})();
