package app

type AdminPayload struct {
	Handle string `json:"handle" validate:"required"`
	Name   string `json:"name"   validate:"required"`
	Email  string `json:"email"  validate:"required,email"`
}

type AdminResponse struct {
	Handle   string `json:"handle"`
	Did      string `json:"did"`
	ApiToken string `json:"apiToken"`
}
