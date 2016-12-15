'use strict';

let solium = require('solium')
let fs = require('fs')
let path = require('path')

let tempPath = process.argv[2]
let filePath = process.argv[3]
let verbose = process.argv[4] !== undefined

if (tempPath === undefined) {
  console.log('Error:', 'File path is undefined.')
  process.exit(1)
}

let pluginFolder = path.dirname(__dirname)

function getSoliumConfiguration(filepath) {
  let configFile = getSoliumUserConfiguration(filepath)
  if (configFile === null) {
    return getSoliumDefaultConfiguration()
  }

  return fs.readFileSync(configFile, 'utf8')
}

function getSoliumUserConfiguration(filepath) {
  let folder = path.dirname(filepath)
  let configFile = path.join(folder, '/', '.soliumrc.json')
  
  if (fs.existsSync(configFile)) {
    return configFile
  }
  
  if (folder === '/') {
    return null
  }

  return getSoliumUserConfiguration(folder)
}

function getSoliumDefaultConfiguration() {
  return fs.readFileSync(path.join(pluginFolder, 'scripts', '.soliumrc.json'), 'utf8')
}

fs.readFile(tempPath, 'utf8', (err, data) => {
  let configFile = getSoliumConfiguration(filePath)
  let errorObjects = solium.lint(data, JSON.parse(configFile))

  console.log('*** Solium results ***')
  errorObjects.forEach((err) => {
    if (verbose) console.log(err)
    console.log([err.line, err.column, err.type, err.message].join(':'))
  })
})
