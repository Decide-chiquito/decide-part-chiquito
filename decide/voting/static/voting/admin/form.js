document.addEventListener('DOMContentLoaded', function () {
    var typeElement = document.getElementById('id_type');
    var optionsGroup = document.getElementById("options-group");


    if (typeElement.value === 'YESNO') {
        optionsGroup.style.display = "none";
    }

    typeElement.addEventListener('change', function () {
        console.log(222);
        console.log(this.value);
        if (this.value === 'YESNO') {
            optionsGroup.style.display = "none";
        } else {
            optionsGroup.style.display = "block";

            var deleteCheckbox = document.getElementById('id_options-0-DELETE');
            var deleteCheckbox1 = document.getElementById('id_options-1-DELETE');
            deleteCheckbox.click();
            deleteCheckbox1.click();

            var continueButton = document.querySelector('button[name="_continue"]');
            continueButton.click();
        }
    });
});