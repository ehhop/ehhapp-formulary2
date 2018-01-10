@app.route("/invoices/new")
def add_invoice():
  #todo
  database.consolidateRecord("path_to_uploaded_invoice")
  return render_template("add_new_invoice.html")
