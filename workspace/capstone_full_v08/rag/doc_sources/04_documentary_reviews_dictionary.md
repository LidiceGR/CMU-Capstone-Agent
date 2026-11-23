# Documentary Review Cases — Data Dictionary (Synthetic Demo)

## Purpose of dbo.OperationChecks
OperationChecks stores supplementary review cases associated with operational requests. Multiple cases may be associated with the same request. A case is about reviewing supporting information, not about the operation's approval decision itself.

## Pending review meaning
A pending documentary review is an unresolved review case. A request in the operation lifecycle state Pending approval is not necessarily the same thing as an operation that has a pending documentary review; these are separate statuses from separate domains.

## Scope and limitations
This document does not prescribe whether unresolved cases block registration, nor does it define what a returned Boolean flag means. Those facts must come from the stored procedures and their SQL conditions. Do not treat a review document as a substitute for examining a called procedure.
