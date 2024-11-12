console.log('Script hit')

let local_type_values = {

}



document.addEventListener("DOMContentLoaded", function () {
    console.log('HERE!')

    let valueTypeField = document.getElementById("id_value_type");
    function updateValueField() {
        valueTypeField = document.getElementById("id_value_type");
let valueField = document.getElementById("id_value");
        console.log('HERE!');
        const selectedType = valueTypeField?.value;

        valueField.type = "text";
        valueField.value = "";

        if (selectedType === "integer") {
            valueField.type = "number";
        } else if (selectedType === "boolean") {
            const select = document.createElement("select");
            select.name = "value";
            select.id = "id_value";

            const trueOption = document.createElement("option");
            trueOption.value = "true";
            trueOption.text = "True";
            select.appendChild(trueOption);

            const falseOption = document.createElement("option");
            falseOption.value = "false";
            falseOption.text = "False";
            select.appendChild(falseOption);

            valueField.parentNode.replaceChild(select, valueField);
        } else if (selectedType === "date") {
            valueField.type = "date";
        } else if (selectedType === "json") {
            valueField.type = "textarea";
            valueField.rows = 5;
            valueField.cols = 40;
        } else if (selectedType === "text" || selectedType === "map") {
            valueField.type = "textarea";
        } else {
            valueField.type = "text";
        }
    }

    updateValueField();

    valueTypeField.addEventListener("change", updateValueField);
});
