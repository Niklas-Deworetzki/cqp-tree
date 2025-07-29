function copyCQP() {
  // Get the text field
  var cqp_query = document.getElementById("cqp_query");

  // Select the text field
  cqp_query.select();
  cqp_query.setSelectionRange(0, 99999); // For mobile devices

  // Copy the text inside the text field
  navigator.clipboard.writeText(cqp_query.value);
}