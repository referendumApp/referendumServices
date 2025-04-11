// Code generated by cmd/lexgen (see Makefile's lexgen); DO NOT EDIT.

package referendumapp

// schema: com.referendumapp.server.createAccount

// ServerCreateAccount_Input is the input argument to a com.referendumapp.server.createAccount call.
type ServerCreateAccount_Input struct {
	// did: Pre-existing atproto DID, being imported to a new account.
	Did         *string `json:"did,omitempty" cborgen:"did,omitempty" validate:"omitempty,did"`
	DisplayName *string `json:"displayName,omitempty" cborgen:"displayName,omitempty" validate:"omitempty,max=100"`
	Email       string  `json:"email" cborgen:"email" validate:"required,email,max=100"`
	// handle: Requested handle for the account.
	Handle string `json:"handle" cborgen:"handle" validate:"required,handle,min=8,max=100"`
	// password: Initial account password. May need to meet instance-specific password strength requirements.
	Password string `json:"password" cborgen:"password" validate:"required,strongpassword,min=8,max=100"`
	// plcOp: A signed DID PLC operation to be submitted as part of importing an existing account to this instance. NOTE: this optional field may be updated when full account migration is implemented.
	PlcOp *interface{} `json:"plcOp,omitempty" cborgen:"plcOp,omitempty" validate:"omitempty"`
	// recoveryKey: DID PLC rotation key (aka, recovery key) to be included in PLC creation operation.
	RecoveryKey       *string `json:"recoveryKey,omitempty" cborgen:"recoveryKey,omitempty" validate:"omitempty"`
	VerificationPhone *string `json:"verificationPhone,omitempty" cborgen:"verificationPhone,omitempty" validate:"omitempty,e164"`
}

// ServerCreateAccount_Output is the output of a com.referendumapp.server.createAccount call.
//
// Account login session returned on successful account creation.
type ServerCreateAccount_Output struct {
	AccessJwt *string `json:"accessJwt,omitempty" cborgen:"accessJwt,omitempty" validate:"omitempty"`
	// did: The DID of the new account.
	Did string `json:"did" cborgen:"did" validate:"required,did"`
	// didDoc: Complete DID document.
	DidDoc      *interface{} `json:"didDoc,omitempty" cborgen:"didDoc,omitempty" validate:"omitempty"`
	DisplayName *string      `json:"displayName,omitempty" cborgen:"displayName,omitempty" validate:"omitempty,min=8,max=100"`
	Handle      string       `json:"handle" cborgen:"handle" validate:"required,handle,min=8,max=100"`
	RefreshJwt  *string      `json:"refreshJwt,omitempty" cborgen:"refreshJwt,omitempty" validate:"omitempty"`
}
