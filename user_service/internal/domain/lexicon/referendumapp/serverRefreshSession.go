// Code generated by cmd/lexgen (see Makefile's lexgen); DO NOT EDIT.

package referendumapp

// schema: com.referendumapp.server.refreshSession

// ServerRefreshSession_Input is the input argument to a com.referendumapp.server.refreshSession call.
type ServerRefreshSession_Input struct {
	RefreshToken string `json:"refreshToken" cborgen:"refreshToken" validate:"required"`
}

// ServerRefreshSession_Output is the output of a com.referendumapp.server.refreshSession call.
type ServerRefreshSession_Output struct {
	AccessToken  string `json:"accessToken" cborgen:"accessToken" validate:"required"`
	RefreshToken string `json:"refreshToken" cborgen:"refreshToken" validate:"required"`
	TokenType    string `json:"tokenType" cborgen:"tokenType" validate:"required"`
}
