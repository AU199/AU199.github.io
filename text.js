document.getElementById('carbon').addEventListener('submit',function(event){
    event.preventDefault();

   
    const average_miles_per_week = parseFloat(document.getElementById('miles').value);

    const amount_driven_year = average_miles_per_week * 52;
    const carbon_per_mile = 404;
    const annual_amount = amount_driven_year*carbon_per_mile / 1000;

    const result_Div = document.getElementById('result');
    result_Div.textContent = 'If continued at this pace, your carbon footprint annualy would approximately be ' + annual_amount.toFixed(2) +' kg of carbon dioxide';

});