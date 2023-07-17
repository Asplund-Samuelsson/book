// https://digitalfox-tutorials.com/tutorial.php?title=How-to-add-remove-input-fields-dynamically-using-javascript

let form = document.forms[0];

function addField(plusElement){
    let displayButton = document.querySelector("form button");
  
    // Stopping the function if the input field has no value.
//    if(plusElement.previousElementSibling.value.trim() === ""){
//       return false;
//    }
  
    // creating the div container.
    let div = document.createElement("div");
    div.setAttribute("class", "field");
  
    // Creating the input elements.
    let dates = document.createElement("input");
    dates.setAttribute("type", "date");
    dates.setAttribute("name", "dates[]");
    dates.setAttribute("value", "{{ request.form['date'] }}")

    let start_times = document.createElement("input");
    start_times.setAttribute("type", "time");
    start_times.setAttribute("name", "start_times[]");
    start_times.setAttribute("value", "{{ request.form['start_time'] }}");

    let end_times = document.createElement("input");
    end_times.setAttribute("type", "time");
    end_times.setAttribute("name", "end_times[]");
    end_times.setAttribute("value", "{{ request.form['end_time'] }}");
 
    // Creating the plus span element.
    let plus = document.createElement("span");
    plus.setAttribute("onclick", "addField(this)");
    let plusText = document.createTextNode("+");
    plus.appendChild(plusText);
  
    // Creating the minus span element.
    let minus = document.createElement("span");
    minus.setAttribute("onclick", "removeField(this)");
    let minusText = document.createTextNode("-");
    minus.appendChild(minusText);
  
    // Adding the elements to the DOM.
    form.insertBefore(div, displayButton);
    div.appendChild(dates);
    div.appendChild(start_times);
    div.appendChild(end_times);
    div.appendChild(plus);
    div.appendChild(minus);
  
    // Un hiding the minus sign.
    plusElement.nextElementSibling.style.display = "block"; // the minus sign
    // Hiding the plus sign.
    plusElement.style.display = "none"; // the plus sign
}


function removeField(minusElement){
    minusElement.parentElement.remove();
}
