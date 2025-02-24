package server

import (
	"fmt"
	"net/http"

	"github.com/referendumApp/referendumServices/internal/models"
)

func handleFollow(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		err := fmt.Errorf("%s method not allowed", r.Method)
		http.Error(w, err.Error(), http.StatusMethodNotAllowed)
		return
	}

	req, err := decodeAndValidate[*models.FollowRequest](r)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	fmt.Println(r.Context().Value("email"))
	fmt.Println(req.UserMessage)
}
