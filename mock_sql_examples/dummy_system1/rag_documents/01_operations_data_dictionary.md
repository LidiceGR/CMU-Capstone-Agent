# Operations Data Dictionary (Synthetic Demo)

## Purpose of dbo.Operations
The Operations table stores records representing requested operational events. A stored record represents a request entered into the operational workflow; it is not, by itself, proof that a financial posting or settlement occurred.

## Column meanings
OperationId identifies the requested operational event. OperationType stores a category key; its business label must be obtained from the controlled Operation types catalog, rather than guessed from the number. Amount represents the magnitude supplied with the request; the unit and posting direction are not established by this document. Status represents the request's progression through an operational workflow; its specific label comes from the Operation statuses catalog.

## Scope and limitations
This dictionary describes what the fields represent. It does not define which operation types may be registered, acceptable amount ranges, required approvals, or any SQL conditions. Those rules must be established from executable source and applicable authoritative requirements.
