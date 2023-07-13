# imports

# set up

# tear down

# add transaction item
## only succeed if transaction in client/pm review states
## should update transaction total value
## transaction updates state (client review or final client review)
## should create log in transaction

# delete transaction item
## only succeed if transaction in client/pm review states
## should update transaction total value
## should create log in transaction
## very common operation for trade admin to deny items we have already in stock

# update transaction item
## update condition - available to be done in grading step
### value should be recalculated using stamped market value when transaction was created
## update the card itself - available to be done in grading step

# approve transaction item
## could do a web approval and final approval fields
### web approval
### admin approves each of them, updates remove admin approval from that item
### final approval
### grades are in and locked, just discussing price for each item
### admin updates various final prices based on grade + value to us + bad information in pricing algos
### these updates revert transaction to final client review
### client can "approve all" or approve one by one but basically doesnt need to press submit until the price is right
### admin can review trade but can not alter transaction in any way after final client approval
## let the admins be able to deny
# deny transaction item