'use strict';

let solium = require('solium')
let fs = require('fs')
let path = require('path')

let tempPath = process.argv[2]
// let filePath = process.argv[3]
let verbose = process.argv[4] !== undefined

if (tempPath === undefined) {
  console.log('Error:', 'File path is undefined.')
  process.exit(1)
}

let pluginFolder = path.dirname(__dirname)

fs.readFile(tempPath, 'utf8', (err, data) => {
  let errorObjects = solium.lint(data, JSON.parse(fs.readFileSync(path.join(pluginFolder, 'scripts', '.soliumrc.json'), 'utf8')))

  console.log('*** Solium results ***')
  errorObjects.forEach((err) => {
    if (verbose) console.log(err)
    console.log([err.line, err.column, err.type, err.message].join(':'))
  })
})
