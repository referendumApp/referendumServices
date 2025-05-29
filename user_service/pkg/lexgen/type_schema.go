//revive:disable:exported
package lexgen

import (
	"fmt"
	"io"
	"log"
	"slices"
	"strings"
)

const (
	Record       = "record"
	Union        = "union"
	Query        = "query"
	Procedure    = "procedure"
	Object       = "object"
	String       = "string"
	Aid          = "aid"
	Integer      = "integer"
	Boolean      = "boolean"
	Float        = "float"
	Array        = "array"
	Subscription = "subscription"
	Ref          = "ref"
	Date         = "datetime"
	Unknown      = "unknown"
	Blob         = "blob"
	Link         = "cid-link"
	Bytes        = "bytes"
	LexBytes     = "util.LexBytes"
	Nil          = "nil"
	Error        = "error"
	Omit         = "omitempty"
)

type OutputType struct {
	Encoding string      `json:"encoding"`
	Schema   *TypeSchema `json:"schema"`
}

type InputType struct {
	Encoding string      `json:"encoding"`
	Schema   *TypeSchema `json:"schema"`
}

// TypeSchema is the content of a lexicon schema file "defs" section.
// https://atproto.com/specs/lexicon
type TypeSchema struct {
	prefix    string // prefix of a major package being processed, e.g. com.atproto
	id        string // parent Schema.ID
	defName   string // parent Schema.Defs[defName] points to this *TypeSchema
	defMap    map[string]*ExtDef
	needsCbor bool
	needsType bool

	Type        string      `json:"type"`
	Key         string      `json:"key"`
	Format      string      `json:"format"`
	Description string      `json:"description"`
	Parameters  *TypeSchema `json:"parameters"`
	Input       *InputType  `json:"input"`
	Output      *OutputType `json:"output"`
	Record      *TypeSchema `json:"record"`

	Ref        string                 `json:"ref"`
	Refs       []string               `json:"refs"`
	Required   []string               `json:"required"`
	Nullable   []string               `json:"nullable"`
	Validate   []string               `json:"validate"`
	Properties map[string]*TypeSchema `json:"properties"`
	MinLength  int                    `json:"minLength"`
	MaxLength  int                    `json:"maxLength"`
	Items      *TypeSchema            `json:"items"`
	Const      any                    `json:"const"`
	Enum       []string               `json:"enum"`
	Closed     bool                   `json:"closed"`

	Default any `json:"default"`
	Minimum any `json:"minimum"`
	Maximum any `json:"maximum"`
}

func (s *TypeSchema) WriteRPC(w io.Writer, typename, inputname string) error {
	pf := printerf(w)
	fname := typename

	params := "ctx context.Context, c *xrpc.Client"
	inpvar := Nil
	inpenc := ""

	if s.Input != nil {
		inpvar = "input"
		inpenc = s.Input.Encoding
		switch s.Input.Encoding {
		case EncodingCBOR, EncodingCAR, EncodingANY, EncodingMP4:
			params = fmt.Sprintf("%s, input io.Reader", params)
		case EncodingJSON:
			params = fmt.Sprintf("%s, input *%s", params, inputname)

		default:
			return fmt.Errorf("unsupported input encoding (RPC input): %q", s.Input.Encoding)
		}
	}

	if s.Parameters != nil {
		if err := orderedMapIter(s.Parameters.Properties, func(name string, t *TypeSchema) error {
			tn, err := s.typeNameForField(name, "", *t)
			if err != nil {
				return err
			}

			// TODO: deal with optional params
			params += fmt.Sprintf(", %s %s", name, tn)
			return nil
		}); err != nil {
			return err
		}
	}

	out := Error
	if s.Output != nil {
		switch s.Output.Encoding {
		case EncodingCBOR, EncodingCAR, EncodingANY, EncodingJSONL, EncodingMP4:
			out = "([]byte, error)"
		case EncodingJSON:
			outname := fname + "_Output"
			if s.Output.Schema.Type == Ref {
				_, outname = s.namesFromRef(s.Output.Schema.Ref)
			}

			out = fmt.Sprintf("(*%s, error)", outname)
		default:
			return fmt.Errorf("unrecognized encoding scheme (RPC output): %q", s.Output.Encoding)
		}
	}

	pf("// %s calls the XRPC method %q.\n", fname, s.id)
	if s.Parameters != nil && len(s.Parameters.Properties) > 0 {
		pf("//\n")
		if err := orderedMapIter(s.Parameters.Properties, func(name string, t *TypeSchema) error {
			if t.Description != "" {
				pf("// %s: %s\n", name, t.Description)
			}
			return nil
		}); err != nil {
			return err
		}
	}
	pf("func %s(%s) %s {\n", fname, params, out)

	outvar := Nil
	errRet := "err"
	outRet := Nil
	if s.Output != nil {
		switch s.Output.Encoding {
		case EncodingCBOR, EncodingCAR, EncodingANY, EncodingJSONL, EncodingMP4:
			pf("buf := new(bytes.Buffer)\n")
			outvar = "buf"
			errRet = "nil, err"
			outRet = "buf.Bytes(), nil"
		case EncodingJSON:
			outname := fname + "_Output"
			if s.Output.Schema.Type == Ref {
				_, outname = s.namesFromRef(s.Output.Schema.Ref)
			}
			pf("\tvar out %s\n", outname)
			outvar = "&out"
			errRet = "nil, err"
			outRet = "&out, nil"
		default:
			return fmt.Errorf("unrecognized output encoding (func signature): %q", s.Output.Encoding)
		}
	}

	queryparams := Nil
	if s.Parameters != nil {
		queryparams = "params"
		pf(`
	params := map[string]interface{}{
`)
		if err := orderedMapIter(s.Parameters.Properties, func(name string, t *TypeSchema) error {
			pf(`"%s": %s,
`, name, name)
			return nil
		}); err != nil {
			return err
		}
		pf("}\n")
	}

	var reqtype string
	switch s.Type {
	case Procedure:
		reqtype = "xrpc.Procedure"
	case Query:
		reqtype = "xrpc.Query"
	default:
		return fmt.Errorf("can only generate RPC for Query or Procedure (got %s)", s.Type)
	}

	pf(
		"\tif err := c.Do(ctx, %s, %q, \"%s\", %s, %s, %s); err != nil {\n",
		reqtype,
		inpenc,
		s.id,
		queryparams,
		inpvar,
		outvar,
	)
	pf("\t\treturn %s\n", errRet)
	pf("\t}\n\n")
	pf("\treturn %s\n", outRet)
	pf("}\n\n")

	return nil
}

func (s *TypeSchema) WriteHandlerStub(w io.Writer, fname, shortname, impname string) error {
	pf := printerf(w)
	paramtypes := []string{"ctx context.Context"}
	if s.Type == Query && s.Parameters != nil {
		var required map[string]bool
		if s.Parameters.Required != nil {
			required = make(map[string]bool)
			for _, r := range s.Required {
				required[r] = true
			}
		}
		if err := orderedMapIter(s.Parameters.Properties, func(k string, t *TypeSchema) error {
			switch t.Type {
			case String:
				paramtypes = append(paramtypes, k+" string")
			case Integer:
				if required != nil && !required[k] {
					paramtypes = append(paramtypes, k+" *int")
				} else {
					paramtypes = append(paramtypes, k+" int")
				}
			case Aid:
				if required != nil && !required[k] {
					paramtypes = append(paramtypes, k+" *atp.Aid")
				} else {
					paramtypes = append(paramtypes, k+" atp.Aid")
				}
			case Float:
				return fmt.Errorf("non-integer numbers currently unsupported")
			case Array:
				paramtypes = append(paramtypes, k+"[]"+t.Items.Type)
			default:
				return fmt.Errorf("unsupported handler parameter type: %s", t.Type)
			}
			return nil
		}); err != nil {
			return err
		}
	}

	returndef := Error
	if s.Output != nil {
		switch s.Output.Encoding {
		case "application/json":
			outname := shortname + "_Output"
			if s.Output.Schema.Type == Ref {
				outname, _ = s.namesFromRef(s.Output.Schema.Ref)
			}
			returndef = fmt.Sprintf("(*%s.%s, error)", impname, outname)
		case "application/cbor", "application/vnd.ipld.car", "*/*":
			returndef = "(io.Reader, error)"
		default:
			return fmt.Errorf("unrecognized output encoding (handler stub): %q", s.Output.Encoding)
		}
	}

	if s.Input != nil {
		switch s.Input.Encoding {
		case "application/json":
			paramtypes = append(paramtypes, fmt.Sprintf("input *%s.%s_Input", impname, shortname))
		case "application/cbor":
			paramtypes = append(paramtypes, "r io.Reader")
		}
	}

	pf("func (s *Server) handle%s(%s) %s {\n", fname, strings.Join(paramtypes, ","), returndef)
	pf("panic(\"not yet implemented\")\n}\n\n")

	return nil
}

func (s *TypeSchema) WriteRPCHandler(w io.Writer, fname, shortname, impname string) error {
	pf := printerf(w)
	tname := shortname

	pf("func (s *Server) Handle%s(c echo.Context) error {\n", fname)

	pf("ctx, span := otel.Tracer(\"server\").Start(c.Request().Context(), %q)\n", "Handle"+fname)
	pf("defer span.End()\n")

	paramtypes := []string{"ctx context.Context"}
	params := []string{"ctx"}
	switch s.Type {
	case Query:
		if s.Parameters != nil {
			// TODO(bnewbold): could be handling 'nullable' here
			required := make(map[string]bool)
			for _, r := range s.Parameters.Required {
				required[r] = true
			}
			for k, v := range s.Parameters.Properties {
				if v.Default != nil {
					required[k] = true
				}
			}
			if err := orderedMapIter(s.Parameters.Properties, func(k string, t *TypeSchema) error {
				switch t.Type {
				case String:
					params = append(params, k)
					paramtypes = append(paramtypes, k+" string")
					pf("%s := c.QueryParam(\"%s\")\n", k, k)
				case Integer:
					params = append(params, k)

					switch {
					case !required[k]:
						paramtypes = append(paramtypes, k+" *int")
						pf(`
              var %s *int
              if p := c.QueryParam("%s"); p != "" {
              %s_val, err := strconv.Atoi(p)
              if err != nil {
              return err
              }
              %s  = &%s_val
              }
              `, k, k, k, k, k)
					case t.Default != nil:
						paramtypes = append(paramtypes, k+" int")
						def, ok := t.Default.(float64)
						if !ok {
							return fmt.Errorf("default value is not a float: %v", t.Default)
						}
						pf(`
              var %s int
              if p := c.QueryParam("%s"); p != "" {
              var err error
              %s, err = strconv.Atoi(p)
              if err != nil {
              return err
              }
              } else {
              %s = %d
              }
              `, k, k, k, k, int(def))
					default:
						paramtypes = append(paramtypes, k+" int")
						pf(`
              %s, err := strconv.Atoi(c.QueryParam("%s"))
              if err != nil {
              return err
              }
              `, k, k)
					}

				case Float:
					return fmt.Errorf("non-integer numbers currently unsupported")
				case Boolean:
					params = append(params, k)

					switch {
					case !required[k]:
						paramtypes = append(paramtypes, k+" *bool")
						pf(`
              var %s *bool
              if p := c.QueryParam("%s"); p != "" {
              %s_val, err := strconv.ParseBool(p)
              if err != nil {
              return err
              }
              %s  = &%s_val
              }
              `, k, k, k, k, k)
					case t.Default != nil:
						paramtypes = append(paramtypes, k+" bool")
						def, ok := t.Default.(bool)
						if !ok {
							return fmt.Errorf("default value is not a bool: %v", t.Default)
						}
						pf(`
              var %s bool
              if p := c.QueryParam("%s"); p != "" {
              var err error
              %s, err = strconv.ParseBool(p)
              if err != nil {
              return err
              }
              } else {
              %s = %v
              }
              `, k, k, k, k, def)
					default:
						paramtypes = append(paramtypes, k+" bool")
						pf(`
              %s, err := strconv.ParseBool(c.QueryParam("%s"))
              if err != nil {
              return err
              }
              `, k, k)
					}

				case Array:
					if t.Items.Type != String {
						return fmt.Errorf("currently only string arrays are supported in query params")
					}
					paramtypes = append(paramtypes, k+" []string")
					params = append(params, k)
					pf(`
            %s := c.QueryParams()["%s"]
            `, k, k)

				default:
					return fmt.Errorf("unsupported handler parameter type: %s", t.Type)
				}
				return nil
			}); err != nil {
				return err
			}
		}
	case Procedure:
		if s.Input != nil {
			intname := impname + "." + tname + "_Input"
			switch s.Input.Encoding {
			case EncodingJSON:
				pf(`
          var body %s
          if err := c.Bind(&body); err != nil {
          return err
          }
          `, intname)
				paramtypes = append(paramtypes, "body *"+intname)
				params = append(params, "&body")
			case EncodingCBOR:
				pf("body := c.Request().Body\n")
				paramtypes = append(paramtypes, "r io.Reader")
				params = append(params, "body")
			case EncodingANY:
				pf("body := c.Request().Body\n")
				pf("contentType := c.Request().Header.Get(\"Content-Type\")\n")
				paramtypes = append(paramtypes, "r io.Reader", "contentType string")
				params = append(params, "body", "contentType")
			case EncodingMP4:
				pf("body := c.Request().Body\n")
				paramtypes = append(paramtypes, "r io.Reader")
				params = append(params, "body")
			default:
				return fmt.Errorf("unrecognized input encoding: %q", s.Input.Encoding)
			}
		}
	default:
		return fmt.Errorf("can only generate handlers for queries or procedures")
	}

	assign := "handleErr"
	returndef := Error
	if s.Output != nil {
		switch s.Output.Encoding {
		case EncodingJSON:
			assign = "out, handleErr"
			outname := tname + "_Output"
			if s.Output.Schema.Type == Ref {
				outname, _ = s.namesFromRef(s.Output.Schema.Ref)
			}
			pf("var out *%s.%s\n", impname, outname)
			returndef = fmt.Sprintf("(*%s.%s, error)", impname, outname)
		case EncodingCBOR, EncodingCAR, EncodingANY, EncodingJSONL, EncodingMP4:
			assign = "out, handleErr"
			pf("var out io.Reader\n")
			returndef = "(io.Reader, error)"
		default:
			return fmt.Errorf("unrecognized output encoding (RPC output handler): %q", s.Output.Encoding)
		}
	}
	pf("var handleErr error\n")
	pf("// func (s *Server) handle%s(%s) %s\n", fname, strings.Join(paramtypes, ","), returndef)
	pf("%s = s.handle%s(%s)\n", assign, fname, strings.Join(params, ","))
	pf("if handleErr != nil {\nreturn handleErr\n}\n")

	if s.Output != nil {
		switch s.Output.Encoding {
		case EncodingJSON:
			pf("return c.JSON(200, out)\n}\n\n")
		case EncodingANY:
			pf("return c.Stream(200, \"application/octet-stream\", out)\n}\n\n")
		case EncodingCBOR:
			pf("return c.Stream(200, \"application/octet-stream\", out)\n}\n\n")
		case EncodingCAR:
			pf("return c.Stream(200, \"application/vnd.ipld.car\", out)\n}\n\n")
		case EncodingJSONL:
			pf("return c.Stream(200, \"application/jsonl\", out)\n}\n\n")
		case EncodingMP4:
			pf("return c.Stream(200, \"video/mp4\", out)\n}\n\n")
		default:
			return fmt.Errorf("unrecognized output encoding (RPC output handler return): %q", s.Output.Encoding)
		}
	} else {
		pf("return nil\n}\n\n")
	}

	return nil
}

func (s *TypeSchema) namesFromRef(r string) (string, string) {
	ts, err := s.lookupRef(r)
	if err != nil {
		panic(err)
	}

	if ts.prefix == "" {
		panic(fmt.Sprintf("no prefix for referenced type: %s", ts.id))
	}

	if s.prefix == "" {
		panic(fmt.Sprintf("no prefix for referencing type: %q %q", s.id, s.defName))
	}

	// TODO: probably not technically correct, but i'm kinda over how lexicon
	// tries to enforce application logic in a schema language
	if ts.Type == String {
		return "INVALID", String
	}

	var pkg string
	if ts.prefix != s.prefix {
		pkg = importNameForPrefix(ts.prefix) + "."
	}

	tname := pkg + ts.TypeName()
	vname := tname
	if strings.Contains(vname, ".") {
		// Trim the package name from the variable name
		vname = strings.Split(vname, ".")[1]
	}

	return vname, tname
}

func (s *TypeSchema) TypeName() string {
	if s.id == "" {
		panic("type schema hint fields not set")
	}
	if s.prefix == "" {
		panic("why no prefix?")
	}
	n := nameFromID(s.id, s.prefix)
	if s.defName != Main {
		n += "_" + capitalizeFirst(s.defName)
	}

	if s.Type == Array {
		n = "[]" + n

		if s.Items.Type == Union {
			n += "_Elem"
		}
	}

	return n
}

// name: enclosing type name
// k: field name
// v: field TypeSchema
func (s *TypeSchema) typeNameForField(name, k string, v TypeSchema) (string, error) {
	switch v.Type {
	case String:
		return String, nil
	case Float:
		return "float64", nil
	case Integer:
		return "int64", nil
	case Aid:
		return "atp.Aid", nil
	case Boolean:
		return "bool", nil
	case Object:
		return "*" + name + "_" + capitalizeFirst(k), nil
	case Ref:
		_, tn := s.namesFromRef(v.Ref)
		if tn[0] == '[' {
			return tn, nil
		}
		return "*" + tn, nil
	case Date:
		// TODO: maybe do a native type?
		return String, nil
	case Unknown:
		// NOTE: sometimes a record, for which we want LexiconTypeDecoder, sometimes any object
		if k == "didDoc" || k == "plcOp" {
			return "interface{}", nil
		} else {
			return "*util.LexiconTypeDecoder", nil
		}
	case Union:
		return "*" + name + "_" + capitalizeFirst(k), nil
	case Blob:
		return "*util.LexBlob", nil
	case Array:
		subt, err := s.typeNameForField(name+"_"+capitalizeFirst(k), "Elem", *v.Items)
		if err != nil {
			return "", err
		}

		return "[]" + subt, nil
	case Link:
		return "util.LexLink", nil
	case Bytes:
		return LexBytes, nil
	default:
		return "", fmt.Errorf("field %q in %s has unsupported type name (%s)", k, name, v.Type)
	}
}

func (ts *TypeSchema) lookupRef(ref string) (*TypeSchema, error) {
	fqref := ref
	if strings.HasPrefix(ref, "#") {
		log.Println("updating fqref: ", ts.id)
		fqref = ts.id + ref
	}

	if strings.HasPrefix(fqref, Bsky) {
		return &TypeSchema{
			defName: Main,
			id:      fqref,
			prefix:  Bsky,
		}, nil
	}

	if strings.HasPrefix(fqref, AtProto) {
		return &TypeSchema{
			defName: Main,
			id:      fqref,
			prefix:  AtProto,
		}, nil
	}

	rr, ok := ts.defMap[fqref]
	if !ok {
		log.Println(ts.defMap)
		panic(fmt.Sprintf("no such ref: %q", fqref))
	}

	return rr.Type, nil
}

// name is the top level type name from outputType
// WriteType is only called on a top level TypeSchema
func (ts *TypeSchema) WriteType(name string, w io.Writer) error {
	if err := ts.writeTypeDefinition(name, w); err != nil {
		return err
	}

	if err := ts.writeTypeMethods(name, w); err != nil {
		return err
	}

	return nil
}

// name is the top level type name from outputType
// writeTypeDefinition is not called recursively, but only on a top level TypeSchema
func (ts *TypeSchema) writeTypeDefinition(name string, w io.Writer) error {
	pf := printerf(w)

	switch {
	case strings.HasSuffix(name, "_Output"):
		pf("// %s is the output of a %s call.\n", name, ts.id)
	case strings.HasSuffix(name, "Input"):
		pf("// %s is the input argument to a %s call.\n", name, ts.id)
	case ts.defName != "":
		pf("// %s is a %q in the %s schema.\n", name, ts.defName, ts.id)
	}
	if ts.Description != "" {
		pf("//\n// %s\n", ts.Description)
	}

	switch ts.Type {
	case String:
		// TODO: deal with max length
		pf("type %s string\n", name)
	case Float:
		pf("type %s float64\n", name)
	case Integer:
		pf("type %s int64\n", name)
	case Aid:
		pf("type %s atp.Aid\n", name)
	case Boolean:
		pf("type %s bool\n", name)
	case Object:
		if ts.needsType {
			pf("//\n// RECORDTYPE: %s\n", name)
		}

		pf("type %s struct {\n", name)

		if ts.needsType {
			var omit string
			if ts.id == "com.atproto.repo.strongRef" { // TODO: hack
				omit = "," + Omit
			}
			cval := ts.id
			if ts.defName != "" && ts.defName != Main {
				cval += "#" + ts.defName
			}
			pf(
				"\tLexiconTypeID string `json:\"$type\" cborgen:\"$type,const=%s%s\" validate:\"required\"`\n",
				cval,
				omit,
			)
		}

		required := make(map[string]bool)
		for _, req := range ts.Required {
			required[req] = true
		}

		nullable := make(map[string]bool)
		for _, req := range ts.Nullable {
			nullable[req] = true
		}

		if err := orderedMapIter(ts.Properties, func(k string, v *TypeSchema) error {
			goname := capitalizeFirst(k)

			tname, err := ts.typeNameForField(name, k, *v)
			if err != nil {
				return err
			}

			var ptr string
			var omit string
			var valTags strings.Builder
			if !required[k] {
				omit = "," + Omit
				if !strings.HasPrefix(tname, "*") && !strings.HasPrefix(tname, "[]") {
					ptr = "*"
				}
				if nullable[k] {
					omit = ""
					if !strings.HasPrefix(tname, "*") && !strings.HasPrefix(tname, "[]") {
						ptr = "*"
					}
				}
				valTags.WriteString(Omit)
			} else {
				if nullable[k] {
					return fmt.Errorf("%s cannot be required and a nullable field", k)
				}
				valTags.WriteString("required")
			}

			if v.Format != "" {
				valTags.WriteString(",")
				valTags.WriteString(v.Format)
			}
			if v.MinLength != 0 {
				valTags.WriteString(",")
				valTags.WriteString(fmt.Sprintf("min=%d", v.MinLength))
			}
			if v.MaxLength != 0 {
				valTags.WriteString(",")
				valTags.WriteString(fmt.Sprintf("max=%d", v.MaxLength))
			}
			if len(v.Validate) > 0 {
				valTags.WriteString(",")
				valTags.WriteString(strings.Join(v.Validate, ","))
			}
			for _, enum := range v.Enum {
				valTags.WriteString(",")
				valTags.WriteString(fmt.Sprintf("oneof=%s", enum))
			}

			jsonOmit, cborOmit := omit, omit

			// Don't generate pointers to lexbytes, as it's already a pointer.
			if ptr == "*" && tname == LexBytes {
				ptr = ""
			}

			// TODO: hard-coded hacks for now, making this type (with underlying type []byte)
			// be omitempty.
			if ptr == "" && tname == LexBytes {
				jsonOmit = "," + Omit
				cborOmit = "," + Omit
			}

			if name == "LabelDefs_SelfLabels" && k == "values" {
				// TODO: regularize weird hack?
				cborOmit += ",preservenil"
			}

			if v.Description != "" {
				pf("\t// %s: %s\n", k, v.Description)
			}
			var tags strings.Builder
			tags.WriteString(fmt.Sprintf("\t%s %s%s `json:\"%s%s\" cborgen:\"%s%s\"", goname, ptr, tname, k, jsonOmit, k, cborOmit))
			if valTags.Len() > 0 {
				tags.WriteString(fmt.Sprintf(" validate:\"%s\"", valTags.String()))
			}
			tags.WriteString("`\n")

			pf(tags.String())
			return nil
		}); err != nil {
			return err
		}

		pf("}\n\n")

	case Array:
		tname, err := ts.typeNameForField(name, "elem", *ts.Items)
		if err != nil {
			return err
		}

		pf("type %s []%s\n", name, tname)

	case Union:
		if len(ts.Refs) > 0 {
			pf("type %s struct {\n", name)
			for _, r := range ts.Refs {
				vname, tname := ts.namesFromRef(r)
				pf("\t%s *%s\n", vname, tname)
			}
			pf("}\n\n")
		}
	default:
		return fmt.Errorf("%s has unrecognized type: %s", name, ts.Type)
	}

	return nil
}

func (ts *TypeSchema) writeTypeMethods(name string, w io.Writer) error {
	switch ts.Type {
	case String, Float, Array, Boolean, Integer, Aid, Object:
		return nil
	case Union:
		if len(ts.Refs) == 0 {
			return fmt.Errorf("%q unsupported for marshaling", name)
		}

		reft, err := ts.lookupRef(ts.Refs[0])
		if err != nil {
			return err
		}

		if reft.Type == String {
			return nil
		}

		if err := ts.writeJsonMarshalerEnum(name, w); err != nil {
			return err
		}

		if err := ts.writeJsonUnmarshalerEnum(name, w); err != nil {
			return err
		}

		if ts.needsCbor {
			if err := ts.writeCborMarshalerEnum(name, w); err != nil {
				return err
			}

			if err := ts.writeCborUnmarshalerEnum(name, w); err != nil {
				return err
			}
		}

		return nil
	default:
		return fmt.Errorf("%q has unrecognized type: %s", name, ts.Type)
	}
}

func (ts *TypeSchema) writeStorageMethods(name string, collection string, w io.Writer) error {
	pf := printerf(w)
	pf("func (t %s) NSID() string {\n", name)
	pf("\treturn \"%s\"\n}", collection)

	pf("\n\nfunc (t %s) Key() string {\n", name)
	switch {
	case ts.Key == "tid":
		pf("\treturn repo.NextTID()")
	case strings.HasPrefix(ts.Key, "literal:"):
		keySplit := strings.Split(ts.Key, ":")
		pf("\treturn \"%s\"", keySplit[1])
	case strings.HasPrefix(ts.Key, "lid:"):
		keySplit := strings.Split(ts.Key, ":")[1:]
		for _, key := range keySplit {
			if !slices.Contains(ts.Record.Required, key) {
				return fmt.Errorf("LID record key fields must be required: %s", key)
			}
			if ts.Record.Properties[key].Type != String {
				return fmt.Errorf("LID record key fields must be a string type: %s", key)
			}
		}
		keyOne := fmt.Sprintf("t.%s", capitalizeFirst(keySplit[0]))
		keyTwo := fmt.Sprintf("t.%s", capitalizeFirst(keySplit[1]))
		keyThree := fmt.Sprintf("t.%s", capitalizeFirst(keySplit[2]))

		pf("\treturn repo.LID(%s, %s, %s)", keyOne, keyTwo, keyThree)
	default:
		return fmt.Errorf("invalid key type: %s", ts.Key)
	}
	pf("\n}")

	return nil
}

func (ts *TypeSchema) writeJsonMarshalerEnum(name string, w io.Writer) error {
	pf := printerf(w)
	pf("func (t *%s) MarshalJSON() ([]byte, error) {\n", name)

	for _, e := range ts.Refs {
		vname, _ := ts.namesFromRef(e)
		if strings.HasPrefix(e, "#") {
			e = ts.id + e
		}

		pf("\tif t.%s != nil {\n", vname)
		pf("\tt.%s.LexiconTypeID = %q\n", vname, e)
		pf("\t\treturn json.Marshal(t.%s)\n\t}\n", vname)
	}

	pf("\treturn nil, fmt.Errorf(\"cannot marshal empty enum\")\n}\n\n")
	return nil
}

func (ts *TypeSchema) writeJsonUnmarshalerEnum(name string, w io.Writer) error {
	pf := printerf(w)
	pf("func (t *%s) UnmarshalJSON(b []byte) (error) {\n", name)
	pf("\ttyp, err := util.TypeExtract(b)\n")
	pf("\tif err != nil {\n\t\treturn err\n\t}\n\n")
	pf("\tswitch typ {\n")
	for _, e := range ts.Refs {
		if strings.HasPrefix(e, "#") {
			e = ts.id + e
		}

		vname, goname := ts.namesFromRef(e)

		pf("\t\tcase \"%s\":\n", e)
		pf("\t\t\tt.%s = new(%s)\n", vname, goname)
		pf("\t\t\treturn json.Unmarshal(b, t.%s)\n", vname)
	}

	if ts.Closed {
		pf(`
			default:
				return fmt.Errorf("closed enums must have a matching value")
		`)
	} else {
		pf(`
			default:
				return nil
		`)
	}

	pf("\t}\n")
	pf("}\n\n")

	return nil
}

func (ts *TypeSchema) writeCborMarshalerEnum(name string, w io.Writer) error {
	pf := printerf(w)
	pf("func (t *%s) MarshalCBOR(w io.Writer) error {\n", name)
	pf(`
	if t == nil {
		_, err := w.Write(cbg.CborNull)
		return err
	}
`)

	for _, e := range ts.Refs {
		vname, _ := ts.namesFromRef(e)
		pf("\tif t.%s != nil {\n", vname)
		pf("\t\treturn t.%s.MarshalCBOR(w)\n\t}\n", vname)
	}

	pf("\treturn fmt.Errorf(\"cannot cbor marshal empty enum\")\n}\n\n")
	return nil
}

func (ts *TypeSchema) writeCborUnmarshalerEnum(name string, w io.Writer) error {
	pf := printerf(w)
	pf("func (t *%s) UnmarshalCBOR(r io.Reader) error {\n", name)
	pf("\ttyp, b, err := util.CborTypeExtractReader(r)\n")
	pf("\tif err != nil {\n\t\treturn err\n\t}\n\n")
	pf("\tswitch typ {\n")
	for _, e := range ts.Refs {
		if strings.HasPrefix(e, "#") {
			e = ts.id + e
		}

		vname, goname := ts.namesFromRef(e)

		pf("\t\tcase \"%s\":\n", e)
		pf("\t\t\tt.%s = new(%s)\n", vname, goname)
		pf("\t\t\treturn t.%s.UnmarshalCBOR(bytes.NewReader(b))\n", vname)
	}

	if ts.Closed {
		pf(`
			default:
				return fmt.Errorf("closed enums must have a matching value")
		`)
	} else {
		pf(`
			default:
				return nil
		`)
	}

	pf("\t}\n")
	pf("}\n\n")

	return nil
}
