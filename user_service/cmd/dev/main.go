//go:build dev

package main

import (
	"io/fs"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"slices"
	"syscall"
	"time"

	"github.com/fsnotify/fsnotify"
	"github.com/referendumApp/referendumServices/pkg/common"
)

var (
	appPath          = "/cmd/api"
	buildCmd         = "go"
	buildArgs        = [4]string{"build", "-o"}
	debounceInterval = 50 * time.Millisecond
	watchExts        = []string{".go"}
	ignoreDirs       = []string{".github", ".vscode", "data_service"}
	binaryName       string
)

func main() {
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		log.Fatalf("Failed to initialize watcher: %v (%T)", err, err)
	}
	defer watcher.Close()

	projectRoot, err := common.FindProjectRoot()
	if err != nil {
		log.Fatalf("Failed to find project Root: %v (%T)", err, err)
	}
	binaryName, err = common.GetEnvOrFail("BINARY_PATH")
	if err != nil {
		log.Fatalf("Failed to get binary name: %v", err)
	}
	binaryPath := filepath.Join(projectRoot, binaryName)
	buildArgs[2] = binaryPath
	buildArgs[3] = filepath.Join(projectRoot, appPath)

	if err := filepath.WalkDir(projectRoot, watchDir(projectRoot, watcher)); err != nil {
		log.Fatal(err)
	}

	cmd, err := buildAndStartApp(binaryPath)
	if err != nil {
		log.Fatalf("Failed to build initial binary: %v (%T)", err, err)
	}

	var lastBuild time.Time
	for {
		select {
		// Only rebuild the app for these specific filesystem events
		case event := <-watcher.Events:
			if isWatchableFile(event.Name) &&
				(event.Has(fsnotify.Write) ||
					event.Has(fsnotify.Create) ||
					event.Has(fsnotify.Rename) ||
					event.Has(fsnotify.Remove)) {

				if time.Since(lastBuild) > debounceInterval {
					log.Printf("Modified file: %s, Operation: %s", event.Name, event.Op)
					if cmd != nil && cmd.Process != nil {
						// Try to gracefully shutdown the process
						if err := cmd.Process.Signal(syscall.SIGTERM); err != nil {
							log.Printf("Failed to send SIGTERM: %v (%T)", err, err)
							// Fall back to force kill
							if err := cmd.Process.Kill(); err != nil {
								log.Printf("Failed to force kill: %v (%T)", err, err)
							}
						}
						// Wait a bit for process to clean up
						time.Sleep(100 * time.Millisecond)
					}

					// Rebuild and restart
					time.Sleep(100 * time.Millisecond)
					cmd = rebuildAndStartApp(binaryPath)
				}
				lastBuild = time.Now()
			}
		case err := <-watcher.Errors:
			log.Printf("Watcher error: %v", err)
		}
	}

}

// Returns a callback function which only adds the relevant directories to the Watcher
func watchDir(projectRoot string, watcher *fsnotify.Watcher) fs.WalkDirFunc {
	return func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}

		if d.IsDir() {
			relPath, err := filepath.Rel(projectRoot, path)
			if err != nil {
				return err
			}

			for _, ignore := range ignoreDirs {
				if matched, _ := filepath.Match(ignore, filepath.Base(relPath)); matched {
					return filepath.SkipDir
				}
			}

			return watcher.Add(path)
		}
		return nil
	}
}

func isWatchableFile(filename string) bool {
	ext := filepath.Ext(filename)
	return slices.Contains(watchExts, ext)
}

func buildAppCmd() *exec.Cmd {
	cmd := exec.Command(buildCmd, buildArgs[:]...)
	cmd.Stderr = os.Stderr
	cmd.Stdout = os.Stdout

	return cmd
}

func startApp(runCmd string) *exec.Cmd {
	cmd := exec.Command(runCmd)
	cmd.Stderr = os.Stderr
	cmd.Stdout = os.Stdout

	if err := cmd.Start(); err != nil {
		log.Printf("Error starting app: %v (%T)", err, err)
		return nil
	}

	return cmd
}

func buildAndStartApp(binaryPath string) (*exec.Cmd, error) {
	// Check if binary exists
	if _, err := os.Stat(binaryPath); os.IsNotExist(err) {
		log.Println("Binary not found, building...")
		cmd := buildAppCmd()
		if err := cmd.Run(); err != nil {
			return nil, err
		}
	}

	return startApp(binaryPath), nil
}

func rebuildAndStartApp(runCmd string) *exec.Cmd {
	log.Println("Rebuilding...")
	cmd := buildAppCmd()
	if err := cmd.Run(); err != nil {
		log.Printf("Error building app: %v (%T)", err, err)
		return nil
	}

	return startApp(runCmd)
}
