package main

import (
	"go.k6.io/k6/cmd"
	_ "kaas.local/tenant-r2-native"
)

func main() { cmd.Execute() }
