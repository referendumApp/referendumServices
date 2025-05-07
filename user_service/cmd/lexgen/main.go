package main

import (
	"errors"
	"fmt"
	"io/fs"
	"log"
	"os"
	"path/filepath"
	"strings"

	lex "github.com/referendumApp/referendumServices/pkg/lexgen"
	cli "github.com/urfave/cli/v2"
)

func findSchemas(dir string, out []string) ([]string, error) {
	err := filepath.Walk(dir, func(path string, info fs.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if info.IsDir() {
			return nil
		}

		if strings.HasSuffix(path, ".json") {
			out = append(out, path)
		}

		return nil
	})
	if err != nil {
		return out, err
	}

	return out, nil
}

// for direct .json lexicon files or directories containing lexicon .json files, get one flat list of all paths to .json files
func expandArgs(args []string) ([]string, error) {
	var out []string
	for _, a := range args {
		st, err := os.Stat(a)
		if err != nil {
			return nil, err
		}
		if st.IsDir() {
			out, err = findSchemas(a, out)
			if err != nil {
				return nil, err
			}
		} else if strings.HasSuffix(a, ".json") {
			out = append(out, a)
		}
	}

	return out, nil
}

func main() {
	app := cli.NewApp()
	app.Name = "lexgen"
	app.Usage = "JSON to Go struct lexicon generator"

	app.Flags = []cli.Flag{
		&cli.StringFlag{
			Name:  "outdir",
			Usage: "Output directory",
		},
		&cli.BoolFlag{
			Name:  "gen-server",
			Usage: "Generate API routes",
		},
		&cli.BoolFlag{
			Name:  "gen-handlers",
			Usage: "Generate API handlers",
		},
		&cli.StringSliceFlag{
			Name:  "types-import",
			Usage: "Map of field names to types separated by ':'",
		},
		&cli.StringFlag{
			Name:  "package",
			Usage: "Package name",
			Value: "schemagen",
		},
		&cli.StringFlag{
			Name:  "build",
			Usage: "JSON literal containing the outdir, package, prefix, and import keys",
			Value: "",
		},
		&cli.StringFlag{
			Name:  "build-file",
			Usage: "Path to a JSON file containing an array of objects containing the outdir, package, prefix, and import keys",
			Value: "",
		},
	}
	app.Action = func(cctx *cli.Context) error {
		paths, err := expandArgs(cctx.Args().Slice())
		if err != nil {
			return err
		}

		if len(paths) == 0 {
			return errors.New("please provide directory or json schema file paths as an arg")
		}

		var schemas []*lex.Schema
		for _, arg := range paths {
			if strings.HasSuffix(arg, "com/atproto/temp/importRepo.json") {
				log.Printf("skipping schema: %s\n", arg)
				continue
			}
			s, schemaErr := lex.ReadSchema(arg)
			if schemaErr != nil {
				return fmt.Errorf("failed to read file %q: %w", arg, schemaErr)
			}

			schemas = append(schemas, s)
		}

		buildLiteral := cctx.String("build")
		buildPath := cctx.String("build-file")
		var packages []lex.Package
		if buildLiteral == "" && buildPath == "" {
			return errors.New("at least one of the --build or --build-file flags must be set")
		}

		if buildLiteral != "" {
			if buildPath != "" {
				return errors.New("must not set both --build and --build-file")
			}
			packages, err = lex.ParsePackages([]byte(buildLiteral))
			if err != nil {
				return fmt.Errorf("--build error, %w", err)
			}
		} else {
			blob, err := os.ReadFile(buildPath)
			if err != nil {
				return fmt.Errorf("--build-file error, %w", err)
			}
			packages, err = lex.ParsePackages(blob)
			if err != nil {
				return fmt.Errorf("--build-file error, %w", err)
			}
		}

		if len(packages) == 0 {
			return errors.New("must specify at least one Package{}")
		}

		if cctx.Bool("gen-server") {
			pkgname := cctx.String("package")
			outdir := cctx.String("outdir")
			if outdir == "" {
				return fmt.Errorf("must specify output directory (--outdir)")
			}
			defmap := lex.BuildExtDefMap(schemas, packages)
			_ = defmap

			paths := cctx.StringSlice("types-import")
			importmap := make(map[string]string)
			for _, p := range paths {
				parts := strings.Split(p, ":")
				importmap[parts[0]] = parts[1]
			}

			handlers := cctx.Bool("gen-handlers")

			if err := lex.CreateHandlerStub(pkgname, importmap, outdir, schemas, handlers); err != nil {
				return err
			}
		} else {
			return lex.Run(schemas, packages)
		}

		return nil
	}

	if err := app.Run(os.Args); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
